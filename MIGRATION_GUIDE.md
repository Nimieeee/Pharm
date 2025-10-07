# PharmGPT Migration Guide: LangChain + Mistral Embeddings

This guide covers migrating from the custom RAG implementation to the enhanced LangChain + Mistral embeddings system.

## Overview

The enhanced RAG system provides:
- **Better Embeddings**: Mistral embeddings (1024 dimensions) vs hash-based (384 dimensions)
- **Improved Processing**: LangChain document loaders with better error handling
- **Enhanced Search**: More accurate similarity search with caching
- **Better Performance**: Optimized text splitting and batch processing

## Migration Process

### Phase 1: Preparation

1. **Backup Your Data**
   ```sql
   -- Run in Supabase SQL editor
   SELECT backup_existing_embeddings();
   ```

2. **Update Environment Variables**
   ```bash
   # Add to your .env file
   MISTRAL_API_KEY=your_mistral_api_key
   USE_MISTRAL_EMBEDDINGS=true
   USE_LANGCHAIN_LOADERS=true
   ENABLE_EMBEDDING_CACHE=true
   EMBEDDING_MIGRATION_ENABLED=true
   ```

3. **Deploy Updated Code**
   - Deploy the enhanced backend with new dependencies
   - Verify health checks pass: `GET /api/v1/health`

### Phase 2: Database Migration

1. **Run Database Schema Migration**
   ```sql
   -- Run backend/migrations/004_upgrade_to_mistral_embeddings.sql
   -- This creates new tables and functions for 1024-dimensional embeddings
   ```

2. **Check Migration Status**
   ```bash
   # Using the validation script
   python backend/scripts/check_migration_status.py
   
   # Or via API
   curl -X GET "https://your-api.com/api/v1/health/migration"
   ```

### Phase 3: Embedding Migration

#### Option A: Automatic Migration (Recommended)

1. **Run Migration Script**
   ```bash
   # Interactive migration
   python backend/scripts/run_migration.py
   
   # Non-interactive with limits
   python backend/scripts/run_migration.py --non-interactive --max-chunks 1000
   ```

2. **Monitor Progress**
   ```bash
   # Check status during migration
   python backend/scripts/check_migration_status.py
   ```

#### Option B: API-Based Migration (Admin Panel)

1. **Check Status**
   ```bash
   curl -X GET "https://your-api.com/api/v1/admin/migration/status" \
        -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

2. **Run Migration**
   ```bash
   curl -X POST "https://your-api.com/api/v1/admin/migration/run?max_chunks=1000" \
        -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

3. **Validate Results**
   ```bash
   curl -X POST "https://your-api.com/api/v1/admin/migration/validate" \
        -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
   ```

### Phase 4: Validation and Cleanup

1. **Validate Migration**
   ```bash
   # Run validation script
   python backend/scripts/validate_deployment.py --url https://your-api.com
   ```

2. **Test End-to-End**
   ```bash
   # Run integration tests
   python backend/tests/test_enhanced_rag_e2e.py
   ```

3. **Clean Up (After Validation)**
   ```sql
   -- Only run after confirming migration success
   SELECT cleanup_migration_artifacts();
   ```

## Configuration Options

### Mistral Embeddings Settings

```bash
# Embedding model and dimensions
MISTRAL_EMBED_MODEL=mistral-embed
MISTRAL_EMBED_DIMENSIONS=1024

# API settings
MISTRAL_MAX_RETRIES=3
MISTRAL_TIMEOUT=30

# Caching
EMBEDDING_CACHE_TTL=3600
EMBEDDING_CACHE_MAX_SIZE=1000
```

### LangChain Settings

```bash
# Text processing
LANGCHAIN_CHUNK_SIZE=1500
LANGCHAIN_CHUNK_OVERLAP=300
LANGCHAIN_CACHE_ENABLED=true

# Feature flags
USE_LANGCHAIN_LOADERS=true
ENABLE_EMBEDDING_CACHE=true
```

### Migration Settings

```bash
# Migration control
EMBEDDING_MIGRATION_ENABLED=true
EMBEDDING_BATCH_SIZE=100
MIGRATION_PARALLEL_WORKERS=2

# Fallback options
FALLBACK_TO_HASH_EMBEDDINGS=false
```

## Monitoring and Troubleshooting

### Health Checks

Monitor system health during and after migration:

```bash
# Overall system health
curl -X GET "https://your-api.com/api/v1/health"

# Embeddings service health
curl -X GET "https://your-api.com/api/v1/health/embeddings"

# Migration progress
curl -X GET "https://your-api.com/api/v1/health/migration"

# Performance metrics
curl -X GET "https://your-api.com/api/v1/health/performance"
```

### Common Issues

#### 1. Mistral API Errors

**Problem**: `401 Unauthorized` or `429 Rate Limit`

**Solution**:
```bash
# Check API key
echo $MISTRAL_API_KEY

# Enable fallback temporarily
FALLBACK_TO_HASH_EMBEDDINGS=true

# Reduce parallel workers
MIGRATION_PARALLEL_WORKERS=1
```

#### 2. Memory Issues

**Problem**: Out of memory during migration

**Solution**:
```bash
# Reduce batch size
EMBEDDING_BATCH_SIZE=50

# Reduce cache size
EMBEDDING_CACHE_MAX_SIZE=500

# Process in smaller chunks
python backend/scripts/run_migration.py --max-chunks 100
```

#### 3. Database Connection Issues

**Problem**: Database timeouts or connection errors

**Solution**:
```bash
# Check database status
curl -X GET "https://your-api.com/api/v1/health/database"

# Verify Supabase settings
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY

# Check database isn't paused (free tier)
```

#### 4. Slow Migration

**Problem**: Migration taking too long

**Solution**:
```bash
# Increase parallel workers (if API allows)
MIGRATION_PARALLEL_WORKERS=4

# Increase timeout
MISTRAL_TIMEOUT=60

# Run during off-peak hours
```

### Performance Optimization

#### For High-Volume Deployments

```bash
# Increase cache and workers
EMBEDDING_CACHE_MAX_SIZE=5000
MIGRATION_PARALLEL_WORKERS=4

# Optimize chunk sizes
LANGCHAIN_CHUNK_SIZE=2000
LANGCHAIN_CHUNK_OVERLAP=400

# Increase timeouts
MISTRAL_TIMEOUT=60
```

#### For Memory-Constrained Environments

```bash
# Reduce cache and workers
EMBEDDING_CACHE_MAX_SIZE=500
MIGRATION_PARALLEL_WORKERS=1

# Smaller chunks
LANGCHAIN_CHUNK_SIZE=1000
LANGCHAIN_CHUNK_OVERLAP=200

# Smaller batches
EMBEDDING_BATCH_SIZE=25
```

## Rollback Procedure

If migration fails or causes issues:

### 1. Immediate Rollback

```bash
# Disable new features
USE_MISTRAL_EMBEDDINGS=false
USE_LANGCHAIN_LOADERS=false

# Restart application
```

### 2. Database Rollback

```sql
-- Rollback database changes
SELECT rollback_embeddings_migration();
```

### 3. Code Rollback

```bash
# Deploy previous version
git checkout previous-version
# Deploy to production
```

## Post-Migration Benefits

After successful migration, you'll have:

### Improved Search Quality
- More accurate semantic search
- Better handling of pharmaceutical terminology
- Improved relevance scoring

### Enhanced Performance
- Faster document processing
- Optimized similarity search
- Intelligent caching

### Better Reliability
- Comprehensive error handling
- Graceful API failure recovery
- Detailed logging and monitoring

### Advanced Features
- Real-time health monitoring
- Performance metrics
- Migration management tools

## API Changes

### New Endpoints

```bash
# Document management
POST /api/v1/ai/documents/upload
POST /api/v1/ai/documents/search
GET  /api/v1/ai/documents/{conversation_id}
DELETE /api/v1/ai/documents/{conversation_id}

# Health monitoring
GET /api/v1/health/embeddings
GET /api/v1/health/migration
GET /api/v1/health/performance

# Admin migration management
GET /api/v1/admin/migration/status
POST /api/v1/admin/migration/run
POST /api/v1/admin/migration/validate
```

### Enhanced Responses

Document upload responses now include:
```json
{
  "success": true,
  "message": "Successfully processed 5 chunks from document.pdf",
  "chunk_count": 5,
  "processing_time": 2.34,
  "errors": []
}
```

Search responses include similarity scores:
```json
{
  "chunks": [
    {
      "id": "uuid",
      "content": "...",
      "similarity": 0.87,
      "metadata": {
        "embedding_version": "mistral-v1",
        "filename": "document.pdf"
      }
    }
  ]
}
```

## Support

For migration assistance:

1. **Check Health Endpoints**: Monitor system status
2. **Review Logs**: Check application logs for errors
3. **Run Validation**: Use provided validation scripts
4. **Contact Support**: Use in-app support form for issues

## Best Practices

1. **Test in Staging**: Always test migration in staging first
2. **Monitor Resources**: Watch API usage and costs
3. **Backup Data**: Always backup before migration
4. **Gradual Rollout**: Consider migrating in batches
5. **Monitor Performance**: Track search quality improvements

---

**Migration completed successfully? 🎉**

Your PharmGPT system now uses state-of-the-art LangChain + Mistral embeddings for superior document processing and search capabilities!