# PharmGPT Backend API

FastAPI backend for the PharmGPT web application with user authentication, RAG functionality, and admin panel.

## Features

- **User Authentication**: JWT-based authentication with refresh tokens
- **RAG System**: Custom implementation + Supabase pgvector for optimized document processing
- **Vector Search**: HNSW indexing for fast similarity search with user isolation
- **Chat API**: AI-powered chat with Mistral integration
- **Admin Panel**: User management and system monitoring
- **Support System**: Contact form and ticket management

## Quick Start

### Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

### Docker

1. **Build the image**
   ```bash
   docker build -t pharmgpt-backend .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env pharmgpt-backend
   ```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `SECRET_KEY` | JWT secret key | Yes |
| `MISTRAL_API_KEY` | Mistral AI API key | Yes |
| `ADMIN_EMAIL` | Default admin email | No |
| `ADMIN_PASSWORD` | Default admin password | No |
| `DEBUG` | Enable debug mode | No |
| `PORT` | Server port | No |

## Database Setup

1. Create a Supabase project
2. Run the SQL migrations in `migrations/` directory
3. Update environment variables with your Supabase credentials

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Deployment

### Render

1. Connect your GitHub repository to Render
2. Use the `render.yaml` configuration
3. Set environment variables in Render dashboard
4. Deploy automatically on push

### Manual Deployment

1. Build and push Docker image
2. Deploy to your preferred platform
3. Set environment variables
4. Run database migrations

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Core configuration
│   ├── models/              # Pydantic models
│   └── services/            # Business logic
├── migrations/              # Database migrations
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
└── render.yaml             # Render deployment config
```

## Development

### Adding New Endpoints

1. Create endpoint in `app/api/v1/endpoints/`
2. Add to router in `app/api/v1/api.py`
3. Create service in `app/services/`
4. Add models in `app/models/`

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Linting
flake8 app/

# Type checking
mypy app/
```

## Security

- JWT tokens with refresh mechanism
- Password hashing with bcrypt
- Input validation with Pydantic
- CORS configuration
- Rate limiting (recommended for production)

## Monitoring

- Health check endpoint: `/health`
- System stats: `/api/v1/admin/system-health`
- Logging configured for production

## Support

For issues and questions:
- Check the API documentation
- Review environment configuration
- Contact support team