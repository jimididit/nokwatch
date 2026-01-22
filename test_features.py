"""Test script for Phase 0 and Phase 1 features."""
import sys
import time
import requests
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_EMAIL = input("Enter your email address for testing: ").strip()

if not TEST_EMAIL:
    print("Error: Email address is required")
    sys.exit(1)

print(f"\n{'='*60}")
print("Nokwatch Phase 0 & Phase 1 Feature Testing")
print(f"{'='*60}\n")

def test_api_endpoint(method, endpoint, data=None, description=""):
    """Test an API endpoint."""
    print(f"Testing: {description}")
    print(f"  {method} {endpoint}")
    
    try:
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(f"{BASE_URL}{endpoint}", json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", timeout=10)
        
        print(f"  Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"  Response: {result}")
        except:
            print(f"  Response: {response.text[:200]}")
        
        success = response.status_code in [200, 201]
        print(f"  Result: {'✓ PASS' if success else '✗ FAIL'}\n")
        return success, result if success else None
        
    except requests.exceptions.ConnectionError:
        print(f"  Error: Could not connect to {BASE_URL}")
        print(f"  Make sure the Flask app is running!\n")
        return False, None
    except Exception as e:
        print(f"  Error: {e}\n")
        return False, None

def main():
    """Run all tests."""
    results = []
    
    # Test 1: Health Check
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    success, _ = test_api_endpoint("GET", "/api/health", description="Health check endpoint")
    results.append(("Health Check", success))
    
    if not success:
        print("ERROR: Cannot connect to server. Please start the Flask app first.")
        return
    
    # Test 2: Test Email
    print("=" * 60)
    print("TEST 2: Test Email Functionality")
    print("=" * 60)
    success, _ = test_api_endpoint(
        "POST", 
        "/api/test-email", 
        data={"email": TEST_EMAIL},
        description="Send test email"
    )
    results.append(("Test Email", success))
    
    if success:
        print(f"  Check your inbox at {TEST_EMAIL} for the test email.\n")
    
    # Test 3: Create Monitor with Basic Settings
    print("=" * 60)
    print("TEST 3: Create Monitor (Basic)")
    print("=" * 60)
    test_job = {
        "name": "Test Monitor - Basic",
        "url": "https://httpbin.org/html",
        "check_interval": 300,
        "match_type": "string",
        "match_pattern": "Herman Melville",
        "match_condition": "contains",
        "email_recipient": TEST_EMAIL,
        "is_active": True
    }
    success, result = test_api_endpoint(
        "POST",
        "/api/jobs",
        data=test_job,
        description="Create basic monitor"
    )
    results.append(("Create Basic Monitor", success))
    
    job_id = None
    if success and result:
        job_id = result.get('id')
        print(f"  Created job ID: {job_id}\n")
    
    # Test 4: Create Monitor with Advanced Features
    print("=" * 60)
    print("TEST 4: Create Monitor (Advanced Features)")
    print("=" * 60)
    advanced_job = {
        "name": "Test Monitor - Advanced",
        "url": "https://httpbin.org/status/200",
        "check_interval": 300,
        "match_type": "string",
        "match_pattern": "test",
        "match_condition": "contains",
        "email_recipient": TEST_EMAIL,
        "is_active": True,
        "notification_throttle_seconds": 300,
        "status_code_monitor": 200,
        "response_time_threshold": 5.0
    }
    success, result = test_api_endpoint(
        "POST",
        "/api/jobs",
        data=advanced_job,
        description="Create monitor with advanced features"
    )
    results.append(("Create Advanced Monitor", success))
    
    advanced_job_id = None
    if success and result:
        advanced_job_id = result.get('id')
        print(f"  Created advanced job ID: {advanced_job_id}\n")
    
    # Test 5: Get All Jobs
    print("=" * 60)
    print("TEST 5: Get All Jobs")
    print("=" * 60)
    success, result = test_api_endpoint("GET", "/api/jobs", description="List all monitors")
    results.append(("Get All Jobs", success))
    
    if success and result:
        jobs = result.get('jobs', [])
        print(f"  Found {len(jobs)} monitor(s)\n")
    
    # Test 6: Run Manual Check
    if job_id:
        print("=" * 60)
        print("TEST 6: Manual Check Trigger")
        print("=" * 60)
        success, _ = test_api_endpoint(
            "POST",
            f"/api/jobs/{job_id}/run-check",
            description="Trigger manual check"
        )
        results.append(("Manual Check", success))
        if success:
            print("  Waiting 3 seconds for check to complete...\n")
            time.sleep(3)
    
    # Test 7: Get Check History
    if job_id:
        print("=" * 60)
        print("TEST 7: Get Check History")
        print("=" * 60)
        success, result = test_api_endpoint(
            "GET",
            f"/api/jobs/{job_id}/history",
            description="Get check history"
        )
        results.append(("Get Check History", success))
        
        if success and result:
            history = result.get('history', [])
            print(f"  Found {len(history)} history entry/entries")
            if history:
                latest = history[0]
                print(f"  Latest check: {latest.get('status')}, HTTP Status: {latest.get('http_status_code', 'N/A')}")
            print()
    
    # Test 8: Update Monitor
    if job_id:
        print("=" * 60)
        print("TEST 8: Update Monitor")
        print("=" * 60)
        update_data = {
            "notification_throttle_seconds": 600,
            "response_time_threshold": 3.0
        }
        success, _ = test_api_endpoint(
            "PUT",
            f"/api/jobs/{job_id}",
            data=update_data,
            description="Update monitor settings"
        )
        results.append(("Update Monitor", success))
    
    # Test 9: Add Notification Channel (Discord - will fail without webhook, but tests API)
    if job_id:
        print("=" * 60)
        print("TEST 9: Add Notification Channel")
        print("=" * 60)
        channel_data = {
            "channel_type": "email",
            "config": {
                "email_addresses": [TEST_EMAIL, TEST_EMAIL]  # Test multiple emails
            }
        }
        success, _ = test_api_endpoint(
            "POST",
            f"/api/jobs/{job_id}/notification-channels",
            data=channel_data,
            description="Add email notification channel"
        )
        results.append(("Add Notification Channel", success))
    
    # Test 10: Get Notification Channels
    if job_id:
        print("=" * 60)
        print("TEST 10: Get Notification Channels")
        print("=" * 60)
        success, result = test_api_endpoint(
            "GET",
            f"/api/jobs/{job_id}/notification-channels",
            description="Get notification channels"
        )
        results.append(("Get Notification Channels", success))
        
        if success and result:
            channels = result.get('channels', [])
            print(f"  Found {len(channels)} channel(s)\n")
    
    # Cleanup: Delete test jobs
    print("=" * 60)
    print("CLEANUP: Deleting Test Jobs")
    print("=" * 60)
    if job_id:
        test_api_endpoint("DELETE", f"/api/jobs/{job_id}", description="Delete basic test job")
    if advanced_job_id:
        test_api_endpoint("DELETE", f"/api/jobs/{advanced_job_id}", description="Delete advanced test job")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
