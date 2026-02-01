#!/usr/bin/env python3
"""
Apply Mistral embeddings migration
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def main():
    """Main function"""
    print("="*80)
    print("Mistral Embeddings Migration")
    print("="*80)
    
    migration_file = Path(__file__).parent.parent / "migrations" / "005_simple_mistral_upgrade.sql"
    
    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return
    
    print("\n📝 Migration file found")
    print(f"📁 Location: {migration_file}")
    
    print("\n" + "="*80)
    print("⚠️  MANUAL MIGRATION REQUIRED")
    print("="*80)
    
    print("\nTo apply this migration, you need to run the SQL in Supabase:")
    print("\nOption 1: Supabase Dashboard")
    print(f"1. Go to: {settings.SUPABASE_URL.replace('https://', 'https://app.')}/project/_/sql")
    print(f"2. Copy the contents of: {migration_file}")
    print("3. Paste and execute in the SQL Editor")
    
    print("\nOption 2: Command Line (if you have psql)")
    print(f"psql <your-database-url> < {migration_file}")
    
    print("\n" + "="*80)
    print("What this migration does:")
    print("="*80)
    print("✅ Upgrades embedding column to 1024 dimensions (Mistral)")
    print("✅ Adds embedding_version tracking")
    print("✅ Adds updated_at timestamp")
    print("✅ Creates new indexes for better performance")
    print("✅ Updates similarity search function")
    print("⚠️  Clears existing embeddings (they will be regenerated)")
    
    print("\n" + "="*80)
    print("After migration:")
    print("="*80)
    print("1. Restart your backend server")
    print("2. Re-upload your documents to generate Mistral embeddings")
    print("3. Enjoy better semantic search! 🚀")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
