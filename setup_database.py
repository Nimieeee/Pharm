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
    
    st.markdown("**Step 1: Run this in Supabase SQL Editor:**")
    
    with open('simple_chatbot_schema.sql', 'r') as f:
        schema_sql = f.read()
    
    st.code(schema_sql, language='sql')
    
    st.markdown("**Step 2: Then run this update:**")
    
    with open('conversation_schema_update.sql', 'r') as f:
        update_sql = f.read()
    
    st.code(update_sql, language='sql')
    
    st.markdown("""
    ### Instructions:
    1. Copy the SQL from Step 1 above
    2. Go to your Supabase Dashboard → SQL Editor
    3. Paste and run the SQL
    4. Copy the SQL from Step 2 above
    5. Paste and run it in a new query
    6. Refresh this page to test
    """)
    
    if st.button("🔄 Test Schema After Setup"):
        if db.check_schema_exists():
            st.success("✅ Schema setup successful!")
        else:
            st.error("❌ Schema setup incomplete")

if __name__ == "__main__":
    setup_database_schema()