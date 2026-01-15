"""
Test Admin Dashboard API metrics
Verify that all calculations are correct
"""
import requests

BASE_URL = "http://127.0.0.1:8000"

def test_admin_dashboard():
    print("="*60)
    print("  TESTING ADMIN DASHBOARD METRICS")
    print("="*60)
    
    # Login as admin
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "admin@moobaan.com",
            "password": "password"
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login successful")
    
    # Get dashboard summary
    print("\n2. Getting dashboard summary...")
    dashboard_response = requests.get(
        f"{BASE_URL}/api/dashboard/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard API failed: {dashboard_response.status_code}")
        print(f"Response: {dashboard_response.text}")
        return
    
    data = dashboard_response.json()
    print("✅ Dashboard API successful")
    
    # Display all metrics
    print("\n" + "="*60)
    print("  ADMIN DASHBOARD SUMMARY")
    print("="*60)
    
    print(f"\n💰 FINANCIAL METRICS:")
    print(f"  Total Outstanding:  ฿{data.get('total_outstanding', 0):,.2f}")
    print(f"  Total Income:       ฿{data.get('total_income', 0):,.2f}")
    print(f"  Current Balance:    ฿{data.get('current_balance', 0):,.2f}")
    print(f"  Total Expenses:     ฿{data.get('total_expenses', 0):,.2f}")
    
    print(f"\n🏠 PROPERTY METRICS:")
    print(f"  Total Houses:       {data.get('total_houses', 0)}")
    print(f"  Active Houses:      {data.get('active_houses', 0)}")
    print(f"  Total Residents:    {data.get('total_residents', 0)}")
    
    print(f"\n📄 INVOICE METRICS:")
    print(f"  Pending Invoices:   {data.get('pending_invoices', 0)}")
    print(f"  Overdue Invoices:   {data.get('overdue_invoices', 0)}")
    
    print(f"\n💳 PAYMENT METRICS:")
    print(f"  Pending Pay-ins:    {data.get('pending_payins', 0)}")
    print(f"  Recent Payments:    {data.get('recent_payments', 0)}")
    
    # Verify calculations
    print("\n" + "="*60)
    print("  VERIFICATION")
    print("="*60)
    
    total_income = data.get('total_income', 0)
    total_outstanding = data.get('total_outstanding', 0)
    current_balance = data.get('current_balance', 0)
    expected_balance = total_income - total_outstanding
    
    print(f"\n📊 Balance Calculation:")
    print(f"  Income:              ฿{total_income:,.2f}")
    print(f"  Outstanding:         ฿{total_outstanding:,.2f}")
    print(f"  Expected Balance:    ฿{expected_balance:,.2f}")
    print(f"  Actual Balance:      ฿{current_balance:,.2f}")
    
    if abs(current_balance - expected_balance) < 0.01:
        print(f"  ✅ Balance calculation CORRECT!")
    else:
        print(f"  ❌ Balance calculation WRONG!")
        print(f"     Difference: ฿{abs(current_balance - expected_balance):,.2f}")
    
    # Check expected values based on current data
    print(f"\n🔍 Expected Values Check:")
    
    # We know from screenshots:
    # - 2 accepted payins: 28/1 (฿2,000) + 28/3 (฿1,700) = ฿3,700
    # - 9 pending invoices: 9 × ฿600 = ฿5,400
    # - 1 pending payin: 28/2 (฿1,800)
    
    expected_income = 3700.0
    expected_outstanding = 5400.0
    expected_pending_payins = 1
    expected_recent_payments = 2
    
    checks = [
        ("Total Income", total_income, expected_income),
        ("Total Outstanding", total_outstanding, expected_outstanding),
        ("Pending Pay-ins", data.get('pending_payins', 0), expected_pending_payins),
        ("Recent Payments", data.get('recent_payments', 0), expected_recent_payments),
    ]
    
    all_correct = True
    for name, actual, expected in checks:
        if abs(actual - expected) < 0.01:
            print(f"  ✅ {name}: {actual} (expected: {expected})")
        else:
            print(f"  ❌ {name}: {actual} (expected: {expected})")
            all_correct = False
    
    print("\n" + "="*60)
    if all_correct:
        print("  ✅ ALL TESTS PASSED!")
    else:
        print("  ❌ SOME TESTS FAILED!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        test_admin_dashboard()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
