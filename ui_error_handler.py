"""
UI Error Handler for Enhanced User Experience
Provides comprehensive error handling for conversation management, document processing, and RAG pipeline failures.
"""

import streamlit as st
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import time
import traceback

from error_handler import ErrorHandler, ErrorType, ErrorSeverity, ErrorInfo

logger = logging.getLogger(__name__)

class UIErrorType(Enum):
    """UI-specific error types"""
    CONVERSATION_CREATION = "conversation_creation"
    CONVERSATION_SWITCHING = "conversation_switching"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_PROCESSING = "document_processing"
    RAG_RETRIEVAL = "rag_retrieval"
    MODEL_SWITCHING = "model_switching"
    THEME_APPLICATION = "theme_application"
    SESSION_MANAGEMENT = "session_management"

@dataclass
class UIErrorContext:
    """Context information for UI errors"""
    user_id: str
    action: str
    component: str
    additional_data: Optional[Dict[str, Any]] = None

class UIErrorHandler:
    """Enhanced error handler for UI components with user-friendly feedback"""
    
    def __init__(self):
        self.base_error_handler = ErrorHandler()
        self.error_history = []
        self.fallback_strategies = {}
        self._setup_fallback_strategies()
    
    def _setup_fallback_strategies(self):
        """Setup fallback strategies for different error types"""
        self.fallback_strategies = {
            UIErrorType.CONVERSATION_CREATION: self._fallback_conversation_creation,
            UIErrorType.CONVERSATION_SWITCHING: self._fallback_conversation_switching,
            UIErrorType.DOCUMENT_PROCESSING: self._fallback_document_processing,
            UIErrorType.RAG_RETRIEVAL: self._fallback_rag_retrieval,
            UIErrorType.MODEL_SWITCHING: self._fallback_model_switching,
        }
    
    def handle_conversation_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """
        Handle conversation-related errors with specific feedback and fallbacks
        
        Args:
            error: The exception that occurred
            context: UI error context
            
        Returns:
            Dictionary with error handling results and fallback actions
        """
        error_type = UIErrorType.CONVERSATION_CREATION if "create" in context.action.lower() else UIErrorType.CONVERSATION_SWITCHING
        
        # Log the error with context
        logger.error(f"Conversation error in {context.component}: {context.action} - {str(error)}")
        
        # Generate user-friendly error message
        if error_type == UIErrorType.CONVERSATION_CREATION:
            return self._handle_conversation_creation_error(error, context)
        else:
            return self._handle_conversation_switching_error(error, context)
    
    def handle_document_processing_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """
        Handle document processing errors with detailed feedback
        
        Args:
            error: The exception that occurred
            context: UI error context
            
        Returns:
            Dictionary with error handling results and user feedback
        """
        logger.error(f"Document processing error: {context.action} - {str(error)}")
        
        error_str = str(error).lower()
        
        # Determine specific error type and provide targeted feedback
        if "upload" in error_str or "file" in error_str:
            return self._handle_document_upload_error(error, context)
        elif "processing" in error_str or "extraction" in error_str:
            return self._handle_document_processing_error_specific(error, context)
        elif "embedding" in error_str or "vector" in error_str:
            return self._handle_embedding_error(error, context)
        else:
            return self._handle_generic_document_error(error, context)
    
    def handle_rag_pipeline_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """
        Handle RAG pipeline errors with fallback mechanisms
        
        Args:
            error: The exception that occurred
            context: UI error context
            
        Returns:
            Dictionary with error handling results and fallback strategy
        """
        logger.error(f"RAG pipeline error: {context.action} - {str(error)}")
        
        error_str = str(error).lower()
        
        # Provide specific handling based on RAG component failure
        if "retrieval" in error_str or "search" in error_str:
            return self._handle_rag_retrieval_error(error, context)
        elif "context" in error_str or "building" in error_str:
            return self._handle_rag_context_error(error, context)
        elif "embedding" in error_str:
            return self._handle_rag_embedding_error(error, context)
        else:
            return self._handle_generic_rag_error(error, context)
    
    def display_error_with_actions(self, error_result: Dict[str, Any]) -> None:
        """
        Display error message with actionable buttons and recovery options
        
        Args:
            error_result: Result from error handling containing message and actions
        """
        severity = error_result.get('severity', 'error')
        message = error_result.get('user_message', 'An unexpected error occurred')
        actions = error_result.get('actions', [])
        fallback_available = error_result.get('fallback_available', False)
        
        # Display error message with appropriate severity
        if severity == 'critical':
            st.error(f"🚨 **Critical Error:** {message}")
        elif severity == 'high':
            st.error(f"❌ **Error:** {message}")
        elif severity == 'medium':
            st.warning(f"⚠️ **Warning:** {message}")
        else:
            st.info(f"ℹ️ **Notice:** {message}")
        
        # Display recovery actions if available
        if actions:
            st.markdown("**Available Actions:**")
            cols = st.columns(len(actions))
            
            for i, action in enumerate(actions):
                with cols[i]:
                    if st.button(action['label'], key=f"error_action_{i}_{time.time()}"):
                        if action.get('callback'):
                            action['callback']()
                        if action.get('rerun', True):
                            st.rerun()
        
        # Display fallback information
        if fallback_available:
            with st.expander("🔄 Alternative Options"):
                fallback_message = error_result.get('fallback_message', 'Alternative methods are available.')
                st.info(fallback_message)
                
                if error_result.get('fallback_action'):
                    if st.button("Try Alternative Method", key=f"fallback_{time.time()}"):
                        error_result['fallback_action']()
                        st.rerun()
    
    def _handle_conversation_creation_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle conversation creation errors"""
        error_str = str(error).lower()
        
        if "database" in error_str or "connection" in error_str:
            return {
                'severity': 'high',
                'user_message': 'Unable to create new conversation due to database connectivity issues. Your existing conversations are safe.',
                'actions': [
                    {
                        'label': '🔄 Retry',
                        'callback': lambda: self._retry_conversation_creation(context),
                        'rerun': True
                    },
                    {
                        'label': '📋 Use Current Conversation',
                        'callback': lambda: self._use_current_conversation(context),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'You can continue using your current conversation or try creating a new one later.',
                'fallback_action': lambda: self._fallback_conversation_creation(context)
            }
        elif "permission" in error_str or "unauthorized" in error_str:
            return {
                'severity': 'critical',
                'user_message': 'You do not have permission to create new conversations. Please contact support.',
                'actions': [
                    {
                        'label': '🔄 Refresh Session',
                        'callback': lambda: st.rerun(),
                        'rerun': True
                    }
                ],
                'fallback_available': False
            }
        else:
            return {
                'severity': 'medium',
                'user_message': 'Failed to create new conversation. You can continue with your current conversation.',
                'actions': [
                    {
                        'label': '🔄 Try Again',
                        'callback': lambda: self._retry_conversation_creation(context),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'Continue using your current conversation while we resolve this issue.',
                'fallback_action': lambda: self._fallback_conversation_creation(context)
            }
    
    def _handle_conversation_switching_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle conversation switching errors"""
        error_str = str(error).lower()
        
        if "not found" in error_str or "invalid" in error_str:
            return {
                'severity': 'medium',
                'user_message': 'The selected conversation could not be found. It may have been deleted.',
                'actions': [
                    {
                        'label': '🏠 Go to Default Conversation',
                        'callback': lambda: self._switch_to_default_conversation(context),
                        'rerun': True
                    },
                    {
                        'label': '🔄 Refresh Conversations',
                        'callback': lambda: self._refresh_conversations(context),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'We\'ll switch you to your default conversation.',
                'fallback_action': lambda: self._fallback_conversation_switching(context)
            }
        else:
            return {
                'severity': 'medium',
                'user_message': 'Unable to switch conversations. Staying in current conversation.',
                'actions': [
                    {
                        'label': '🔄 Try Again',
                        'callback': lambda: self._retry_conversation_switching(context),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'Continue with your current conversation.',
                'fallback_action': lambda: self._fallback_conversation_switching(context)
            }
    
    def _handle_document_upload_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle document upload errors"""
        error_str = str(error).lower()
        
        if "size" in error_str or "large" in error_str:
            return {
                'severity': 'medium',
                'user_message': 'File is too large to upload. Please try a smaller file or split large documents.',
                'actions': [
                    {
                        'label': '📄 Try Different File',
                        'callback': lambda: self._clear_file_uploader(),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'You can try uploading smaller files or use URL extraction for web content.',
                'fallback_action': lambda: self._suggest_alternative_upload_methods()
            }
        elif "format" in error_str or "type" in error_str:
            return {
                'severity': 'medium',
                'user_message': 'Unsupported file format. Please upload PDF, DOCX, TXT, or HTML files.',
                'actions': [
                    {
                        'label': '📄 Choose Different File',
                        'callback': lambda: self._clear_file_uploader(),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'Supported formats: PDF, DOCX, TXT, HTML. You can also try URL extraction.',
                'fallback_action': lambda: self._show_supported_formats()
            }
        else:
            return {
                'severity': 'high',
                'user_message': 'Failed to upload document. Please check your internet connection and try again.',
                'actions': [
                    {
                        'label': '🔄 Retry Upload',
                        'callback': lambda: self._retry_document_upload(context),
                        'rerun': True
                    }
                ],
                'fallback_available': True,
                'fallback_message': 'You can continue chatting without documents or try uploading later.',
                'fallback_action': lambda: self._fallback_document_processing(context)
            }
    
    def _handle_document_processing_error_specific(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle specific document processing errors"""
        return {
            'severity': 'medium',
            'user_message': 'Document uploaded but processing failed. The file may be corrupted or in an unsupported format.',
            'actions': [
                {
                    'label': '🔄 Retry Processing',
                    'callback': lambda: self._retry_document_processing(context),
                    'rerun': True
                },
                {
                    'label': '📄 Try Different File',
                    'callback': lambda: self._clear_file_uploader(),
                    'rerun': True
                }
            ],
            'fallback_available': True,
            'fallback_message': 'You can continue chatting with general knowledge while we resolve this.',
            'fallback_action': lambda: self._fallback_document_processing(context)
        }
    
    def _handle_embedding_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle embedding generation errors"""
        return {
            'severity': 'medium',
            'user_message': 'Document uploaded but failed to generate embeddings for search. You can still chat without document context.',
            'actions': [
                {
                    'label': '🔄 Retry Processing',
                    'callback': lambda: self._retry_embedding_generation(context),
                    'rerun': True
                }
            ],
            'fallback_available': True,
            'fallback_message': 'The AI will use general knowledge instead of your documents.',
            'fallback_action': lambda: self._enable_general_mode(context)
        }
    
    def _handle_rag_retrieval_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle RAG retrieval errors"""
        return {
            'severity': 'low',
            'user_message': 'Unable to search your documents for relevant information. Using general knowledge instead.',
            'actions': [
                {
                    'label': '🔄 Retry Search',
                    'callback': lambda: self._retry_rag_retrieval(context),
                    'rerun': False
                }
            ],
            'fallback_available': True,
            'fallback_message': 'The AI will provide answers using its general knowledge base.',
            'fallback_action': lambda: self._fallback_rag_retrieval(context)
        }
    
    def _handle_rag_context_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle RAG context building errors"""
        return {
            'severity': 'low',
            'user_message': 'Found relevant documents but failed to build context. Switching to general knowledge mode.',
            'actions': [],
            'fallback_available': True,
            'fallback_message': 'The AI will answer using general pharmacology knowledge.',
            'fallback_action': lambda: self._fallback_rag_retrieval(context)
        }
    
    def _handle_generic_document_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle generic document errors"""
        return {
            'severity': 'medium',
            'user_message': 'Document operation failed. You can continue chatting without document assistance.',
            'actions': [
                {
                    'label': '🔄 Try Again',
                    'callback': lambda: self._retry_document_operation(context),
                    'rerun': True
                }
            ],
            'fallback_available': True,
            'fallback_message': 'Continue with general AI assistance.',
            'fallback_action': lambda: self._fallback_document_processing(context)
        }
    
    def _handle_generic_rag_error(self, error: Exception, context: UIErrorContext) -> Dict[str, Any]:
        """Handle generic RAG pipeline errors"""
        return {
            'severity': 'low',
            'user_message': 'Document search temporarily unavailable. Using general knowledge for your question.',
            'actions': [],
            'fallback_available': True,
            'fallback_message': 'The AI will provide general pharmacology assistance.',
            'fallback_action': lambda: self._fallback_rag_retrieval(context)
        }
    
    # Fallback strategy implementations
    def _fallback_conversation_creation(self, context: UIErrorContext) -> None:
        """Fallback for conversation creation failure"""
        if 'current_conversation_id' not in st.session_state:
            # Create a temporary conversation ID for session continuity
            st.session_state.current_conversation_id = f"temp_{int(time.time())}"
        st.info("💬 Continuing with current conversation. You can try creating a new conversation later.")
    
    def _fallback_conversation_switching(self, context: UIErrorContext) -> None:
        """Fallback for conversation switching failure"""
        # Stay in current conversation
        st.info("💬 Staying in current conversation. Your messages are safe.")
    
    def _fallback_document_processing(self, context: UIErrorContext) -> None:
        """Fallback for document processing failure"""
        st.info("🤖 Switching to general knowledge mode. You can still ask pharmacology questions!")
        if 'rag_mode_disabled' not in st.session_state:
            st.session_state.rag_mode_disabled = True
    
    def _fallback_rag_retrieval(self, context: UIErrorContext) -> None:
        """Fallback for RAG retrieval failure"""
        st.info("🧠 Using general pharmacology knowledge for your question.")
        if 'use_general_knowledge' not in st.session_state:
            st.session_state.use_general_knowledge = True
    
    def _fallback_model_switching(self, context: UIErrorContext) -> None:
        """Fallback for model switching failure"""
        st.info("🤖 Continuing with current model. You can try switching later.")
    
    # Helper methods for error recovery actions
    def _retry_conversation_creation(self, context: UIErrorContext) -> None:
        """Retry conversation creation"""
        if 'retry_conversation_creation' not in st.session_state:
            st.session_state.retry_conversation_creation = True
    
    def _retry_conversation_switching(self, context: UIErrorContext) -> None:
        """Retry conversation switching"""
        if 'retry_conversation_switching' not in st.session_state:
            st.session_state.retry_conversation_switching = True
    
    def _use_current_conversation(self, context: UIErrorContext) -> None:
        """Use current conversation as fallback"""
        st.info("💬 Continuing with your current conversation.")
    
    def _switch_to_default_conversation(self, context: UIErrorContext) -> None:
        """Switch to default conversation"""
        st.session_state.switch_to_default = True
    
    def _refresh_conversations(self, context: UIErrorContext) -> None:
        """Refresh conversation list"""
        if 'refresh_conversations' not in st.session_state:
            st.session_state.refresh_conversations = True
    
    def _clear_file_uploader(self) -> None:
        """Clear file uploader state"""
        if 'file_uploader' in st.session_state:
            del st.session_state.file_uploader
    
    def _retry_document_upload(self, context: UIErrorContext) -> None:
        """Retry document upload"""
        self._clear_file_uploader()
        st.info("📄 Please select your files again to retry upload.")
    
    def _retry_document_processing(self, context: UIErrorContext) -> None:
        """Retry document processing"""
        if 'retry_document_processing' not in st.session_state:
            st.session_state.retry_document_processing = True
    
    def _retry_embedding_generation(self, context: UIErrorContext) -> None:
        """Retry embedding generation"""
        if 'retry_embedding_generation' not in st.session_state:
            st.session_state.retry_embedding_generation = True
    
    def _retry_rag_retrieval(self, context: UIErrorContext) -> None:
        """Retry RAG retrieval"""
        if 'retry_rag_retrieval' not in st.session_state:
            st.session_state.retry_rag_retrieval = True
    
    def _suggest_alternative_upload_methods(self) -> None:
        """Suggest alternative upload methods"""
        st.info("💡 **Alternative options:**\n- Try uploading smaller files\n- Use URL extraction for web content\n- Split large documents into smaller parts")
    
    def _show_supported_formats(self) -> None:
        """Show supported file formats"""
        st.info("📄 **Supported formats:**\n- PDF (.pdf)\n- Word Documents (.docx)\n- Text Files (.txt)\n- HTML Files (.html, .htm)")
    
    def _enable_general_mode(self, context: UIErrorContext) -> None:
        """Enable general knowledge mode"""
        st.session_state.general_mode_enabled = True
        st.info("🧠 General knowledge mode enabled. Ask any pharmacology question!")
    
    def _retry_document_operation(self, context: UIErrorContext) -> None:
        """Retry generic document operation"""
        if 'retry_document_operation' not in st.session_state:
            st.session_state.retry_document_operation = True

# Global UI error handler instance
_ui_error_handler = UIErrorHandler()

def get_ui_error_handler() -> UIErrorHandler:
    """Get the global UI error handler instance"""
    return _ui_error_handler

def with_ui_error_handling(error_type: UIErrorType, component: str, action: str):
    """
    Decorator for UI functions to add comprehensive error handling
    
    Args:
        error_type: Type of UI error expected
        component: UI component name
        action: Action being performed
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract user_id from args/kwargs if available
                user_id = kwargs.get('user_id') or (args[0] if args else 'unknown')
                
                context = UIErrorContext(
                    user_id=str(user_id),
                    action=action,
                    component=component,
                    additional_data={'args': str(args), 'kwargs': str(kwargs)}
                )
                
                ui_error_handler = get_ui_error_handler()
                
                if error_type in [UIErrorType.CONVERSATION_CREATION, UIErrorType.CONVERSATION_SWITCHING]:
                    error_result = ui_error_handler.handle_conversation_error(e, context)
                elif error_type in [UIErrorType.DOCUMENT_UPLOAD, UIErrorType.DOCUMENT_PROCESSING]:
                    error_result = ui_error_handler.handle_document_processing_error(e, context)
                elif error_type == UIErrorType.RAG_RETRIEVAL:
                    error_result = ui_error_handler.handle_rag_pipeline_error(e, context)
                else:
                    # Generic error handling
                    error_result = {
                        'severity': 'medium',
                        'user_message': f'An error occurred in {component}: {str(e)}',
                        'actions': [],
                        'fallback_available': False
                    }
                
                ui_error_handler.display_error_with_actions(error_result)
                
                # Return None or appropriate fallback value
                return None
        
        return wrapper
    return decorator