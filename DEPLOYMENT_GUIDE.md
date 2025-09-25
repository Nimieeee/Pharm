# Streamlit Cloud Deployment Guide

This guide covers deploying the Pharmacology Chat Application to Streamlit Cloud.

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Streamlit Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **Supabase Project**: Set up your Supabase database with pgvector extension
4. **Groq API Key**: Obtain API key from [console.groq.com](https://console.groq.com)

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository contains:
- `requirements.txt` with all dependencies
- `.streamlit/config.toml` for Streamlit configuration
- `app.py` as your main application file
- All necessary Python modules

### 2. Deploy to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Select the branch (usually `main`)
5. Set the main file path to `app.py`
6. Click "Deploy"

### 3. Configure Secrets

In your Streamlit Cloud app dashboard:

1. Go to "Settings" → "Secrets"
2. Add the following secrets in TOML format:

```toml
# Supabase Configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_supabase_anon_key"
SUPABASE_SERVICE_KEY = "your_supabase_service_key"

# Groq API Configuration  
GROQ_API_KEY = "your_groq_api_key"
GROQ_FAST_MODEL = "gemma2-9b-it"
GROQ_PREMIUM_MODEL = "qwen/qwen3-32b"

# Application Configuration
APP_SECRET_KEY = "your_secure_random_key"
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"

# Health Check Configuration
HEALTH_CHECK_ENABLED = true
HEALTH_CHECK_TOKEN = "your_health_check_token"

# Optional: Embedding Model
ST_EMBEDDINGS_MODEL = "all-MiniLM-L6-v2"
```

### 4. Database Setup

Ensure your Supabase database is properly configured:

1. **Enable pgvector extension**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Run migrations**: Use the migration scripts in the `migrations/` folder

3. **Set up Row Level Security (RLS)**: Ensure user data isolation

### 5. Verify Deployment

1. **Access your app**: Use the URL provided by Streamlit Cloud
2. **Test authentication**: Try signing up and logging in
3. **Test chat functionality**: Send a message and verify responses
4. **Check health status**: Visit `/health` endpoint (if configured)

## Health Check Endpoint

Access the health check at: `https://your-app.streamlit.app/?page=health&token=your_health_check_token`

The health check monitors:
- Database connectivity
- Groq API status
- System resources
- Application health

## Environment Variables

The application supports both Streamlit secrets and environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Yes | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | No | Supabase service key (only needed for database migrations) |
| `GROQ_API_KEY` | Yes | Groq API key for AI models |
| `GROQ_FAST_MODEL` | No | Fast model name (default: gemma2-9b-it) |
| `GROQ_PREMIUM_MODEL` | No | Premium model name (default: qwen/qwen3-32b) |
| `APP_SECRET_KEY` | No | Application secret key |
| `ENVIRONMENT` | No | Environment (development/production) |
| `LOG_LEVEL` | No | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `HEALTH_CHECK_ENABLED` | No | Enable health check endpoint |
| `HEALTH_CHECK_TOKEN` | No | Token for health check authorization |

## Performance Optimization

### Memory Management

The application includes memory optimization features:
- CPU-only PyTorch for reduced memory footprint
- Garbage collection in RAG pipeline
- Efficient vector search with batching
- Session state cleanup

### Caching

Streamlit caching is configured for:
- Database connections
- Model configurations
- Embedding computations
- Vector search results

## Monitoring and Logging

### Application Logs

Logs are available in the Streamlit Cloud dashboard under "Logs".

### Health Monitoring

The health check endpoint provides:
- Service status (database, API, system resources)
- Performance metrics
- Error summaries
- System uptime

### Error Tracking

The application includes built-in error monitoring:
- Error counting and categorization
- Recent error history
- Context-aware error logging
- User-specific error tracking

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Check `requirements.txt` for missing dependencies
   - Verify Python version compatibility

2. **Memory Issues**:
   - Use CPU-only PyTorch
   - Reduce batch sizes in document processing
   - Clear session state regularly

3. **Database Connection Issues**:
   - Verify Supabase URL and keys
   - Check network connectivity
   - Ensure RLS policies are correct

4. **API Rate Limits**:
   - Implement request queuing
   - Add retry mechanisms
   - Monitor API usage

### Debug Mode

For debugging, set in secrets:
```toml
LOG_LEVEL = "DEBUG"
ENVIRONMENT = "development"
```

## Security Considerations

1. **Secrets Management**: Never commit secrets to version control
2. **API Keys**: Rotate keys regularly
3. **Database Security**: Use RLS policies for data isolation
4. **HTTPS**: Streamlit Cloud provides HTTPS by default
5. **Authentication**: Implement proper session management

## Scaling Considerations

1. **Database**: Monitor connection pool usage
2. **API Limits**: Implement rate limiting and queuing
3. **Memory**: Use efficient data structures and cleanup
4. **Caching**: Implement appropriate caching strategies

## Support

For deployment issues:
1. Check Streamlit Cloud documentation
2. Review application logs
3. Use the health check endpoint
4. Monitor error tracking

## Updates and Maintenance

1. **Code Updates**: Push to GitHub to trigger redeployment
2. **Dependencies**: Update `requirements.txt` as needed
3. **Secrets**: Update through Streamlit Cloud dashboard
4. **Database**: Run migrations for schema changes