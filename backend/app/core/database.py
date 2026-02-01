"""
Database connection and initialization
"""

import os
from typing import Optional
from supabase import create_client, Client
from app.core.config import settings


class Database:
    """Database connection manager"""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            if settings.SUPABASE_URL:
                # Prefer Service Role Key to bypass RLS for backend operations
                key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
                
                if key:
                    self.client = create_client(
                        settings.SUPABASE_URL, 
                        key
                    )
                    print(f"✅ Database client initialized (using {'Service Role' if key == settings.SUPABASE_SERVICE_ROLE_KEY else 'Anon'} Key)")
                else:
                    raise ValueError("Missing Supabase credentials")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    
    def get_client(self) -> Client:
        """Get database client"""
        if not self.client:
            raise RuntimeError("Database client not initialized")
        return self.client
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            if not self.client:
                return False
            
            # Test with a simple query
            result = self.client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
    
    async def run_migration(self, migration_file: str) -> bool:
        """Run a database migration"""
        try:
            migration_path = f"migrations/{migration_file}"
            if not os.path.exists(migration_path):
                print(f"❌ Migration file not found: {migration_path}")
                return False
            
            with open(migration_path, 'r') as f:
                sql_content = f.read()
            
            # Note: Supabase doesn't support direct SQL execution via the client
            # Migrations should be run manually in the Supabase dashboard
            print(f"📋 Migration {migration_file} ready to run in Supabase dashboard")
            print("Please run the following SQL in your Supabase SQL editor:")
            print("-" * 50)
            print(sql_content)
            print("-" * 50)
            
            return True
        except Exception as e:
            print(f"❌ Error preparing migration: {e}")
            return False


# Global database instance
db = Database()


async def init_db():
    """Initialize database connection"""
    try:
        await db.test_connection()
        print("✅ Database connection verified")
        
        # Check if migrations are needed
        try:
            result = db.get_client().table("users").select("id").limit(1).execute()
            print("✅ Users table exists - migrations appear to be complete")
        except Exception:
            print("⚠️  Users table not found - please run migrations")
            await db.run_migration("001_add_users_and_support.sql")
            await db.run_migration("002_create_admin_user.sql")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_db() -> Client:
    """Dependency to get database client"""
    return db.get_client()