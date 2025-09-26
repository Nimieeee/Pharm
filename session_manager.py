"""
Session Manager for Pharmacology Chat App
Handles user sessions and Streamlit session state integration
"""

import streamlit as st
from typing import Optional, Dict, Any
from dataclasses import dataclass
from auth_manager import User, AuthenticationManager

@dataclass
class UserSession:
    """User session data model"""
    user_id: str
    email: str
    preferences: Dict[str, Any]
    model_preference: str = "fast"
    theme: str = "dark"
    is_authenticated: bool = True

class SessionManager:
    """Manages user sessions and Streamlit session state"""
    
    def __init__(self, auth_manager: AuthenticationManager):
        """
        Initialize session manager
        
        Args:
            auth_manager: Authentication manager instance
        """
        self.auth_manager = auth_manager
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'user_session' not in st.session_state:
            st.session_state.user_session = None
        if 'authentication_status' not in st.session_state:
            st.session_state.authentication_status = None
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        if 'model_preference' not in st.session_state:
            st.session_state.model_preference = "fast"
        if 'theme' not in st.session_state:
            st.session_state.theme = "dark"
        if 'conversation_history' not in st.session_state:
            st.session_state.conversation_history = []
        
        # Conversation management session state
        if 'current_conversation_id' not in st.session_state:
            st.session_state.current_conversation_id = None
        if 'user_conversations' not in st.session_state:
            st.session_state.user_conversations = []
        if 'conversation_switched' not in st.session_state:
            st.session_state.conversation_switched = False
        if 'conversation_isolation_user_id' not in st.session_state:
            st.session_state.conversation_isolation_user_id = None
    
    def initialize_session(self, user_id: str, email: str, preferences: Dict[str, Any] = None) -> None:
        """
        Initialize user session after successful authentication
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            preferences: User preferences dictionary
        """
        # Ensure user exists in database
        self._ensure_user_exists(user_id, email)
        
        # Load preferences from database if not provided
        if preferences is None:
            preferences = self.load_user_preferences(user_id)
            
        user_session = UserSession(
            user_id=user_id,
            email=email,
            preferences=preferences,
            model_preference=preferences.get('model_preference', 'fast'),
            theme=preferences.get('theme', 'dark'),
            is_authenticated=True
        )
        
        # Store in Streamlit session state
        st.session_state.user_session = user_session
        st.session_state.authentication_status = "authenticated"
        st.session_state.user_preferences = preferences
        st.session_state.model_preference = user_session.model_preference
        st.session_state.theme = user_session.theme
        
        # Initialize empty conversation history for new session
        st.session_state.conversation_history = []
        
        # Initialize conversation management session state with proper isolation
        st.session_state.current_conversation_id = None
        st.session_state.user_conversations = []
        st.session_state.conversation_switched = False
        st.session_state.conversation_isolation_user_id = user_id
    
    def get_user_session(self) -> Optional[UserSession]:
        """
        Get current user session
        
        Returns:
            UserSession if user is authenticated, None otherwise
        """
        return st.session_state.get('user_session')
    
    def clear_session(self) -> None:
        """Clear user session and reset session state"""
        st.session_state.user_session = None
        st.session_state.authentication_status = None
        st.session_state.user_preferences = {}
        st.session_state.model_preference = "fast"
        st.session_state.theme = "dark"
        st.session_state.conversation_history = []
        
        # Clear conversation management session state
        st.session_state.current_conversation_id = None
        st.session_state.user_conversations = []
        st.session_state.conversation_switched = False
        st.session_state.conversation_isolation_user_id = None
        
        # Clear any other session-specific data (but preserve the core conversation management keys we just set)
        core_conversation_keys = {
            'current_conversation_id', 'user_conversations', 
            'conversation_switched', 'conversation_isolation_user_id'
        }
        keys_to_clear = [key for key in st.session_state.keys() 
                        if (key.startswith('user_') or key.startswith('chat_') or key.startswith('conversation_'))
                        and key not in core_conversation_keys]
        for key in keys_to_clear:
            del st.session_state[key]
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated in current session
        
        Returns:
            True if authenticated, False otherwise
        """
        # Check if we have a valid Supabase auth session
        try:
            current_user = self.auth_manager.get_current_user()
            if current_user:
                # Ensure our session state matches the auth state
                if not st.session_state.get('user_session'):
                    # Initialize session from Supabase auth
                    self.initialize_session(current_user.id, current_user.email, current_user.preferences)
                return True
        except Exception:
            pass  # Fall through to session state check
        
        # Check session state as fallback
        user_session = self.get_user_session()
        return user_session is not None and user_session.is_authenticated
    
    def get_user_id(self) -> Optional[str]:
        """
        Get current user ID
        
        Returns:
            User ID if authenticated, None otherwise
        """
        # First try to get from Supabase auth (most reliable)
        try:
            current_user = self.auth_manager.get_current_user()
            if current_user and current_user.id:
                return current_user.id
        except Exception:
            pass  # Fall through to session state
        
        # Fallback to session state
        user_session = self.get_user_session()
        if user_session:
            return user_session.user_id
        
        return None
    
    def get_user_email(self) -> Optional[str]:
        """
        Get current user email
        
        Returns:
            User email if authenticated, None otherwise
        """
        # First try to get from Supabase auth
        try:
            current_user = self.auth_manager.get_current_user()
            if current_user and current_user.email:
                return current_user.email
        except Exception:
            pass  # Fall through to session state
        
        # Fallback to session state
        user_session = self.get_user_session()
        return user_session.email if user_session else None
    
    def update_model_preference(self, model_preference: str) -> None:
        """
        Update user's model preference in session and database
        
        Args:
            model_preference: "fast" or "premium"
        """
        # Temporary fix: Just update session state, ignore user_session object
        st.session_state.model_preference = model_preference
        
        # Original code (commented out temporarily)
        # if self.is_authenticated():
        #     st.session_state.model_preference = model_preference
        #     user_session = st.session_state.user_session
        #     if user_session:
        #         user_session.model_preference = model_preference
        #         st.session_state.user_session = user_session
        #     
        #     # Persist to database
        #     self._persist_user_preferences()
    
    def update_theme(self, theme: str) -> None:
        """
        Update user's theme preference - enforces permanent dark theme
        
        Args:
            theme: Theme preference (always forced to "dark")
        """
        # Force dark theme regardless of input
        st.session_state.theme = "dark"
    
    def get_model_preference(self) -> str:
        """
        Get current model preference
        
        Returns:
            Model preference ("fast" or "premium")
        """
        return st.session_state.get('model_preference', 'fast')
    
    def get_theme(self) -> str:
        """
        Get current theme - always returns dark theme
        
        Returns:
            Theme ("dark" - permanent dark theme)
        """
        # Always return dark theme
        return "dark"
    
    def validate_session(self) -> bool:
        """
        Validate current session with authentication manager
        
        Returns:
            True if session is valid, False otherwise
        """
        # First check if we have a session in session state
        user_session = st.session_state.get('user_session')
        if user_session and user_session.is_authenticated:
            # We have a valid session state, that's good enough for now
            return True
        
        # Try to get from Supabase auth as backup
        try:
            current_user = self.auth_manager.get_current_user()
            if current_user:
                # Initialize session from Supabase auth
                self.initialize_session(current_user.id, current_user.email, current_user.preferences)
                return True
        except Exception:
            pass  # Fall through to return False
        
        # No valid session found
        return False
    
    def refresh_session(self) -> bool:
        """
        Refresh current session
        
        Returns:
            True if refresh successful, False otherwise
        """
        if not self.is_authenticated():
            return False
            
        success = self.auth_manager.refresh_session()
        if not success:
            self.clear_session()
            
        return success
    
    def _persist_user_preferences(self) -> bool:
        """
        Persist user preferences to database
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        try:
            user_session = self.get_user_session()
            if not user_session:
                return False
            
            # Get current user from auth manager
            current_user = self.auth_manager.get_current_user()
            if not current_user:
                return False
            
            # Update preferences in database
            preferences = {
                'model_preference': user_session.model_preference,
                'theme': user_session.theme,
                **user_session.preferences  # Merge with existing preferences
            }
            
            # Use Supabase client to update user preferences
            from database_utils import get_database_client
            db_client = get_database_client()
            
            if db_client:
                result = db_client.table('users').update({
                    'preferences': preferences
                }).eq('id', current_user.id).execute()
                
                if result.data:
                    # Update session preferences
                    user_session.preferences = preferences
                    st.session_state.user_session = user_session
                    return True
            
            return False
            
        except Exception as e:
            st.error(f"Failed to persist user preferences: {e}")
            return False
    
    def _ensure_user_exists(self, user_id: str, email: str) -> bool:
        """
        Ensure user exists in the users table, create if not exists
        
        Args:
            user_id: User's unique identifier
            email: User's email address
            
        Returns:
            True if user exists or was created successfully
        """
        try:
            # Use the auth manager's client to ensure we have the right permissions
            db_client = self.auth_manager.supabase
            
            # Check if user already exists
            result = db_client.table('users').select('id').eq('id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                # User already exists
                return True
            
            # User doesn't exist, create them
            user_data = {
                'id': user_id,
                'email': email,
                'preferences': {
                    'model_preference': 'fast',
                    'theme': 'dark'
                },
                'subscription_tier': 'free'
            }
            
            create_result = db_client.table('users').insert(user_data).execute()
            
            if create_result.data:
                print(f"✅ Created user record for {email}")
                return True
            else:
                print(f"❌ Failed to create user record for {email}")
                return False
                
        except Exception as e:
            print(f"❌ Error ensuring user exists: {e}")
            # Don't fail the session initialization, just log the error
            return False
    
    def load_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Load user preferences from database
        
        Args:
            user_id: User ID to load preferences for
            
        Returns:
            Dictionary of user preferences
        """
        try:
            # Use the auth manager's client
            db_client = self.auth_manager.supabase
            
            if db_client:
                result = db_client.table('users').select('preferences').eq('id', user_id).execute()
                
                if result.data and len(result.data) > 0:
                    return result.data[0].get('preferences', {})
            
            return {
                'model_preference': 'fast',
                'theme': 'light'
            }
            
        except Exception as e:
            print(f"Failed to load user preferences: {e}")
            return {
                'model_preference': 'fast',
                'theme': 'light'
            }
    
    def switch_conversation(self, conversation_id: str) -> bool:
        """
        Switch to a different conversation and ensure proper isolation
        
        Args:
            conversation_id: ID of the conversation to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        user_id = self.get_user_id()
        if not user_id:
            return False
        
        # Ensure conversation isolation - verify the conversation belongs to the current user
        if not self._verify_conversation_ownership(user_id, conversation_id):
            return False
        
        # Clear current conversation history to prevent data leakage
        st.session_state.conversation_history = []
        
        # Update current conversation
        old_conversation_id = st.session_state.current_conversation_id
        st.session_state.current_conversation_id = conversation_id
        st.session_state.conversation_switched = True
        
        # Update isolation tracking
        st.session_state.conversation_isolation_user_id = user_id
        
        return True
    
    def get_current_conversation_id(self) -> Optional[str]:
        """
        Get the current conversation ID with user isolation check
        
        Returns:
            Current conversation ID if valid, None otherwise
        """
        if not self.is_authenticated():
            return None
        
        user_id = self.get_user_id()
        if not user_id:
            return None
        
        # Verify conversation isolation
        if st.session_state.conversation_isolation_user_id != user_id:
            # User has changed, clear conversation state
            st.session_state.current_conversation_id = None
            st.session_state.conversation_isolation_user_id = user_id
            return None
        
        return st.session_state.current_conversation_id
    
    def set_current_conversation_id(self, conversation_id: str) -> bool:
        """
        Set the current conversation ID with proper isolation
        
        Args:
            conversation_id: ID of the conversation to set as current
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_authenticated():
            return False
        
        user_id = self.get_user_id()
        if not user_id:
            return False
        
        # Verify conversation ownership
        if not self._verify_conversation_ownership(user_id, conversation_id):
            return False
        
        st.session_state.current_conversation_id = conversation_id
        st.session_state.conversation_isolation_user_id = user_id
        return True
    
    def update_user_conversations(self, conversations: list) -> None:
        """
        Update the list of user conversations in session state
        
        Args:
            conversations: List of conversation objects for the current user
        """
        if not self.is_authenticated():
            return
        
        user_id = self.get_user_id()
        if not user_id:
            return
        
        # Only update if conversations belong to current user (additional safety check)
        st.session_state.user_conversations = conversations
        st.session_state.conversation_isolation_user_id = user_id
    
    def get_user_conversations(self) -> list:
        """
        Get user conversations from session state with isolation check
        
        Returns:
            List of conversations for current user
        """
        if not self.is_authenticated():
            return []
        
        user_id = self.get_user_id()
        if not user_id:
            return []
        
        # Verify conversation isolation
        if st.session_state.conversation_isolation_user_id != user_id:
            # User has changed, clear conversation state
            st.session_state.user_conversations = []
            st.session_state.conversation_isolation_user_id = user_id
            return []
        
        return st.session_state.user_conversations
    
    def was_conversation_switched(self) -> bool:
        """
        Check if conversation was recently switched
        
        Returns:
            True if conversation was switched, False otherwise
        """
        switched = st.session_state.get('conversation_switched', False)
        if switched:
            # Reset the flag after checking
            st.session_state.conversation_switched = False
        return switched
    
    def _verify_conversation_ownership(self, user_id: str, conversation_id: str) -> bool:
        """
        Verify that a conversation belongs to the specified user
        
        Args:
            user_id: User ID to verify ownership for
            conversation_id: Conversation ID to verify
            
        Returns:
            True if conversation belongs to user, False otherwise
        """
        try:
            # Use the auth manager's client to verify ownership
            db_client = self.auth_manager.supabase
            
            if db_client:
                result = db_client.table('conversations').select('user_id').eq(
                    'id', conversation_id
                ).eq('user_id', user_id).eq('is_active', True).execute()
                
                return len(result.data or []) > 0
            
            return False
            
        except Exception as e:
            print(f"Error verifying conversation ownership: {e}")
            return False