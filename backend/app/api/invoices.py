from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app.models import Invoice, InvoiceCreate, InvoiceType, InvoiceStatus, InvoiceItem
from app.mock_data import MOCK_INVOICES, MOCK_HOUSES

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

# In-memory storage
invoices_db = list(MOCK_INVOICES)
next_id = max([inv.id for inv in invoices_db]) + 1
next_item_id = max([item.id for inv in invoices_db for item in inv.items]) + 1


@router.get("", response_model=List[Invoice])
async def list_invoices(
    house_id: int = None,
    invoice_type: str = None,
    status: str = None
):
    """List all invoices with optional filters"""
    result = invoices_db
    
    if house_id:
        result = [inv for inv in result if inv.house_id == house_id]
    
    if invoice_type:
        result = [inv for inv in result if inv.invoice_type.value == invoice_type]
    
    if status:
        result = [inv for inv in result if inv.status.value == status]
    
    return result


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: int):
    """Get a specific invoice by ID"""
    invoice = next((inv for inv in invoices_db if inv.id == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("", response_model=Invoice)
async def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice (manual)"""
    global next_id, next_item_id
    
    # Check house exists
    house = next((h for h in MOCK_HOUSES if h.id == invoice.house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Create invoice items with IDs
    items_with_ids = []
    for item in invoice.items:
        items_with_ids.append(InvoiceItem(
            id=next_item_id,
            description=item.description,
            amount=item.amount
        ))
        next_item_id += 1
    
    total = sum(item.amount for item in items_with_ids)
    
    new_invoice = Invoice(
        id=next_id,
        house_id=invoice.house_id,
        house_number=house.house_number,
        invoice_type=invoice.invoice_type,
        cycle=invoice.cycle,
        total=total,
        status=InvoiceStatus.PENDING,
        due_date=invoice.due_date,
        items=items_with_ids,
        created_at=datetime.now()
    )
    invoices_db.append(new_invoice)
    next_id += 1
    return new_invoice


@router.put("/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: int, invoice: InvoiceCreate):
    """Update an existing invoice"""
    global next_item_id
    
    existing = next((inv for inv in invoices_db if inv.id == invoice_id), None)
    if not existing:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check house exists
    house = next((h for h in MOCK_HOUSES if h.id == invoice.house_id), None)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    
    # Update invoice items
    items_with_ids = []
    for item in invoice.items:
        items_with_ids.append(InvoiceItem(
            id=next_item_id,
            description=item.description,
            amount=item.amount
        ))
        next_item_id += 1
    
    total = sum(item.amount for item in items_with_ids)
    
    existing.house_id = invoice.house_id
    existing.house_number = house.house_number
    existing.invoice_type = invoice.invoice_type
    existing.cycle = invoice.cycle
    existing.due_date = invoice.due_date
    existing.items = items_with_ids
    existing.total = total
    
    return existing


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int):
    """Delete an invoice"""
    global invoices_db
    invoice = next((inv for inv in invoices_db if inv.id == invoice_id), None)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoices_db = [inv for inv in invoices_db if inv.id != invoice_id]
    return {"message": "Invoice deleted successfully"}


@router.post("/generate-monthly")
async def generate_monthly_invoices():
    """Generate monthly invoices for all active houses"""
    global next_id, next_item_id
    from datetime import date
    from dateutil.relativedelta import relativedelta
    
    # Get current month cycle
    now = datetime.now()
    cycle = now.strftime("%Y-%m")
    due_date = date(now.year, now.month, 1) + relativedelta(months=1, days=-1)
    
    generated_count = 0
    
    # Generate for all active houses
    for house in MOCK_HOUSES:
        if house.status.value != "active":
            continue
        
        # Check if invoice already exists for this cycle
        existing = next((inv for inv in invoices_db 
                        if inv.house_id == house.id 
                        and inv.cycle == cycle 
                        and inv.invoice_type == InvoiceType.AUTO_MONTHLY), None)
        
        if existing:
            continue
        
        # Create default monthly invoice items
        items = [
            InvoiceItem(id=next_item_id, description="ค่าส่วนกลาง", amount=2000.0),
            InvoiceItem(id=next_item_id + 1, description="ค่าน้ำ", amount=500.0),
            InvoiceItem(id=next_item_id + 2, description="ค่าไฟ", amount=500.0),
        ]
        next_item_id += 3
        
        new_invoice = Invoice(
            id=next_id,
            house_id=house.id,
            house_number=house.house_number,
            invoice_type=InvoiceType.AUTO_MONTHLY,
            cycle=cycle,
            total=3000.0,
            status=InvoiceStatus.PENDING,
            due_date=due_date,
            items=items,
            created_at=datetime.now()
        )
        invoices_db.append(new_invoice)
        next_id += 1
        generated_count += 1
    
    return {
        "message": f"Generated {generated_count} monthly invoices for cycle {cycle}",
        "cycle": cycle,
        "count": generated_count
    }
