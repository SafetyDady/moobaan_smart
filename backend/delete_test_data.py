"""Delete TEST001 house and all related data"""
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.db.models.house import House
from app.db.models.invoice import Invoice
from app.db.models.payin_report import PayinReport
from app.db.models.invoice_payment import InvoicePayment
from app.db.models.income_transaction import IncomeTransaction

db = SessionLocal()

# Find house TEST001
house = db.query(House).filter(House.house_code == 'TEST001').first()
if house:
    print(f'Found house: {house.id} - {house.house_code}')
    
    # Get all invoices for this house
    invoices = db.query(Invoice).filter(Invoice.house_id == house.id).all()
    invoice_ids = [inv.id for inv in invoices]
    
    # Delete related invoice_payments first
    if invoice_ids:
        payment_count = db.query(InvoicePayment).filter(InvoicePayment.invoice_id.in_(invoice_ids)).delete(synchronize_session=False)
        print(f'Deleted {payment_count} invoice payments')
    
    # Delete related income_transactions
    income_count = db.query(IncomeTransaction).filter(IncomeTransaction.house_id == house.id).delete()
    print(f'Deleted {income_count} income transactions')
    
    # Delete related payins
    payin_count = db.query(PayinReport).filter(PayinReport.house_id == house.id).delete()
    print(f'Deleted {payin_count} payins')
    
    # Delete related invoices
    invoice_count = db.query(Invoice).filter(Invoice.house_id == house.id).delete()
    print(f'Deleted {invoice_count} invoices')
    
    # Delete the house
    db.delete(house)
    db.commit()
    print('House TEST001 and all related data deleted successfully!')
else:
    print('House TEST001 not found')

db.close()
