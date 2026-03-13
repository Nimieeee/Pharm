"""
Embedding Migration Service
Handles gradual migration from hash-based to Mistral embeddings
"""

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from supabase import Client

from app.core.config import settings
from app.services.embeddings import embeddings_service

logger = logging.getLogger(__name__)


class EmbeddingMigrationService:
    """Service for managing gradual migration to Mistral embeddings"""
    
    def __init__(self, db: Client):
        self.db = db
        self.embeddings_service = embeddings_service
        self.migration_stats = {
            "total_processed": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_chunks": 0,
            "start_time": None,
            "end_time": None
        }
        
        logger.info("✅ Embedding migration service initialized")
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status and statistics"""
        try:
            # Get migration progress from database view
            result = self.db.table("embedding_migration_progress").select("*").execute()
            
            if result.data and len(result.data) > 0:
                progress = result.data[0]
                
                return {
                    "migration_enabled": settings.EMBEDDING_MIGRATION_ENABLED,
                    "total_chunks": progress.get("total_chunks", 0),
                    "old_embeddings": progress.get("old_embeddings", 0),
                    "new_embeddings": progress.get("new_embeddings", 0),
                    "pending_migration": progress.get("pending_migration", 0),
                    "migration_percentage": progress.get("migration_percentage", 0),
                    "embedding_versions": progress.get("embedding_versions", []),
                    "runtime_stats": self.migration_stats,
                    "configuration": {
                        "batch_size": settings.EMBEDDING_BATCH_SIZE,
                        "parallel_workers": settings.MIGRATION_PARALLEL_WORKERS,
                        "use_mistral_embeddings": settings.USE_MISTRAL_EMBEDDINGS
                    }
                }
            else:
                return {
                    "migration_enabled": settings.EMBEDDING_MIGRATION_ENABLED,
                    "error": "Could not retrieve migration progress",
                    "runtime_stats": self.migration_stats
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting migration status: {e}")
            return {
                "migration_enabled": settings.EMBEDDING_MIGRATION_ENABLED,
                "error": f"Migration status error: {str(e)}",
                "runtime_stats": self.migration_stats
            }
    
    async def get_pending_chunks(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get chunks that need embedding migration"""
        try:
            query = self.db.table("document_chunks").select(
                "id, content, metadata, embedding_version, created_at"
            ).in_(
                "embedding_version", 
                ["hash-v1", "pending-migration", "hash-fallback"]
            ).order("created_at")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            chunks = result.data or []
            logger.info(f"Found {len(chunks)} chunks pending migration")
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Error getting pending chunks: {e}")
            return []
    
    async def migrate_chunk_embedding(self, chunk_id: str, content: str) -> Tuple[bool, str]:
        """
        Migrate a single chunk's embedding to Mistral
        
        Args:
            chunk_id: Chunk UUID
            content: Chunk content
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Generate new embedding using Mistral
            embedding = await self.embeddings_service.generate_embedding(content)
            
            if not embedding:
                return False, "Failed to generate Mistral embedding"
            
            # Validate embedding dimensions
            if len(embedding) != settings.MISTRAL_EMBED_DIMENSIONS:
                return False, f"Invalid embedding dimensions: {len(embedding)}"
            
            # Update chunk in database
            update_data = {
                "embedding": embedding,
                "embedding_version": "mistral-v1",
                "updated_at": "now()"
            }
            
            result = self.db.table("document_chunks").update(update_data).eq(
                "id", chunk_id
            ).execute()
            
            if result.data and len(result.data) > 0:
                return True, "Successfully migrated to Mistral embedding"
            else:
                return False, "Database update failed"
                
        except Exception as e:
            error_msg = f"Migration error: {str(e)}"
            logger.error(f"❌ {error_msg} for chunk {chunk_id}")
            return False, error_msg
    
    async def migrate_batch(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Migrate a batch of chunks
        
        Args:
            chunks: List of chunk data dictionaries
            
        Returns:
            Batch migration results
        """
        if not chunks:
            return {"success": 0, "failed": 0, "errors": []}
        
        logger.info(f"Migrating batch of {len(chunks)} chunks")
        
        # Use semaphore to limit concurrent migrations
        semaphore = asyncio.Semaphore(settings.MIGRATION_PARALLEL_WORKERS)
        
        async def migrate_single_chunk(chunk: Dict[str, Any]) -> Tuple[bool, str, str]:
            async with semaphore:
                chunk_id = chunk["id"]
                content = chunk["content"]
                
                success, message = await self.migrate_chunk_embedding(chunk_id, content)
                return success, message, chunk_id
        
        # Process chunks concurrently
        tasks = [migrate_single_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        batch_results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "successful_ids": [],
            "failed_ids": []
        }
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results["failed"] += 1
                batch_results["errors"].append(f"Chunk {i}: {str(result)}")
                batch_results["failed_ids"].append(chunks[i]["id"])
            else:
                success, message, chunk_id = result
                if success:
                    batch_results["success"] += 1
                    batch_results["successful_ids"].append(chunk_id)
                else:
                    batch_results["failed"] += 1
                    batch_results["errors"].append(f"Chunk {chunk_id}: {message}")
                    batch_results["failed_ids"].append(chunk_id)
        
        # Update migration stats
        self.migration_stats["total_processed"] += len(chunks)
        self.migration_stats["successful_migrations"] += batch_results["success"]
        self.migration_stats["failed_migrations"] += batch_results["failed"]
        
        logger.info(
            f"✅ Batch migration completed: {batch_results['success']} success, "
            f"{batch_results['failed']} failed"
        )
        
        return batch_results
    
    async def run_migration(
        self, 
        max_chunks: Optional[int] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the embedding migration process
        
        Args:
            max_chunks: Maximum number of chunks to migrate (None for all)
            batch_size: Size of each batch (None for default)
            
        Returns:
            Migration results
        """
        if not settings.EMBEDDING_MIGRATION_ENABLED:
            return {
                "success": False,
                "message": "Migration is disabled in configuration",
                "stats": self.migration_stats
            }
        
        if not settings.USE_MISTRAL_EMBEDDINGS:
            return {
                "success": False,
                "message": "Mistral embeddings are disabled",
                "stats": self.migration_stats
            }
        
        batch_size = batch_size or settings.EMBEDDING_BATCH_SIZE
        self.migration_stats["start_time"] = time.time()
        
        logger.info(f"🚀 Starting embedding migration (batch_size={batch_size})")
        
        try:
            # Get initial status
            initial_status = await self.get_migration_status()
            total_pending = initial_status.get("pending_migration", 0) + initial_status.get("old_embeddings", 0)
            
            if total_pending == 0:
                return {
                    "success": True,
                    "message": "No chunks need migration",
                    "stats": self.migration_stats
                }
            
            logger.info(f"Found {total_pending} chunks needing migration")
            
            # Process chunks in batches
            processed_total = 0
            all_errors = []
            
            while True:
                # Check if we've reached the limit
                if max_chunks and processed_total >= max_chunks:
                    logger.info(f"Reached maximum chunk limit: {max_chunks}")
                    break
                
                # Get next batch
                remaining_limit = None
                if max_chunks:
                    remaining_limit = min(batch_size, max_chunks - processed_total)
                else:
                    remaining_limit = batch_size
                
                pending_chunks = await self.get_pending_chunks(remaining_limit)
                
                if not pending_chunks:
                    logger.info("No more chunks to migrate")
                    break
                
                # Migrate batch
                batch_results = await self.migrate_batch(pending_chunks)
                processed_total += len(pending_chunks)
                all_errors.extend(batch_results["errors"])
                
                # Log progress
                logger.info(
                    f"Progress: {processed_total}/{total_pending} chunks processed "
                    f"({(processed_total/total_pending)*100:.1f}%)"
                )
                
                # Small delay between batches to avoid overwhelming the API
                await asyncio.sleep(0.5)
            
            self.migration_stats["end_time"] = time.time()
            migration_duration = self.migration_stats["end_time"] - self.migration_stats["start_time"]
            
            # Get final status
            final_status = await self.get_migration_status()
            
            result = {
                "success": True,
                "message": f"Migration completed in {migration_duration:.2f} seconds",
                "stats": self.migration_stats,
                "initial_status": initial_status,
                "final_status": final_status,
                "errors": all_errors[:10] if all_errors else []  # Limit error list
            }
            
            if all_errors:
                result["message"] += f" with {len(all_errors)} errors"
            
            logger.info(f"✅ {result['message']}")
            return result
            
        except Exception as e:
            self.migration_stats["end_time"] = time.time()
            error_msg = f"Migration failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return {
                "success": False,
                "message": error_msg,
                "stats": self.migration_stats
            }
    
    async def migrate_conversation_chunks(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Migrate all chunks for a specific conversation
        
        Args:
            conversation_id: Conversation UUID
            user_id: User UUID
            
        Returns:
            Migration results for the conversation
        """
        try:
            # Get chunks for this conversation that need migration
            result = self.db.table("document_chunks").select(
                "id, content, metadata, embedding_version"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user_id)
            ).in_(
                "embedding_version", 
                ["hash-v1", "pending-migration", "hash-fallback"]
            ).execute()
            
            chunks = result.data or []
            
            if not chunks:
                return {
                    "success": True,
                    "message": "No chunks need migration for this conversation",
                    "migrated_count": 0
                }
            
            logger.info(f"Migrating {len(chunks)} chunks for conversation {conversation_id}")
            
            # Migrate all chunks for this conversation
            batch_results = await self.migrate_batch(chunks)
            
            return {
                "success": batch_results["failed"] == 0,
                "message": f"Migrated {batch_results['success']}/{len(chunks)} chunks",
                "migrated_count": batch_results["success"],
                "failed_count": batch_results["failed"],
                "errors": batch_results["errors"]
            }
            
        except Exception as e:
            error_msg = f"Conversation migration failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "migrated_count": 0
            }
    
    async def validate_migration(self) -> Dict[str, Any]:
        """Validate that migration was successful"""
        try:
            # Get migration statistics
            status = await self.get_migration_status()
            
            validation = {
                "valid": True,
                "issues": [],
                "statistics": status
            }
            
            # Check for pending migrations
            if status.get("pending_migration", 0) > 0:
                validation["issues"].append(
                    f"{status['pending_migration']} chunks still pending migration"
                )
            
            # Check for old embeddings
            if status.get("old_embeddings", 0) > 0:
                validation["issues"].append(
                    f"{status['old_embeddings']} chunks still using old embeddings"
                )
            
            # Check migration percentage
            migration_percentage = status.get("migration_percentage", 0)
            if migration_percentage < 100:
                validation["issues"].append(
                    f"Migration only {migration_percentage}% complete"
                )
            
            # Test embedding generation
            try:
                test_embedding = await self.embeddings_service.generate_embedding("test migration")
                if not test_embedding or len(test_embedding) != settings.MISTRAL_EMBED_DIMENSIONS:
                    validation["issues"].append("Embedding generation test failed")
            except Exception as e:
                validation["issues"].append(f"Embedding test error: {str(e)}")
            
            validation["valid"] = len(validation["issues"]) == 0
            
            if validation["valid"]:
                logger.info("✅ Migration validation passed")
            else:
                logger.warning(f"⚠️  Migration validation found {len(validation['issues'])} issues")
            
            return validation
            
        except Exception as e:
            logger.error(f"❌ Migration validation error: {e}")
            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "statistics": {}
            }
    
    def reset_migration_stats(self) -> None:
        """Reset migration statistics"""
        self.migration_stats = {
            "total_processed": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_chunks": 0,
            "start_time": None,
            "end_time": None
        }
        logger.info("✅ Migration statistics reset")


# Global migration service instance
migration_service = None

def get_migration_service(db: Client) -> EmbeddingMigrationService:
    """Get or create migration service instance"""
    global migration_service
    if migration_service is None:
        migration_service = EmbeddingMigrationService(db)
    return migration_service