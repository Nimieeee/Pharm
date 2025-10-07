"""
Security utilities and middleware
"""

from functools import wraps
from typing import Optional, Callable
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client

from app.core.database import get_db
from app.services.auth import AuthService
from app.models.user import User

security = HTTPBearer()


class SecurityMiddleware:
    """Security middleware for request processing"""
    
    def __init__(self, db: Client):
        self.auth_service = AuthService(db)
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials
    ) -> Optional[User]:
        """Get current user from JWT token"""
        try:
            # Verify token
            token_data = self.auth_service.verify_token(credentials.credentials)
            
            # Get user
            user = await self.auth_service.get_user_by_email(token_data.email)
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception:
            return None
    
    async def require_auth(
        self, 
        credentials: HTTPAuthorizationCredentials
    ) -> User:
        """Require authentication and return user"""
        user = await self.get_current_user(credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return user
    
    async def require_admin(
        self, 
        credentials: HTTPAuthorizationCredentials
    ) -> User:
        """Require admin authentication and return user"""
        user = await self.require_auth(credentials)
        if not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user


# Global security middleware instance
def get_security_middleware(db: Client = Depends(get_db)) -> SecurityMiddleware:
    """Get security middleware instance"""
    return SecurityMiddleware(db)


# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    security_middleware: SecurityMiddleware = Depends(get_security_middleware)
) -> User:
    """Dependency to get current authenticated user"""
    return await security_middleware.require_auth(credentials)


async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    security_middleware: SecurityMiddleware = Depends(get_security_middleware)
) -> User:
    """Dependency to get current authenticated admin user"""
    return await security_middleware.require_admin(credentials)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    security_middleware: SecurityMiddleware = Depends(get_security_middleware)
) -> Optional[User]:
    """Dependency to get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    return await security_middleware.get_current_user(credentials)


# Decorator functions
def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator is for non-FastAPI functions
        # For FastAPI endpoints, use the Depends(get_current_user) dependency
        return await func(*args, **kwargs)
    return wrapper


def require_admin(func: Callable) -> Callable:
    """Decorator to require admin access"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator is for non-FastAPI functions
        # For FastAPI endpoints, use the Depends(get_current_admin_user) dependency
        return await func(*args, **kwargs)
    return wrapper


class UserContext:
    """User context for request processing"""
    
    def __init__(self):
        self.user: Optional[User] = None
        self.is_authenticated: bool = False
        self.is_admin: bool = False
    
    def set_user(self, user: Optional[User]):
        """Set current user context"""
        self.user = user
        self.is_authenticated = user is not None
        self.is_admin = user.is_admin if user else False
    
    def require_auth(self):
        """Require authentication"""
        if not self.is_authenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
    
    def require_admin(self):
        """Require admin access"""
        self.require_auth()
        if not self.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
    
    def can_access_resource(self, resource_user_id: str) -> bool:
        """Check if user can access a resource"""
        if not self.is_authenticated:
            return False
        
        # Admin can access all resources
        if self.is_admin:
            return True
        
        # User can access their own resources
        return str(self.user.id) == resource_user_id


# Request context middleware
async def add_user_context(
    request: Request,
    user: Optional[User] = Depends(get_optional_user)
):
    """Add user context to request"""
    context = UserContext()
    context.set_user(user)
    request.state.user_context = context
    return context


def get_user_context(request: Request) -> UserContext:
    """Get user context from request"""
    return getattr(request.state, 'user_context', UserContext())