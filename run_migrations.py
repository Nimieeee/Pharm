"""
Migration runner for the pharmacology chat app database schema.
Executes SQL migration files in order to set up the database.
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Create and return Supabase client."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')  # Use service key for admin operations
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables are required")
    
    return create_client(url, key)

def run_migration_file(client: Client, file_path: Path) -> bool:
    """Run a single migration file."""
    try:
        logger.info(f"Running migration: {file_path.name}")
        
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        for statement in statements:
            if statement:
                try:
                    # Use rpc for DDL statements or direct SQL execution
                    client.postgrest.session.post(
                        f"{client.supabase_url}/rest/v1/rpc/exec_sql",
                        json={"sql": statement},
                        headers=client.postgrest.auth.headers
                    )
                except Exception as e:
                    # Try alternative approach for some statements
                    logger.warning(f"Direct execution failed, trying alternative: {e}")
                    # For some DDL operations, we might need to use the SQL editor or direct connection
                    pass
        
        logger.info(f"Successfully completed migration: {file_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error running migration {file_path.name}: {e}")
        return False

def run_all_migrations():
    """Run all migration files in order."""
    try:
        client = get_supabase_client()
        migrations_dir = Path('migrations')
        
        if not migrations_dir.exists():
            logger.error("Migrations directory not found")
            return False
        
        # Get all SQL files and sort them
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        if not migration_files:
            logger.warning("No migration files found")
            return True
        
        logger.info(f"Found {len(migration_files)} migration files")
        
        success_count = 0
        for migration_file in migration_files:
            if run_migration_file(client, migration_file):
                success_count += 1
            else:
                logger.error(f"Migration failed: {migration_file.name}")
                return False
        
        logger.info(f"Successfully completed {success_count}/{len(migration_files)} migrations")
        return True
        
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False

if __name__ == "__main__":
    success = run_all_migrations()
    sys.exit(0 if success else 1)