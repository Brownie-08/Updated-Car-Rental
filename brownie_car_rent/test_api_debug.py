#!/usr/bin/env python
"""
Simple API test to debug the chat connection error.
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'brownie_car_rent.settings')
django.setup()

def test_imports():
    """Test if all imports are working correctly."""
    print("Testing imports...")
    
    try:
        from system.nlu_service import nlu_service
        print("✓ NLU service imported successfully")
    except Exception as e:
        print(f"✗ NLU service import failed: {e}")
        return False
    
    try:
        from system.session_model_service import session_model_service
        print("✓ Session model service imported successfully")
    except Exception as e:
        print(f"✗ Session model service import failed: {e}")
        return False
    
    try:
        from system.user_context_service import user_context_service
        print("✓ User context service imported successfully")
    except Exception as e:
        print(f"✗ User context service import failed: {e}")
        return False
    
    try:
        from system.ai_assistant_service import ai_assistant_service
        print("✓ AI assistant service imported successfully")
    except Exception as e:
        print(f"✗ AI assistant service import failed: {e}")
        return False
    
    return True

def test_nlu_service():
    """Test NLU service functionality."""
    print("\nTesting NLU service...")
    
    try:
        from system.nlu_service import nlu_service
        result = nlu_service.analyze_message("I want to book a car")
        print(f"✓ NLU analysis successful: {result}")
        return True
    except Exception as e:
        print(f"✗ NLU analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_session_model():
    """Test session model service."""
    print("\nTesting Session Model service...")
    
    try:
        from system.session_model_service import session_model_service
        model = session_model_service.get_session_model("test_session")
        print(f"✓ Session model created successfully")
        print(f"  - Fleet cars count: {len(model.get('fleet', []))}")
        print(f"  - Categories count: {len(model.get('categories', []))}")
        return True
    except Exception as e:
        print(f"✗ Session model creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_context():
    """Test user context service."""
    print("\nTesting User Context service...")
    
    try:
        from system.user_context_service import user_context_service
        context = user_context_service.get_or_create_context("test_session")
        print(f"✓ User context created successfully")
        print(f"  - User type: {context.user_type}")
        print(f"  - Is returning: {context.is_returning}")
        return True
    except Exception as e:
        print(f"✗ User context creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_assistant():
    """Test AI assistant service."""
    print("\nTesting AI Assistant service...")
    
    try:
        from system.ai_assistant_service import ai_assistant_service
        
        # Test basic message processing
        response = ai_assistant_service.process_message(
            session_id="test_session",
            message="I want to book a car"
        )
        
        print(f"✓ AI assistant processing successful")
        print(f"  - Intent: {response.get('intent')}")
        print(f"  - Response text: {response.get('text', '')[:100]}...")
        return True
        
    except Exception as e:
        print(f"✗ AI assistant processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🔍 Debugging Chat API Connection Error\n")
    print("=" * 50)
    
    all_passed = True
    
    # Test imports
    all_passed &= test_imports()
    
    # Test individual services
    all_passed &= test_nlu_service()
    all_passed &= test_session_model()
    all_passed &= test_user_context()
    all_passed &= test_ai_assistant()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! The services should be working correctly.")
        print("The connection error might be related to:")
        print("- Frontend JavaScript issues")
        print("- CSRF token problems") 
        print("- Network/server configuration")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())