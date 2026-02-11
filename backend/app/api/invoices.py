from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.models import Invoice as InvoiceSchema, InvoiceCreate, InvoiceType, InvoiceStatus, InvoiceItem
from app.db.models import (
    Invoice as InvoiceDB, 
    House as HouseDB,
    IncomeTransaction,
    InvoicePayment,
    PayinReport
)
from app.db.models.invoice import InvoiceStatus as InvoiceStatusEnum
from app.db.models.payin_report import PayinStatus
from app.db.models.house import HouseStatus
from app.core.deps import get_db, require_admin_or_accounting, get_current_user
from app.db.models.user import User
from app.core.period_lock import validate_period_not_locked
from decimal import Decimal

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


# ============================================
# Manual Invoice Request Schema (Phase D.1)
# ============================================
class ManualInvoiceCreate(BaseModel):
    """Schema for creating a manual invoice"""
    house_id: int = Field(..., description="Target house ID")
    amount: float = Field(..., gt=0, description="Invoice amount (must be > 0)")
    description: str = Field(..., min_length=1, description="Reason/description for invoice")
    due_date: date = Field(..., description="Payment due date")
    note: Optional[str] = Field(None, description="Additional notes")


# ============================================
# Manual Invoice Endpoint (Phase D.1)
# ============================================
@router.post("/manual")
async def create_manual_invoice(
    data: ManualInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Create a manual invoice for special cases.
    
    Permission: SUPER_ADMIN, ACCOUNTING only
    
    Rules:
    - is_manual = true (always)
    - cycle_year = 0, cycle_month = 0 (not tied to billing cycle)
    - Cannot edit existing invoices via this endpoint
    """
    # Validate house exists and is active
    house = db.query(HouseDB).filter(HouseDB.id == data.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    if house.house_status != HouseStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="House is not active")
    
    # Validate due_date >= today
    if data.due_date < date.today():
        raise HTTPException(status_code=400, detail="Due date must be today or in the future")
    
    # Phase G.1: Check period lock for issue date
    validate_period_not_locked(db, date.today(), "invoice")
    
    # Create manual invoice
    new_invoice = InvoiceDB(
        house_id=data.house_id,
        cycle_year=0,  # Manual invoices don't belong to a billing cycle
        cycle_month=0,
        issue_date=date.today(),
        due_date=data.due_date,
        total_amount=Decimal(str(data.amount)),
        status=InvoiceStatusEnum.ISSUED,
        notes=data.note,
        created_by=current_user.id,
        is_manual=True,
        manual_reason=data.description
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    
    return {
        "id": new_invoice.id,
        "house_id": new_invoice.house_id,
        "house_code": house.house_code,
        "amount": float(new_invoice.total_amount),
        "description": new_invoice.manual_reason,
        "due_date": new_invoice.due_date.isoformat(),
        "status": new_invoice.status.value,
        "is_manual": True,
        "created_by": current_user.id,
        "created_at": new_invoice.created_at.isoformat() if new_invoice.created_at else None,
        "message": "Manual invoice created successfully"
    }


@router.get("", response_model=List[InvoiceSchema])
async def list_invoices(
    db: Session = Depends(get_db),
    house_id: int = None,
    status: str = None,
    is_manual: bool = None
):
    """List all invoices with optional filters"""
    query = db.query(InvoiceDB)
    
    if house_id:
        query = query.filter(InvoiceDB.house_id == house_id)
    
    if status:
        query = query.filter(InvoiceDB.status == status)
    
    # Filter by manual/auto-generated
    if is_manual is not None:
        query = query.filter(InvoiceDB.is_manual == is_manual)
    
    invoices = query.all()
    
    # Convert to schema format
    result = []
    for idx, inv in enumerate(invoices):
        house = db.query(HouseDB).filter(HouseDB.id == inv.house_id).first()
        
        # Calculate paid and outstanding (now considering credits)
        paid_amount = inv.get_total_paid()
        total_credited = inv.get_total_credited()
        net_amount = inv.get_net_amount()
        outstanding_amount = inv.get_remaining_balance()
        is_fully_credited = inv.is_fully_credited()
        
        # Determine status from actual data
        if is_fully_credited:
            actual_status = "CREDITED"  # Cancelled by credit note
        elif inv.status:
            actual_status = inv.status.value
        else:
            actual_status = "ISSUED"
        
        # Determine invoice type and cycle based on is_manual
        if inv.is_manual:
            inv_type = InvoiceType.MANUAL
            cycle_str = "MANUAL"
            description = inv.manual_reason or "Manual Invoice"
        else:
            inv_type = InvoiceType.AUTO_MONTHLY
            cycle_str = f"{inv.cycle_year}-{inv.cycle_month:02d}"
            description = inv.notes or "ค่าส่วนกลาง"
        
        result.append(InvoiceSchema(
            id=inv.id,
            house_id=inv.house_id,
            house_number=house.house_code if house else "Unknown",
            invoice_type=inv_type,
            cycle=cycle_str,
            total=float(inv.total_amount),
            paid=paid_amount,
            outstanding=outstanding_amount,
            status=actual_status,
            due_date=inv.due_date,
            items=[
                InvoiceItem(
                    id=0,
                    description=description,
                    amount=float(inv.total_amount)
                )
            ],
            created_at=inv.created_at,
            is_manual=inv.is_manual,
            manual_reason=inv.manual_reason,
            # Phase D.2: Credit note fields
            total_credited=total_credited,
            net_amount=net_amount,
            is_fully_credited=is_fully_credited
        ))
    
    return result


@router.get("/allocatable-ledgers")
async def get_allocatable_ledgers(
    house_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of ledger entries (IncomeTransactions) that can be allocated to invoices.
    
    Criteria:
    - Created from ACCEPTED pay-ins (recognized income)
    - Has remaining amount > 0 (not fully allocated)
    - Optionally filtered by house_id
    """
    query = db.query(IncomeTransaction).join(
        PayinReport, IncomeTransaction.payin_id == PayinReport.id
    ).filter(
        PayinReport.status == PayinStatus.ACCEPTED  # Only from accepted pay-ins
    )
    
    if house_id:
        query = query.filter(IncomeTransaction.house_id == house_id)
    
    ledgers = query.all()
    
    # Filter to only those with remaining amount
    allocatable = []
    for ledger in ledgers:
        remaining = ledger.get_unallocated_amount()
        if remaining > 0:
            house = db.query(HouseDB).filter(HouseDB.id == ledger.house_id).first()
            allocatable.append({
                "id": ledger.id,
                "house_id": ledger.house_id,
                "house_code": house.house_code if house else None,
                "payin_id": ledger.payin_id,
                "amount": float(ledger.amount),
                "allocated": ledger.get_total_applied(),
                "remaining": remaining,
                "received_at": ledger.received_at.isoformat() if ledger.received_at else None,
                "created_at": ledger.created_at.isoformat() if ledger.created_at else None
            })
    
    return {
        "ledgers": allocatable,
        "count": len(allocatable)
    }


@router.get("/{invoice_id}", response_model=InvoiceSchema)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a specific invoice by ID"""
    inv = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    house = db.query(HouseDB).filter(HouseDB.id == inv.house_id).first()
    
    return InvoiceSchema(
        id=inv.id,
        house_id=inv.house_id,
        house_number=house.house_code if house else "Unknown",
        invoice_type=InvoiceType.AUTO_MONTHLY,
        cycle=f"{inv.cycle_year}-{inv.cycle_month:02d}",
        total=float(inv.total_amount),
        status=InvoiceStatus.PENDING,
        due_date=inv.due_date,
        items=[
            InvoiceItem(
                id=0,
                description=inv.notes or "ค่าส่วนกลาง",
                amount=float(inv.total_amount)
            )
        ],
        created_at=inv.created_at
    )



@router.post("", response_model=InvoiceSchema)
async def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice (manual)"""
    
    # Check house exists
    house = db.query(HouseDB).filter(HouseDB.id == invoice.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Parse cycle (YYYY-MM format)
    try:
        year, month = invoice.cycle.split("-")
        cycle_year = int(year)
        cycle_month = int(month)
    except:
        raise HTTPException(status_code=400, detail="Invalid cycle format. Use YYYY-MM")
    
    # Calculate total from items
    total = sum(item.amount for item in invoice.items)
    
    # Create new invoice in database
    new_invoice = InvoiceDB(
        house_id=invoice.house_id,
        cycle_year=cycle_year,
        cycle_month=cycle_month,
        issue_date=datetime.now().date(),
        due_date=invoice.due_date,
        total_amount=Decimal(str(total)),
        status="ISSUED",
        notes=invoice.items[0].description if invoice.items else "ค่าส่วนกลาง"
    )
    
    db.add(new_invoice)
    db.commit()
    db.refresh(new_invoice)
    
    # Convert to schema
    return InvoiceSchema(
        id=new_invoice.id,
        house_id=new_invoice.house_id,
        house_number=house.house_code,
        invoice_type=InvoiceType(new_invoice.invoice_type),
        cycle=invoice.cycle,
        total=float(total),
        status=InvoiceStatus.PENDING,
        due_date=new_invoice.due_date,
        items=invoice.items,
        created_at=new_invoice.created_at
    )



@router.put("/{invoice_id}", response_model=InvoiceSchema)
async def update_invoice(invoice_id: int, invoice: InvoiceCreate, db: Session = Depends(get_db)):
    """Update an existing invoice"""
    
    existing = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check house exists
    house = db.query(HouseDB).filter(HouseDB.id == invoice.house_id).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Parse cycle
    try:
        year, month = invoice.cycle.split("-")
        cycle_year = int(year)
        cycle_month = int(month)
    except:
        raise HTTPException(status_code=400, detail="Invalid cycle format. Use YYYY-MM")
    
    # Calculate total
    total = sum(item.amount for item in invoice.items)
    
    # Update fields
    existing.house_id = invoice.house_id
    existing.cycle_year = cycle_year
    existing.cycle_month = cycle_month
    existing.total_amount = Decimal(str(total))
    existing.due_date = invoice.due_date
    existing.notes = invoice.items[0].description if invoice.items else existing.notes
    
    db.commit()
    db.refresh(existing)
    
    return InvoiceSchema(
        id=existing.id,
        house_id=existing.house_id,
        house_number=house.house_code,
        invoice_type=InvoiceType.AUTO_MONTHLY,
        cycle=invoice.cycle,
        total=float(total),
        status=InvoiceStatus.PENDING,
        due_date=existing.due_date,
        items=invoice.items,
        created_at=existing.created_at
    )



@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete an invoice"""
    invoice = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}



@router.post("/generate-monthly")
async def generate_monthly_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """Generate monthly invoices for all active houses.
    Optionally pass ?year=YYYY&month=MM to generate for a specific period.
    """
    from app.services.accounting import AccountingService
    
    # Use provided year/month or default to current month
    now = datetime.now()
    target_year = year if year else now.year
    target_month = month if month else now.month
    
    # Validate
    if not (1 <= target_month <= 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
    if not (2000 <= target_year <= 3000):
        raise HTTPException(status_code=400, detail="Year must be between 2000 and 3000")
    
    # Call static method with correct arguments
    generated = AccountingService.auto_generate_invoices(
        db=db,
        year=target_year,
        month=target_month,
        created_by_id=current_user.id
    )
    
    return {
        "message": f"Generated {len(generated)} monthly invoices for {target_year}-{target_month:02d}",
        "cycle": f"{target_year}-{target_month:02d}",
        "count": len(generated),
        "invoices": [
            {
                "id": inv.id,
                "house_code": db.query(HouseDB).filter(HouseDB.id == inv.house_id).first().house_code,
                "cycle": f"{inv.cycle_year}-{inv.cycle_month:02d}",
                "total": float(inv.total_amount)
            }
            for inv in generated
        ]
    }


# ==================== LEDGER → INVOICE APPLICATION ====================

class ApplyPaymentRequest(BaseModel):
    """Request to apply ledger (IncomeTransaction) to invoice"""
    income_transaction_id: int = Field(..., description="ID of the ledger entry (IncomeTransaction)")
    amount: Decimal = Field(..., gt=0, description="Amount to apply (must be > 0)")
    note: Optional[str] = Field(None, description="Optional note for this application")


@router.get("/{invoice_id}/detail")
async def get_invoice_detail(
    invoice_id: int, 
    db: Session = Depends(get_db)
):
    """
    Get invoice with full payment details including:
    - Total amount
    - Paid amount (sum of allocations)
    - Outstanding amount
    - Payment status
    - Payment history
    """
    inv = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    house = db.query(HouseDB).filter(HouseDB.id == inv.house_id).first()
    
    # Calculate payment totals
    total_paid = inv.get_total_paid()
    outstanding = inv.get_outstanding_amount()
    
    # Get payment history
    payments = db.query(InvoicePayment).filter(
        InvoicePayment.invoice_id == invoice_id
    ).all()
    
    payment_history = []
    for payment in payments:
        income_txn = db.query(IncomeTransaction).filter(
            IncomeTransaction.id == payment.income_transaction_id
        ).first()
        payin = db.query(PayinReport).filter(
            PayinReport.id == income_txn.payin_id
        ).first() if income_txn else None
        
        payment_history.append({
            "id": payment.id,
            "amount": float(payment.amount),
            "applied_at": payment.applied_at.isoformat() if payment.applied_at else None,
            "income_transaction_id": payment.income_transaction_id,
            "ledger_date": income_txn.received_at.isoformat() if income_txn else None,
            "payin_id": payin.id if payin else None
        })
    
    return {
        "id": inv.id,
        "house_id": inv.house_id,
        "house_code": house.house_code if house else None,
        "owner_name": house.owner_name if house else None,
        "cycle_year": inv.cycle_year,
        "cycle_month": inv.cycle_month,
        "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
        "due_date": inv.due_date.isoformat() if inv.due_date else None,
        "total_amount": float(inv.total_amount),
        "paid_amount": total_paid,
        "outstanding_amount": outstanding,
        "status": inv.status.value if inv.status else None,
        "notes": inv.notes,
        "created_at": inv.created_at.isoformat() if inv.created_at else None,
        "payments": payment_history
    }


@router.post("/{invoice_id}/apply-payment")
async def apply_payment_to_invoice(
    invoice_id: int,
    request: ApplyPaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_accounting)
):
    """
    Apply ledger (IncomeTransaction) to invoice with strict validation.
    
    Preconditions:
    1. Invoice must exist and not be fully paid
    2. Ledger (IncomeTransaction) must exist and be from ACCEPTED pay-in
    3. Ledger must have sufficient remaining amount
    4. Amount to apply must not exceed invoice outstanding
    
    Creates immutable InvoicePayment record and updates invoice status atomically.
    """
    # 1. Validate invoice
    invoice = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    outstanding = invoice.get_outstanding_amount()
    if outstanding <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot apply payment: Invoice is already fully paid"
        )
    
    # 2. Validate ledger (IncomeTransaction)
    ledger = db.query(IncomeTransaction).filter(
        IncomeTransaction.id == request.income_transaction_id
    ).first()
    if not ledger:
        raise HTTPException(status_code=404, detail="Ledger entry (IncomeTransaction) not found")
    
    # 3. Verify ledger is from ACCEPTED pay-in
    payin = db.query(PayinReport).filter(PayinReport.id == ledger.payin_id).first()
    if not payin or payin.status != PayinStatus.ACCEPTED:
        raise HTTPException(
            status_code=400,
            detail="Cannot apply: Ledger entry must be from an ACCEPTED pay-in"
        )
    
    # 4. Check ledger remaining amount
    ledger_remaining = ledger.get_unallocated_amount()
    if ledger_remaining <= 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot apply: Ledger entry is fully allocated"
        )
    
    # 5. Validate amount to apply
    amount_to_apply = float(request.amount)
    
    if amount_to_apply > outstanding:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot apply ฿{amount_to_apply:.2f}: Exceeds invoice outstanding ฿{outstanding:.2f}"
        )
    
    if amount_to_apply > ledger_remaining:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot apply ฿{amount_to_apply:.2f}: Exceeds ledger remaining ฿{ledger_remaining:.2f}"
        )
    
    # 6. ATOMIC TRANSACTION: Create payment record + Update invoice status
    try:
        # Create immutable payment record
        payment = InvoicePayment(
            invoice_id=invoice_id,
            income_transaction_id=ledger.id,
            amount=request.amount
        )
        db.add(payment)
        
        # Flush to ensure payment is visible for status calculation
        db.flush()
        db.refresh(invoice)
        
        # Update invoice status based on new total paid
        invoice.update_status()
        
        db.commit()
        db.refresh(payment)
        db.refresh(invoice)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply payment: {str(e)}"
        )
    
    # Return updated invoice state
    new_outstanding = invoice.get_outstanding_amount()
    
    return {
        "message": "Payment applied successfully",
        "invoice_id": invoice_id,
        "payment": {
            "id": payment.id,
            "amount": float(payment.amount),
            "applied_at": payment.applied_at.isoformat() if payment.applied_at else None,
            "ledger_id": ledger.id
        },
        "invoice": {
            "id": invoice.id,
            "total_amount": float(invoice.total_amount),
            "paid_amount": invoice.get_total_paid(),
            "outstanding_amount": new_outstanding,
            "status": invoice.status.value if invoice.status else None
        },
        "ledger": {
            "id": ledger.id,
            "remaining_amount": ledger.get_unallocated_amount()
        }
    }


@router.get("/{invoice_id}/payments")
async def get_invoice_payments(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """
    Get payment allocation history for an invoice (audit trail).
    Shows all InvoicePayment records with ledger details.
    """
    invoice = db.query(InvoiceDB).filter(InvoiceDB.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    payments = db.query(InvoicePayment).filter(
        InvoicePayment.invoice_id == invoice_id
    ).order_by(InvoicePayment.applied_at.desc()).all()
    
    payment_records = []
    for payment in payments:
        ledger = db.query(IncomeTransaction).filter(
            IncomeTransaction.id == payment.income_transaction_id
        ).first()
        payin = db.query(PayinReport).filter(
            PayinReport.id == ledger.payin_id
        ).first() if ledger else None
        
        payment_records.append({
            "id": payment.id,
            "amount": float(payment.amount),
            "applied_at": payment.applied_at.isoformat() if payment.applied_at else None,
            "ledger": {
                "id": ledger.id if ledger else None,
                "amount": float(ledger.amount) if ledger else 0,
                "received_at": ledger.received_at.isoformat() if ledger else None,
                "payin_id": payin.id if payin else None
            } if ledger else None
        })
    
    return {
        "invoice_id": invoice_id,
        "payments": payment_records,
        "count": len(payment_records),
        "total_paid": invoice.get_total_paid(),
        "outstanding": invoice.get_outstanding_amount()
    }


