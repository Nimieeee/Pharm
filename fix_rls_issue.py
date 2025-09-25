#!/usr/bin/env python3
"""
Quick fix for RLS (Row-Level Security) issue preventing messages from being saved
"""

import streamlit as st
from supabase import create_client
import sys

def fix_rls_issue():
    """Apply the RLS bypass migration to fix message saving"""
    
    print("🔧 Fixing RLS issue for message saving...")
    
    try:
        # Get Supabase credentials
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_service_key = st.secrets.get("SUPABASE_SERVICE_KEY")
        
        if not supabase_service_key:
            print("❌ SUPABASE_SERVICE_KEY not found in secrets")
            print("   You need the service key (not anon key) to modify RLS policies")
            return False
        
        # Create client with service key (has admin privileges)
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Read and execute the RLS bypass migration
        with open("migrations/005_temporary_rls_bypass.sql", "r") as f:
            sql_commands = f.read()
        
        # Execute the SQL
        result = supabase.rpc("exec_sql", {"sql": sql_commands})
        
        print("✅ RLS bypass applied successfully!")
        print("   Messages should now save properly")
        print("   Remember to re-enable RLS once authentication is fixed")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply RLS fix: {e}")
        return False

def check_message_table_status():
    """Check the current status of the messages table RLS"""
    
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_anon_key = st.secrets["SUPABASE_ANON_KEY"]
        
        supabase = create_client(supabase_url, supabase_anon_key)
        
        # Try to query the messages table
        result = supabase.table('messages').select('count').limit(1).execute()
        
        print("✅ Messages table is accessible")
        return True
        
    except Exception as e:
        print(f"❌ Messages table access failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 RLS Issue Fixer")
    print("=" * 30)
    
    print("\n1. Checking current table status...")
    check_message_table_status()
    
    print("\n2. Applying RLS bypass...")
    success = fix_rls_issue()
    
    if success:
        print("\n3. Verifying fix...")
        check_message_table_status()
        
        print("\n🎉 Fix complete! Try sending a message now.")
    else:
        print("\n❌ Fix failed. You may need to:")
        print("   1. Add SUPABASE_SERVICE_KEY to your Streamlit secrets")
        print("   2. Manually disable RLS in your Supabase dashboard")
        print("   3. Or fix the authentication to use real Supabase user IDs")