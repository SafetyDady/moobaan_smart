from app.db.models.payin_report import PayinReport, PayinStatus
from app.db.session import SessionLocal

db = SessionLocal()
p = db.query(PayinReport).filter(PayinReport.id == 17).first()

print(f'Status type: {type(p.status)}')
print(f'Status value: {p.status}')
print(f'Status repr: {repr(p.status)}')
print(f'Is Enum: {isinstance(p.status, PayinStatus)}')
print(f'Equals PENDING enum: {p.status == PayinStatus.PENDING}')
print(f'Equals string: {p.status == "PENDING"}')
print(f'PayinStatus.PENDING value: {PayinStatus.PENDING}')
print(f'PayinStatus.PENDING repr: {repr(PayinStatus.PENDING)}')

db.close()
