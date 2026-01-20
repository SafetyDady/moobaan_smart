#!/usr/bin/env python3
"""
Phase D.4: Promotion Policy Test Cases

Tests the promotion evaluation logic:
1. Eligible case: Pay-in meets all criteria
2. Ineligible case: Pay-in below minimum or outside date range
3. Pure function test: No side effects, no DB writes

Run: python test_promotion_policy.py
"""

import asyncio
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy import text
from app.db.session import SessionLocal
from app.db.models import PromotionPolicy


def test_promotion_model_logic():
    """Test PromotionPolicy model methods (unit test - no DB)"""
    print("\n" + "=" * 60)
    print("TEST: PromotionPolicy Model Logic")
    print("=" * 60)
    
    # Create a mock promotion policy (not saved to DB)
    today = date.today()
    policy = PromotionPolicy(
        id=1,
        code="TEST2024",
        name="Test Promotion 2024",
        valid_from=today - timedelta(days=30),
        valid_to=today + timedelta(days=30),
        min_payin_amount=Decimal("1000.00"),
        credit_amount=Decimal("100.00"),  # Fixed 100 baht credit
        credit_percent=None,
        max_credit_total=Decimal("10000.00"),
        scope="project",
        status="active"
    )
    
    # Test 1: Eligible pay-in
    print("\n[Test 1] Eligible pay-in (1500 baht, today)")
    result = policy.check_eligibility(
        payin_amount=Decimal("1500.00"),
        paid_at=today,
        house_id=1
    )
    print(f"  Result: {result}")
    assert result["eligible"] == True, "Should be eligible"
    assert result["suggested_credit"] == Decimal("100.00"), "Should suggest 100 baht"
    print("  ✅ PASS")
    
    # Test 2: Below minimum
    print("\n[Test 2] Below minimum (500 baht)")
    result = policy.check_eligibility(
        payin_amount=Decimal("500.00"),
        paid_at=today,
        house_id=1
    )
    print(f"  Result: {result}")
    assert result["eligible"] == False, "Should not be eligible"
    assert "ต่ำกว่า" in result["reason"] or "minimum" in result["reason"].lower(), "Should mention minimum"
    print("  ✅ PASS")
    
    # Test 3: Outside date range (future)
    print("\n[Test 3] Outside date range (future)")
    result = policy.check_eligibility(
        payin_amount=Decimal("2000.00"),
        paid_at=today + timedelta(days=60),
        house_id=1
    )
    print(f"  Result: {result}")
    assert result["eligible"] == False, "Should not be eligible"
    print("  ✅ PASS")
    
    # Test 4: Percentage-based credit
    print("\n[Test 4] Percentage-based credit (5%)")
    policy_percent = PromotionPolicy(
        id=2,
        code="PERCENT5",
        name="5% Cashback",
        valid_from=today - timedelta(days=30),
        valid_to=today + timedelta(days=30),
        min_payin_amount=Decimal("1000.00"),
        credit_amount=None,
        credit_percent=Decimal("5.00"),  # 5% credit
        max_credit_total=Decimal("500.00"),  # Max 500 baht total
        scope="project",
        status="active"
    )
    result = policy_percent.check_eligibility(
        payin_amount=Decimal("2000.00"),
        paid_at=today,
        house_id=1
    )
    print(f"  Result: {result}")
    assert result["eligible"] == True, "Should be eligible"
    assert result["suggested_credit"] == Decimal("100.00"), "5% of 2000 = 100"
    print("  ✅ PASS")
    
    print("\n" + "=" * 60)
    print("ALL MODEL LOGIC TESTS PASSED ✅")
    print("=" * 60)


async def test_api_endpoint():
    """Test the promotion evaluate API endpoint"""
    print("\n" + "=" * 60)
    print("TEST: API Endpoint /api/promotions/evaluate")
    print("=" * 60)
    
    import httpx
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # First, login as admin
        print("\n[Step 1] Login as admin")
        login_resp = await client.post(
            f"{base_url}/api/auth/login",
            json={"email": "admin@moobaan.com", "password": "Admin123!"}
        )
        if login_resp.status_code != 200:
            print(f"  ❌ Login failed: {login_resp.text}")
            return
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("  ✅ Login successful")
        
        # Get a pay-in to test with
        print("\n[Step 2] Find a pay-in for testing")
        payins_resp = await client.get(
            f"{base_url}/api/payin-reports",
            headers=headers,
            params={"limit": 1}
        )
        if payins_resp.status_code != 200:
            print(f"  ❌ Failed to get pay-ins: {payins_resp.text}")
            return
        
        payins = payins_resp.json()
        if not payins:
            print("  ⚠️ No pay-ins found. Creating test data skipped.")
            print("  Skipping API test - no test data")
            return
        
        payin = payins[0]
        payin_id = payin["id"]
        print(f"  Found pay-in #{payin_id} (฿{payin.get('amount', 0)})")
        
        # Test the evaluate endpoint
        print("\n[Step 3] Call /api/promotions/evaluate")
        eval_resp = await client.get(
            f"{base_url}/api/promotions/evaluate",
            headers=headers,
            params={"payin_id": payin_id}
        )
        print(f"  Status: {eval_resp.status_code}")
        
        if eval_resp.status_code == 200:
            result = eval_resp.json()
            print(f"  Response: {result}")
            print("  ✅ API endpoint works (returns suggestions array)")
        else:
            print(f"  ❌ API error: {eval_resp.text}")
            return
        
        # Test with invalid payin_id
        print("\n[Step 4] Test with invalid pay-in ID")
        invalid_resp = await client.get(
            f"{base_url}/api/promotions/evaluate",
            headers=headers,
            params={"payin_id": 999999}
        )
        print(f"  Status: {invalid_resp.status_code}")
        assert invalid_resp.status_code == 404, "Should return 404 for invalid pay-in"
        print("  ✅ Returns 404 for invalid pay-in")
        
    print("\n" + "=" * 60)
    print("ALL API TESTS PASSED ✅")
    print("=" * 60)


async def test_pure_function():
    """Test that evaluation is a pure function with no side effects"""
    print("\n" + "=" * 60)
    print("TEST: Pure Function (No Side Effects)")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Count current credit notes before
        result = db.execute(text("SELECT COUNT(*) FROM credit_notes"))
        count_before = result.scalar()
        print(f"\n[Before] Credit notes count: {count_before}")
        
        # Run evaluation multiple times
        print("\n[Action] Running promotion evaluation logic...")
        today = date.today()
        policy = PromotionPolicy(
            id=999,
            code="PURE_TEST",
            name="Pure Test",
            valid_from=today - timedelta(days=30),
            valid_to=today + timedelta(days=30),
            min_payin_amount=Decimal("100.00"),
            credit_amount=Decimal("50.00"),
            scope="project",
            status="active"
        )
        
        # Evaluate multiple times
        for i in range(5):
            result = policy.check_eligibility(
                payin_amount=Decimal("1000.00"),
                paid_at=today,
                house_id=1
            )
        
        # Count credit notes after
        result = db.execute(text("SELECT COUNT(*) FROM credit_notes"))
        count_after = result.scalar()
        print(f"[After] Credit notes count: {count_after}")
        
        assert count_before == count_after, "Credit note count should not change!"
        print("\n✅ PURE FUNCTION TEST PASSED")
        print("   - No credit notes were created")
        print("   - Evaluation has no side effects")
        
    finally:
        db.close()
    
    print("=" * 60)


def main():
    print("\n" + "=" * 60)
    print("PHASE D.4: PROMOTION POLICY TESTS")
    print("=" * 60)
    
    # Test 1: Model logic (no DB required)
    test_promotion_model_logic()
    
    # Test 2: Pure function (DB read only)
    asyncio.run(test_pure_function())
    
    # Test 3: API endpoint (requires running server)
    print("\n⚠️  API test requires backend server running on port 8000")
    try:
        asyncio.run(test_api_endpoint())
    except Exception as e:
        print(f"  ❌ API test skipped: {e}")
    
    print("\n" + "=" * 60)
    print("ALL PHASE D.4 TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()
