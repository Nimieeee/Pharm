"""
Health Check Endpoints for Enhanced RAG System
Provides comprehensive health monitoring for all RAG components
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.database import get_db
from app.services.enhanced_rag import EnhancedRAGService
from app.services.embeddings import embeddings_service
from app.services.migration import get_migration_service
from app.core.logging_config import rag_logger

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=Dict[str, Any])
async def get_system_health(db: Client = Depends(get_db)):
    """
    Get comprehensive system health status
    
    Returns:
        System health information including all components
    """
    try:
        # Initialize services
        rag_service = EnhancedRAGService(db)
        migration_service = get_migration_service(db)
        
        # Get health from all components
        health_status = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "components": {},
            "errors": [],
            "warnings": []
        }
        
        # Check RAG service health
        try:
            rag_health = await rag_service.get_service_health()
            health_status["components"]["rag_service"] = rag_health
            
            if rag_health["status"] != "healthy":
                health_status["status"] = "degraded"
                health_status["errors"].extend(rag_health.get("errors", []))
        except Exception as e:
            health_status["components"]["rag_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"RAG service error: {str(e)}")
        
        # Check embeddings service health
        try:
            embeddings_health = await embeddings_service.health_check()
            health_status["components"]["embeddings_service"] = embeddings_health
            
            if embeddings_health["status"] != "healthy":
                if health_status["status"] == "healthy":
                    health_status["status"] = "degraded"
                health_status["errors"].extend(embeddings_health.get("errors", []))
        except Exception as e:
            health_status["components"]["embeddings_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Embeddings service error: {str(e)}")
        
        # Check migration service health
        try:
            migration_status = await migration_service.get_migration_status()
            health_status["components"]["migration_service"] = {
                "status": "healthy",
                "migration_enabled": migration_status.get("migration_enabled", False),
                "migration_progress": migration_status.get("migration_percentage", 0)
            }
            
            # Add warning if migration is incomplete
            if migration_status.get("migration_percentage", 100) < 100:
                health_status["warnings"].append(
                    f"Migration {migration_status.get('migration_percentage', 0)}% complete"
                )
        except Exception as e:
            health_status["components"]["migration_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["warnings"].append(f"Migration service error: {str(e)}")
        
        # Test database connectivity
        try:
            test_result = db.table("document_chunks").select("id").limit(1).execute()
            health_status["components"]["database"] = {
                "status": "healthy",
                "connection": "active",
                "test_query": "passed"
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "connection": "failed",
                "error": str(e)
            }
            health_status["status"] = "unhealthy"
            health_status["errors"].append(f"Database error: {str(e)}")
        
        # Add performance statistics
        try:
            performance_stats = rag_logger.get_performance_stats()
            health_status["performance"] = performance_stats
        except Exception as e:
            health_status["warnings"].append(f"Performance stats error: {str(e)}")
        
        # Set final status
        if health_status["errors"]:
            health_status["status"] = "unhealthy"
        elif health_status["warnings"]:
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
        
        # Log health check
        logger.info(f"Health check completed: {health_status['status']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/embeddings", response_model=Dict[str, Any])
async def get_embeddings_health():
    """
    Get detailed embeddings service health
    
    Returns:
        Embeddings service health and statistics
    """
    try:
        health = await embeddings_service.health_check()
        cache_stats = embeddings_service.get_cache_stats()
        
        return {
            "health": health,
            "cache_statistics": cache_stats,
            "configuration": {
                "model": health.get("model"),
                "dimensions": health.get("dimensions"),
                "cache_enabled": health.get("cache_enabled"),
                "client_available": health.get("client_available")
            }
        }
        
    except Exception as e:
        logger.error(f"Embeddings health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embeddings health check failed: {str(e)}"
        )


@router.get("/migration", response_model=Dict[str, Any])
async def get_migration_health(db: Client = Depends(get_db)):
    """
    Get migration service health and progress
    
    Returns:
        Migration status and progress information
    """
    try:
        migration_service = get_migration_service(db)
        status = await migration_service.get_migration_status()
        
        # Add validation results
        validation = await migration_service.validate_migration()
        
        return {
            "migration_status": status,
            "validation": validation,
            "recommendations": []
        }
        
    except Exception as e:
        logger.error(f"Migration health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Migration health check failed: {str(e)}"
        )


@router.get("/database", response_model=Dict[str, Any])
async def get_database_health(db: Client = Depends(get_db)):
    """
    Get database health and vector search performance
    
    Returns:
        Database health and performance metrics
    """
    try:
        health = {
            "status": "healthy",
            "tests": {},
            "statistics": {},
            "errors": []
        }
        
        # Test basic connectivity
        try:
            result = db.table("document_chunks").select("count").execute()
            health["tests"]["connectivity"] = "passed"
        except Exception as e:
            health["tests"]["connectivity"] = "failed"
            health["errors"].append(f"Connectivity test failed: {str(e)}")
            health["status"] = "unhealthy"
        
        # Test vector operations (if data exists)
        try:
            # Get a sample embedding for testing
            sample_result = db.table("document_chunks").select(
                "embedding"
            ).not_.is_("embedding", "null").limit(1).execute()
            
            if sample_result.data and len(sample_result.data) > 0:
                sample_embedding = sample_result.data[0]["embedding"]
                
                # Test similarity search
                search_result = db.rpc(
                    'match_documents_with_user_isolation_v2',
                    {
                        'query_embedding': sample_embedding,
                        'conversation_uuid': '00000000-0000-0000-0000-000000000000',
                        'user_session_uuid': '00000000-0000-0000-0000-000000000000',
                        'match_threshold': 0.1,
                        'match_count': 1
                    }
                ).execute()
                
                health["tests"]["vector_search"] = "passed"
                health["statistics"]["sample_search_results"] = len(search_result.data or [])
            else:
                health["tests"]["vector_search"] = "skipped"
                health["statistics"]["reason"] = "No embeddings found for testing"
                
        except Exception as e:
            health["tests"]["vector_search"] = "failed"
            health["errors"].append(f"Vector search test failed: {str(e)}")
            if health["status"] == "healthy":
                health["status"] = "degraded"
        
        # Get table statistics
        try:
            stats_result = db.rpc('get_embedding_migration_stats').execute()
            if stats_result.data and len(stats_result.data) > 0:
                stats = stats_result.data[0]
                health["statistics"]["chunks"] = {
                    "total": stats.get("total_chunks", 0),
                    "old_embeddings": stats.get("old_embeddings", 0),
                    "new_embeddings": stats.get("new_embeddings", 0),
                    "pending_migration": stats.get("pending_migration", 0)
                }
        except Exception as e:
            health["errors"].append(f"Statistics query failed: {str(e)}")
        
        return health
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Database health check failed: {str(e)}"
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """
    Get system performance metrics
    
    Returns:
        Performance statistics and metrics
    """
    try:
        # Get performance stats from logger
        performance_stats = rag_logger.get_performance_stats()
        
        # Get embeddings cache stats
        cache_stats = embeddings_service.get_cache_stats()
        
        return {
            "performance_statistics": performance_stats,
            "cache_statistics": cache_stats,
            "system_metrics": {
                "total_operations": sum(
                    stats.get("count", 0) 
                    for stats in performance_stats.values()
                ),
                "average_success_rate": sum(
                    stats.get("success_rate", 0) 
                    for stats in performance_stats.values()
                ) / len(performance_stats) if performance_stats else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Performance metrics failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Performance metrics failed: {str(e)}"
        )


@router.post("/test-embedding", response_model=Dict[str, Any])
async def test_embedding_generation():
    """
    Test embedding generation functionality
    
    Returns:
        Embedding generation test results
    """
    try:
        import time
        
        test_text = "This is a test document for pharmaceutical research."
        start_time = time.time()
        
        # Generate test embedding
        embedding = await embeddings_service.generate_embedding(test_text)
        
        duration = time.time() - start_time
        
        if embedding:
            return {
                "success": True,
                "message": "Embedding generation test passed",
                "test_details": {
                    "text_length": len(test_text),
                    "embedding_dimensions": len(embedding),
                    "generation_time": duration,
                    "model": embeddings_service.get_cache_stats().get("model"),
                    "cache_stats": embeddings_service.get_cache_stats()
                }
            }
        else:
            return {
                "success": False,
                "message": "Embedding generation test failed",
                "test_details": {
                    "text_length": len(test_text),
                    "generation_time": duration,
                    "error": "No embedding returned"
                }
            }
            
    except Exception as e:
        logger.error(f"Embedding test failed: {e}")
        return {
            "success": False,
            "message": f"Embedding generation test failed: {str(e)}",
            "test_details": {
                "error": str(e)
            }
        }


@router.post("/clear-cache", response_model=Dict[str, Any])
async def clear_embeddings_cache():
    """
    Clear embeddings cache (admin operation)
    
    Returns:
        Cache clearing results
    """
    try:
        # Get stats before clearing
        before_stats = embeddings_service.get_cache_stats()
        
        # Clear cache
        embeddings_service.clear_cache()
        
        # Get stats after clearing
        after_stats = embeddings_service.get_cache_stats()
        
        return {
            "success": True,
            "message": "Embeddings cache cleared successfully",
            "before_stats": before_stats,
            "after_stats": after_stats
        }
        
    except Exception as e:
        logger.error(f"Cache clearing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache clearing failed: {str(e)}"
        )


@router.post("/reset-performance-stats", response_model=Dict[str, Any])
async def reset_performance_statistics():
    """
    Reset performance statistics (admin operation)
    
    Returns:
        Reset confirmation
    """
    try:
        # Get stats before reset
        before_stats = rag_logger.get_performance_stats()
        
        # Reset stats
        rag_logger.clear_performance_stats()
        
        # Get stats after reset
        after_stats = rag_logger.get_performance_stats()
        
        return {
            "success": True,
            "message": "Performance statistics reset successfully",
            "before_stats": before_stats,
            "after_stats": after_stats
        }
        
    except Exception as e:
        logger.error(f"Performance stats reset failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Performance stats reset failed: {str(e)}"
        )