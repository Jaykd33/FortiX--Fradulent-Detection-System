#!/usr/bin/env python3
"""
Test script to verify the FortiX backend is working correctly.
"""

import requests
import json
import time

def test_backend():
    """Test the backend endpoints."""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing FortiX Backend API")
    print("=" * 40)
    
    try:
        # Test root endpoint
        print("1. Testing root endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test dashboard KPIs
        print("\n2. Testing dashboard KPIs...")
        response = requests.get(f"{base_url}/api/dashboard/kpis")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            kpis = response.json()
            print(f"   KPIs: {json.dumps(kpis, indent=2)}")
        
        # Test transactions endpoint
        print("\n3. Testing transactions endpoint...")
        response = requests.get(f"{base_url}/api/v1/transactions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            transactions = response.json()
            print(f"   Transactions count: {len(transactions)}")
        
        # Test live transactions
        print("\n4. Testing live transactions...")
        response = requests.get(f"{base_url}/api/dashboard/live_transactions")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            live_tx = response.json()
            print(f"   Live transactions count: {len(live_tx)}")
        
        # Test dataset info
        print("\n5. Testing dataset info...")
        response = requests.get(f"{base_url}/api/dataset/dataset-info")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            dataset_info = response.json()
            print(f"   Dataset info: {json.dumps(dataset_info, indent=2)}")
        
        print("\n✅ All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend server.")
        print("💡 Make sure the server is running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Error testing backend: {e}")

if __name__ == "__main__":
    test_backend()
