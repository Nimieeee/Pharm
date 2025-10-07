#!/usr/bin/env python3
"""
Script to update embedding dimensions from 384 to 1024 for Mistral embeddings
WARNING: This will delete all existing document embeddings!
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client, Client
from app.core.config import settings


def update_embedding_dimensions():
    """Update database to support 1024-dimensional Mistral embeddings"""
    
    print("=" * 60)
    print("UPDATE EMBEDDING DIMENSIONS TO 1024 (MISTRAL)")
    print("=" * 60)
    print()
    print("⚠️  WARNING: This will DELETE all existing document embeddings!")
    print("⚠️  You will need to re-upload all documents after this migration.")
    print()
    
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    print()
    print("Connecting to Supabase...")
    
    try:
        db: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        print("✅ Connected to Supabase")
        print()
        
        # Read migration SQL
        migration_file = Path(__file__).parent.parent / "migrations" / "006_update_embedding_dimensions.sql"
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        print("Applying migration...")
        print()
        
        # Execute migration (note: Supabase Python client doesn't support raw SQL directly)
        # You'll need to run this SQL manually in Supabase SQL Editor
        print("=" * 60)
        print("MANUAL STEP REQUIRED:")
        print("=" * 60)
        print()
        print("Please run the following SQL in your Supabase SQL Editor:")
        print()
        print(sql)
        print()
        print("=" * 60)
        print()
        print("After running the SQL:")
        print("1. All existing document embeddings will be deleted")
        print("2. The embedding column will support 1024 dimensions")
        print("3. You can upload documents with Mistral embeddings")
        print()
        print("✅ Migration SQL displayed above")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_embedding_dimensions()
