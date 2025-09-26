#!/usr/bin/env python3
"""
Apply temporary RLS fix to get chat working
Run this script to disable RLS on messages table temporarily
"""

import streamlit as st
from supabase import create_client

def apply_rls_fix():
    """Apply the temporary RLS fix"""
    try:
        # Get Supabase credentials from secrets
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_service_key = st.secrets.get("SUPABASE_SERVICE_KEY")
        
        if not supabase_service_key:
            print("❌ SUPABASE_SERVICE_KEY not found in secrets")
            print("   You need the service key (not anon key) to modify RLS policies")
            print("   Alternative: Run this SQL in your Supabase SQL editor:")
            print("   ALTER TABLE messages DISABLE ROW LEVEL SECURITY;")
            return False
        
        # Create client with service key (has admin privileges)
        supabase = create_client(supabase_url, supabase_service_key)
        
        # Execute the RLS disable command
        result = supabase.rpc('exec_sql', {
            'sql': 'ALTER TABLE messages DISABLE ROW LEVEL SECURITY;'
        })
        
        print("✅ RLS disabled on messages table!")
        print("   Messages should now save properly")
        print("   Remember to re-enable RLS once authentication is fully fixed")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to apply RLS fix: {e}")
        print("\n📝 Manual fix:")
        print("   1. Go to your Supabase dashboard")
        print("   2. Navigate to SQL Editor")
        print("   3. Run: ALTER TABLE messages DISABLE ROW LEVEL SECURITY;")
        return False

if __name__ == "__main__":
    print("🔧 Applying temporary RLS fix...")
    apply_rls_fix()