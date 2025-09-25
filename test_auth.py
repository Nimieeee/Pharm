"""
Test script for authentication system
Run this to verify authentication components work correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_auth_imports():
    """Test that all authentication modules can be imported"""
    try:
        from auth_manager import AuthenticationManager, AuthResult, User
        from session_manager import SessionManager, UserSession
        from auth_ui import AuthInterface
        from auth_guard import AuthGuard, RouteProtection
        print("✅ All authentication modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_auth_manager_init():
    """Test authentication manager initialization"""
    try:
        from auth_manager import AuthenticationManager
        auth_manager = AuthenticationManager()
        print("✅ Authentication manager initialized successfully")
        return True
    except Exception as e:
        if "secrets" in str(e).lower():
            print("⚠️  Supabase secrets not configured in Streamlit.")
            return False
        print(f"❌ Authentication manager initialization failed: {e}")
        return False

def test_session_manager_init():
    """Test session manager initialization"""
    try:
        from auth_manager import AuthenticationManager
        from session_manager import SessionManager
        
        auth_manager = AuthenticationManager()
        session_manager = SessionManager(auth_manager)
        print("✅ Session manager initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Session manager initialization failed: {e}")
        return False

def test_auth_guard_init():
    """Test authentication guard initialization"""
    try:
        from auth_manager import AuthenticationManager
        from session_manager import SessionManager
        from auth_guard import AuthGuard
        
        auth_manager = AuthenticationManager()
        session_manager = SessionManager(auth_manager)
        auth_guard = AuthGuard(auth_manager, session_manager)
        print("✅ Authentication guard initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Authentication guard initialization failed: {e}")
        return False

def test_environment_setup():
    """Test Streamlit secrets setup"""
    try:
        import streamlit as st
        required_secrets = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY"
        ]
        
        missing_secrets = []
        for secret in required_secrets:
            try:
                st.secrets[secret]
            except KeyError:
                missing_secrets.append(secret)
        
        if missing_secrets:
            print(f"❌ Missing Streamlit secrets: {', '.join(missing_secrets)}")
            print("Please configure these secrets in your Streamlit app settings.")
            return False
        else:
            print("✅ Streamlit secrets configured")
            return True
    except Exception as e:
        print(f"❌ Error checking Streamlit secrets: {e}")
        print("Note: This test should be run in a Streamlit context.")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Authentication System")
    print("=" * 40)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Module Imports", test_auth_imports),
        ("Auth Manager Init", test_auth_manager_init),
        ("Session Manager Init", test_session_manager_init),
        ("Auth Guard Init", test_auth_guard_init),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed. Check the error above.")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication system is ready.")
        print("\nTo run the app:")
        print("streamlit run auth_app.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()