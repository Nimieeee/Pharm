#!/usr/bin/env python3
"""
Debug script to trace the chat message flow and identify where messages are getting lost
"""

import streamlit as st
import sys
import traceback
from datetime import datetime

def debug_chat_flow():
    """Debug the chat message flow step by step"""
    
    print("🔍 DEBUGGING CHAT MESSAGE FLOW")
    print("=" * 50)
    
    # Step 1: Test imports
    print("\n1. Testing imports...")
    try:
        from app import PharmacologyChat
        print("✅ App imports successful")
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return
    
    # Step 2: Test configuration
    print("\n2. Testing configuration...")
    try:
        from deployment_config import deployment_config
        print(f"✅ Environment: {deployment_config.environment}")
        print(f"✅ Config keys: {list(deployment_config.config.keys())}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return
    
    # Step 3: Test database connection
    print("\n3. Testing database connection...")
    try:
        from supabase import create_client
        db_config = deployment_config.get_database_config()
        
        if not db_config.get('url') or not db_config.get('anon_key'):
            print("❌ Missing database credentials")
            print("   Create .streamlit/secrets.toml with:")
            print("   SUPABASE_URL = 'your_url'")
            print("   SUPABASE_ANON_KEY = 'your_key'")
            return
        
        client = create_client(db_config['url'], db_config['anon_key'])
        print("✅ Supabase client created")
        
        # Test database access
        result = client.table('users').select('count').limit(1).execute()
        print("✅ Database connection verified")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   This is likely why messages aren't appearing!")
        return
    
    # Step 4: Test message store
    print("\n4. Testing message store...")
    try:
        from message_store import MessageStore
        message_store = MessageStore(client)
        print("✅ Message store initialized")
        
        # Test saving a message (with mock user)
        test_user_id = "test-user-123"
        test_message = message_store.save_message(
            user_id=test_user_id,
            role="user", 
            content="Test message",
            metadata={"debug": True}
        )
        
        if test_message:
            print("✅ Test message saved successfully")
            
            # Test retrieving messages
            messages = message_store.get_conversation_history(test_user_id, limit=1)
            if messages:
                print("✅ Test message retrieved successfully")
                
                # Clean up test message
                message_store.delete_user_messages(test_user_id)
                print("✅ Test message cleaned up")
            else:
                print("❌ Could not retrieve test message")
        else:
            print("❌ Could not save test message")
            
    except Exception as e:
        print(f"❌ Message store test failed: {e}")
        traceback.print_exc()
        return
    
    # Step 5: Test authentication components
    print("\n5. Testing authentication...")
    try:
        from auth_manager import AuthenticationManager
        from session_manager import SessionManager
        
        auth_manager = AuthenticationManager()
        session_manager = SessionManager(auth_manager)
        print("✅ Authentication components initialized")
        
        # Check if user is authenticated (will be False in debug mode)
        is_auth = session_manager.is_authenticated()
        print(f"✅ Authentication status: {is_auth}")
        
        if not is_auth:
            print("⚠️  User not authenticated - this could prevent message saving")
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return
    
    # Step 6: Test chat manager
    print("\n6. Testing chat manager...")
    try:
        from chat_manager import ChatManager
        
        chat_manager = ChatManager(client, session_manager)
        print("✅ Chat manager initialized")
        
        # Note: Can't test message sending without authentication
        print("⚠️  Cannot test message sending without authentication")
        
    except Exception as e:
        print(f"❌ Chat manager test failed: {e}")
        return
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSIS COMPLETE")
    print("=" * 50)
    
    print("\nMost likely issues:")
    print("1. Missing .streamlit/secrets.toml file with database credentials")
    print("2. User not authenticated when trying to send messages")
    print("3. Session validation preventing message saving")
    
    print("\nTo fix:")
    print("1. Create .streamlit/secrets.toml with your Supabase credentials")
    print("2. Ensure user authentication is working")
    print("3. Check browser console for JavaScript errors")
    print("4. Check Streamlit logs for authentication errors")

if __name__ == "__main__":
    debug_chat_flow()