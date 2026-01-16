#!/usr/bin/env python3
"""
Test Bank Statement Import - Phase R1
Tests CSV parsing, validation, and import functionality
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.db.models.bank_account import BankAccount
from app.services.csv_parser import CSVParserService
from app.services.bank_statement_validator import BankStatementValidator


def test_csv_parsing():
    """Test CSV parsing with Dec25.csv"""
    print("\n=== Testing CSV Parsing ===")
    
    # Read test CSV file
    csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'Dec25.csv')
    
    if not os.path.exists(csv_path):
        print(f"❌ Test file not found: {csv_path}")
        return False
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        csv_content = f.read()
    
    # Parse CSV
    try:
        parsed_data = CSVParserService.parse_csv(csv_content)
        print(f"✅ CSV parsed successfully")
        print(f"   Header row index: {parsed_data['header_row_index']}")
        print(f"   Metadata rows: {len(parsed_data['metadata_rows'])}")
        print(f"   Transactions: {len(parsed_data['transactions'])}")
        
        # Show first transaction
        if parsed_data['transactions']:
            first_txn = parsed_data['transactions'][0]
            print(f"\n   First transaction:")
            print(f"     Date: {first_txn['effective_at']}")
            print(f"     Description: {first_txn['description']}")
            print(f"     Debit: {first_txn['debit']}")
            print(f"     Credit: {first_txn['credit']}")
            print(f"     Balance: {first_txn['balance']}")
        
        # Extract balance info
        opening, closing = CSVParserService.extract_balance_info(
            parsed_data['metadata_rows'],
            parsed_data['transactions']
        )
        print(f"\n   Opening balance: {opening}")
        print(f"   Closing balance: {closing}")
        
        return parsed_data
        
    except Exception as e:
        print(f"❌ CSV parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_fingerprint_generation(parsed_data):
    """Test fingerprint generation"""
    print("\n=== Testing Fingerprint Generation ===")
    
    if not parsed_data or not parsed_data['transactions']:
        print("❌ No parsed data available")
        return False
    
    # Test fingerprint for first transaction
    txn = parsed_data['transactions'][0]
    test_account_id = "00000000-0000-0000-0000-000000000001"
    
    fingerprint = CSVParserService.generate_fingerprint(test_account_id, txn)
    print(f"✅ Generated fingerprint: {fingerprint[:16]}...")
    
    # Generate same fingerprint again - should match
    fingerprint2 = CSVParserService.generate_fingerprint(test_account_id, txn)
    if fingerprint == fingerprint2:
        print(f"✅ Fingerprints are deterministic (match)")
    else:
        print(f"❌ Fingerprints don't match!")
        return False
    
    return True


def test_validation():
    """Test validation rules"""
    print("\n=== Testing Validation ===")
    
    db = SessionLocal()
    
    try:
        # Create a test bank account
        test_account = BankAccount(
            bank_code="KBANK",
            account_no_masked="xxx-x-xxxxx-1234",
            account_type="CASHFLOW",
            currency="THB",
            is_active=True,
        )
        db.add(test_account)
        db.commit()
        db.refresh(test_account)
        
        print(f"✅ Created test bank account: {test_account.id}")
        
        # Parse test CSV
        csv_path = os.path.join(os.path.dirname(__file__), 'test_data', 'Dec25.csv')
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            csv_content = f.read()
        
        parsed_data = CSVParserService.parse_csv(csv_content)
        transactions = parsed_data['transactions']
        
        # Test validation for December 2025
        result = BankStatementValidator.validate_batch(
            db=db,
            bank_account_id=str(test_account.id),
            year=2025,
            month=12,
            transactions=transactions,
        )
        
        print(f"\n   Validation result:")
        print(f"     Valid: {result.is_valid()}")
        print(f"     Errors: {len(result.errors)}")
        print(f"     Warnings: {len(result.warnings)}")
        
        if result.errors:
            print(f"\n   ❌ Errors:")
            for error in result.errors:
                print(f"      - {error}")
        
        if result.warnings:
            print(f"\n   ⚠️  Warnings:")
            for warning in result.warnings:
                print(f"      - {warning}")
        
        # Test duplicate month validation
        print(f"\n=== Testing Duplicate Month Validation ===")
        
        from app.db.models.bank_statement_batch import BankStatementBatch
        from app.db.models.user import User
        
        # Get or create admin user
        admin = db.query(User).filter(User.email == "admin@moobaan.com").first()
        if not admin:
            print("❌ Admin user not found")
            return False
        
        # Create a batch for Dec 2025
        batch = BankStatementBatch(
            bank_account_id=test_account.id,
            year=2025,
            month=12,
            source_type="CSV",
            original_filename="Dec25.csv",
            uploaded_by=admin.id,
            status="CONFIRMED",
        )
        db.add(batch)
        db.commit()
        
        print(f"✅ Created test batch for Dec 2025")
        
        # Try to validate same month again - should fail
        result2 = BankStatementValidator.validate_batch(
            db=db,
            bank_account_id=str(test_account.id),
            year=2025,
            month=12,
            transactions=transactions,
        )
        
        if not result2.is_valid():
            print(f"✅ Duplicate month correctly blocked")
            print(f"   Error: {result2.errors[0]}")
        else:
            print(f"❌ Duplicate month validation failed!")
            return False
        
        # Clean up
        db.delete(batch)
        db.delete(test_account)
        db.commit()
        
        print(f"\n✅ All validation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Bank Statement Import - Phase R1 Tests")
    print("=" * 60)
    
    # Test CSV parsing
    parsed_data = test_csv_parsing()
    if not parsed_data:
        print("\n❌ CSV parsing tests failed")
        return
    
    # Test fingerprint generation
    if not test_fingerprint_generation(parsed_data):
        print("\n❌ Fingerprint tests failed")
        return
    
    # Test validation
    if not test_validation():
        print("\n❌ Validation tests failed")
        return
    
    print("\n" + "=" * 60)
    print("✅ All Phase R1 tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
