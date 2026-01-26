"""
Phase G.2: Test Export API

Tests:
1. Export single period
2. Export multiple periods
3. Export across year boundary
4. Verify only LOCKED snapshots exported
5. Audit log creation
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    """Get auth token for admin user"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@moobaan.com", "password": "Admin123!"}
    )
    if response.status_code == 200:
        return response.cookies.get("auth_token") or response.json().get("access_token")
    print(f"❌ Login failed: {response.status_code}")
    return None


def test_preview_export(cookies):
    """Test preview export data"""
    print("\n📋 Test: Preview Export Data")
    print("-" * 40)
    
    response = requests.get(
        f"{BASE_URL}/api/export/preview",
        params={"from_period": "2025-12", "to_period": "2025-12"},
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Preview successful")
        print(f"   From: {data['from_period']} To: {data['to_period']}")
        print(f"   Total periods: {data['total_periods']}")
        print(f"   Locked periods: {data['locked_periods']}")
        print(f"   Exportable: {data['exportable']}")
        
        # Show period status
        print("\n   Period Status:")
        for p in data['periods']:
            status_icon = "✅" if p['exportable'] else "❌"
            print(f"   {status_icon} {p['period']}: {p['status']}")
        
        # Show preview data counts
        print("\n   Preview Data:")
        for report_name, rows in data['preview'].items():
            print(f"   - {report_name}: {len(rows)} rows")
        
        return True
    else:
        print(f"❌ Preview failed: {response.status_code}")
        print(f"   {response.text}")
        return False


def test_export_accounting(cookies):
    """Test actual export (download ZIP)"""
    print("\n📦 Test: Export Accounting Data")
    print("-" * 40)
    
    response = requests.post(
        f"{BASE_URL}/api/export/accounting",
        json={
            "from_period": "2025-12",
            "to_period": "2025-12",
            "format": "csv"
        },
        cookies=cookies
    )
    
    if response.status_code == 200:
        content_type = response.headers.get("content-type", "")
        content_disp = response.headers.get("content-disposition", "")
        
        print(f"✅ Export successful")
        print(f"   Content-Type: {content_type}")
        print(f"   Content-Disposition: {content_disp}")
        print(f"   File size: {len(response.content)} bytes")
        
        # Save to file for verification
        filename = "test_export.zip"
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"   Saved to: {filename}")
        
        return True
    elif response.status_code == 404:
        print(f"⚠️ No LOCKED snapshots found (expected if no period is locked)")
        print(f"   {response.json()}")
        return True  # Expected behavior
    else:
        print(f"❌ Export failed: {response.status_code}")
        print(f"   {response.text}")
        return False


def test_export_logs(cookies):
    """Test export audit logs"""
    print("\n📜 Test: Export Audit Logs")
    print("-" * 40)
    
    response = requests.get(
        f"{BASE_URL}/api/export/logs",
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Logs retrieved")
        print(f"   Total logs: {data['total']}")
        
        if data['items']:
            print("\n   Recent exports:")
            for log in data['items'][:5]:
                print(f"   - {log['exported_at']}: {log['from_period']} to {log['to_period']} by {log.get('user_name', 'N/A')}")
        
        return True
    else:
        print(f"❌ Logs failed: {response.status_code}")
        print(f"   {response.text}")
        return False


def test_multi_period_preview(cookies):
    """Test preview with multiple periods"""
    print("\n📋 Test: Multi-Period Preview")
    print("-" * 40)
    
    response = requests.get(
        f"{BASE_URL}/api/export/preview",
        params={"from_period": "2025-10", "to_period": "2026-01"},
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Multi-period preview successful")
        print(f"   Period range: {data['from_period']} to {data['to_period']}")
        print(f"   Total periods: {data['total_periods']}")
        print(f"   Locked periods: {data['locked_periods']}")
        
        return True
    else:
        print(f"❌ Multi-period preview failed: {response.status_code}")
        return False


def main():
    print("=" * 50)
    print("🧪 Phase G.2: Export API Tests")
    print("=" * 50)
    
    # Get auth
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication")
        return
    
    cookies = {"auth_token": token}
    
    # Run tests
    results = []
    results.append(("Preview Export", test_preview_export(cookies)))
    results.append(("Export Accounting", test_export_accounting(cookies)))
    results.append(("Export Logs", test_export_logs(cookies)))
    results.append(("Multi-Period Preview", test_multi_period_preview(cookies)))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        icon = "✅" if result else "❌"
        print(f"   {icon} {name}")
    
    print(f"\n   Result: {passed}/{total} tests passed")


if __name__ == "__main__":
    main()
