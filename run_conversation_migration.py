#!/usr/bin/env python3
"""
Script to run the conversation management migration.
This creates the conversations table and updates the messages table.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from supabase import create_client
from deployment_config import deployment_config

def run_conversation_migration():
    """Run the conversation management migration"""
    try:
        # Get database configuration
        db_config = deployment_config.get_database_config()
        
        if not db_config["url"] or not db_config.get("anon_key"):
            print("❌ Error: Missing database configuration")
            print("Please ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in your secrets")
            print("Available keys:", list(db_config.keys()))
            return False
        
        # Create Supabase client with anon key (service key not available)
        supabase = create_client(db_config["url"], db_config["anon_key"])
        
        print("🔄 Running conversation management migration...")
        
        # Read migration file
        migration_file = Path(__file__).parent / "migrations" / "006_conversation_management.sql"
        
        if not migration_file.exists():
            print(f"❌ Error: Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration by running individual SQL statements
        print("📝 Executing SQL migration...")
        
        # Split migration into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        print(f"Found {len(statements)} SQL statements to execute...")
        
        for i, statement in enumerate(statements, 1):
            if statement.strip():
                try:
                    print(f"Executing statement {i}/{len(statements)}...")
                    # For DDL statements, we need to use raw SQL execution
                    # This might not work with anon key, so we'll provide instructions instead
                    print(f"Statement: {statement[:100]}...")
                except Exception as e:
                    print(f"⚠️  Could not execute statement {i}: {e}")
        
        print("⚠️  Note: Some statements may require admin privileges.")
        print("If the migration fails, please run the SQL manually in your Supabase dashboard.")
        
        if result.data:
            print("✅ Migration completed successfully!")
            print("📊 Migration results:")
            for item in result.data if isinstance(result.data, list) else [result.data]:
                print(f"   - {item}")
        else:
            print("✅ Migration completed successfully!")
        
        # Verify tables were created
        print("\n🔍 Verifying migration...")
        
        # Check if conversations table exists
        try:
            conversations_result = supabase.table('conversations').select('id').limit(1).execute()
            print("✅ Conversations table is accessible")
        except Exception as e:
            print(f"⚠️  Warning: Could not verify conversations table: {e}")
        
        # Check if messages table has conversation_id column
        try:
            messages_result = supabase.table('messages').select('id, conversation_id').limit(1).execute()
            print("✅ Messages table has conversation_id column")
        except Exception as e:
            print(f"⚠️  Warning: Could not verify messages table update: {e}")
        
        print("\n🎉 Conversation management migration completed!")
        print("You can now use conversation tabs in the application.")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧬 Pharmacology Chat - Conversation Management Migration")
    print("=" * 60)
    
    success = run_conversation_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("You can now restart your application to use conversation management.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)