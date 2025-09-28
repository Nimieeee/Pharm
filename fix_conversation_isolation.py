#!/usr/bin/env python3
"""
Fix Conversation Isolation Issue
This script helps identify and fix the conversation isolation problem
where documents from one conversation appear in another.
"""

import os
import streamlit as st
from database import SimpleChatbotDB

def check_schema_status():
    """Check if the user session schema update has been applied"""
    db = SimpleChatbotDB()
    
    if not db.client:
        print("❌ No database connection available")
        return False
    
    try:
        # Check if user_session_id column exists in document_chunks table
        result = db.client.rpc('check_column_exists', {
            'table_name': 'document_chunks',
            'column_name': 'user_session_id'
        }).execute()
        
        return result.data[0]['exists'] if result.data else False
        
    except Exception as e:
        # Try a different approach - query the table structure
        try:
            result = db.client.table("document_chunks").select("user_session_id").limit(1).execute()
            return True  # If this works, the column exists
        except Exception:
            return False  # Column doesn't exist

def main():
    print("🔍 Checking conversation isolation status...")
    
    if check_schema_status():
        print("✅ User session schema is already applied")
        print("📋 The conversation isolation should be working correctly")
        
        # Additional check - look for documents without proper isolation
        db = SimpleChatbotDB()
        if db.client:
            try:
                result = db.client.table("document_chunks").select("conversation_id, user_session_id").execute()
                
                if result.data:
                    # Check for documents with default/missing user_session_id
                    anonymous_docs = [doc for doc in result.data if doc.get('user_session_id') in [None, 'anonymous']]
                    
                    if anonymous_docs:
                        print(f"⚠️  Found {len(anonymous_docs)} documents with default user_session_id")
                        print("💡 These documents might appear in multiple conversations")
                    else:
                        print("✅ All documents have proper user session isolation")
                        
            except Exception as e:
                print(f"❌ Error checking document isolation: {str(e)}")
    else:
        print("❌ User session schema update has NOT been applied")
        print("🔧 This is causing the conversation isolation issue")
        print("\n📋 To fix this issue:")
        print("1. Go to your Supabase Dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Run the contents of 'user_session_schema_update.sql'")
        print("4. Restart your Streamlit app")
        
        # Show the SQL content
        try:
            with open('user_session_schema_update.sql', 'r') as f:
                sql_content = f.read()
                print("\n" + "="*50)
                print("SQL TO RUN IN SUPABASE:")
                print("="*50)
                print(sql_content)
                print("="*50)
        except FileNotFoundError:
            print("❌ user_session_schema_update.sql file not found")

if __name__ == "__main__":
    main()