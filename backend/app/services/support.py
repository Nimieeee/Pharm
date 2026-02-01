"""
Support service for managing support requests
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.models.support import (
    SupportRequest, SupportRequestCreate, SupportRequestUpdate, 
    SupportRequestResponse
)
from app.models.user import User


class SupportService:
    """Support service for managing support requests"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def create_support_request(
        self, 
        request_data: SupportRequestCreate,
        user: Optional[User] = None
    ) -> SupportRequest:
        """Create a new support request"""
        try:
            # Prepare request data
            request_dict = request_data.dict()
            if user:
                request_dict["user_id"] = str(user.id)
            
            # Insert support request
            result = self.db.table("support_requests").insert(request_dict).execute()
            
            if not result.data:
                raise Exception("Failed to create support request")
            
            request_record = result.data[0]
            return SupportRequest(**request_record)
            
        except Exception as e:
            raise Exception(f"Failed to create support request: {str(e)}")
    
    async def get_user_support_requests(self, user: User) -> List[SupportRequest]:
        """Get all support requests for a user"""
        try:
            result = self.db.table("support_requests").select(
                "*"
            ).eq("user_id", str(user.id)).order("created_at", desc=True).execute()
            
            requests = []
            for request_record in result.data or []:
                support_request = SupportRequest(**request_record)
                requests.append(support_request)
            
            return requests
            
        except Exception as e:
            raise Exception(f"Failed to get user support requests: {str(e)}")
    
    async def get_support_request(
        self, 
        request_id: UUID, 
        user: Optional[User] = None
    ) -> Optional[SupportRequest]:
        """Get a specific support request"""
        try:
            query = self.db.table("support_requests").select("*").eq("id", str(request_id))
            
            # If user is provided, filter by user_id (for user access)
            if user and not user.is_admin:
                query = query.eq("user_id", str(user.id))
            
            result = query.execute()
            
            if not result.data:
                return None
            
            request_record = result.data[0]
            return SupportRequest(**request_record)
            
        except Exception as e:
            raise Exception(f"Failed to get support request: {str(e)}")
    
    async def get_all_support_requests(
        self, 
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all support requests (admin only)"""
        try:
            query = self.db.table("support_requests").select(
                "*, users(email, first_name, last_name)"
            ).order("created_at", desc=True)
            
            if status:
                query = query.eq("status", status)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            
            # Format requests with user info
            requests = []
            for request_record in result.data or []:
                user_info = request_record.get("users", {}) or {}
                
                request_dict = {
                    "id": request_record["id"],
                    "user_id": request_record.get("user_id"),
                    "email": request_record["email"],
                    "subject": request_record["subject"],
                    "message": request_record["message"],
                    "status": request_record["status"],
                    "admin_response": request_record.get("admin_response"),
                    "created_at": request_record["created_at"],
                    "updated_at": request_record["updated_at"],
                    "user_name": f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip() or "Anonymous",
                    "user_email": user_info.get("email", request_record["email"])
                }
                requests.append(request_dict)
            
            return requests
            
        except Exception as e:
            raise Exception(f"Failed to get support requests: {str(e)}")
    
    async def update_support_request(
        self, 
        request_id: UUID, 
        update_data: SupportRequestUpdate
    ) -> Optional[SupportRequest]:
        """Update a support request (admin only)"""
        try:
            # Get existing request
            existing = await self.get_support_request(request_id)
            if not existing:
                return None
            
            # Update request
            update_dict = update_data.dict(exclude_unset=True)
            if not update_dict:
                return existing
            
            result = self.db.table("support_requests").update(
                update_dict
            ).eq("id", str(request_id)).execute()
            
            if not result.data:
                return None
            
            request_record = result.data[0]
            return SupportRequest(**request_record)
            
        except Exception as e:
            raise Exception(f"Failed to update support request: {str(e)}")
    
    async def respond_to_support_request(
        self, 
        response_data: SupportRequestResponse
    ) -> Optional[SupportRequest]:
        """Respond to a support request (admin only)"""
        try:
            # Update request with response
            update_data = SupportRequestUpdate(
                status=response_data.status,
                admin_response=response_data.response
            )
            
            return await self.update_support_request(
                response_data.request_id, 
                update_data
            )
            
        except Exception as e:
            raise Exception(f"Failed to respond to support request: {str(e)}")
    
    async def get_support_stats(self) -> Dict[str, Any]:
        """Get support request statistics"""
        try:
            # Get all support requests
            result = self.db.table("support_requests").select("status, created_at").execute()
            requests_data = result.data or []
            
            # Count by status
            status_counts = {
                "open": 0,
                "in_progress": 0,
                "resolved": 0,
                "closed": 0
            }
            
            for request in requests_data:
                status = request.get("status", "open")
                if status in status_counts:
                    status_counts[status] += 1
            
            # Recent requests (last 7 days)
            from datetime import timedelta
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            recent_requests = len([
                r for r in requests_data 
                if r.get("created_at", "") > seven_days_ago
            ])
            
            return {
                "total": len(requests_data),
                "by_status": status_counts,
                "recent": recent_requests,
                "response_rate": round(
                    (status_counts["resolved"] + status_counts["closed"]) / 
                    max(len(requests_data), 1) * 100, 1
                )
            }
            
        except Exception as e:
            raise Exception(f"Failed to get support stats: {str(e)}")
    
    async def delete_support_request(self, request_id: UUID) -> bool:
        """Delete a support request (admin only)"""
        try:
            result = self.db.table("support_requests").delete().eq(
                "id", str(request_id)
            ).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete support request: {str(e)}")