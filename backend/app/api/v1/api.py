"""
API v1 router configuration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, ai, admin, support, health, lab_report, transcription, visualize, export, research_tasks, slides, docs, admet, literature


api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(export.router, prefix="/ai", tags=["export"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(support.router, prefix="/support", tags=["support"])
api_router.include_router(lab_report.router, prefix="/lab-report", tags=["lab-report"])
api_router.include_router(transcription.router, tags=["audio"])
api_router.include_router(visualize.router, prefix="/visualize", tags=["visualize"])
api_router.include_router(research_tasks.router, prefix="/research", tags=["research"])
api_router.include_router(slides.router, prefix="/slides", tags=["slides"])
api_router.include_router(docs.router, prefix="/docs", tags=["docs"])
api_router.include_router(admet.router, prefix="/admet", tags=["admet"])
api_router.include_router(literature.router, prefix="/literature", tags=["literature"])