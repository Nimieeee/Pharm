"""
ConversationUI component for managing conversation tabs and navigation.
Provides tab-based interface for creating and switching between conversations.
Enhanced with comprehensive error handling and user feedback.
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import uuid
import logging

from conversation_manager import ConversationManager, Conversation
from theme_manager import ThemeManager
from ui_error_handler import UIErrorHandler, UIErrorType, UIErrorContext, with_ui_error_handling

logger = logging.getLogger(__name__)


class ConversationUI:
    """UI component for conversation management with tab navigation"""
    
    def __init__(self, conversation_manager: ConversationManager, theme_manager: ThemeManager, session_manager=None):
        """
        Initialize ConversationUI
        
        Args:
            conversation_manager: ConversationManager instance
            theme_manager: ThemeManager instance
            session_manager: SessionManager instance for conversation isolation
        """
        self.conversation_manager = conversation_manager
        self.theme_manager = theme_manager
        self.session_manager = session_manager or st.session_state.get('session_manager')
        self.ui_error_handler = UIErrorHandler()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for conversation UI"""
        if 'current_conversation_id' not in st.session_state:
            st.session_state.current_conversation_id = None
        if 'conversations_loaded' not in st.session_state:
            st.session_state.conversations_loaded = False
        if 'show_new_conversation_dialog' not in st.session_state:
            st.session_state.show_new_conversation_dialog = False
        if 'conversation_title_input' not in st.session_state:
            st.session_state.conversation_title_input = ""
    
    def render_conversation_tabs(self, user_id: str) -> Dict[str, Any]:
        """
        Render conversation tabs interface with comprehensive error handling
        
        Args:
            user_id: Current user ID
            
        Returns:
            Dictionary with conversation management actions and current conversation
        """
        result = {
            'current_conversation_id': None,
            'conversation_changed': False,
            'new_conversation_created': False,
            'conversation_deleted': False,
            'error_occurred': False
        }
        
        try:
            # Load conversations with error handling
            conversations = self._load_conversations_with_error_handling(user_id)
            
            # Ensure user has at least one conversation
            if not conversations:
                default_conv = self._create_default_conversation_with_error_handling(user_id)
                if default_conv:
                    conversations = [default_conv]
                    st.session_state.current_conversation_id = default_conv.id
                else:
                    # Failed to create default conversation
                    result['error_occurred'] = True
                    return result
            
            # Set current conversation if not set, using session manager for proper isolation
            current_conv_id = self._get_current_conversation_id_safely()
            if not current_conv_id and conversations:
                self._set_current_conversation_id_safely(conversations[0].id)
            
            # Render the tabs interface
            if conversations:
                result.update(self._render_tabs_interface_with_error_handling(user_id, conversations))
            
        except Exception as e:
            logger.error(f"Error rendering conversation tabs for user {user_id}: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="render_conversation_tabs",
                component="ConversationUI"
            )
            error_result = self.ui_error_handler.handle_conversation_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            result['error_occurred'] = True
        
        return result
    
    def _render_tabs_interface(self, user_id: str, conversations: List[Conversation]) -> Dict[str, Any]:
        """Render the actual tabs interface"""
        current_conv_id = self.session_manager.get_current_conversation_id() if self.session_manager else st.session_state.current_conversation_id
        result = {
            'current_conversation_id': current_conv_id,
            'conversation_changed': False,
            'new_conversation_created': False,
            'conversation_deleted': False
        }
        
        # Create tabs
        tab_labels = []
        for conv in conversations:
            # Truncate long titles for tabs
            title = conv.title if len(conv.title) <= 20 else conv.title[:17] + "..."
            tab_labels.append(f"💬 {title}")
        
        # Add "+" tab for new conversation
        tab_labels.append("➕ New")
        
        # Render tabs
        tabs = st.tabs(tab_labels)
        
        # Handle conversation tabs
        for i, conv in enumerate(conversations):
            with tabs[i]:
                # Check if this tab is selected (active)
                current_conv_id = self.session_manager.get_current_conversation_id() if self.session_manager else st.session_state.current_conversation_id
                if current_conv_id != conv.id:
                    # Tab was clicked, switch conversation with proper isolation
                    if self.session_manager:
                        success = self.session_manager.switch_conversation(conv.id)
                        if success:
                            result['conversation_changed'] = True
                            result['current_conversation_id'] = conv.id
                    else:
                        # Fallback to direct session state update
                        st.session_state.current_conversation_id = conv.id
                        result['conversation_changed'] = True
                        result['current_conversation_id'] = conv.id
                
                # Render conversation info and controls
                self._render_conversation_info(user_id, conv)
        
        # Handle "New" tab
        with tabs[-1]:
            new_conv_result = self._render_new_conversation_interface(user_id)
            if new_conv_result['created']:
                result['new_conversation_created'] = True
                result['current_conversation_id'] = new_conv_result['conversation_id']
                
                # Use session manager for proper conversation isolation
                if self.session_manager:
                    self.session_manager.set_current_conversation_id(new_conv_result['conversation_id'])
                else:
                    # Fallback to direct session state update
                    st.session_state.current_conversation_id = new_conv_result['conversation_id']
        
        return result
    
    def _render_conversation_info(self, user_id: str, conversation: Conversation) -> None:
        """Render conversation information and controls"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{conversation.title}**")
            st.caption(f"📅 Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")
            st.caption(f"💬 Messages: {conversation.message_count}")
            
            if conversation.last_message_preview:
                preview = conversation.last_message_preview
                if len(preview) > 100:
                    preview = preview[:97] + "..."
                st.caption(f"💭 Last: {preview}")
        
        with col2:
            # Edit title button
            if st.button("✏️", key=f"edit_{conversation.id}", help="Edit title"):
                self._show_edit_title_dialog(user_id, conversation)
        
        with col3:
            # Delete conversation button (only if not the last conversation)
            conversations = self.conversation_manager.get_user_conversations(user_id)
            if len(conversations) > 1:
                if st.button("🗑️", key=f"delete_{conversation.id}", help="Delete conversation"):
                    self._show_delete_confirmation_dialog(user_id, conversation)
    
    def _render_new_conversation_interface(self, user_id: str) -> Dict[str, Any]:
        """Render interface for creating new conversations"""
        result = {'created': False, 'conversation_id': None}
        
        st.markdown("### ➕ Create New Conversation")
        st.markdown("Start a fresh conversation thread")
        
        # Title input
        title = st.text_input(
            "Conversation Title (optional)",
            placeholder="Enter a title or leave blank for auto-generation",
            key="new_conversation_title"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Conversation", key="create_new_conv", type="primary"):
                # Create new conversation
                conv_title = title.strip() if title.strip() else "New Conversation"
                new_conversation = self.conversation_manager.create_conversation(user_id, conv_title)
                
                if new_conversation:
                    result['created'] = True
                    result['conversation_id'] = new_conversation.id
                    st.success(f"✅ Created conversation: {new_conversation.title}")
                    st.rerun()
                else:
                    st.error("❌ Failed to create conversation")
        
        with col2:
            st.caption("💡 Tip: You can rename conversations later")
        
        return result
    
    def _show_edit_title_dialog(self, user_id: str, conversation: Conversation) -> None:
        """Show dialog for editing conversation title"""
        with st.expander("✏️ Edit Conversation Title", expanded=True):
            new_title = st.text_input(
                "New Title",
                value=conversation.title,
                key=f"edit_title_{conversation.id}"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save", key=f"save_title_{conversation.id}", type="primary"):
                    if new_title.strip() and new_title.strip() != conversation.title:
                        success = self.conversation_manager.update_conversation_title(
                            user_id, conversation.id, new_title.strip()
                        )
                        if success:
                            st.success("✅ Title updated!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to update title")
            
            with col2:
                if st.button("Cancel", key=f"cancel_edit_{conversation.id}"):
                    st.rerun()
    
    def _show_delete_confirmation_dialog(self, user_id: str, conversation: Conversation) -> None:
        """Show confirmation dialog for deleting conversation"""
        with st.expander("🗑️ Delete Conversation", expanded=True):
            st.warning(f"⚠️ Are you sure you want to delete '{conversation.title}'?")
            st.caption("This will permanently delete all messages in this conversation.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Yes, Delete", key=f"confirm_delete_{conversation.id}", type="primary"):
                    success = self.conversation_manager.delete_conversation(user_id, conversation.id)
                    if success:
                        # Switch to another conversation
                        conversations = self.conversation_manager.get_user_conversations(user_id)
                        if conversations:
                            st.session_state.current_conversation_id = conversations[0].id
                        else:
                            # Create a new default conversation
                            default_conv = self.conversation_manager.create_conversation(user_id, "Default Conversation")
                            if default_conv:
                                st.session_state.current_conversation_id = default_conv.id
                        
                        st.success("✅ Conversation deleted!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete conversation")
            
            with col2:
                if st.button("Cancel", key=f"cancel_delete_{conversation.id}"):
                    st.rerun()
    
    def render_conversation_selector_sidebar(self, user_id: str) -> Optional[str]:
        """
        Render a compact conversation selector in the sidebar
        
        Args:
            user_id: Current user ID
            
        Returns:
            Selected conversation ID or None
        """
        st.sidebar.markdown("### 💬 Conversations")
        
        conversations = self.conversation_manager.get_user_conversations(user_id)
        
        if not conversations:
            st.sidebar.info("No conversations yet")
            return None
        
        # Create options for selectbox
        options = {}
        for conv in conversations:
            title = conv.title if len(conv.title) <= 30 else conv.title[:27] + "..."
            label = f"{title} ({conv.message_count} msgs)"
            options[label] = conv.id
        
        # Current selection
        current_label = None
        if st.session_state.current_conversation_id:
            for label, conv_id in options.items():
                if conv_id == st.session_state.current_conversation_id:
                    current_label = label
                    break
        
        # Render selectbox
        selected_label = st.sidebar.selectbox(
            "Select Conversation",
            options=list(options.keys()),
            index=list(options.keys()).index(current_label) if current_label else 0,
            key="sidebar_conversation_selector"
        )
        
        selected_id = options[selected_label]
        
        # Update session state if changed
        if selected_id != st.session_state.current_conversation_id:
            st.session_state.current_conversation_id = selected_id
        
        # New conversation button
        if st.sidebar.button("➕ New Conversation", key="sidebar_new_conv"):
            new_conv = self.conversation_manager.create_conversation(user_id, "New Conversation")
            if new_conv:
                st.session_state.current_conversation_id = new_conv.id
                st.rerun()
        
        return selected_id
    
    def get_current_conversation(self, user_id: str) -> Optional[Conversation]:
        """
        Get the currently selected conversation
        
        Args:
            user_id: Current user ID
            
        Returns:
            Current Conversation object or None
        """
        if not st.session_state.current_conversation_id:
            return None
        
        return self.conversation_manager.get_conversation(
            user_id, st.session_state.current_conversation_id
        )
    
    def auto_generate_title_from_message(self, user_id: str, conversation_id: str, 
                                       first_message: str) -> bool:
        """
        Auto-generate conversation title from first message if title is generic
        
        Args:
            user_id: User ID
            conversation_id: Conversation ID
            first_message: First user message
            
        Returns:
            True if title was updated, False otherwise
        """
        try:
            conversation = self.conversation_manager.get_conversation(user_id, conversation_id)
            if not conversation:
                return False
            
            # Only auto-generate if current title is generic
            generic_titles = ["New Conversation", "Default Conversation"]
            if conversation.title not in generic_titles:
                return False
            
            # Generate new title
            new_title = self.conversation_manager.generate_conversation_title(first_message)
            
            # Update title
            return self.conversation_manager.update_conversation_title(
                user_id, conversation_id, new_title
            )
            
        except Exception as e:
            logger.error(f"Error auto-generating title for conversation {conversation_id}: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="auto_generate_title",
                component="ConversationUI",
                additional_data={'conversation_id': conversation_id, 'message': first_message[:100]}
            )
            error_result = self.ui_error_handler.handle_conversation_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            return False
    
    # Error handling helper methods
    def _load_conversations_with_error_handling(self, user_id: str) -> List[Conversation]:
        """Load conversations with error handling and retry logic"""
        try:
            return self.conversation_manager.get_user_conversations(user_id)
        except Exception as e:
            logger.error(f"Error loading conversations for user {user_id}: {e}")
            
            # Check if this is a retry attempt
            if st.session_state.get('retry_load_conversations', False):
                st.session_state.retry_load_conversations = False
                # Try one more time
                try:
                    return self.conversation_manager.get_user_conversations(user_id)
                except Exception as retry_error:
                    logger.error(f"Retry failed for loading conversations: {retry_error}")
                    st.error("❌ Unable to load conversations. Please refresh the page.")
                    return []
            else:
                # Offer retry option
                if st.button("🔄 Retry Loading Conversations"):
                    st.session_state.retry_load_conversations = True
                    st.rerun()
                return []
    
    def _create_default_conversation_with_error_handling(self, user_id: str) -> Optional[Conversation]:
        """Create default conversation with error handling"""
        try:
            return self.conversation_manager.get_or_create_default_conversation(user_id)
        except Exception as e:
            logger.error(f"Error creating default conversation for user {user_id}: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="create_default_conversation",
                component="ConversationUI"
            )
            error_result = self.ui_error_handler.handle_conversation_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            return None
    
    def _get_current_conversation_id_safely(self) -> Optional[str]:
        """Get current conversation ID with error handling"""
        try:
            if self.session_manager:
                return self.session_manager.get_current_conversation_id()
            else:
                return st.session_state.get('current_conversation_id')
        except Exception as e:
            logger.error(f"Error getting current conversation ID: {e}")
            return None
    
    def _set_current_conversation_id_safely(self, conversation_id: str) -> bool:
        """Set current conversation ID with error handling"""
        try:
            if self.session_manager:
                return self.session_manager.set_current_conversation_id(conversation_id)
            else:
                st.session_state.current_conversation_id = conversation_id
                return True
        except Exception as e:
            logger.error(f"Error setting current conversation ID: {e}")
            return False
    
    def _render_tabs_interface_with_error_handling(self, user_id: str, conversations: List[Conversation]) -> Dict[str, Any]:
        """Render tabs interface with comprehensive error handling"""
        try:
            return self._render_tabs_interface(user_id, conversations)
        except Exception as e:
            logger.error(f"Error rendering tabs interface: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="render_tabs_interface",
                component="ConversationUI"
            )
            error_result = self.ui_error_handler.handle_conversation_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            
            # Return safe fallback result
            return {
                'current_conversation_id': conversations[0].id if conversations else None,
                'conversation_changed': False,
                'new_conversation_created': False,
                'conversation_deleted': False,
                'error_occurred': True
            }


def inject_conversation_css() -> None:
    """Inject CSS for conversation tabs styling"""
    css = """
    <style>
    /* Conversation tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--background-secondary, #f8f9fa);
        padding: 8px;
        border-radius: 8px;
        margin-bottom: 16px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 8px 16px;
        background-color: var(--background-color, #ffffff);
        border: 1px solid var(--border-color, #e0e0e0);
        border-radius: 6px;
        color: var(--text-color, #333333);
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--hover-color, #f0f0f0);
        border-color: var(--primary-color, #1f77b4);
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color, #1f77b4) !important;
        color: white !important;
        border-color: var(--primary-color, #1f77b4) !important;
    }
    
    /* Conversation info styling */
    .conversation-info {
        padding: 16px;
        background-color: var(--background-secondary, #f8f9fa);
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid var(--border-color, #e0e0e0);
    }
    
    .conversation-stats {
        display: flex;
        gap: 16px;
        margin-top: 8px;
    }
    
    .conversation-stat {
        padding: 4px 8px;
        background-color: var(--background-color, #ffffff);
        border-radius: 4px;
        font-size: 0.85em;
        color: var(--text-secondary, #666666);
    }
    
    /* New conversation interface */
    .new-conversation-card {
        padding: 24px;
        background: linear-gradient(135deg, var(--primary-color, #1f77b4) 0%, var(--secondary-color, #17a2b8) 100%);
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 16px;
    }
    
    .new-conversation-card h3 {
        margin-bottom: 8px;
        color: white;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .stTabs [data-baseweb="tab-list"] {
            flex-wrap: wrap;
        }
        
        .stTabs [data-baseweb="tab"] {
            min-width: 120px;
            font-size: 0.9em;
        }
        
        .conversation-stats {
            flex-direction: column;
            gap: 8px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)