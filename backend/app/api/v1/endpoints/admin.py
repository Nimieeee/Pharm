"""
Admin API endpoints
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_admin_user
from app.services.admin import AdminService
from app.models.user import User, UserProfile

router = APIRouter()


def get_admin_service(db: Client = Depends(get_db)) -> AdminService:
    """Get admin service"""
    return AdminService(db)


@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get system statistics
    
    Requires admin access. Returns overall system metrics including:
    - User counts and activity
    - Conversation and message statistics
    - Document upload metrics
    - Support request status
    """
    try:
        stats = await admin_service.get_system_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system stats: {str(e)}"
        )


@router.get("/users", response_model=List[UserProfile])
async def get_all_users(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, min_length=1),
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get all users with profiles
    
    Requires admin access. Returns list of all users with:
    - Basic user information
    - Account status
    - Conversation counts
    - Registration date
    
    Query parameters:
    - **limit**: Maximum number of users to return
    - **offset**: Number of users to skip (for pagination)
    - **search**: Search term to filter users by email or name
    """
    try:
        users = await admin_service.get_all_users(limit, offset, search)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user_details(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get detailed user information
    
    Requires admin access. Returns detailed information about a specific user.
    """
    try:
        user = await admin_service.get_user_details(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user details: {str(e)}"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: UUID,
    is_active: bool,
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Update user active status
    
    Requires admin access. Activate or deactivate a user account.
    """
    try:
        success = await admin_service.update_user_status(user_id, is_active)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        status_text = "activated" if is_active else "deactivated"
        return {"message": f"User {status_text} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user status: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Delete user and all associated data
    
    Requires admin access. Permanently deletes a user and all their:
    - Conversations
    - Messages
    - Uploaded documents
    - Support requests
    
    This action cannot be undone.
    """
    try:
        # Prevent admin from deleting themselves
        if user_id == current_admin.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own admin account"
            )
        
        success = await admin_service.delete_user_data(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {"message": "User and all associated data deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.get("/conversations", response_model=List[Dict[str, Any]])
async def get_all_conversations(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get all conversations across all users
    
    Requires admin access. Returns list of all conversations with:
    - Conversation details
    - Associated user information
    - Message and document counts
    - Activity timestamps
    
    Query parameters:
    - **limit**: Maximum number of conversations to return
    - **offset**: Number of conversations to skip (for pagination)
    """
    try:
        conversations = await admin_service.get_all_conversations(limit, offset)
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/system-health", response_model=Dict[str, Any])
async def get_system_health(
    current_admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get system health status
    
    Requires admin access. Returns system health information including:
    - Database connectivity
    - Recent activity metrics
    - Service status
    - System version
    """
    try:
        health = await admin_service.get_system_health()
        return health
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )