"""
Protected Chat Application - Integrates authentication with chat interface
Main application entry point with authentication checks and protected routes
"""

import streamlit as st
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# Import authentication and session management
from auth_manager import AuthenticationManager, AuthResult
from session_manager import SessionManager
from auth_ui import AuthInterface

# Import chat functionality
from chat_manager import ChatManager
from message_store import Message

# Import UI components
from theme_manager import ThemeManager
from ui_components import ChatInterface

# Import RAG and model components
from rag_orchestrator_optimized import RAGOrchestrator
from model_manager import ModelManager
from run_migrations import get_supabase_client

# Import document management components
from document_manager import DocumentManager
from document_ui import DocumentInterface

# Configure Streamlit page
st.set_page_config(
    page_title="🧬 Pharmacology Chat Assistant",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

class ProtectedChatApp:
    """Main application class with authentication integration"""
    
    def __init__(self):
        """Initialize the protected chat application"""
        self.initialize_managers()
        self.initialize_ui_components()
    
    def initialize_managers(self):
        """Initialize all manager instances"""
        try:
            # Initialize authentication manager
            self.auth_manager = AuthenticationManager()
            
            # Initialize session manager
            self.session_manager = SessionManager(self.auth_manager)
            
            # Initialize theme manager
            self.theme_manager = ThemeManager()
            
            # Initialize Supabase client for chat functionality
            self.supabase_client = get_supabase_client()
            
            # Initialize chat manager (only if authenticated)
            self.chat_manager = None
            if self.session_manager.is_authenticated():
                self.chat_manager = ChatManager(self.supabase_client, self.session_manager)
            
            # Initialize model manager
            self.model_manager = ModelManager()
            
            # Initialize RAG orchestrator (only if authenticated)
            self.rag_orchestrator = None
            if self.session_manager.is_authenticated():
                self.rag_orchestrator = RAGOrchestrator(
                    supabase_client=self.supabase_client,
                    model_manager=self.model_manager
                )
            
            # Initialize document manager (only if authenticated)
            self.document_manager = None
            if self.session_manager.is_authenticated():
                self.document_manager = DocumentManager(self.supabase_client)
            
        except Exception as e:
            st.error(f"Failed to initialize application: {e}")
            st.stop()
    
    def initialize_ui_components(self):
        """Initialize UI component instances"""
        self.auth_interface = AuthInterface(self.auth_manager, self.session_manager)
        self.chat_interface = ChatInterface(self.theme_manager)
        
        # Initialize document interface (only if authenticated)
        self.document_interface = None
        if self.session_manager.is_authenticated() and self.document_manager:
            self.document_interface = DocumentInterface(self.document_manager)
    
    def run(self):
        """Main application entry point"""
        # Apply current theme
        self.theme_manager.apply_theme()
        
        # Check authentication status
        if not self.session_manager.is_authenticated():
            self.render_authentication_page()
        else:
            self.render_protected_chat_interface()
    
    def render_authentication_page(self):
        """Render authentication page for unauthenticated users"""
        # Clear any existing chat data from session
        self._clear_chat_session_data()
        
        # Render authentication interface
        self.auth_interface.render_auth_page()
    
    def render_protected_chat_interface(self):
        """Render the main chat interface for authenticated users"""
        # Validate session
        if not self.session_manager.validate_session():
            st.error("Your session has expired. Please sign in again.")
            self.session_manager.clear_session()
            st.rerun()
            return
        
        # Initialize chat components if not already done
        if self.chat_manager is None:
            self.chat_manager = ChatManager(self.supabase_client, self.session_manager)
        
        if self.rag_orchestrator is None:
            self.rag_orchestrator = RAGOrchestrator(
                supabase_client=self.supabase_client,
                model_manager=self.model_manager
            )
        
        if self.document_manager is None:
            self.document_manager = DocumentManager(self.supabase_client)
            
        if self.document_interface is None:
            self.document_interface = DocumentInterface(self.document_manager)
        
        # Check if user wants to view document management page
        if st.session_state.get('show_document_page', False):
            self._render_document_management_page()
        else:
            # Render main chat interface
            self._render_chat_header()
            self._render_sidebar()
            self._render_chat_area()
    
    def _render_chat_header(self):
        """Render the chat interface header"""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("🧬 Pharmacology Chat Assistant")
        
        with col2:
            # Model indicator
            model_pref = self.session_manager.get_model_preference()
            model_display = "🚀 Fast Mode" if model_pref == "fast" else "⭐ Premium Mode"
            st.markdown(f"**{model_display}**")
        
        with col3:
            # Connection status
            if self.supabase_client:
                st.markdown("🟢 **Connected**")
            else:
                st.markdown("🔴 **Disconnected**")
    
    def _render_sidebar(self):
        """Render the sidebar with user profile and settings"""
        with st.sidebar:
            # User profile section
            self.auth_interface.render_user_profile()
            
            # Chat controls
            st.markdown("---")
            st.subheader("💬 Chat Controls")
            
            user_id = self.session_manager.get_user_id()
            if user_id:
                # Get message stats
                stats = self.chat_manager.get_user_message_stats(user_id)
                st.write(f"**Total messages:** {stats.get('total_messages', 0)}")
                st.write(f"**Recent messages:** {stats.get('recent_messages', 0)}")
                
                # Clear conversation button
                if st.button("🗑️ Clear Conversation", use_container_width=True):
                    if self.chat_manager.clear_conversation(user_id):
                        st.success("Conversation cleared!")
                        # Clear session conversation history
                        st.session_state.conversation_history = []
                        st.rerun()
                    else:
                        st.error("Failed to clear conversation")
            
            # Document management section
            st.markdown("---")
            if self.document_interface:
                self.document_interface.render_sidebar_summary(user_id)
            
            # Theme toggle removed - permanent dark theme
            st.markdown("---")
            st.markdown("🌙 **Dark Mode** (Permanent)")
    
    def _render_chat_area(self):
        """Render the main chat area"""
        user_id = self.session_manager.get_user_id()
        if not user_id:
            st.error("User session invalid")
            return
        
        # Initialize conversation history in session state if not present
        if 'conversation_history' not in st.session_state:
            # Load conversation history from database
            messages = self.chat_manager.get_conversation_history(user_id, limit=50)
            st.session_state.conversation_history = messages
        
        # Display conversation history
        conversation_container = st.container()
        with conversation_container:
            self.chat_interface.render_chat_history(
                st.session_state.get('conversation_history', [])
            )
        
        # Chat input area
        st.markdown("---")
        user_input = self.chat_interface.render_message_input(
            placeholder="Ask about pharmacology topics..."
        )
        
        # Process user input
        if user_input:
            self._process_user_message(user_id, user_input)
    
    def _process_user_message(self, user_id: str, message_content: str):
        """Process a user message and generate AI response"""
        try:
            # Get model preference
            model_preference = self.session_manager.get_model_preference()
            
            # Save user message
            user_response = self.chat_manager.send_message(
                user_id=user_id,
                message_content=message_content,
                model_type=model_preference
            )
            
            if not user_response.success:
                st.error(f"Failed to save message: {user_response.error_message}")
                return
            
            # Add user message to session history
            if 'conversation_history' not in st.session_state:
                st.session_state.conversation_history = []
            
            st.session_state.conversation_history.append(user_response.message)
            
            # Generate AI response
            with st.spinner("Generating response..."):
                try:
                    # Get conversation context
                    context = self.chat_manager.get_conversation_context(user_id, limit=10)
                    
                    # Generate response using RAG
                    rag_response = self.rag_orchestrator.process_query(
                        user_id=user_id,
                        query=message_content,
                        model_type=model_preference,
                        conversation_history=context.messages
                    )
                    
                    if rag_response.success:
                        # Save assistant response
                        assistant_response = self.chat_manager.save_assistant_response(
                            user_id=user_id,
                            response_content=rag_response.response,
                            model_used=rag_response.model_used,
                            metadata={
                                "sources_used": len(rag_response.sources),
                                "processing_time": rag_response.processing_time
                            }
                        )
                        
                        if assistant_response.success:
                            # Add assistant message to session history
                            st.session_state.conversation_history.append(assistant_response.message)
                        else:
                            st.error(f"Failed to save AI response: {assistant_response.error_message}")
                    else:
                        st.error(f"Failed to generate response: {rag_response.error_message}")
                
                except Exception as e:
                    st.error(f"Error generating response: {e}")
            
            # Rerun to update the chat display
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing message: {e}")
    
    def _clear_chat_session_data(self):
        """Clear chat-related session data"""
        keys_to_clear = [
            'conversation_history',
            'last_message_id',
            'chat_context'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def require_authentication(self) -> bool:
        """
        Check if user is authenticated and redirect if not
        
        Returns:
            True if authenticated, False otherwise
        """
        if not self.session_manager.is_authenticated():
            st.warning("🔒 Please sign in to access the chat interface.")
            st.info("You'll be redirected to the login page.")
            return False
        
        # Validate session
        if not self.session_manager.validate_session():
            st.error("Your session has expired. Please sign in again.")
            self.session_manager.clear_session()
            return False
        
        return True
    
    def _render_document_management_page(self):
        """Render the document management page"""
        user_id = self.session_manager.get_user_id()
        if not user_id:
            st.error("User session invalid")
            return
        
        # Header with back button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back to Chat"):
                st.session_state.show_document_page = False
                st.rerun()
        
        # Render document management interface
        if self.document_interface:
            self.document_interface.render_document_page(user_id)


def main():
    """Main application entry point"""
    app = ProtectedChatApp()
    app.run()


if __name__ == "__main__":
    main()