"""
Benchside Backend API
FastAPI application for the Benchside web application
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import shutil
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.api.v1.api import api_router
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting PharmGPT Backend API...")
    setup_logging()
    await init_db()
    print("✅ Database initialized")
    
    # Start the background scheduler
    from app.services.scheduler import start_scheduler, stop_scheduler
    start_scheduler()
    
    # Warmup: Pre-initialize services to avoid cold-start on first request
    try:
        from app.services.embeddings import embeddings_service
        # Make a dummy embedding call to warm up the Mistral connection
        await embeddings_service.generate_embedding("warmup")
        print("✅ Embeddings service warmed up")
    except Exception as e:
        print(f"⚠️ Warmup embedding failed (non-critical): {e}")
    
    yield
    # Shutdown
    stop_scheduler()
    # Shutdown
    stop_scheduler()
    print("🛑 Shutting down Benchside Backend API...")


# Create FastAPI app
app = FastAPI(
    title="Benchside API",
    description="AI-Powered Pharmacology Assistant Backend API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for frontend deployments
# Allow Netlify, Vercel domains and localhost for development
allowed_origins = []
for origin in settings.ALLOWED_ORIGINS:
    if "*" in origin:
        # For wildcard patterns, we'll use allow_origin_regex
        continue
    allowed_origins.append(origin)

# Explicitly add production domains to ensure they work even if regex fails
allowed_origins.extend([
    "https://benchside.vercel.app",
    "https://www.benchside.vercel.app",
    "https://pharmgpt.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://(benchside|pharmgpt).*\.vercel\.app", # Support preview branches
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add proxy headers middleware for correct HTTPS redirects behind Cloudflare
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount uploads directory for profile pictures and documents
os.makedirs("uploads/avatars", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
@app.head("/")
async def root():
    """Root endpoint - supports both GET and HEAD requests"""
    return {
        "message": "PharmGPT Backend API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
@app.head("/health")
async def health_check():
    """Health check endpoint - supports both GET and HEAD requests"""
    return {
        "status": "healthy",
        "service": "pharmgpt-backend",
        "version": "2.0.0"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.DEBUG else "Internal server error"
            }
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 7860)),
        reload=settings.DEBUG
    )