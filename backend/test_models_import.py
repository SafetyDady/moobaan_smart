"""
Simple test to check if models can be imported without errors
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("🔍 Testing model imports...")

try:
    from app.db.models import (
        User, House, PayinReport, IncomeTransaction,
        BankTransaction, BankStatementBatch, BankAccount
    )
    print("✅ All models imported successfully")
    
    print(f"\n✅ PayinReport.matched_statement_txn: {PayinReport.matched_statement_txn}")
    print(f"✅ BankTransaction.matched_payin: {BankTransaction.matched_payin}")
    print(f"✅ IncomeTransaction.payin: {IncomeTransaction.payin}")
    print(f"✅ PayinReport.income_transaction: {PayinReport.income_transaction}")
    
    print("\n🎯 All relationships configured correctly!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
