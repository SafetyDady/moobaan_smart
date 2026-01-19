"""
Test Bank Reconciliation API endpoints
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Login as admin
print("🔐 Logging in as admin...")
login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
    "email": "admin@test.com",
    "password": "admin123"
})
assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
token = login_resp.json()["access_token"]
print(f"✅ Logged in successfully")

headers = {"Authorization": f"Bearer {token}"}

# List unmatched transactions
print("\n📋 Listing unmatched credit transactions...")
resp = requests.get(f"{BASE_URL}/api/bank-statements/transactions/unmatched", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    print(f"✅ Found {data['count']} unmatched transactions")
    if data['count'] > 0:
        print(f"   First transaction: {data['items'][0]['id']} - {data['items'][0]['description']} - {data['items'][0]['credit']} THB")
        txn_id = data['items'][0]['id']
    else:
        print("⚠️  No unmatched transactions found")
        txn_id = None
else:
    print(f"❌ Failed: {resp.text}")
    txn_id = None

# List pending payins
print("\n📋 Listing pending pay-ins...")
resp = requests.get(f"{BASE_URL}/api/payin-reports?status=PENDING", headers=headers)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    payins = resp.json()
    print(f"✅ Found {len(payins)} pending pay-ins")
    if len(payins) > 0:
        print(f"   First pay-in: ID {payins[0]['id']} - House {payins[0]['house_code']} - {payins[0]['amount']} THB")
        payin_id = payins[0]['id']
    else:
        print("⚠️  No pending pay-ins found")
        payin_id = None
else:
    print(f"❌ Failed: {resp.text}")
    payin_id = None

# Try matching if we have both
if txn_id and payin_id:
    print(f"\n🔗 Attempting to match transaction {txn_id} with pay-in {payin_id}...")
    resp = requests.post(
        f"{BASE_URL}/api/bank-statements/transactions/{txn_id}/match",
        json={"payin_id": payin_id},
        headers=headers
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"✅ Match successful: {resp.json()['message']}")
        
        # Try to accept without matching (should fail)
        print(f"\n✅ Now the pay-in should be accepted (it's matched)")
        # Verify matching worked
        resp = requests.get(f"{BASE_URL}/api/payin-reports?status=PENDING", headers=headers)
        if resp.status_code == 200:
            matched_payin = next((p for p in resp.json() if p['id'] == payin_id), None)
            if matched_payin:
                print(f"   Pay-in matched_statement_txn_id: {matched_payin.get('matched_statement_txn_id', 'N/A')}")
                print(f"   Pay-in is_matched: {matched_payin.get('is_matched', False)}")
        
        # Try to unmatch
        print(f"\n🔓 Attempting to unmatch transaction {txn_id}...")
        resp = requests.post(
            f"{BASE_URL}/api/bank-statements/transactions/{txn_id}/unmatch",
            headers=headers
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✅ Unmatch successful: {resp.json()['message']}")
        else:
            print(f"❌ Unmatch failed: {resp.text}")
        
    else:
        print(f"❌ Match failed: {resp.text}")
else:
    print("\n⚠️  Skipping match test (missing transaction or pay-in)")

print("\n✅ Test completed!")
