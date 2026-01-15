"""
Test script to verify resident API works correctly
Tests:
1. Resident login
2. /api/auth/me returns house_id and house_code
3. /api/invoices filters by house_id correctly
4. /api/dashboard/summary calculates balance correctly
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_resident_login():
    print_section("TEST 1: Resident Login")
    
    # Use JSON format (LoginRequest model expects email/password)
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "resident@moobaan.com",
            "password": "password"
        }
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"✅ Login successful!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Login failed!")
        print(f"Response: {response.text}")
        return None

def test_auth_me(token):
    print_section("TEST 2: /api/auth/me - Get User Info")
    
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User info retrieved!")
        print(f"Email: {data.get('email')}")
        print(f"Role: {data.get('role')}")
        print(f"House ID: {data.get('house_id')}")
        print(f"House Code: {data.get('house_code')}")
        
        if data.get('role') == 'resident':
            if data.get('house_id'):
                print(f"✅ Resident has house_id: {data.get('house_id')}")
            else:
                print(f"❌ WARNING: Resident has NO house_id!")
                
            if data.get('house_code'):
                print(f"✅ Resident has house_code: {data.get('house_code')}")
            else:
                print(f"❌ WARNING: Resident has NO house_code!")
        
        return data
    else:
        print(f"❌ Failed to get user info!")
        print(f"Response: {response.text}")
        return None

def test_invoices_api(token, house_id):
    print_section("TEST 3: /api/invoices - Filter by house_id")
    
    response = requests.get(
        f"{BASE_URL}/api/invoices",
        params={"house_id": house_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        invoices = response.json()
        print(f"✅ Invoices retrieved: {len(invoices)} invoices")
        
        total = 0
        for inv in invoices:
            # Handle both formats: cycle_year/cycle_month or cycle field
            if 'cycle' in inv:
                cycle = inv['cycle']
            else:
                cycle = f"{inv.get('cycle_year', '?')}-{inv.get('cycle_month', 0):02d}"
            
            amount = inv.get('total_amount') or inv.get('total', 0)
            status = inv.get('status', 'unknown')
            print(f"  • {cycle}: ฿{amount} ({status})")
            total += float(amount)
        
        print(f"\n💰 Total unpaid: ฿{total}")
        
        # Verify all invoices belong to the correct house
        wrong_house = [inv for inv in invoices if inv['house_id'] != house_id]
        if wrong_house:
            print(f"❌ ERROR: Found {len(wrong_house)} invoices from OTHER houses!")
            for inv in wrong_house:
                print(f"  • Invoice {inv['id']} belongs to house {inv['house_id']}")
        else:
            print(f"✅ All invoices belong to house {house_id}")
        
        return invoices
    else:
        print(f"❌ Failed to get invoices!")
        print(f"Response: {response.text}")
        return None

def test_dashboard_summary(token, house_id):
    print_section("TEST 4: /api/dashboard/summary - Balance Calculation")
    
    response = requests.get(
        f"{BASE_URL}/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dashboard summary retrieved!")
        print(f"\nSummary for House {house_id}:")
        print(f"  • Current Balance: ฿{data.get('current_balance')}")
        print(f"  • Total Income: ฿{data.get('total_income')}")
        print(f"  • Total Outstanding: ฿{data.get('total_outstanding')}")
        print(f"  • Pending Invoices: {data.get('pending_invoices')}")
        print(f"  • Recent Payments: {data.get('recent_payments')}")
        
        # Verify calculation
        current_balance = data.get('current_balance', 0)
        total_income = data.get('total_income', 0)
        total_outstanding = data.get('total_outstanding', 0)
        
        expected_balance = total_income - total_outstanding
        
        print(f"\n📊 Balance Check:")
        print(f"  Income: ฿{total_income}")
        print(f"  Outstanding: ฿{total_outstanding}")
        print(f"  Expected Balance: ฿{expected_balance}")
        print(f"  Actual Balance: ฿{current_balance}")
        
        if abs(current_balance - expected_balance) < 0.01:
            print(f"  ✅ Balance calculation is CORRECT!")
        else:
            print(f"  ❌ Balance calculation is WRONG!")
        
        return data
    else:
        print(f"❌ Failed to get dashboard summary!")
        print(f"Response: {response.text}")
        return None

def main():
    print("\n" + "="*60)
    print("  RESIDENT API TEST SUITE")
    print("  Testing: resident@moobaan.com (House 28/1)")
    print("="*60)
    
    # Test 1: Login
    token = test_resident_login()
    if not token:
        print("\n❌ FAILED: Cannot proceed without login token")
        return
    
    # Test 2: Get user info
    user_data = test_auth_me(token)
    if not user_data:
        print("\n❌ FAILED: Cannot proceed without user data")
        return
    
    house_id = user_data.get('house_id')
    house_code = user_data.get('house_code')
    
    if not house_id:
        print("\n❌ FAILED: Resident has no house_id")
        return
    
    # Test 3: Get invoices
    invoices = test_invoices_api(token, house_id)
    
    # Test 4: Get dashboard summary
    summary = test_dashboard_summary(token, house_id)
    
    # Final Summary
    print_section("FINAL SUMMARY")
    print(f"✅ Resident: resident@moobaan.com")
    print(f"✅ House: {house_code} (ID: {house_id})")
    
    if invoices is not None:
        print(f"✅ Invoices: {len(invoices)} found")
    else:
        print(f"❌ Invoices: Failed to retrieve")
    
    if summary is not None:
        print(f"✅ Dashboard: Balance = ฿{summary.get('current_balance')}")
    else:
        print(f"❌ Dashboard: Failed to retrieve")
    
    print("\n" + "="*60)
    print("  TEST COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
