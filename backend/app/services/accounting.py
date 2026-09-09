"""
Accounting service for managing house balances, invoices, payments, and credit notes.

This module implements the complete accounting system following these principles:
1. Balance is DERIVED from transactions, never stored directly
2. Invoices are NEVER deleted or silently modified
3. All balance changes are auditable via transactions
4. Credit notes are used for debt reduction instead of deleting invoices
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from calendar import monthrange
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, and_, or_
from app.core.timezone import BANGKOK_TZ
from app.services.invoice_locking import lock_invoice, lock_ledger, lock_invoices
from app.services.automatic_allocation import prepare_allocation, apply_prepared_funds
from app.services.accounting_reports import (
    month_dates, month_snapshot, monthly_statement, range_statement, dated_outstanding,
)

from app.db.models import (
    House, HouseStatus, Invoice, InvoiceStatus, PayinReport, PayinStatus,
    IncomeTransaction, InvoicePayment, PaymentStatus, CreditNote, User
)


class AccountingService:
    """Service class for all accounting operations."""
    
    # Thai month names for bilingual support
    THAI_MONTHS = [
        "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
        "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
    ]
    
    ENGLISH_MONTHS = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    @staticmethod
    def auto_generate_invoices(
        db: Session, 
        year: int, 
        month: int, 
        base_amount: Decimal = Decimal("600.00"),
        created_by_id: Optional[int] = None
    ) -> List[Invoice]:
        """
        Auto-generate monthly invoices for ALL houses regardless of status.
        This function is idempotent - running twice will not create duplicates.
        
        Args:
            db: Database session
            year: Invoice year
            month: Invoice month (1-12)
            base_amount: Default monthly fee amount
            created_by_id: ID of user creating invoices (optional)
            
        Returns:
            List of created invoices
        """
        # Input validation
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if year < 2000 or year > 3000:
            raise ValueError("Year must be between 2000 and 3000")

        # Get all houses
        houses = db.query(House).all()
        scope = prepare_allocation(db, [house.id for house in houses])
        created_invoices = []
        
        # Calculate dates
        issue_date = date(year, month, 1)
        due_date = issue_date + timedelta(days=30)  # 30 days to pay
        
        for house in houses:
            # Check if invoice already exists for this house/cycle
            existing_invoice = db.query(Invoice).filter(
                and_(
                    Invoice.house_id == house.id,
                    Invoice.cycle_year == year,
                    Invoice.cycle_month == month,
                    Invoice.is_manual.is_(False),
                )
            ).first()
            
            if existing_invoice:
                continue  # Skip if already exists (idempotent)
            
            # Create new invoice
            invoice = Invoice(
                house_id=house.id,
                cycle_year=year,
                cycle_month=month,
                issue_date=issue_date,
                due_date=due_date,
                total_amount=base_amount,
                status=InvoiceStatus.ISSUED,
                created_by=created_by_id,
                notes=f"Auto-generated invoice for {year}-{month:02d}"
            )
            
            db.add(invoice)
            created_invoices.append(invoice)
        
        if created_invoices:
            created_houses = {inv.house_id for inv in created_invoices}
            scope.house_ids = tuple(sorted(created_houses))
            scope.ledgers = [entry for entry in scope.ledgers if entry.house_id in created_houses]
            scope.invoices = [inv for inv in scope.invoices if inv.house_id in created_houses] + created_invoices
            apply_prepared_funds(db, scope)
        db.commit()
        return created_invoices

    @staticmethod
    def accept_payin(
        db: Session, 
        payin_id: int, 
        accepted_by_user_id: int
    ) -> IncomeTransaction:
        """
        Accept a PayIn and create an immutable IncomeTransaction.
        Only SUPER_ADMIN users can accept payments.
        
        Args:
            db: Database session
            payin_id: ID of PayIn to accept
            accepted_by_user_id: ID of SUPER_ADMIN user
            
        Returns:
            Created IncomeTransaction
            
        Raises:
            ValueError: If payin cannot be accepted
            PermissionError: If user is not SUPER_ADMIN
        """
        # Verify user is SUPER_ADMIN
        user = db.query(User).filter(User.id == accepted_by_user_id).first()
        if not user or user.role != "super_admin":
            raise PermissionError("Only SUPER_ADMIN users can accept payments")
        
        # Get PayIn
        payin = db.query(PayinReport).filter(PayinReport.id == payin_id).first()
        if not payin:
            raise ValueError(f"PayIn {payin_id} not found")
        
        if not payin.can_be_accepted():
            raise ValueError(f"PayIn {payin_id} cannot be accepted (status: {payin.status})")
        
        # ===== NEW: Enforce Bank Statement Matching =====
        if payin.matched_statement_txn_id is None:
            raise ValueError(
                "PayIn must be matched with a bank statement transaction before acceptance. "
                "Please match this pay-in with a bank transaction first."
            )
        # ============================================
        
        from app.db.models import BankTransaction, PostingStatus
        bank = (db.query(BankTransaction).filter(BankTransaction.id == payin.matched_statement_txn_id)
                .populate_existing().with_for_update().first())
        if not bank or bank.matched_payin_id != payin.id:
            raise ValueError("Pay-in bank match changed; review required")
        scope = prepare_allocation(db, [payin.house_id])
        db.refresh(payin)
        if not payin.can_be_accepted():
            raise ValueError("Pay-in is no longer eligible for acceptance")

        # Verify house exists and get house status
        house = db.query(House).filter(House.id == payin.house_id).first()
        if not house:
            raise ValueError(f"House {payin.house_id} not found")
        
        # Check if IncomeTransaction already exists (prevent double accept)
        existing_income = db.query(IncomeTransaction).filter(
            IncomeTransaction.payin_id == payin_id
        ).first()
        if existing_income:
            raise ValueError(f"PayIn {payin_id} already has an IncomeTransaction")
        
        try:
            # Update PayIn status
            payin.status = PayinStatus.ACCEPTED
            payin.accepted_by = accepted_by_user_id
            payin.accepted_at = datetime.utcnow()
            
            # Create IncomeTransaction
            income_transaction = IncomeTransaction(
                house_id=payin.house_id,
                payin_id=payin_id,
                amount=payin.amount,
                received_at=bank.effective_at,
                reference_bank_transaction_id=bank.id,
            )
            
            db.add(income_transaction)
            bank.posting_status = PostingStatus.POSTED
            scope.ledgers.append(income_transaction)
            apply_prepared_funds(db, scope)
            db.commit()
            
            return income_transaction
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to accept payment: {str(e)}")

    @staticmethod
    def apply_payment_to_invoice(
        db: Session,
        income_transaction_id: int,
        invoice_id: int,
        amount: Decimal,
        *,
        commit: bool = True,
    ) -> InvoicePayment:
        """
        Apply payment from IncomeTransaction to specific Invoice.
        Supports partial payments and multiple invoices per payment.
        
        Args:
            db: Database session
            income_transaction_id: ID of IncomeTransaction
            invoice_id: ID of Invoice to pay
            amount: Amount to apply
            
        Returns:
            Created InvoicePayment
            
        Raises:
            ValueError: If payment cannot be applied
        """
        amount = Decimal(str(amount))
        # Get IncomeTransaction
        income_transaction = lock_ledger(db, income_transaction_id)
        if not income_transaction:
            raise ValueError(f"IncomeTransaction {income_transaction_id} not found")
        if income_transaction.status and income_transaction.status.value == 'REVERSED':
            raise ValueError("Cannot apply a reversed ledger")
        if not amount.is_finite() or amount <= 0 or amount != amount.quantize(Decimal('0.01')):
            raise ValueError("Payment must be positive with at most two decimal places")
        
        # Get Invoice
        invoice = lock_invoice(db, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Verify houses match
        if income_transaction.house_id != invoice.house_id:
            raise ValueError("Income transaction and invoice must be for the same house")
        
        # Check available amount in IncomeTransaction
        available_amount = Decimal(str(income_transaction.get_unallocated_amount()))
        if amount > available_amount:
            raise ValueError(
                f"Amount {amount} exceeds available amount {available_amount} "
                f"in IncomeTransaction {income_transaction_id}"
            )
        
        # Check outstanding amount in Invoice
        outstanding = Decimal(str(invoice.get_outstanding_amount()))
        if amount > outstanding:
            raise ValueError(
                f"Amount {amount} exceeds outstanding amount {outstanding} "
                f"for Invoice {invoice_id}"
            )
        
        try:
            # Create InvoicePayment
            payment = InvoicePayment(
                invoice_id=invoice_id,
                income_transaction_id=income_transaction_id,
                amount=amount
            )
            
            db.add(payment)
            db.flush()  # Get payment ID
            db.expire(invoice, ["payments", "credit_notes"])
            
            # Update invoice status
            invoice.update_status()
            
            if commit:
                db.commit()
            return payment
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to apply payment: {str(e)}")

    @staticmethod
    def issue_credit_note(
        db: Session,
        house_id: int,
        amount: Decimal,
        reason: str,
        created_by_id: int,
        reference: Optional[str] = None
    ) -> CreditNote:
        """
        Issue a credit note to reduce house balance.
        Used for debt negotiation, discounts, and other balance reductions.
        
        Args:
            db: Database session
            house_id: ID of house
            amount: Credit amount (positive number)
            reason: Reason for credit (required)
            created_by_id: ID of user creating credit note
            reference: Optional reference number
            
        Returns:
            Created CreditNote
            
        Raises:
            ValueError: If credit note cannot be issued
        """
        # Verify user has permission (accounting or super_admin)
        user = db.query(User).filter(User.id == created_by_id).first()
        if not user or user.role not in ["accounting", "super_admin"]:
            raise PermissionError("Only accounting or super_admin users can issue credit notes")
        
        # Verify house exists
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise ValueError(f"House {house_id} not found")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Credit note amount must be positive")
        
        # Validate reason
        if not reason or not reason.strip():
            raise ValueError("Credit note reason is required")
        
        try:
            # Create CreditNote
            credit_note = CreditNote(
                house_id=house_id,
                amount=amount,
                reason=reason.strip(),
                reference=reference,
                created_by=created_by_id
            )
            
            db.add(credit_note)
            db.commit()
            
            return credit_note
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Failed to issue credit note: {str(e)}")

    @staticmethod
    def calculate_house_balance(db: Session, house_id: int) -> Dict:
        """Current invoice settlement balance; unallocated receipts are separate cash."""
        house = db.get(House, house_id)
        if not house:
            raise ValueError(f"House {house_id} not found")
        invoices = db.query(Invoice).options(
            selectinload(Invoice.payments), selectinload(Invoice.credit_notes),
        ).filter(Invoice.house_id == house_id).all()
        return {
            "house_id": house_id, "house_code": house.house_code, "owner_name": house.owner_name,
            "total_invoiced": sum((Decimal(i.total_amount) for i in invoices), Decimal('0')),
            "total_credited": sum((i.get_total_credited_decimal() for i in invoices), Decimal('0')),
            "total_paid": sum((i.get_total_paid_decimal() for i in invoices), Decimal('0')),
            "outstanding_balance": sum((i.get_remaining_balance_decimal() for i in invoices), Decimal('0')),
        }

    @staticmethod
    def get_house_financial_summary(db: Session, house_id: int) -> Dict:
        """
        Get comprehensive financial summary for a house including:
        - Balance breakdown
        - Recent invoices
        - Recent payments
        - Credit notes (if user has permission)
        
        Args:
            db: Database session
            house_id: ID of house
            
        Returns:
            Complete financial summary
        """
        balance = AccountingService.calculate_house_balance(db, house_id)
        
        # Get recent invoices (last 12 months)
        recent_invoices = db.query(Invoice).filter(
            Invoice.house_id == house_id
        ).order_by(
            Invoice.cycle_year.desc(),
            Invoice.cycle_month.desc()
        ).limit(12).all()
        
        # Get recent payments (last 12 months)
        recent_payments = db.query(InvoicePayment).join(
            Invoice
        ).join(
            IncomeTransaction
        ).filter(
            InvoicePayment.status == PaymentStatus.ACTIVE,
            Invoice.house_id == house_id
        ).order_by(
            InvoicePayment.applied_at.desc()
        ).limit(12).all()
        
        # Get credit notes
        credit_notes = db.query(CreditNote).join(Invoice, Invoice.id == CreditNote.invoice_id).filter(
            Invoice.house_id == house_id,
            CreditNote.status == 'applied',
        ).order_by(
            CreditNote.created_at.desc()
        ).all()
        
        return {
            "balance": balance,
            "recent_invoices": [{**invoice.to_dict(), "status": invoice.get_settlement_status()} for invoice in recent_invoices],
            "recent_payments": [payment.to_dict() for payment in recent_payments],
            "credit_notes": [note.to_dict() for note in credit_notes],
            "summary": {
                "total_invoices": len(recent_invoices),
                "total_payments": len(recent_payments),
                "total_credit_notes": len(credit_notes)
            }
        }

    @staticmethod
    def auto_apply_payments_fifo(
        db: Session,
        income_transaction_id: int
    ) -> List[InvoicePayment]:
        """
        Auto-apply unused household funds to oldest due invoices using FIFO.
        
        Args:
            db: Database session
            income_transaction_id: Receipt identifying the household (not an invoice selection)
            
        Returns:
            List of created InvoicePayment records
        """
        income_transaction = db.get(IncomeTransaction, income_transaction_id)
        if not income_transaction:
            raise ValueError(f"IncomeTransaction {income_transaction_id} not found")
        scope = prepare_allocation(db, [income_transaction.house_id])
        if income_transaction.status and income_transaction.status.value == 'REVERSED':
            raise ValueError("Cannot apply a reversed ledger")
        payments_created = apply_prepared_funds(db, scope)
        db.commit()
        return payments_created

    @staticmethod
    def _get_month_end_date(year: int, month: int) -> date:
        """Get the last day of the specified month"""
        last_day = monthrange(year, month)[1]
        return date(year, month, last_day)
    
    
    @staticmethod
    def generate_house_statement(db: Session, house_id: int, year: int, month: int) -> Dict:
        """Monthly receipt statement; summary and rows share one dated cash view."""
        month_dates(year, month)
        return monthly_statement(db, house_id, year, month,
            AccountingService.THAI_MONTHS[month - 1], AccountingService.ENGLISH_MONTHS[month - 1])
    
    @staticmethod
    def generate_aging_report(
        db: Session,
        year: int,
        month: int,
        house_status_filter: Optional[List[str]] = None,
        min_outstanding: Optional[Decimal] = None
    ) -> List[Dict]:
        """
        Generate aging report for all houses as of month-end.
        
        Provides receivables overview with aging buckets:
        - 0-30 days overdue
        - 31-90 days overdue  
        - >90 days overdue
        
        Overdue definition: invoice.due_date < end_of_month AND invoice not fully paid
        
        Args:
            db: Database session
            year: Year (e.g., 2024)
            month: Month (1-12)
            house_status_filter: Optional list of house statuses to include
            min_outstanding: Optional minimum outstanding amount filter
            
        Returns:
            List of house aging data
        """
        period_end = AccountingService._get_month_end_date(year, month)
        
        # Build house filter
        house_query = db.query(House)
        if house_status_filter:
            house_query = house_query.filter(House.house_status.in_(house_status_filter))
        
        houses = house_query.all()
        aging_data = []
        
        for house in houses:
            # Restated month-end debt: currently ACTIVE allocations dated by receipt,
            # applied credits dated by creation, irrespective of the stored status.
            unpaid_invoices = db.query(Invoice).options(
                selectinload(Invoice.payments).selectinload(InvoicePayment.income_transaction),
                selectinload(Invoice.credit_notes),
            ).filter(Invoice.house_id == house.id, Invoice.issue_date <= period_end).all()
            bucket_0_30 = Decimal('0')
            bucket_31_90 = Decimal('0')
            bucket_90_plus = Decimal('0')
            total_outstanding = Decimal('0')
            for invoice in unpaid_invoices:
                outstanding = dated_outstanding(invoice, period_end)
                if outstanding <= 0:
                    continue
                total_outstanding += outstanding
                if invoice.due_date >= period_end:
                    continue
                days_overdue = (period_end - invoice.due_date).days
                if days_overdue <= 30:
                    bucket_0_30 += outstanding
                elif days_overdue <= 90:
                    bucket_31_90 += outstanding
                else:
                    bucket_90_plus += outstanding

            # Apply minimum outstanding filter
            if min_outstanding and total_outstanding < min_outstanding:
                continue
            
            aging_data.append({
                "house_id": house.id,
                "house_code": house.house_code,
                "owner_name": house.owner_name,
                "house_status": house.house_status.value,
                "bucket_0_30": float(bucket_0_30),
                "bucket_31_90": float(bucket_31_90),
                "bucket_90_plus": float(bucket_90_plus),
                "total_outstanding": float(total_outstanding),
                "as_of_date": period_end.isoformat()
            })
        
        # Sort by total outstanding descending
        aging_data.sort(key=lambda x: x["total_outstanding"], reverse=True)
        
        return aging_data

    @staticmethod
    def calculate_month_end_snapshot(db: Session, house_id: int, year: int, month: int) -> Dict:
        """Cash view of currently valid transactions through month-end in Bangkok.

        Uses invoice issue dates, POSTED receipt dates (including unallocated
        money), and applied credit dates. It is derived, not a locked snapshot.
        """
        return month_snapshot(db, house_id, year, month)

    @staticmethod
    def calculate_aggregated_snapshot(
        db: Session,
        year: int,
        month: int
    ) -> Dict:
        """
        Calculate aggregated month-end snapshot for ALL houses.
        
        This reuses the per-house calculation logic to ensure consistency.
        Admin-only endpoint for overall financial position.
        
        Args:
            db: Database session
            year: Target year
            month: Target month (1-12)
            
        Returns:
            Dict with aggregated snapshot data and per-house details
            
        Raises:
            ValueError: If invalid month
        """
        # Validate inputs
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if year < 2000 or year > 3000:
            raise ValueError("Year must be between 2000 and 3000")
        
        # Get all houses
        houses = db.query(House).all()
        
        # Calculate snapshot for each house
        house_snapshots = []
        total_opening = Decimal('0')
        total_invoices = Decimal('0')
        total_payments = Decimal('0')
        total_credits = Decimal('0')
        total_closing = Decimal('0')
        
        for house in houses:
            snapshot = AccountingService.calculate_month_end_snapshot(
                db=db,
                house_id=house.id,
                year=year,
                month=month
            )
            house_snapshots.append(snapshot)
            
            # Aggregate totals
            total_opening += Decimal(str(snapshot["opening_balance"]))
            total_invoices += Decimal(str(snapshot["invoice_total"]))
            total_payments += Decimal(str(snapshot["payment_total"]))
            total_credits += Decimal(str(snapshot["credit_total"]))
            total_closing += Decimal(str(snapshot["closing_balance"]))
        
        return {
            "year": year,
            "month": month,
            "total_houses": len(houses),
            "opening_balance": float(total_opening),
            "invoice_total": float(total_invoices),
            "payment_total": float(total_payments),
            "credit_total": float(total_credits),
            "closing_balance": float(total_closing),
            "houses": house_snapshots
        }

    @staticmethod
    def generate_statement(db: Session, house_id: int, start_date: date, end_date: date) -> Dict:
        """Exact inclusive date range, with consistent opening/rows/closing.

        Do not substitute month-end balances for mid-month dates and do not
        turn query/validation failures into zero balances.
        """
        return range_statement(db, house_id, start_date, end_date)
