"""
Bank Statement Validation Service
Implements validation rules for bank statement imports
"""
from datetime import datetime, date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.db.models.bank_statement_batch import BankStatementBatch
from app.db.models.bank_transaction import BankTransaction
import calendar


class ValidationResult:
    """Result of validation with errors and warnings"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, message: str):
        """Add a blocking error"""
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a non-blocking warning"""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any blocking errors"""
        return len(self.errors) > 0
    
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)"""
        return not self.has_errors()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'is_valid': self.is_valid(),
        }


class BankStatementValidator:
    """Validator for bank statement imports"""
    
    @staticmethod
    def validate_batch(
        db: Session,
        bank_account_id: str,
        year: int,
        month: int,
        transactions: List[Dict],
    ) -> ValidationResult:
        """
        Validate a bank statement batch before import
        
        Checks:
        1. No existing batch for same account + year + month
        2. All transaction dates fall within the selected month
        3. No duplicate fingerprints exist
        4. Warnings for incomplete month coverage
        """
        result = ValidationResult()
        
        # ===== HARD ERROR: Check for existing batch =====
        existing_batch = db.query(BankStatementBatch).filter(
            BankStatementBatch.bank_account_id == bank_account_id,
            BankStatementBatch.year == year,
            BankStatementBatch.month == month,
        ).first()
        
        if existing_batch:
            result.add_error(
                f"A statement batch for {year}-{month:02d} already exists for this bank account. "
                f"Batch ID: {existing_batch.id}, Status: {existing_batch.status}"
            )
            # Return early if batch exists - other validations don't matter
            return result
        
        if not transactions:
            result.add_error("No valid transactions found in CSV file")
            return result
        
        # Get month date range
        first_day_of_month = date(year, month, 1)
        last_day_of_month = date(year, month, calendar.monthrange(year, month)[1])
        
        # Track transaction dates for validation
        transaction_dates = []
        
        # ===== HARD ERROR: Check all transaction dates fall within selected month =====
        for idx, txn in enumerate(transactions):
            txn_date = txn['effective_at'].date() if isinstance(txn['effective_at'], datetime) else txn['effective_at']
            transaction_dates.append(txn_date)
            
            if txn_date.year != year or txn_date.month != month:
                result.add_error(
                    f"Transaction #{idx + 1} (date: {txn_date.isoformat()}) falls outside selected month {year}-{month:02d}"
                )
        
        # If there are date errors, return early
        if result.has_errors():
            return result
        
        # ===== WARNING: Check for incomplete month coverage =====
        if transaction_dates:
            first_txn_date = min(transaction_dates)
            last_txn_date = max(transaction_dates)
            
            # Check if first transaction is after day 1
            if first_txn_date > first_day_of_month:
                days_missing = (first_txn_date - first_day_of_month).days
                result.add_warning(
                    f"First transaction is on {first_txn_date.isoformat()}, "
                    f"which is {days_missing} day(s) after the start of the month"
                )
            
            # Check if last transaction is before last day of month
            if last_txn_date < last_day_of_month:
                days_missing = (last_day_of_month - last_txn_date).days
                result.add_warning(
                    f"Last transaction is on {last_txn_date.isoformat()}, "
                    f"which is {days_missing} day(s) before the end of the month"
                )
        
        # ===== WARNING: Check for missing balance column =====
        transactions_with_balance = [txn for txn in transactions if txn.get('balance') is not None]
        if len(transactions_with_balance) == 0:
            result.add_warning("No balance information found in any transaction")
        elif len(transactions_with_balance) < len(transactions):
            missing_count = len(transactions) - len(transactions_with_balance)
            result.add_warning(
                f"{missing_count} transaction(s) are missing balance information"
            )
        
        return result
    
    @staticmethod
    def check_duplicate_fingerprints(
        db: Session,
        bank_account_id: str,
        fingerprints: List[str],
    ) -> ValidationResult:
        """
        Check if any fingerprints already exist for this bank account
        This is a separate check that happens after initial validation
        """
        result = ValidationResult()
        
        # Query for existing fingerprints
        existing_transactions = db.query(BankTransaction).filter(
            BankTransaction.bank_account_id == bank_account_id,
            BankTransaction.fingerprint.in_(fingerprints)
        ).all()
        
        if existing_transactions:
            existing_fps = {txn.fingerprint for txn in existing_transactions}
            duplicate_count = len(existing_fps)
            
            result.add_error(
                f"Found {duplicate_count} duplicate transaction(s) that already exist in the database. "
                f"These transactions may have been imported in a previous batch."
            )
        
        return result
