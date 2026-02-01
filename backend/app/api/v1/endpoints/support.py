"""
Support API endpoints
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin_user, get_optional_user
from app.services.support import SupportService
from app.models.user import User
from app.models.support import (
    SupportRequest, SupportRequestCreate, SupportRequestUpdate, 
    SupportRequestResponse
)

router = APIRouter()


def get_support_service(db: Client = Depends(get_db)) -> SupportService:
    """Get support service"""
    return SupportService(db)


@router.post("/requests", response_model=SupportRequest, status_code=status.HTTP_201_CREATED)
async def create_support_request(
    request_data: SupportRequestCreate,
    current_user: Optional[User] = Depends(get_optional_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Create a new support request
    
    Can be used by authenticated users or anonymous users.
    
    - **email**: Contact email address
    - **subject**: Brief description of the issue
    - **message**: Detailed description of the issue or question
    """
    try:
        support_request = await support_service.create_support_request(
            request_data, current_user
        )
        return support_request
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create support request: {str(e)}"
        )


@router.get("/requests", response_model=List[SupportRequest])
async def get_user_support_requests(
    current_user: User = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Get all support requests for the current user
    
    Returns list of support requests created by the authenticated user.
    """
    try:
        requests = await support_service.get_user_support_requests(current_user)
        return requests
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get support requests: {str(e)}"
        )


@router.get("/requests/{request_id}", response_model=SupportRequest)
async def get_support_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Get a specific support request
    
    Users can only access their own support requests.
    Admins can access any support request.
    """
    try:
        support_request = await support_service.get_support_request(
            request_id, current_user
        )
        
        if not support_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support request not found"
            )
        
        return support_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get support request: {str(e)}"
        )


# Admin endpoints
@router.get("/admin/requests", response_model=List[Dict[str, Any]])
async def get_all_support_requests(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_admin: User = Depends(get_current_admin_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Get all support requests (admin only)
    
    Returns list of all support requests with user information.
    
    Query parameters:
    - **status**: Filter by status (open, in_progress, resolved, closed)
    - **limit**: Maximum number of requests to return
    - **offset**: Number of requests to skip (for pagination)
    """
    try:
        # Validate status filter
        if status_filter and status_filter not in ['open', 'in_progress', 'resolved', 'closed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter"
            )
        
        requests = await support_service.get_all_support_requests(
            status_filter, limit, offset
        )
        return requests
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get support requests: {str(e)}"
        )


@router.put("/admin/requests/{request_id}", response_model=SupportRequest)
async def update_support_request(
    request_id: UUID,
    update_data: SupportRequestUpdate,
    current_admin: User = Depends(get_current_admin_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Update a support request (admin only)
    
    - **status**: New status (open, in_progress, resolved, closed)
    - **admin_response**: Admin response to the request
    """
    try:
        support_request = await support_service.update_support_request(
            request_id, update_data
        )
        
        if not support_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support request not found"
            )
        
        return support_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update support request: {str(e)}"
        )


@router.post("/admin/requests/{request_id}/respond", response_model=SupportRequest)
async def respond_to_support_request(
    request_id: UUID,
    response: str,
    status_update: str = "resolved",
    current_admin: User = Depends(get_current_admin_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Respond to a support request (admin only)
    
    - **response**: Admin response message
    - **status_update**: New status after response (default: resolved)
    """
    try:
        # Validate status
        if status_update not in ['in_progress', 'resolved', 'closed']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status. Must be: in_progress, resolved, or closed"
            )
        
        response_data = SupportRequestResponse(
            request_id=request_id,
            response=response,
            status=status_update
        )
        
        support_request = await support_service.respond_to_support_request(response_data)
        
        if not support_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support request not found"
            )
        
        return support_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to respond to support request: {str(e)}"
        )


@router.delete("/admin/requests/{request_id}")
async def delete_support_request(
    request_id: UUID,
    current_admin: User = Depends(get_current_admin_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Delete a support request (admin only)
    
    Permanently deletes a support request. This action cannot be undone.
    """
    try:
        success = await support_service.delete_support_request(request_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Support request not found"
            )
        
        return {"message": "Support request deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete support request: {str(e)}"
        )


@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_support_stats(
    current_admin: User = Depends(get_current_admin_user),
    support_service: SupportService = Depends(get_support_service)
):
    """
    Get support request statistics (admin only)
    
    Returns statistics about support requests including:
    - Total count
    - Count by status
    - Recent activity
    - Response rate
    """
    try:
        stats = await support_service.get_support_stats()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get support stats: {str(e)}"
        )