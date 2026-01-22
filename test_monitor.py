"""Test script for monitoring functionality without waiting for real website changes."""
import sys
from models import get_db, init_db
from monitor import check_website
from email_service import send_notification
from scheduler import run_check

def test_with_mock_url():
    """Test monitoring with a known test URL that contains predictable content."""
    print("Testing monitor with httpbin.org (test service)...")
    
    test_job = {
        'id': 999,
        'name': 'Test Monitor',
        'url': 'https://httpbin.org/html',  # Returns HTML content
        'match_type': 'string',
        'match_pattern': 'Herman Melville',  # This text is always in httpbin.org/html
        'match_condition': 'contains',
        'email_recipient': 'test@example.com',
        'is_active': True
    }
    
    print(f"Checking URL: {test_job['url']}")
    print(f"Looking for pattern: '{test_job['match_pattern']}'")
    print(f"Match condition: {test_job['match_condition']}")
    print("-" * 50)
    
    result = check_website(test_job)
    
    print(f"Success: {result['success']}")
    print(f"Match Found: {result.get('match_found', False)}")
    print(f"Response Time: {result.get('response_time', 0):.2f} seconds")
    print(f"Content Length: {result.get('content_length', 0)} characters")
    
    if result.get('error_message'):
        print(f"Error: {result['error_message']}")
    
    return result

def test_pattern_matching():
    """Test different pattern matching scenarios."""
    print("\n" + "=" * 50)
    print("Testing Pattern Matching")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            'name': 'String Match - Contains',
            'url': 'https://httpbin.org/html',
            'match_type': 'string',
            'match_pattern': 'Herman Melville',
            'match_condition': 'contains',
            'expected': True
        },
        {
            'name': 'String Match - Not Contains',
            'url': 'https://httpbin.org/html',
            'match_type': 'string',
            'match_pattern': 'ThisTextDoesNotExist',
            'match_condition': 'not_contains',
            'expected': True  # Should match because text doesn't exist
        },
        {
            'name': 'Regex Match',
            'url': 'https://httpbin.org/html',
            'match_type': 'regex',
            'match_pattern': r'Herman\s+Melville',
            'match_condition': 'contains',
            'expected': True
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 50)
        
        job = {
            'id': i,
            'name': test_case['name'],
            'url': test_case['url'],
            'match_type': test_case['match_type'],
            'match_pattern': test_case['match_pattern'],
            'match_condition': test_case['match_condition'],
            'email_recipient': 'test@example.com',
            'is_active': True
        }
        
        result = check_website(job)
        match_found = result.get('match_found', False)
        passed = match_found == test_case['expected']
        
        print(f"Pattern: {test_case['match_pattern']}")
        print(f"Expected Match: {test_case['expected']}")
        print(f"Actual Match: {match_found}")
        print(f"Status: {'✓ PASS' if passed else '✗ FAIL'}")
        
        if not result['success']:
            print(f"Error: {result.get('error_message', 'Unknown error')}")

def test_email_notification():
    """Test email notification functionality."""
    print("\n" + "=" * 50)
    print("Testing Email Notification")
    print("=" * 50)
    
    test_job = {
        'name': 'Test Email Notification',
        'url': 'https://example.com',
        'email_recipient': input("Enter your email address to test: ").strip()
    }
    
    test_status = {
        'match_found': True,
        'response_time': 0.5,
        'content_length': 1000
    }
    
    print(f"\nSending test email to {test_job['email_recipient']}...")
    success = send_notification(test_job, test_status, is_test=True)
    
    if success:
        print("✓ Email sent successfully!")
        print("Check your inbox for the test email.")
    else:
        print("✗ Failed to send email. Check your SMTP configuration.")

def main():
    """Main test function."""
    print("=" * 50)
    print("Website Monitor - Test Suite")
    print("=" * 50)
    print("\nThis script allows you to test monitoring functionality")
    print("without waiting for real websites to change.\n")
    
    # Initialize database
    init_db()
    
    while True:
        print("\nSelect a test:")
        print("1. Test basic monitoring with httpbin.org")
        print("2. Test pattern matching scenarios")
        print("3. Test email notification")
        print("4. Run all tests")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            test_with_mock_url()
        elif choice == '2':
            test_pattern_matching()
        elif choice == '3':
            test_email_notification()
        elif choice == '4':
            test_with_mock_url()
            test_pattern_matching()
            print("\nSkipping email test (requires user input)")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
