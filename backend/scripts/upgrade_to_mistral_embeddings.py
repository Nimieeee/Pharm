#!/usr/bin/env python3
"""
Script to upgrade database to use Mistral embeddings (1024 dimensions)
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from app.core.config import settings


def get_db() -> Client:
    """Get database client"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def check_current_schema(db: Client):
    """Check current database schema"""
    print("🔍 Checking current database schema...")
    
    try:
        # Check if document_chunks table exists
        result = db.table("document_chunks").select("*").limit(1).execute()
        print(f"✅ document_chunks table exists with {len(result.data)} sample records")
        
        # Check embedding dimension by querying a record
        if result.data:
            sample = result.data[0]
            if 'embedding' in sample and sample['embedding']:
                embedding_dim = len(sample['embedding'])
                print(f"📊 Current embedding dimension: {embedding_dim}")
                return embedding_dim
        
        print("⚠️ No embeddings found in database")
        return None
        
    except Exception as e:
        print(f"❌ Error checking schema: {e}")
        return None


def check_migration_status(db: Client):
    """Check if migration has been applied"""
    print("\n🔍 Checking migration status...")
    
    try:
        # Try to call the new function
        result = db.rpc('get_embedding_migration_stats').execute()
        
        if result.data:
            stats = result.data[0]
            print(f"✅ Migration functions exist")
            print(f"📊 Total chunks: {stats.get('total_chunks', 0)}")
            print(f"📊 Old embeddings: {stats.get('old_embeddings', 0)}")
            print(f"📊 New embeddings: {stats.get('new_embeddings', 0)}")
            print(f"📊 Pending migration: {stats.get('pending_migration', 0)}")
            print(f"📊 Versions: {stats.get('embedding_versions', [])}")
            return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Migration not yet applied: {e}")
        return False


def apply_migration(db: Client):
    """Apply the migration SQL"""
    print("\n🚀 Applying migration...")
    
    migration_file = Path(__file__).parent.parent / "migrations" / "004_upgrade_to_mistral_embeddings.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("📝 Executing migration SQL...")
        # Note: Supabase client doesn't support raw SQL execution
        # You need to run this manually in Supabase SQL editor
        print("\n" + "="*80)
        print("⚠️  MANUAL STEP REQUIRED:")
        print("="*80)
        print("\nPlease run the following SQL in your Supabase SQL Editor:")
        print(f"\n1. Go to: {settings.SUPABASE_URL.replace('https://', 'https://app.')}/project/_/sql")
        print(f"2. Copy the contents of: {migration_file}")
        print("3. Execute the SQL")
        print("\nOr run this command:")
        print(f"cat {migration_file} | psql <your-database-url>")
        print("\n" + "="*80)
        
        return False
        
    except Exception as e:
        print(f"❌ Error reading migration file: {e}")
        return False


def main():
    """Main function"""
    print("="*80)
    print("Mistral Embeddings Migration Tool")
    print("="*80)
    
    # Get database client
    db = get_db()
    
    # Check current schema
    current_dim = check_current_schema(db)
    
    # Check migration status
    migration_applied = check_migration_status(db)
    
    if not migration_applied:
        print("\n⚠️  Migration has not been applied yet")
        apply_migration(db)
        print("\n💡 After applying the migration, run this script again to verify")
        return
    
    if current_dim == 1024:
        print("\n✅ Database is already using 1024-dimensional embeddings!")
        print("✅ Mistral embeddings are ready to use")
    elif current_dim == 384:
        print("\n⚠️  Database is using 384-dimensional embeddings")
        print("💡 Migration functions are available but table hasn't been swapped")
        print("\nTo complete migration:")
        print("1. Backup existing data: SELECT backup_existing_embeddings();")
        print("2. Migrate structure: SELECT migrate_to_new_embeddings();")
        print("3. Re-upload documents to generate new embeddings")
        print("4. Swap tables: SELECT swap_to_new_embeddings_table();")
    else:
        print("\n⚠️  Unknown embedding dimension or no embeddings found")
        print("💡 You can start fresh by uploading documents")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
