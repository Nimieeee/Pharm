
import os
from supabase import create_client, Client
from app.core.config import settings

def run_migration():
    print("🚀 Running Migration 014: Add Translations Columns")
    
    # Initialize Supabase Client
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    db: Client = create_client(url, key)
    
    # Read SQL file
    with open("/var/www/pharmgpt-backend/migrations/014_add_translations_columns.sql", "r") as f:
        sql_content = f.read()
    
    # Execute SQL (splitting by statement if needed, or use rpc if available, but raw execution via postgrest is limited)
    # Actually, supabase-py doesn't support raw SQL execution easily unless via RPC.
    # But we can try to use psycopg2 if available, or just use the dashboard?
    # Wait, the user has been managing this. Let's check dependencies.
    # If psycopg2 is installed, we use that.
    
    try:
        import psycopg2
        # We need the connection string. It is usually in DATABASE_URL env var.
        conn_str = os.getenv("DATABASE_URL")
        # If not set, we might fail.
        if not conn_str:
            # Construct from components if possible, or fail.
            # Usually Supabase gives a postgres connection string.
            # Let's try to assume it's in .env
            pass
            
        print(f"🔌 Connecting to DB...")
        conn = psycopg2.connect(conn_str)
        cur = conn.cursor()
        
        print("📝 Executing SQL...")
        cur.execute(sql_content)
        conn.commit()
        
        print("✅ Migration applied successfully!")
        cur.close()
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 not installed. Cannot run raw SQL migration from script.")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
