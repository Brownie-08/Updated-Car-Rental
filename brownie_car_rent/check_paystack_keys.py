#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brownie_car_rent.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.conf import settings
import environ

def check_keys():
    print("=== Paystack Key Configuration Check ===")
    
    # Check environment variables directly
    print("\n1. Environment Variables (.env file):")
    env = environ.Env()
    
    try:
        public_key_env = env('PAYSTACK_PUBLIC_KEY', default='NOT_SET')
        secret_key_env = env('PAYSTACK_SECRET_KEY', default='NOT_SET')
        
        print(f"   PAYSTACK_PUBLIC_KEY: {public_key_env[:15]}... ({len(public_key_env)} chars)")
        print(f"   PAYSTACK_SECRET_KEY: {secret_key_env[:15]}... ({len(secret_key_env)} chars)")
    except Exception as e:
        print(f"   Error reading env vars: {e}")
    
    # Check Django settings
    print("\n2. Django Settings:")
    public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', 'NOT_SET')
    secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', 'NOT_SET')
    
    print(f"   settings.PAYSTACK_PUBLIC_KEY: {public_key[:15]}... ({len(public_key)} chars)")
    print(f"   settings.PAYSTACK_SECRET_KEY: {secret_key[:15]}... ({len(secret_key)} chars)")
    
    # Validate key formats
    print("\n3. Key Validation:")
    if public_key.startswith('pk_test_'):
        print("   ✅ Public key format is correct (test mode)")
    elif public_key.startswith('pk_live_'):
        print("   ✅ Public key format is correct (live mode)")
    else:
        print(f"   ❌ Public key format is invalid: {public_key[:20]}...")
    
    if secret_key.startswith('sk_test_'):
        print("   ✅ Secret key format is correct (test mode)")
    elif secret_key.startswith('sk_live_'):
        print("   ✅ Secret key format is correct (live mode)")
    else:
        print(f"   ❌ Secret key format is invalid: {secret_key[:20]}...")
    
    # Check Paystack library configuration
    print("\n4. Paystack Library Configuration:")
    try:
        import os as os_check
        paystack_env_key = os_check.environ.get('PAYSTACK_SECRET_KEY', 'NOT_SET')
        print(f"   os.environ['PAYSTACK_SECRET_KEY']: {paystack_env_key[:15]}... ({len(paystack_env_key)} chars)")
        
        from paystackapi.transaction import Transaction
        print("   ✅ Paystack library can be imported")
        
        # Test a simple API call
        try:
            # This should fail gracefully if keys are invalid
            response = Transaction.list()
            print("   ✅ Paystack API connection successful")
        except Exception as e:
            if "Invalid key" in str(e) or "Unauthorized" in str(e):
                print(f"   ❌ Paystack API key validation failed: {e}")
            else:
                print(f"   ⚠️  Paystack API call error (may be network): {e}")
        
    except Exception as e:
        print(f"   ❌ Paystack library error: {e}")
    
    print("\n5. Recommendations:")
    if public_key == 'NOT_SET' or secret_key == 'NOT_SET':
        print("   - Add Paystack keys to your .env file")
    elif not (public_key.startswith('pk_') and secret_key.startswith('sk_')):
        print("   - Check key formats in .env file")
    elif public_key.startswith('pk_test_') and secret_key.startswith('sk_live_'):
        print("   - Key environment mismatch: public is test, secret is live")
    elif public_key.startswith('pk_live_') and secret_key.startswith('sk_test_'):
        print("   - Key environment mismatch: public is live, secret is test")
    else:
        print("   - Keys appear to be properly configured")

if __name__ == "__main__":
    check_keys()