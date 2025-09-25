"""
Authentication Manager for Pharmacology Chat App
Handles user authentication using Supabase Auth with comprehensive error handling
"""

import streamlit as st
from supabase import create_client, Client
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
import time

from error_handler import ErrorHandler, ErrorType, with_error_handling, RetryConfig

logger = logging.getLogger(__name__)

@dataclass
class AuthResult:
    """Result of authentication operations"""
    success: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    error_message: Optional[str] = None
    user_data: Optional[Dict[str, Any]] = None

@dataclass
class User:
    """User data model"""
    id: str
    email: str
    created_at: str
    preferences: Dict[str, Any]
    subscription_tier: str = "free"

class AuthenticationManager:
    """Manages user authentication with Supabase Auth and comprehensive error handling"""
    
    def __init__(self):
        """Initialize Supabase client with error handling"""
        self.error_handler = ErrorHandler()
        self.retry_config = RetryConfig(max_attempts=3, base_delay=2.0)
        
        try:
            self.supabase_url = st.secrets["SUPABASE_URL"]
            self.supabase_key = st.secrets["SUPABASE_ANON_KEY"]
        except KeyError as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.AUTHENTICATION, "configuration"
            )
            st.error(f"🔧 Configuration Error: Missing {e} in Streamlit secrets.")
            st.info("📝 Please add the required secrets in your Streamlit app settings.")
            st.stop()
        
        try:
            self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
            # Test connection
            self._test_connection()
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.AUTHENTICATION, "initialization"
            )
            self.error_handler.display_error_to_user(error_info)
            st.stop()
    
    def _test_connection(self):
        """Test Supabase connection"""
        try:
            # Simple test to verify connection
            self.supabase.auth.get_session()
        except Exception as e:
            raise Exception(f"Failed to connect to Supabase: {str(e)}")
    
    def sign_up(self, email: str, password: str) -> AuthResult:
        """
        Register a new user with comprehensive error handling
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            AuthResult with success status and user data or error message
        """
        # Validate input
        if not email or not password:
            return AuthResult(
                success=False,
                error_message="Email and password are required."
            )
        
        if len(password) < 6:
            return AuthResult(
                success=False,
                error_message="Password must be at least 6 characters long."
            )
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    logger.info(f"User registration successful: {email}")
                    return AuthResult(
                        success=True,
                        user_id=response.user.id,
                        email=response.user.email,
                        user_data=response.user.user_metadata
                    )
                else:
                    return AuthResult(
                        success=False,
                        error_message="Registration failed. Please check your email and try again."
                    )
                    
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorType.AUTHENTICATION, "sign_up"
                )
                
                # If this is the last attempt
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"Registration failed after {attempt} attempts: {str(e)}")
                    return AuthResult(
                        success=False,
                        error_message=error_info.user_message
                    )
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying registration in {delay:.1f} seconds")
                time.sleep(delay)
        
        return AuthResult(
            success=False,
            error_message="Registration failed after multiple attempts. Please try again later."
        )
    
    def sign_in(self, email: str, password: str) -> AuthResult:
        """
        Sign in an existing user with comprehensive error handling
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            AuthResult with success status and user data or error message
        """
        # Validate input
        if not email or not password:
            return AuthResult(
                success=False,
                error_message="Email and password are required."
            )
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                response = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    logger.info(f"User login successful: {email}")
                    return AuthResult(
                        success=True,
                        user_id=response.user.id,
                        email=response.user.email,
                        user_data=response.user.user_metadata
                    )
                else:
                    return AuthResult(
                        success=False,
                        error_message="Invalid credentials. Please check your email and password."
                    )
                    
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorType.AUTHENTICATION, "sign_in"
                )
                
                # Don't retry for credential errors
                error_str = str(e).lower()
                if "invalid" in error_str or "unauthorized" in error_str or "credentials" in error_str:
                    return AuthResult(
                        success=False,
                        error_message="Invalid email or password. Please check your credentials."
                    )
                
                # If this is the last attempt
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"Login failed after {attempt} attempts: {str(e)}")
                    return AuthResult(
                        success=False,
                        error_message=error_info.user_message
                    )
                
                # Wait before retry for network/service errors
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying login in {delay:.1f} seconds")
                time.sleep(delay)
        
        return AuthResult(
            success=False,
            error_message="Login failed after multiple attempts. Please try again later."
        )
    
    def sign_out(self) -> bool:
        """
        Sign out the current user with error handling
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.supabase.auth.sign_out()
            logger.info("User signed out successfully")
            return True
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.AUTHENTICATION, "sign_out"
            )
            # For sign out, we'll show a warning but still consider it successful
            # since the user intent is to log out
            st.warning(f"⚠️ {error_info.user_message}")
            logger.warning(f"Sign out error (continuing anyway): {str(e)}")
            return True  # Return True to allow user to continue
    
    def get_current_user(self) -> Optional[User]:
        """
        Get the currently authenticated user with error handling
        
        Returns:
            User object if authenticated, None otherwise
        """
        try:
            user = self.supabase.auth.get_user()
            if user and user.user:
                return User(
                    id=user.user.id,
                    email=user.user.email,
                    created_at=user.user.created_at,
                    preferences=user.user.user_metadata or {},
                    subscription_tier="free"  # Default tier
                )
            return None
        except Exception as e:
            # Log the error but don't show to user as this is called frequently
            logger.debug(f"Error getting current user: {str(e)}")
            return None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is currently authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.get_current_user() is not None
    
    def refresh_session(self) -> bool:
        """
        Refresh the current session with error handling
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase.auth.refresh_session()
            if response.user is not None:
                logger.debug("Session refreshed successfully")
                return True
            return False
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.AUTHENTICATION, "refresh_session"
            )
            logger.warning(f"Session refresh failed: {str(e)}")
            return False
    
    def validate_session(self) -> bool:
        """
        Validate current session and handle session expiry
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            user = self.get_current_user()
            if user is None:
                return False
            
            # Try to refresh session if it's close to expiry
            if not self.refresh_session():
                logger.info("Session validation failed - user needs to re-authenticate")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Session validation error: {str(e)}")
            return False