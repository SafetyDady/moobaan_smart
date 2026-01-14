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
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.db.models import (
    House, HouseStatus, Invoice, InvoiceStatus, PayinReport, PayinStatus,
    IncomeTransaction, InvoicePayment, CreditNote, User
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
                    Invoice.cycle_month == month
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
                received_at=payin.transfer_date
            )
            
            db.add(income_transaction)
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
        amount: Decimal
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
        # Get IncomeTransaction
        income_transaction = db.query(IncomeTransaction).filter(
            IncomeTransaction.id == income_transaction_id
        ).first()
        if not income_transaction:
            raise ValueError(f"IncomeTransaction {income_transaction_id} not found")
        
        # Get Invoice
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        # Verify houses match
        if income_transaction.house_id != invoice.house_id:
            raise ValueError("Income transaction and invoice must be for the same house")
        
        # Check available amount in IncomeTransaction
        available_amount = income_transaction.get_unallocated_amount()
        if amount > available_amount:
            raise ValueError(
                f"Amount {amount} exceeds available amount {available_amount} "
                f"in IncomeTransaction {income_transaction_id}"
            )
        
        # Check outstanding amount in Invoice
        outstanding = invoice.get_outstanding_amount()
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
            
            # Update invoice status
            invoice.update_status()
            
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
    def calculate_house_balance(db: Session, house_id: int) -> Dict[str, Decimal]:
        """
        Calculate current balance for a house based on all transactions.
        Balance = SUM(invoices) - SUM(credit_notes) - SUM(applied_payments)
        
        Args:
            db: Database session
            house_id: ID of house
            
        Returns:
            Dictionary with balance breakdown
        """
        # Verify house exists
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise ValueError(f"House {house_id} not found")
        
        # Calculate total invoiced amount
        total_invoiced = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            Invoice.house_id == house_id
        ).scalar() or Decimal("0")
        
        # Calculate total credit notes
        total_credited = db.query(func.coalesce(func.sum(CreditNote.amount), 0)).filter(
            CreditNote.house_id == house_id
        ).scalar() or Decimal("0")
        
        # Calculate total payments applied to invoices
        total_paid = db.query(
            func.coalesce(func.sum(InvoicePayment.amount), 0)
        ).join(
            Invoice
        ).filter(
            Invoice.house_id == house_id
        ).scalar() or Decimal("0")
        
        # Calculate outstanding balance
        outstanding_balance = total_invoiced - total_credited - total_paid
        
        return {
            "total_invoiced": Decimal(str(total_invoiced)),
            "total_credited": Decimal(str(total_credited)),
            "total_paid": Decimal(str(total_paid)),
            "outstanding_balance": Decimal(str(outstanding_balance)),
            "house_id": house_id,
            "house_code": house.house_code,
            "owner_name": house.owner_name
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
            Invoice.house_id == house_id
        ).order_by(
            InvoicePayment.applied_at.desc()
        ).limit(12).all()
        
        # Get credit notes
        credit_notes = db.query(CreditNote).filter(
            CreditNote.house_id == house_id
        ).order_by(
            CreditNote.created_at.desc()
        ).all()
        
        return {
            "balance": balance,
            "recent_invoices": [invoice.to_dict() for invoice in recent_invoices],
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
        Auto-apply payment to oldest unpaid invoices using FIFO method.
        
        Args:
            db: Database session
            income_transaction_id: ID of IncomeTransaction to apply
            
        Returns:
            List of created InvoicePayment records
        """
        income_transaction = db.query(IncomeTransaction).filter(
            IncomeTransaction.id == income_transaction_id
        ).first()
        
        if not income_transaction:
            raise ValueError(f"IncomeTransaction {income_transaction_id} not found")
        
        available_amount = income_transaction.get_unallocated_amount()
        if available_amount <= 0:
            return []  # Nothing to apply
        
        # Get unpaid invoices for this house, ordered by oldest first
        unpaid_invoices = db.query(Invoice).filter(
            and_(
                Invoice.house_id == income_transaction.house_id,
                Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
            )
        ).order_by(
            Invoice.cycle_year.asc(),
            Invoice.cycle_month.asc(),
            Invoice.id.asc()
        ).all()
        
        payments_created = []
        remaining_amount = available_amount
        
        for invoice in unpaid_invoices:
            if remaining_amount <= 0:
                break
            
            outstanding = invoice.get_outstanding_amount()
            if outstanding <= 0:
                continue
            
            # Apply payment (partial or full)
            amount_to_apply = min(remaining_amount, outstanding)
            
            payment = AccountingService.apply_payment_to_invoice(
                db=db,
                income_transaction_id=income_transaction_id,
                invoice_id=invoice.id,
                amount=amount_to_apply
            )
            
            payments_created.append(payment)
            remaining_amount -= amount_to_apply
        
        return payments_created
    
    @staticmethod
    def _get_month_end_date(year: int, month: int) -> date:
        """Get the last day of the specified month"""
        last_day = monthrange(year, month)[1]
        return date(year, month, last_day)
    
    @staticmethod
    def calculate_month_end_snapshot(
        db: Session,
        house_id: int,
        year: int,
        month: int
    ) -> Dict:
        """
        Calculate month-end financial snapshot for a house as of last day of specified month.
        
        This provides a reliable "as of end-of-month" financial view using:
        - Invoice.issue_date <= last_day_of_month
        - IncomeTransaction.received_at <= last_day_of_month
        - CreditNote.created_at <= last_day_of_month
        
        Balance is DERIVED, never stored, following same logic as Excel month-end closing.
        
        Args:
            db: Database session
            house_id: ID of house
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary with opening balance, period totals, and closing balance
        """
        # Validate inputs
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        if year < 2000 or year > 3000:
            raise ValueError("Year must be between 2000 and 3000")
        
        # Verify house exists
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise ValueError(f"House {house_id} not found")
        
        # Calculate period end date
        period_end = AccountingService._get_month_end_date(year, month)
        
        # Calculate opening balance (closing balance of previous month)
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        
        # Opening balance = previous month's closing balance
        prev_period_end = AccountingService._get_month_end_date(prev_year, prev_month)
        
        # Calculate cumulative totals up to previous month end
        prev_invoiced = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            and_(
                Invoice.house_id == house_id,
                Invoice.issue_date <= prev_period_end
            )
        ).scalar() or Decimal("0")
        
        prev_credited = db.query(func.coalesce(func.sum(CreditNote.amount), 0)).filter(
            and_(
                CreditNote.house_id == house_id,
                CreditNote.created_at <= prev_period_end
            )
        ).scalar() or Decimal("0")
        
        prev_paid = db.query(
            func.coalesce(func.sum(InvoicePayment.amount), 0)
        ).join(
            Invoice
        ).join(
            IncomeTransaction
        ).filter(
            and_(
                Invoice.house_id == house_id,
                IncomeTransaction.received_at <= prev_period_end
            )
        ).scalar() or Decimal("0")
        
        opening_balance = prev_invoiced - prev_credited - prev_paid
        
        # Calculate current month totals
        month_start = date(year, month, 1)
        
        # Invoices issued in current month
        invoice_total = db.query(func.coalesce(func.sum(Invoice.total_amount), 0)).filter(
            and_(
                Invoice.house_id == house_id,
                Invoice.issue_date >= month_start,
                Invoice.issue_date <= period_end
            )
        ).scalar() or Decimal("0")
        
        # Credit notes issued in current month
        credit_total = db.query(func.coalesce(func.sum(CreditNote.amount), 0)).filter(
            and_(
                CreditNote.house_id == house_id,
                CreditNote.created_at >= month_start,
                CreditNote.created_at <= period_end
            )
        ).scalar() or Decimal("0")
        
        # Payments received in current month
        payment_total = db.query(
            func.coalesce(func.sum(InvoicePayment.amount), 0)
        ).join(
            Invoice
        ).join(
            IncomeTransaction
        ).filter(
            and_(
                Invoice.house_id == house_id,
                IncomeTransaction.received_at >= month_start,
                IncomeTransaction.received_at <= period_end
            )
        ).scalar() or Decimal("0")
        
        # Calculate closing balance
        closing_balance = opening_balance + invoice_total - payment_total - credit_total
        
        return {
            "house_id": house_id,
            "house_code": house.house_code,
            "owner_name": house.owner_name,
            "period": f"{year:04d}-{month:02d}",
            "period_end": period_end.isoformat(),
            "opening_balance": Decimal(str(opening_balance)),
            "invoice_total": Decimal(str(invoice_total)),
            "payment_total": Decimal(str(payment_total)),
            "credit_total": Decimal(str(credit_total)),
            "closing_balance": Decimal(str(closing_balance))
        }
    
    @staticmethod
    def generate_house_statement(
        db: Session,
        house_id: int,
        year: int,
        month: int
    ) -> Dict:
        """
        Generate house financial statement for specified month.
        
        Statement provides bilingual (Thai + English) month-end based summary
        suitable for download as PDF or Excel.
        
        Args:
            db: Database session
            house_id: ID of house
            year: Year (e.g., 2024)
            month: Month (1-12)
            
        Returns:
            Dictionary with statement header, summary, and transaction timeline
        """
        # Get month-end snapshot for summary
        snapshot = AccountingService.calculate_month_end_snapshot(db, house_id, year, month)
        house = db.query(House).filter(House.id == house_id).first()
        
        period_end = AccountingService._get_month_end_date(year, month)
        month_start = date(year, month, 1)
        
        # Get all transactions for the month in chronological order
        transactions = []
        
        # Get invoices for the month
        invoices = db.query(Invoice).filter(
            and_(
                Invoice.house_id == house_id,
                Invoice.issue_date >= month_start,
                Invoice.issue_date <= period_end
            )
        ).order_by(Invoice.issue_date.asc()).all()
        
        for invoice in invoices:
            transactions.append({
                "date": invoice.issue_date,
                "type": "invoice",
                "type_th": "ใบแจ้งหนี้",
                "type_en": "Invoice",
                "reference": f"INV-{invoice.cycle_year}-{invoice.cycle_month:02d}",
                "description": f"Monthly fee {invoice.cycle_year}-{invoice.cycle_month:02d}",
                "description_th": f"ค่าบริการรายเดือน {invoice.cycle_year}-{invoice.cycle_month:02d}",
                "amount": float(invoice.total_amount),
                "is_debit": True,
                "source_id": invoice.id,
                "source_table": "invoices"
            })
        
        # Get payments for the month
        payments = db.query(InvoicePayment).join(
            Invoice
        ).join(
            IncomeTransaction
        ).filter(
            and_(
                Invoice.house_id == house_id,
                IncomeTransaction.received_at >= month_start,
                IncomeTransaction.received_at <= period_end
            )
        ).order_by(IncomeTransaction.received_at.asc()).all()
        
        for payment in payments:
            transactions.append({
                "date": payment.income_transaction.received_at.date(),
                "type": "payment",
                "type_th": "รับชำระ",
                "type_en": "Payment",
                "reference": f"PAY-{payment.income_transaction.id}",
                "description": f"Payment for invoice {payment.invoice_id}",
                "description_th": f"ชำระใบแจ้งหนี้ {payment.invoice_id}",
                "amount": float(payment.amount),
                "is_debit": False,
                "source_id": payment.id,
                "source_table": "invoice_payments"
            })
        
        # Get credit notes for the month
        credit_notes = db.query(CreditNote).filter(
            and_(
                CreditNote.house_id == house_id,
                CreditNote.created_at >= month_start,
                CreditNote.created_at <= period_end
            )
        ).order_by(CreditNote.created_at.asc()).all()
        
        for credit_note in credit_notes:
            transactions.append({
                "date": credit_note.created_at.date(),
                "type": "credit_note",
                "type_th": "ลดหนี้",
                "type_en": "Credit Note",
                "reference": f"CR-{credit_note.id}",
                "description": credit_note.reason,
                "description_th": credit_note.reason,
                "amount": float(credit_note.amount),
                "is_debit": False,
                "source_id": credit_note.id,
                "source_table": "credit_notes"
            })
        
        # Sort all transactions chronologically
        transactions.sort(key=lambda x: x["date"])
        
        # Calculate running balance
        running_balance = float(snapshot["opening_balance"])
        for transaction in transactions:
            if transaction["is_debit"]:
                running_balance += transaction["amount"]
            else:
                running_balance -= transaction["amount"]
            transaction["running_balance"] = running_balance
        
        return {
            "header": {
                "house_code": house.house_code,
                "owner_name": house.owner_name,
                "house_status": house.house_status.value,
                "period": f"{year:04d}-{month:02d}",
                "period_th": f"{AccountingService.THAI_MONTHS[month-1]} {year + 543}",  # Buddhist year
                "period_en": f"{AccountingService.ENGLISH_MONTHS[month-1]} {year}",
                "statement_date": datetime.now().date().isoformat(),
                "closing_balance": float(snapshot["closing_balance"])
            },
            "summary": {
                "opening_balance": {
                    "th": "ยอดยกมา",
                    "en": "Opening Balance",
                    "amount": float(snapshot["opening_balance"])
                },
                "invoices": {
                    "th": "ใบแจ้งหนี้เดือนนี้",
                    "en": "Invoices This Month",
                    "amount": float(snapshot["invoice_total"])
                },
                "payments": {
                    "th": "รับชำระ",
                    "en": "Payments Received",
                    "amount": -float(snapshot["payment_total"])  # Negative for display
                },
                "credit_notes": {
                    "th": "ลดหนี้/ปรับปรุงหนี้",
                    "en": "Credit Notes / Debt Adjustment",
                    "amount": -float(snapshot["credit_total"])  # Negative for display
                },
                "closing_balance": {
                    "th": "ยอดคงเหลือปลายเดือน",
                    "en": "Closing Balance",
                    "amount": float(snapshot["closing_balance"])
                }
            },
            "transactions": transactions,
            "snapshot": snapshot
        }
    
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
            # Get all unpaid invoices as of period end
            unpaid_invoices = db.query(Invoice).filter(
                and_(
                    Invoice.house_id == house.id,
                    Invoice.issue_date <= period_end,
                    Invoice.status.in_([InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID])
                )
            ).all()
            
            # Calculate aging buckets
            bucket_0_30 = Decimal("0")
            bucket_31_90 = Decimal("0")
            bucket_90_plus = Decimal("0")
            total_outstanding = Decimal("0")
            
            for invoice in unpaid_invoices:
                # Calculate outstanding amount for this invoice as of period end
                outstanding = Decimal(str(invoice.total_amount))
                
                # Subtract payments received up to period end
                payments_received = db.query(
                    func.coalesce(func.sum(InvoicePayment.amount), 0)
                ).join(
                    IncomeTransaction
                ).filter(
                    and_(
                        InvoicePayment.invoice_id == invoice.id,
                        IncomeTransaction.received_at <= period_end
                    )
                ).scalar() or Decimal("0")
                
                outstanding -= Decimal(str(payments_received))
                
                if outstanding <= 0:
                    continue  # Fully paid
                
                total_outstanding += outstanding
                
                # Determine aging bucket
                if invoice.due_date >= period_end:
                    # Not overdue yet
                    continue
                
                days_overdue = (period_end - invoice.due_date).days
                
                if 0 <= days_overdue <= 30:
                    bucket_0_30 += outstanding
                elif 31 <= days_overdue <= 90:
                    bucket_31_90 += outstanding
                else:  # > 90 days
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