"""
Test Accept Workflow: Match → Accept → Ledger Creation

This test validates the complete workflow:
1. Match a Pay-in with a Bank Transaction
2. Accept the matched Pay-in
3. Verify immutable ledger (IncomeTransaction) is created
4. Verify references to both pay-in and bank transaction
"""

import requests
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

# Admin credentials
ADMIN_EMAIL = "admin@moobaan.com"
ADMIN_PASSWORD = "password"


def login_admin():
    """Login as admin and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data["access_token"]


def get_pending_payins(token):
    """Get all PENDING pay-ins"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/payin-reports?status=PENDING", headers=headers)
    assert response.status_code == 200, f"Failed to get payins: {response.text}"
    return response.json()


def get_unmatched_bank_transactions(token):
    """Get all unmatched bank transactions (credits only)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/bank-statements/transactions/unmatched", headers=headers)
    assert response.status_code == 200, f"Failed to get transactions: {response.text}"
    # API returns {"items": [...], "count": X}
    data = response.json()
    return data.get("items", [])


def match_payin_with_bank_txn(token, bank_txn_id, payin_id):
    """Match a pay-in with a bank transaction"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/bank-statements/transactions/{bank_txn_id}/match",
        headers=headers,
        json={"payin_id": payin_id}
    )
    assert response.status_code == 200, f"Matching failed: {response.text}"
    print(f"✅ MATCH: Pay-in #{payin_id} ↔ Bank Txn {bank_txn_id}")
    return response.json()


def accept_payin(token, payin_id):
    """Accept a matched pay-in (creates ledger entry)"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/payin-reports/{payin_id}/accept",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ ACCEPT FAILED: {response.json()}")
        return None
    
    data = response.json()
    print(f"✅ ACCEPT: Pay-in #{payin_id} → Status: {data['status']}")
    
    if "ledger" in data:
        ledger = data["ledger"]
        print(f"   📒 Ledger Created:")
        print(f"      - ID: {ledger['id']}")
        print(f"      - Amount: {ledger['amount']}")
        print(f"      - Bank Txn ID: {ledger['reference_bank_transaction_id']}")
        print(f"      - Received At: {ledger['received_at']}")
    
    return data


def test_reject_unmatched_accept(token):
    """Test: Cannot accept pay-in that is not matched"""
    print("\n🧪 TEST 1: Reject Accept on Unmatched Pay-in")
    
    payins = get_pending_payins(token)
    if not payins:
        print("⏭️  No PENDING payins to test")
        return
    
    # Find unmatched pay-in
    unmatched = next((p for p in payins if not p["is_matched"]), None)
    if not unmatched:
        print("⏭️  All PENDING payins are matched")
        return
    
    # Try to accept unmatched pay-in (should fail)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/payin-reports/{unmatched['id']}/accept",
        headers=headers
    )
    
    if response.status_code == 400:
        error = response.json()
        if "Must be matched" in error["detail"]:
            print(f"✅ PASS: Correctly rejected unmatched pay-in")
            print(f"   Error: {error['detail']}")
        else:
            print(f"❌ FAIL: Wrong error message: {error['detail']}")
    else:
        print(f"❌ FAIL: Expected 400, got {response.status_code}")


def test_match_and_accept_workflow(token):
    """Test: Complete workflow - Match → Accept → Ledger Creation"""
    print("\n🧪 TEST 2: Complete Match → Accept → Ledger Workflow")
    
    # Get unmatched pay-in and bank transaction
    payins = get_pending_payins(token)
    bank_txns = get_unmatched_bank_transactions(token)  # Now returns list directly
    
    if not payins:
        print("⏭️  No PENDING payins")
        return
    
    if not bank_txns:
        print("⏭️  No unmatched bank transactions")
        return
    
    # Find unmatched pay-in
    unmatched_payin = next((p for p in payins if not p["is_matched"]), None)
    if not unmatched_payin:
        print("⏭️  All PENDING payins are already matched")
        return
    
    # Find bank transaction with matching amount
    matching_bank_txn = next(
        (txn for txn in bank_txns if float(txn["credit"]) == float(unmatched_payin["amount"])),
        None
    )
    
    if not matching_bank_txn:
        # Use first bank txn and first matching payin with that amount
        bank_txn = bank_txns[0]
        matching_payin = next(
            (p for p in payins if not p["is_matched"] and float(p["amount"]) == float(bank_txn["credit"])),
            None
        )
        if not matching_payin:
            print(f"⏭️  No pay-in found with amount matching any bank transaction")
            return
        unmatched_payin = matching_payin
    else:
        bank_txn = matching_bank_txn
    
    print(f"\n📋 Setup:")
    print(f"   Pay-in #{unmatched_payin['id']}: ฿{unmatched_payin['amount']} (House {unmatched_payin['house_number']})")
    print(f"   Bank Txn: ฿{bank_txn['credit']} - {bank_txn['description'][:50]}")
    
    # Step 1: Match
    print(f"\n🔗 Step 1: Match Pay-in with Bank Transaction")
    match_result = match_payin_with_bank_txn(token, bank_txn["id"], unmatched_payin["id"])
    
    # Step 2: Accept (creates ledger)
    print(f"\n✅ Step 2: Accept Pay-in (Create Ledger Entry)")
    accept_result = accept_payin(token, unmatched_payin["id"])
    
    if accept_result is None:
        print("❌ FAIL: Accept failed")
        return
    
    # Validation
    print(f"\n🔍 Validation:")
    assert accept_result["status"] == "ACCEPTED", f"Status should be ACCEPTED, got {accept_result['status']}"
    print(f"   ✓ Pay-in status = ACCEPTED")
    
    assert "ledger" in accept_result, "Ledger entry should be created"
    print(f"   ✓ Ledger entry created")
    
    ledger = accept_result["ledger"]
    assert ledger["reference_bank_transaction_id"] == bank_txn["id"], "Ledger should reference bank transaction"
    print(f"   ✓ Ledger references correct bank transaction")
    
    assert float(ledger["amount"]) == float(unmatched_payin["amount"]), "Ledger amount should match pay-in amount"
    print(f"   ✓ Ledger amount matches pay-in amount")
    
    print(f"\n✅ TEST PASSED: Complete workflow executed successfully")


def test_idempotency_double_accept(token):
    """Test: Cannot accept the same pay-in twice"""
    print("\n🧪 TEST 3: Idempotency - Cannot Accept Twice")
    
    # Get already accepted pay-in
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/payin-reports?status=ACCEPTED", headers=headers)
    
    if response.status_code != 200:
        print("⏭️  Cannot fetch accepted payins")
        return
    
    accepted_payins = response.json()
    if not accepted_payins:
        print("⏭️  No accepted payins to test")
        return
    
    payin = accepted_payins[0]
    print(f"   Testing with Pay-in #{payin['id']} (already ACCEPTED)")
    
    # Try to accept again (should fail)
    response = requests.post(
        f"{BASE_URL}/api/payin-reports/{payin['id']}/accept",
        headers=headers
    )
    
    if response.status_code == 400:
        error = response.json()
        if "already accepted" in error["detail"].lower():
            print(f"✅ PASS: Correctly rejected double accept")
            print(f"   Error: {error['detail']}")
        else:
            print(f"⚠️  PARTIAL: Rejected but wrong message: {error['detail']}")
    else:
        print(f"❌ FAIL: Expected 400, got {response.status_code}")


def main():
    """Run all tests"""
    print("=" * 70)
    print("🚀 Accept → Ledger Creation Workflow Tests")
    print("=" * 70)
    
    # Login
    print("\n🔐 Logging in as admin...")
    token = login_admin()
    print(f"✅ Logged in successfully")
    
    # Run tests
    test_reject_unmatched_accept(token)
    test_match_and_accept_workflow(token)
    test_idempotency_double_accept(token)
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
