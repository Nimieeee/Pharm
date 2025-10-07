# Environment Variables Configuration

This document describes all environment variables used by the PharmGPT backend with LangChain and Mistral embeddings integration.

## Required Variables

### Database Configuration
- `SUPABASE_URL` - Supabase project URL (required)
- `SUPABASE_ANON_KEY` - Supabase anonymous key (required)

### Security Configuration
- `SECRET_KEY` - JWT secret key, minimum 32 characters (required)

### AI Model Configuration
- `MISTRAL_API_KEY` - Mistral AI API key for embeddings (required for production)

## Optional Variables

### Basic Application Settings
- `DEBUG` - Enable debug mode (default: `false`)
- `PORT` - Server port (default: `8000`)
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins

### Admin Configuration
- `ADMIN_EMAIL` - Default admin email (default: `admin@pharmgpt.com`)
- `ADMIN_PASSWORD` - Default admin password (auto-generated if not set)

### Mistral Embeddings Configuration
- `MISTRAL_EMBED_MODEL` - Mistral embedding model name (default: `mistral-embed`)
- `MISTRAL_EMBED_DIMENSIONS` - Embedding dimensions (default: `1024`)
- `MISTRAL_MAX_RETRIES` - Maximum API retry attempts (default: `3`)
- `MISTRAL_TIMEOUT` - API timeout in seconds (default: `30`)

### LangChain Configuration
- `LANGCHAIN_CHUNK_SIZE` - Text chunk size in characters (default: `1500`)
- `LANGCHAIN_CHUNK_OVERLAP` - Chunk overlap in characters (default: `300`)
- `LANGCHAIN_CACHE_ENABLED` - Enable LangChain caching (default: `true`)

### Embedding Cache Configuration
- `EMBEDDING_CACHE_TTL` - Cache time-to-live in seconds (default: `3600`)
- `EMBEDDING_CACHE_MAX_SIZE` - Maximum cache entries (default: `1000`)

### Migration Configuration
- `EMBEDDING_MIGRATION_ENABLED` - Enable embedding migration (default: `false`)
- `EMBEDDING_BATCH_SIZE` - Migration batch size (default: `100`)
- `MIGRATION_PARALLEL_WORKERS` - Parallel migration workers (default: `2`)

### Feature Flags
- `USE_MISTRAL_EMBEDDINGS` - Use Mistral embeddings API (default: `true`)
- `USE_LANGCHAIN_LOADERS` - Use LangChain document loaders (default: `true`)
- `ENABLE_EMBEDDING_CACHE` - Enable embedding caching (default: `true`)
- `FALLBACK_TO_HASH_EMBEDDINGS` - Fallback to hash embeddings if Mistral fails (default: `false`)

### Additional AI Models (Optional)
- `GROQ_API_KEY` - Groq API key for fast inference (optional)

## Environment File Example

Create a `.env` file in the backend directory:

```bash
# Required Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SECRET_KEY=your-32-character-secret-key-here
MISTRAL_API_KEY=your-mistral-api-key

# Optional Configuration
DEBUG=false
PORT=8000
ADMIN_EMAIL=admin@pharmgpt.com
ADMIN_PASSWORD=your-secure-password

# CORS Configuration
ALLOWED_ORIGINS=https://pharmgpt.netlify.app,http://localhost:3000,http://localhost:5173

# Mistral Embeddings
MISTRAL_EMBED_MODEL=mistral-embed
MISTRAL_EMBED_DIMENSIONS=1024
MISTRAL_MAX_RETRIES=3
MISTRAL_TIMEOUT=30

# LangChain Settings
LANGCHAIN_CHUNK_SIZE=1500
LANGCHAIN_CHUNK_OVERLAP=300
LANGCHAIN_CACHE_ENABLED=true

# Embedding Cache
EMBEDDING_CACHE_TTL=3600
EMBEDDING_CACHE_MAX_SIZE=1000

# Migration Settings (for production migration)
EMBEDDING_MIGRATION_ENABLED=false
EMBEDDING_BATCH_SIZE=100
MIGRATION_PARALLEL_WORKERS=2

# Feature Flags
USE_MISTRAL_EMBEDDINGS=true
USE_LANGCHAIN_LOADERS=true
ENABLE_EMBEDDING_CACHE=true
FALLBACK_TO_HASH_EMBEDDINGS=false
```

## Deployment-Specific Configuration

### Render Deployment
All variables are configured in `render.yaml`. Sensitive variables like API keys should be set in the Render dashboard.

### Docker Deployment
Pass environment variables using `-e` flags or an environment file:

```bash
docker run -p 8000:8000 --env-file .env pharmgpt-backend
```

### Local Development
Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration Validation

The application validates configuration on startup:

- Required variables must be present
- Numeric values must be within valid ranges
- Chunk overlap must be less than chunk size
- API keys are validated (warnings for missing keys)

## Performance Tuning

### For High-Volume Deployments
```bash
# Increase cache size and workers
EMBEDDING_CACHE_MAX_SIZE=5000
MIGRATION_PARALLEL_WORKERS=4

# Optimize chunk sizes for your content
LANGCHAIN_CHUNK_SIZE=2000
LANGCHAIN_CHUNK_OVERLAP=400
```

### For Memory-Constrained Environments
```bash
# Reduce cache size and workers
EMBEDDING_CACHE_MAX_SIZE=500
MIGRATION_PARALLEL_WORKERS=1

# Smaller chunks
LANGCHAIN_CHUNK_SIZE=1000
LANGCHAIN_CHUNK_OVERLAP=200
```

### For Development
```bash
# Enable debug mode and reduce timeouts
DEBUG=true
MISTRAL_TIMEOUT=10
EMBEDDING_CACHE_TTL=300

# Enable fallback for testing without API key
FALLBACK_TO_HASH_EMBEDDINGS=true
```

## Security Considerations

1. **Never commit API keys** to version control
2. **Use strong SECRET_KEY** (32+ random characters)
3. **Restrict ALLOWED_ORIGINS** in production
4. **Rotate API keys** regularly
5. **Use environment-specific configurations**

## Troubleshooting

### Common Issues

1. **Mistral API Errors**
   - Check `MISTRAL_API_KEY` is valid
   - Verify API quota and rate limits
   - Enable `FALLBACK_TO_HASH_EMBEDDINGS` for testing

2. **Database Connection Issues**
   - Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY`
   - Check network connectivity
   - Ensure database is not paused (free tier)

3. **Performance Issues**
   - Increase `EMBEDDING_CACHE_MAX_SIZE`
   - Reduce `LANGCHAIN_CHUNK_SIZE` for faster processing
   - Increase `MISTRAL_TIMEOUT` for slow networks

4. **Memory Issues**
   - Reduce `EMBEDDING_CACHE_MAX_SIZE`
   - Decrease `MIGRATION_PARALLEL_WORKERS`
   - Use smaller `LANGCHAIN_CHUNK_SIZE`

### Health Check Endpoints

Monitor configuration and performance:

- `GET /api/v1/health` - Overall system health
- `GET /api/v1/health/embeddings` - Embeddings service status
- `GET /api/v1/health/migration` - Migration progress
- `GET /api/v1/health/performance` - Performance metrics

### Logging

Enable structured logging by setting appropriate log levels:

```bash
# For production
DEBUG=false

# For development/debugging
DEBUG=true
```

Logs include performance metrics, API response times, and error details for troubleshooting.