#!/usr/bin/env python3
"""
Embedding Migration Runner for PharmGPT Backend
Runs the embedding migration process with progress monitoring
"""

import asyncio
import sys
import os
import time
import signal
from pathlib import Path
from typing import Dict, Any, Optional

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_db
from app.services.migration import get_migration_service


class MigrationRunner:
    """Handles migration execution with monitoring and control"""
    
    def __init__(self):
        self.migration_service = None
        self.db = None
        self.should_stop = False
        self.start_time = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n⚠️  Received signal {signum}, stopping migration gracefully...")
        self.should_stop = True
    
    async def initialize(self):
        """Initialize migration service"""
        try:
            self.db = get_db()
            self.migration_service = get_migration_service(self.db)
            print("✅ Migration service initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize migration service: {e}")
            return False
    
    async def check_prerequisites(self) -> bool:
        """Check if migration can be run"""
        try:
            # Check if migration is enabled
            status = await self.migration_service.get_migration_status()
            
            if not status.get('migration_enabled', False):
                print("❌ Migration is disabled in configuration")
                print("   Set EMBEDDING_MIGRATION_ENABLED=true to enable migration")
                return False
            
            # Check if Mistral embeddings are enabled
            config = status.get('configuration', {})
            if not config.get('use_mistral_embeddings', False):
                print("❌ Mistral embeddings are disabled")
                print("   Set USE_MISTRAL_EMBEDDINGS=true to enable Mistral embeddings")
                return False
            
            # Check if there are chunks to migrate
            pending = status.get('pending_migration', 0)
            old_embeddings = status.get('old_embeddings', 0)
            total_to_migrate = pending + old_embeddings
            
            if total_to_migrate == 0:
                print("✅ No chunks need migration - all are up to date")
                return False
            
            print(f"📊 Migration prerequisites check:")
            print(f"   Total chunks to migrate: {total_to_migrate}")
            print(f"   Pending migration: {pending}")
            print(f"   Old embeddings: {old_embeddings}")
            print(f"   Batch size: {config.get('batch_size', 100)}")
            print(f"   Parallel workers: {config.get('parallel_workers', 2)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Prerequisites check failed: {e}")
            return False
    
    async def run_migration_with_monitoring(
        self, 
        max_chunks: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run migration with progress monitoring"""
        
        print(f"🚀 Starting embedding migration...")
        if max_chunks:
            print(f"   Limited to {max_chunks} chunks")
        
        self.start_time = time.time()
        
        try:
            # Get initial status
            initial_status = await self.migration_service.get_migration_status()
            initial_pending = initial_status.get('pending_migration', 0) + initial_status.get('old_embeddings', 0)
            
            print(f"📈 Initial state: {initial_pending} chunks to migrate")
            print("=" * 60)
            
            # Run migration
            result = await self.migration_service.run_migration(
                max_chunks=max_chunks,
                batch_size=batch_size
            )
            
            # Get final status
            final_status = await self.migration_service.get_migration_status()
            final_pending = final_status.get('pending_migration', 0) + final_status.get('old_embeddings', 0)
            
            # Calculate results
            migrated_count = initial_pending - final_pending
            duration = time.time() - self.start_time
            
            print("=" * 60)
            print(f"📊 Migration Results:")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Chunks migrated: {migrated_count}")
            print(f"   Success rate: {result['stats']['successful_migrations']}/{result['stats']['total_processed']}")
            
            if result['stats']['failed_migrations'] > 0:
                print(f"   Failed migrations: {result['stats']['failed_migrations']}")
            
            print(f"   Final progress: {final_status.get('migration_percentage', 0):.1f}%")
            
            return {
                "success": result.get('success', False),
                "migrated_count": migrated_count,
                "duration": duration,
                "initial_pending": initial_pending,
                "final_pending": final_pending,
                "migration_percentage": final_status.get('migration_percentage', 0),
                "stats": result.get('stats', {}),
                "errors": result.get('errors', [])
            }
            
        except Exception as e:
            duration = time.time() - self.start_time if self.start_time else 0
            print(f"❌ Migration failed after {duration:.2f} seconds: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": duration
            }
    
    async def validate_migration_results(self) -> bool:
        """Validate migration results"""
        try:
            print("\n🔬 Validating migration results...")
            
            validation = await self.migration_service.validate_migration()
            
            if validation.get('valid', False):
                print("✅ Migration validation PASSED")
                return True
            else:
                print("❌ Migration validation FAILED")
                issues = validation.get('issues', [])
                for issue in issues:
                    print(f"   - {issue}")
                return False
                
        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return False
    
    async def run_interactive_migration(self):
        """Run migration with user interaction"""
        
        # Check prerequisites
        if not await self.check_prerequisites():
            return False
        
        # Get user confirmation
        status = await self.migration_service.get_migration_status()
        total_chunks = status.get('pending_migration', 0) + status.get('old_embeddings', 0)
        
        print(f"\n⚠️  About to migrate {total_chunks} chunks to Mistral embeddings")
        print("   This process may take several minutes and will use API quota")
        
        response = input("\nProceed with migration? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Migration cancelled by user")
            return False
        
        # Run migration
        result = await self.run_migration_with_monitoring()
        
        if result.get('success', False):
            # Validate results
            validation_passed = await self.validate_migration_results()
            
            if validation_passed:
                print("\n🎉 Migration completed successfully!")
                return True
            else:
                print("\n⚠️  Migration completed but validation failed")
                print("   Some chunks may need manual review")
                return False
        else:
            print(f"\n💥 Migration failed: {result.get('error', 'Unknown error')}")
            return False


async def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run embedding migration")
    parser.add_argument(
        "--max-chunks", 
        type=int, 
        default=None, 
        help="Maximum number of chunks to migrate"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=None, 
        help="Batch size for migration"
    )
    parser.add_argument(
        "--non-interactive", 
        action="store_true", 
        help="Run without user confirmation"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true", 
        help="Only validate existing migration"
    )
    
    args = parser.parse_args()
    
    # Initialize migration runner
    runner = MigrationRunner()
    
    if not await runner.initialize():
        sys.exit(1)
    
    # Validate only mode
    if args.validate_only:
        print("🔬 Running migration validation only...")
        validation_passed = await runner.validate_migration_results()
        sys.exit(0 if validation_passed else 1)
    
    # Run migration
    if args.non_interactive:
        # Non-interactive mode
        if not await runner.check_prerequisites():
            sys.exit(1)
        
        result = await runner.run_migration_with_monitoring(
            max_chunks=args.max_chunks,
            batch_size=args.batch_size
        )
        
        success = result.get('success', False)
        if success:
            validation_passed = await runner.validate_migration_results()
            sys.exit(0 if validation_passed else 1)
        else:
            sys.exit(1)
    else:
        # Interactive mode
        success = await runner.run_interactive_migration()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())