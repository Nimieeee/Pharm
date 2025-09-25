"""
Database Initialization and Schema Validation
Handles database setup and provides graceful fallbacks for missing tables
"""

import logging
from typing import Dict, Any, Optional, List
from supabase import Client

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Handles database initialization and schema validation"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.required_tables = ['users', 'messages', 'documents']
        self.schema_status = {}
    
    def check_database_schema(self) -> Dict[str, Any]:
        """Check if required database tables exist"""
        status = {
            'initialized': False,
            'missing_tables': [],
            'available_tables': [],
            'needs_migration': False
        }
        
        try:
            # Try to query each required table
            for table in self.required_tables:
                try:
                    # Simple query to check if table exists and has expected columns
                    result = self.client.table(table).select("*").limit(1).execute()
                    status['available_tables'].append(table)
                    logger.info(f"Table '{table}' is available")
                except Exception as e:
                    status['missing_tables'].append(table)
                    logger.warning(f"Table '{table}' is not available: {e}")
            
            # Check if all tables are available
            status['initialized'] = len(status['missing_tables']) == 0
            status['needs_migration'] = len(status['missing_tables']) > 0
            
            self.schema_status = status
            return status
            
        except Exception as e:
            logger.error(f"Database schema check failed: {e}")
            status['error'] = str(e)
            return status
    
    def get_migration_instructions(self) -> List[str]:
        """Get instructions for setting up the database"""
        return [
            "🔧 Database Setup Required",
            "",
            "Your Supabase database needs to be initialized with the required tables.",
            "",
            "**Option 1: Run SQL directly in Supabase Dashboard**",
            "1. Go to your Supabase project dashboard",
            "2. Navigate to SQL Editor",
            "3. Copy and paste the contents of these files in order:",
            "   - migrations/001_initial_schema.sql",
            "   - migrations/002_rls_policies.sql", 
            "   - migrations/003_vector_functions.sql",
            "4. Execute each migration file",
            "",
            "**Option 2: Use Supabase CLI (if you have it installed)**",
            "1. Clone the repository locally",
            "2. Set environment variables:",
            "   - SUPABASE_URL=your_project_url",
            "   - SUPABASE_SERVICE_KEY=your_service_key",
            "3. Run: python run_migrations.py",
            "",
            "**Option 3: Manual Table Creation**",
            "If you prefer, you can create the tables manually using the SQL",
            "provided in the migration files.",
            "",
            "Once the database is set up, refresh this page to continue."
        ]
    
    def create_fallback_user(self, email: str) -> Optional[str]:
        """Create a fallback user entry if users table exists"""
        try:
            if 'users' in self.schema_status.get('available_tables', []):
                result = self.client.table('users').insert({
                    'email': email,
                    'preferences': {},
                    'subscription_tier': 'free'
                }).execute()
                
                if result.data:
                    return result.data[0]['id']
            return None
        except Exception as e:
            logger.error(f"Failed to create fallback user: {e}")
            return None
    
    def get_database_status_message(self) -> str:
        """Get a user-friendly database status message"""
        if not self.schema_status:
            return "Database status unknown. Please check your connection."
        
        if self.schema_status['initialized']:
            return "✅ Database is properly initialized and ready to use."
        
        missing_count = len(self.schema_status['missing_tables'])
        available_count = len(self.schema_status['available_tables'])
        
        if missing_count == len(self.required_tables):
            return "❌ Database is not initialized. Please run the migration scripts."
        else:
            return f"⚠️ Partial database setup: {available_count}/{len(self.required_tables)} tables available."

def check_and_initialize_database(supabase_client: Client) -> DatabaseInitializer:
    """Check database status and return initializer"""
    initializer = DatabaseInitializer(supabase_client)
    initializer.check_database_schema()
    return initializer

def render_database_setup_instructions(initializer: DatabaseInitializer):
    """Render database setup instructions in Streamlit"""
    import streamlit as st
    
    st.error("🔧 Database Setup Required")
    
    status = initializer.schema_status
    if status.get('missing_tables'):
        st.write("**Missing Tables:**")
        for table in status['missing_tables']:
            st.write(f"- {table}")
    
    if status.get('available_tables'):
        st.write("**Available Tables:**")
        for table in status['available_tables']:
            st.write(f"✅ {table}")
    
    st.markdown("---")
    
    instructions = initializer.get_migration_instructions()
    for instruction in instructions:
        if instruction.startswith("**"):
            st.markdown(instruction)
        elif instruction.startswith("🔧"):
            st.subheader(instruction)
        elif instruction == "":
            st.write("")
        else:
            st.write(instruction)
    
    st.markdown("---")
    st.info("💡 **Tip**: The easiest way is to copy the SQL from the migration files and run them in your Supabase SQL Editor.")
    
    # Add refresh button
    if st.button("🔄 Check Database Status Again"):
        st.rerun()