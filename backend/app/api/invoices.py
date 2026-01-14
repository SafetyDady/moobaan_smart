from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from app.models import Invoice as InvoiceSchema, InvoiceCreate, InvoiceType, InvoiceStatus, InvoiceItem
from app.db.models import Invoice as InvoiceDB, House as HouseDB
from app.core.deps import get_db
from decimal import Decimal

router = APIRouter(prefix="/api/invoices", tags=["invoices"])


@router.get("", response_model=List[InvoiceSchema])
async def list_invoices(
    db: Session = Depends(get_db),
    house_id: int = None,
    status: str = None
):
    """List all invoices with optional filters"""
    query = db.query(InvoiceDB)
    
    if house_id:
        query = query.filter(InvoiceDB.house_id == house_id)
    
    if status:
        query = query.filter(InvoiceDB.status == status)
    
    invoices = query.all()
    
    # Convert to schema format
    result = []
    for idx, inv in enumerate(invoices):
        house = db.query(HouseDB).filter(HouseDB.id == inv.house_id).first()
        result.append(InvoiceSchema(
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
        ))
    
    return result



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
async def generate_monthly_invoices(db: Session = Depends(get_db)):
    """Generate monthly invoices for all active houses"""
    from app.services.accounting import AccountingService
    
    # Get current month
    now = datetime.now()
    
    # Call static method with correct arguments
    generated = AccountingService.auto_generate_invoices(
        db=db,
        year=now.year,
        month=now.month
    )
    
    return {
        "message": f"Generated {len(generated)} monthly invoices for {now.year}-{now.month:02d}",
        "cycle": f"{now.year}-{now.month:02d}",
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


