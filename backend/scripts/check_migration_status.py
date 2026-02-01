#!/usr/bin/env python3
"""
Migration Status Checker for PharmGPT Backend
Checks the status of embedding migration and provides recommendations
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.services.migration import get_migration_service


async def check_migration_status():
    """Check and display migration status"""
    print("🔍 Checking embedding migration status...")
    print("=" * 50)
    
    try:
        # Get database connection
        db = get_db()
        
        # Get migration service
        migration_service = get_migration_service(db)
        
        # Get migration status
        status = await migration_service.get_migration_status()
        
        # Display status
        print(f"Migration Enabled: {status.get('migration_enabled', False)}")
        print(f"Total Chunks: {status.get('total_chunks', 0)}")
        print(f"Old Embeddings: {status.get('old_embeddings', 0)}")
        print(f"New Embeddings: {status.get('new_embeddings', 0)}")
        print(f"Pending Migration: {status.get('pending_migration', 0)}")
        print(f"Migration Progress: {status.get('migration_percentage', 0):.1f}%")
        
        # Display embedding versions
        versions = status.get('embedding_versions', [])
        if versions:
            print(f"Embedding Versions: {', '.join(versions)}")
        
        # Display configuration
        config = status.get('configuration', {})
        if config:
            print("\nConfiguration:")
            for key, value in config.items():
                print(f"  {key}: {value}")
        
        # Validate migration
        print("\n🔬 Running migration validation...")
        validation = await migration_service.validate_migration()
        
        if validation.get('valid', False):
            print("✅ Migration validation PASSED")
        else:
            print("❌ Migration validation FAILED")
            issues = validation.get('issues', [])
            for issue in issues:
                print(f"  - {issue}")
        
        # Provide recommendations
        print("\n💡 Recommendations:")
        
        migration_percentage = status.get('migration_percentage', 0)
        pending_count = status.get('pending_migration', 0)
        old_count = status.get('old_embeddings', 0)
        
        if migration_percentage == 0:
            print("  - No migration detected. This is normal for new deployments.")
            print("  - New documents will use Mistral embeddings automatically.")
        elif migration_percentage < 100:
            print(f"  - Migration is {migration_percentage:.1f}% complete")
            if pending_count > 0:
                print(f"  - {pending_count} chunks are pending migration")
                print("  - Run migration to complete the process:")
                print("    python scripts/run_migration.py")
            if old_count > 0:
                print(f"  - {old_count} chunks still use old embeddings")
                print("  - Consider running full migration for better search quality")
        else:
            print("  - Migration is complete!")
            print("  - All chunks are using Mistral embeddings")
        
        # Check if Mistral API is available
        if not status.get('configuration', {}).get('use_mistral_embeddings', False):
            print("  - Mistral embeddings are disabled")
            print("  - Enable USE_MISTRAL_EMBEDDINGS=true for better search quality")
        
        return status
        
    except Exception as e:
        print(f"❌ Error checking migration status: {e}")
        return None


async def run_migration_if_needed():
    """Run migration if there are pending chunks"""
    try:
        # Get database connection
        db = get_db()
        
        # Get migration service
        migration_service = get_migration_service(db)
        
        # Check status
        status = await migration_service.get_migration_status()
        
        pending_count = status.get('pending_migration', 0)
        old_count = status.get('old_embeddings', 0)
        
        if pending_count == 0 and old_count == 0:
            print("✅ No migration needed - all chunks are up to date")
            return True
        
        total_to_migrate = pending_count + old_count
        print(f"🚀 Starting migration for {total_to_migrate} chunks...")
        
        # Run migration
        result = await migration_service.run_migration()
        
        if result.get('success', False):
            print("✅ Migration completed successfully!")
            print(f"   {result['stats']['successful_migrations']} chunks migrated")
            if result['stats']['failed_migrations'] > 0:
                print(f"   {result['stats']['failed_migrations']} chunks failed")
            return True
        else:
            print(f"❌ Migration failed: {result.get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False


async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check embedding migration status")
    parser.add_argument(
        "--migrate", 
        action="store_true", 
        help="Run migration if needed"
    )
    parser.add_argument(
        "--output", 
        default=None, 
        help="Output file for status (JSON)"
    )
    
    args = parser.parse_args()
    
    # Check migration status
    status = await check_migration_status()
    
    if status is None:
        sys.exit(1)
    
    # Save status if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(status, f, indent=2)
        print(f"\n📄 Status saved to {args.output}")
    
    # Run migration if requested
    if args.migrate:
        print("\n" + "=" * 50)
        success = await run_migration_if_needed()
        if not success:
            sys.exit(1)
    
    print("\n✅ Migration status check completed")


if __name__ == "__main__":
    asyncio.run(main())