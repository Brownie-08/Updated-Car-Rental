#!/usr/bin/env python
"""
Test script to verify Paystack integration setup
Run this from the Django project directory: python test_paystack_integration.py
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brownie_car_rent.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

# Now we can import Django models
try:
    from system.models import Order, Car
    from system.payment_models import PaymentTransaction, PaymentMethod
    from system.payment_services import PaystackPaymentService
    from django.contrib.auth import get_user_model
    from django.conf import settings
    
    User = get_user_model()
    
    def test_paystack_integration():
        """Test the Paystack integration setup"""
        
        print("🔍 Testing Paystack Integration Setup")
        print("=" * 50)
        
        # Test 1: Check if Paystack library is available
        try:
            from paystackapi.transaction import Transaction
            from paystackapi.verification import Verification
            print("✅ Paystack library is installed and importable")
        except ImportError as e:
            print(f"❌ Paystack library not found: {e}")
            print("   Install with: pip install paystackapi")
            return False
        
        # Test 2: Check environment variables
        public_key = getattr(settings, 'PAYSTACK_PUBLIC_KEY', None)
        secret_key = getattr(settings, 'PAYSTACK_SECRET_KEY', None)
        
        if public_key and public_key.startswith('pk_'):
            print("✅ Paystack public key is configured")
        else:
            print("⚠️  Paystack public key not configured or invalid")
            print("   Add PAYSTACK_PUBLIC_KEY=pk_test_xxxxx to your .env file")
        
        if secret_key and secret_key.startswith('sk_'):
            print("✅ Paystack secret key is configured")
        else:
            print("⚠️  Paystack secret key not configured or invalid")
            print("   Add PAYSTACK_SECRET_KEY=sk_test_xxxxx to your .env file")
        
        # Test 3: Check database models
        try:
            # Check if PaymentMethod model works
            paystack_method, created = PaymentMethod.objects.get_or_create(
                name='paystack',
                defaults={
                    'display_name': 'Card Payment (Paystack)',
                    'description': 'Secure payment via Paystack',
                    'processing_fee_percentage': 1.5
                }
            )
            if created:
                print("✅ PaymentMethod model created for Paystack")
            else:
                print("✅ PaymentMethod model already exists for Paystack")
        except Exception as e:
            print(f"❌ Database model error: {e}")
            print("   Run: python manage.py migrate")
            return False
        
        # Test 4: Check if PaystackPaymentService is working
        try:
            service = PaystackPaymentService()
            print("✅ PaystackPaymentService class is instantiable")
        except Exception as e:
            print(f"❌ PaystackPaymentService error: {e}")
            return False
        
        # Test 5: Template and URL configuration check
        from django.urls import reverse
        try:
            paystack_callback_url = reverse('system:paystack_callback', args=[1])
            paystack_webhook_url = reverse('system:paystack_webhook')
            print("✅ Paystack URLs are properly configured")
            print(f"   Callback URL pattern: {paystack_callback_url}")
            print(f"   Webhook URL pattern: {paystack_webhook_url}")
        except Exception as e:
            print(f"❌ URL configuration error: {e}")
            return False
        
        # Test 6: Check if order creation view has Paystack support
        try:
            from system.views import order_created
            print("✅ Order creation view is accessible")
        except Exception as e:
            print(f"❌ Order creation view error: {e}")
            return False
        
        print("\n🎉 Integration Test Summary:")
        print("=" * 50)
        
        if public_key and secret_key:
            print("✅ Ready to test with real Paystack API keys!")
            print("\n📋 Next Steps:")
            print("1. Start your Django development server: python manage.py runserver")
            print("2. Create a booking and select 'Paystack' as payment method")
            print("3. Use test card: 4084 0840 8408 4081")
            print("4. Check that payment modal appears instead of redirect")
            
            print(f"\n🔗 Test URLs:")
            print(f"   - Booking page: http://127.0.0.1:8000/createOrder/")
            print(f"   - Car list: http://127.0.0.1:8000/carlist/")
            
            print(f"\n🔐 API Keys Status:")
            print(f"   - Public Key: {public_key[:15]}..." if public_key else "   - Public Key: Not set")
            print(f"   - Secret Key: {secret_key[:15]}..." if secret_key else "   - Secret Key: Not set")
        else:
            print("⚠️  Configuration needed - Add your Paystack API keys to .env file")
        
        return True
    
    if __name__ == "__main__":
        test_paystack_integration()
        
except Exception as e:
    print(f"❌ Error setting up test environment: {e}")
    print("Make sure you're running this from the Django project directory")