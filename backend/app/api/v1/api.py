"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, ai, admin, support, health

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(health.router, prefix="/health", tags=["health"])