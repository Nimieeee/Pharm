"""
Database Setup Helper
Run this to set up the database schema for multi-conversation support
"""

import streamlit as st
from database import SimpleChatbotDB

def setup_database_schema():
    """Setup the complete database schema"""
    st.title("🗄️ Database Setup")
    
    st.markdown("""
    ## Multi-Conversation Database Setup
    
    This will set up the required tables for multi-conversation support.
    """)
    
    db = SimpleChatbotDB()
    
    if not db.is_connected():
        st.error("❌ Not connected to database. Please check your Supabase credentials.")
        return
    
    # Check current schema
    st.markdown("### Current Schema Status")
    
    tables_to_check = ["conversations", "messages", "document_chunks"]
    schema_status = {}
    
    for table in tables_to_check:
        try:
            result = db.client.table(table).select("id").limit(1).execute()
            schema_status[table] = "✅ Exists"
        except Exception as e:
            schema_status[table] = f"❌ Missing: {str(e)}"
    
    for table, status in schema_status.items():
        st.write(f"**{table}:** {status}")
    
    # Show SQL to run
    st.markdown("### SQL to Run in Supabase")
    
    st.markdown("**Step 1: Run this COMPLETE setup script in Supabase SQL Editor:**")
    st.info("⚠️ This will clean up any existing function conflicts and set up everything properly")
    
    with open('cleanup_and_setup_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    st.code(schema_sql, language='sql')
    
    st.markdown("**Step 2 (Optional): If you have existing document data, run this migration:**")
    
    with open('migrate_existing_data.sql', 'r') as f:
        migration_sql = f.read()
    
    st.code(migration_sql, language='sql')
    
    st.markdown("""
    ### Instructions:
    1. **Copy the COMPLETE setup SQL** from Step 1 above
    2. **Go to your Supabase Dashboard** → **SQL Editor**
    3. **Paste and run the SQL** (this will clean up conflicts and set up everything)
    4. **If you have existing document data**, copy and run the migration SQL from Step 2
    5. **Refresh this page** to test the setup
    
    ⚠️ **Important:** The cleanup script will remove any existing function conflicts and set up the schema properly.
    """)
    
    if st.button("🔄 Test Schema After Setup"):
        if db.check_schema_exists():
            st.success("✅ Schema setup successful!")
        else:
            st.error("❌ Schema setup incomplete")

if __name__ == "__main__":
    setup_database_schema()