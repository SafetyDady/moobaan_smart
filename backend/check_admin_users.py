#!/usr/bin/env python3
"""Check admin user role"""
from app.db.session import SessionLocal
from app.db.models.user import User

db = SessionLocal()

# Find all admin users
admins = db.query(User).filter(User.role.in_(['super_admin', 'accounting'])).all()

print("Admin Users:")
print("=" * 60)
for u in admins:
    print(f"\nID: {u.id}")
    print(f"Email: {u.email}")
    print(f"Name: {u.full_name}")
    print(f"Role: {u.role}")
    print(f"Active: {u.is_active}")

db.close()
