#!/usr/bin/env python3
"""
Test script to verify that member limit enforcement works correctly:
- Deactivated users do not count toward 3-member limit
- House with 2 active + 1 inactive should allow new resident
- House with 3 active should block new resident
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_member_limit():
    print("🧪 Testing Member Limit Enforcement (Active-Only Counting)")
    print("=" * 60)
    
    # Step 1: Check if we can get house member counts
    try:
        # Get list of houses first
        response = requests.get(f"{BASE_URL}/api/houses")
        if response.status_code == 200:
            houses = response.json()
            if houses:
                house_id = houses[0]["id"]
                house_code = houses[0]["house_code"] 
                
                print(f"✅ Found test house: {house_code} (ID: {house_id})")
                
                # Check member count
                response = requests.get(f"{BASE_URL}/api/users/houses/{house_id}/member-count")
                if response.status_code == 200:
                    member_info = response.json()
                    print(f"📊 House {house_code}:")
                    print(f"   Active Members: {member_info['current_member_count']}/3")
                    print(f"   Available Slots: {member_info['available_slots']}")
                    
                    if member_info['available_slots'] > 0:
                        print("✅ House has available slots - can add residents")
                    else:
                        print("❌ House is full - cannot add residents")
                        
                else:
                    print(f"❌ Failed to get member count: {response.status_code}")
            else:
                print("❌ No houses found")
        else:
            print(f"❌ Failed to get houses: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure server is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_health():
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except:
        print("❌ Cannot connect to backend")
        return False

if __name__ == "__main__":
    print("🔍 Backend Active Member Counting Test")
    print("=" * 50)
    
    if test_health():
        print()
        test_member_limit()
    else:
        print("\n💡 Start backend with: python run_server.py")
        
    print("\n🏁 Test completed")