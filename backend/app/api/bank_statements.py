"""
Bank Statement API Endpoints
Desktop-only admin endpoints for bank statement import
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from app.db.session import get_db
from app.core.deps import get_current_user, require_role
from app.db.models.user import User
from app.db.models.bank_account import BankAccount
from app.db.models.bank_statement_batch import BankStatementBatch
from app.db.models.bank_transaction import BankTransaction
from app.services.csv_parser import CSVParserService
from app.services.bank_statement_validator import BankStatementValidator


router = APIRouter(prefix="/api/bank-statements", tags=["bank-statements"])


# ===== Request/Response Models =====

class BankAccountCreate(BaseModel):
    bank_code: str
    account_no_masked: str
    account_type: str = "CASHFLOW"
    currency: str = "THB"


class BankAccountResponse(BaseModel):
    id: str
    bank_code: str
    account_no_masked: str
    account_type: str
    currency: str
    is_active: bool
    created_at: str
    updated_at: str


class CSVPreviewResponse(BaseModel):
    header_row_index: int
    metadata_rows: List[List[str]]
    transactions: List[dict]
    transaction_count: int
    date_range_start: Optional[str]
    date_range_end: Optional[str]
    validation: dict


class ConfirmImportRequest(BaseModel):
    bank_account_id: str
    year: int
    month: int
    filename: str
    csv_content: str  # Base64 or raw CSV content


class BatchResponse(BaseModel):
    id: str
    bank_account_id: str
    year: int
    month: int
    source_type: str
    original_filename: str
    status: str
    transaction_count: int
    date_range_start: Optional[str]
    date_range_end: Optional[str]
    opening_balance: Optional[float]
    closing_balance: Optional[float]
    warnings: Optional[List[str]]
    uploaded_at: str


# ===== Bank Account Endpoints =====

@router.get("/bank-accounts", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """List all active bank accounts"""
    accounts = db.query(BankAccount).filter(BankAccount.is_active == True).all()
    return [account.to_dict() for account in accounts]


@router.post("/bank-accounts", response_model=BankAccountResponse)
async def create_bank_account(
    data: BankAccountCreate,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """Create a new bank account"""
    account = BankAccount(
        bank_code=data.bank_code,
        account_no_masked=data.account_no_masked,
        account_type=data.account_type,
        currency=data.currency,
        is_active=True,
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    return account.to_dict()


# ===== CSV Upload & Preview Endpoints =====

@router.post("/upload-preview")
async def upload_and_preview_csv(
    bank_account_id: str,
    year: int,
    month: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Upload CSV and get preview with validation
    Does NOT save to database
    """
    # ===== REQUEST INSTRUMENTATION =====
    print("=" * 70)
    print("📤 UPLOAD-PREVIEW REQUEST")
    print("=" * 70)
    print(f"received_form_keys: bank_account_id={bank_account_id}, year={year}, month={month}")
    print(f"received_file_name: {file.filename if file else 'NONE'}")
    print(f"received_file_size_bytes: {file.size if hasattr(file, 'size') else 'UNKNOWN'}")
    print(f"file_content_type: {file.content_type if file else 'NONE'}")
    print("=" * 70)
    
    # ===== VALIDATION: File must exist =====
    if not file or not file.filename:
        raise HTTPException(
            status_code=422,
            detail="CSV file missing"
        )
    
    # Verify bank account exists
    bank_account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # ===== CHECK FOR DUPLICATE BATCH EARLY =====
    existing_batch = db.query(BankStatementBatch).filter(
        BankStatementBatch.bank_account_id == bank_account_id,
        BankStatementBatch.year == year,
        BankStatementBatch.month == month,
    ).first()
    
    if existing_batch:
        raise HTTPException(
            status_code=409,
            detail={
                'message': f"A statement batch for {year}-{month:02d} already exists for this bank account",
                'batch_id': str(existing_batch.id),
                'batch_status': existing_batch.status,
                'uploaded_at': existing_batch.uploaded_at.isoformat() if existing_batch.uploaded_at else None,
            }
        )
    
    # Read CSV content
    try:
        content = await file.read()
        csv_content = content.decode('utf-8-sig')  # Handle BOM
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {str(e)}")
    
    # Parse CSV with diagnostics (ALL ENHANCEMENTS ACTIVE)
    try:
        parsed_data = CSVParserService.parse_csv(csv_content, enable_diagnostics=True)
        diagnostics = parsed_data.get('diagnostics')
    except ValueError as e:
        # Enhanced error response with helpful info
        raise HTTPException(
            status_code=400, 
            detail={
                'message': str(e),
                'hint': 'Please check that the CSV file has proper column headers (Date, Description, Debit/Credit, Balance)',
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    transactions = parsed_data['transactions']
    
    # Log diagnostics in development (console only, not in response unless error)
    if diagnostics:
        print("=" * 60)
        print("📊 CSV PARSER DIAGNOSTICS")
        print("=" * 60)
        print(f"Delimiter detected: '{diagnostics.detected_delimiter}'")
        print(f"Header row index: {diagnostics.header_row_index}")
        print(f"Detected columns: {diagnostics.detected_columns}")
        print(f"Total rows: {diagnostics.total_rows}")
        print(f"Parsed rows: {diagnostics.parsed_rows}")
        print(f"Skipped rows: {diagnostics.skipped_rows}")
        if diagnostics.skip_reasons:
            print("Skip reasons:")
            for reason, count in sorted(diagnostics.skip_reasons.items(), key=lambda x: -x[1])[:3]:
                print(f"  • {reason}: {count} row(s)")
        print(f"CSV date range: {diagnostics.csv_date_range['start']} to {diagnostics.csv_date_range['end']}")
        print("=" * 60)
    
    # Check if no transactions were parsed
    if not transactions:
        error_detail = {
            'message': 'No valid transactions found in CSV file',
            'detected_columns': diagnostics.detected_columns if diagnostics else [],
            'expected_columns': diagnostics.expected_columns if diagnostics else ['date', 'description', 'debit/credit', 'balance'],
            'total_rows': diagnostics.total_rows if diagnostics else 0,
            'parsed_rows': diagnostics.parsed_rows if diagnostics else 0,
            'skip_reasons': diagnostics.skip_reasons if diagnostics else {},
        }
        
        # Add hint if selected year/month doesn't match CSV
        if diagnostics and diagnostics.csv_date_range['start']:
            error_detail['csv_date_range'] = diagnostics.csv_date_range
            error_detail['hint'] = f"CSV contains dates from {diagnostics.csv_date_range['start']} to {diagnostics.csv_date_range['end']}. Check if selected month/year matches."
        
        raise HTTPException(status_code=400, detail=error_detail)
    
    # Generate fingerprints for all transactions
    for txn in transactions:
        txn['fingerprint'] = CSVParserService.generate_fingerprint(bank_account_id, txn)
    
    # Validate batch
    validation_result = BankStatementValidator.validate_batch(
        db=db,
        bank_account_id=bank_account_id,
        year=year,
        month=month,
        transactions=transactions,
    )
    
    # Check for duplicate fingerprints (only if no errors so far)
    if validation_result.is_valid():
        fingerprints = [txn['fingerprint'] for txn in transactions]
        duplicate_check = BankStatementValidator.check_duplicate_fingerprints(
            db=db,
            bank_account_id=bank_account_id,
            fingerprints=fingerprints,
        )
        validation_result.errors.extend(duplicate_check.errors)
    
    # Extract balance info
    opening_balance, closing_balance = CSVParserService.extract_balance_info(
        parsed_data['metadata_rows'],
        transactions
    )
    
    # Prepare response
    date_range_start = min(txn['effective_at'] for txn in transactions).isoformat() if transactions else None
    date_range_end = max(txn['effective_at'] for txn in transactions).isoformat() if transactions else None
    
    # Check for year/month mismatch warning
    if transactions and (year or month):
        first_date = min(txn['effective_at'] for txn in transactions)
        last_date = max(txn['effective_at'] for txn in transactions)
        
        # Add warning if dates don't match selected month/year
        if first_date.year != year or first_date.month != month or last_date.year != year or last_date.month != month:
            validation_result.warnings.append(
                f"Selected period {year}/{month} doesn't match CSV date range ({date_range_start} to {date_range_end})"
            )
    
    # Convert transactions to serializable format
    transactions_preview = []
    for txn in transactions[:100]:  # Limit preview to first 100
        transactions_preview.append({
            'effective_at': txn['effective_at'].isoformat(),
            'description': txn['description'],
            'details': txn.get('details'),
            'debit': float(txn['debit']) if txn['debit'] else None,
            'credit': float(txn['credit']) if txn['credit'] else None,
            'balance': float(txn['balance']) if txn['balance'] else None,
            'channel': txn['channel'],
        })
    
    response_data = {
        'header_row_index': parsed_data['header_row_index'],
        'metadata_rows': parsed_data['metadata_rows'],
        'transactions': transactions_preview,
        'transaction_count': len(transactions),
        'date_range_start': date_range_start,
        'date_range_end': date_range_end,
        'opening_balance': float(opening_balance) if opening_balance else None,
        'closing_balance': float(closing_balance) if closing_balance else None,
        'validation': validation_result.to_dict(),
    }
    
    # Include diagnostics only if there were issues (for debugging)
    if diagnostics and (diagnostics.skipped_rows > 0 or not transactions):
        response_data['diagnostics'] = diagnostics.to_dict()
    
    return response_data


# ===== Confirm Import Endpoint =====

@router.post("/confirm-import", response_model=BatchResponse)
async def confirm_import(
    bank_account_id: str,
    year: int,
    month: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """
    Confirm and execute the import
    Creates BankStatementBatch and BankTransaction records
    """
    # Verify bank account exists
    bank_account = db.query(BankAccount).filter(BankAccount.id == bank_account_id).first()
    if not bank_account:
        raise HTTPException(status_code=404, detail="Bank account not found")
    
    # Read and parse CSV (same as preview)
    try:
        content = await file.read()
        csv_content = content.decode('utf-8-sig')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV file: {str(e)}")
    
    try:
        parsed_data = CSVParserService.parse_csv(csv_content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")
    
    transactions = parsed_data['transactions']
    
    # Generate fingerprints
    for txn in transactions:
        txn['fingerprint'] = CSVParserService.generate_fingerprint(bank_account_id, txn)
    
    # Validate (final check)
    validation_result = BankStatementValidator.validate_batch(
        db=db,
        bank_account_id=bank_account_id,
        year=year,
        month=month,
        transactions=transactions,
    )
    
    # Check duplicates
    fingerprints = [txn['fingerprint'] for txn in transactions]
    duplicate_check = BankStatementValidator.check_duplicate_fingerprints(
        db=db,
        bank_account_id=bank_account_id,
        fingerprints=fingerprints,
    )
    validation_result.errors.extend(duplicate_check.errors)
    
    # Block import if there are errors
    if not validation_result.is_valid():
        raise HTTPException(
            status_code=400,
            detail={
                'message': 'Validation failed',
                'errors': validation_result.errors,
                'warnings': validation_result.warnings,
            }
        )
    
    # Extract balance info
    opening_balance, closing_balance = CSVParserService.extract_balance_info(
        parsed_data['metadata_rows'],
        transactions
    )
    
    # Create batch
    date_range_start = min(txn['effective_at'] for txn in transactions) if transactions else None
    date_range_end = max(txn['effective_at'] for txn in transactions) if transactions else None
    
    batch = BankStatementBatch(
        bank_account_id=bank_account_id,
        year=year,
        month=month,
        source_type="CSV",
        original_filename=file.filename,
        uploaded_by=current_user.id,
        status="CONFIRMED",
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        warnings=validation_result.warnings if validation_result.warnings else None,
    )
    
    db.add(batch)
    db.flush()  # Get batch ID
    
    # Create transactions
    for txn in transactions:
        db_transaction = BankTransaction(
            bank_statement_batch_id=batch.id,
            bank_account_id=bank_account_id,
            effective_at=txn['effective_at'],
            description=txn['description'],
            debit=txn['debit'],
            credit=txn['credit'],
            balance=txn['balance'],
            channel=txn['channel'],
            raw_row=txn['raw_row'],
            fingerprint=txn['fingerprint'],
        )
        db.add(db_transaction)
    
    db.commit()
    db.refresh(batch)
    
    # Return batch info
    return {
        'id': str(batch.id),
        'bank_account_id': str(batch.bank_account_id),
        'year': batch.year,
        'month': batch.month,
        'source_type': batch.source_type,
        'original_filename': batch.original_filename,
        'status': batch.status,
        'transaction_count': len(transactions),
        'date_range_start': batch.date_range_start.isoformat() if batch.date_range_start else None,
        'date_range_end': batch.date_range_end.isoformat() if batch.date_range_end else None,
        'opening_balance': float(batch.opening_balance) if batch.opening_balance else None,
        'closing_balance': float(batch.closing_balance) if batch.closing_balance else None,
        'warnings': batch.warnings,
        'uploaded_at': batch.uploaded_at.isoformat() if batch.uploaded_at else None,
    }


# ===== List Batches Endpoint =====

@router.get("/batches", response_model=List[BatchResponse])
async def list_batches(
    bank_account_id: Optional[str] = None,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """List all statement batches, optionally filtered by bank account"""
    query = db.query(BankStatementBatch)
    
    if bank_account_id:
        query = query.filter(BankStatementBatch.bank_account_id == bank_account_id)
    
    batches = query.order_by(BankStatementBatch.year.desc(), BankStatementBatch.month.desc()).all()
    
    result = []
    for batch in batches:
        # Count transactions
        txn_count = db.query(BankTransaction).filter(
            BankTransaction.bank_statement_batch_id == batch.id
        ).count()
        
        result.append({
            'id': str(batch.id),
            'bank_account_id': str(batch.bank_account_id),
            'year': batch.year,
            'month': batch.month,
            'source_type': batch.source_type,
            'original_filename': batch.original_filename,
            'status': batch.status,
            'transaction_count': txn_count,
            'date_range_start': batch.date_range_start.isoformat() if batch.date_range_start else None,
            'date_range_end': batch.date_range_end.isoformat() if batch.date_range_end else None,
            'opening_balance': float(batch.opening_balance) if batch.opening_balance else None,
            'closing_balance': float(batch.closing_balance) if batch.closing_balance else None,
            'warnings': batch.warnings,
            'uploaded_at': batch.uploaded_at.isoformat() if batch.uploaded_at else None,
        })
    
    return result

# ===== Get Transactions by Batch Endpoint =====

@router.get("/batches/{batch_id}/transactions")
async def get_batch_transactions(
    batch_id: str,
    current_user: User = Depends(require_role(["super_admin", "accounting"])),
    db: Session = Depends(get_db),
):
    """Get all transactions for a specific batch"""
    # Verify batch exists
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid batch ID format")
    
    batch = db.query(BankStatementBatch).filter(BankStatementBatch.id == batch_uuid).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Get transactions
    transactions = db.query(BankTransaction).filter(
        BankTransaction.bank_statement_batch_id == batch_uuid
    ).order_by(BankTransaction.effective_at.asc()).all()
    
    return {
        'batch_id': str(batch.id),
        'batch_info': {
            'year': batch.year,
            'month': batch.month,
            'filename': batch.original_filename,
            'date_range_start': batch.date_range_start.isoformat() if batch.date_range_start else None,
            'date_range_end': batch.date_range_end.isoformat() if batch.date_range_end else None,
        },
        'transactions': [txn.to_dict() for txn in transactions],
        'count': len(transactions),
    }