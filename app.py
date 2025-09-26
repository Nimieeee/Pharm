# app.py - Main Pharmacology Chat Application with Authentication
import os
import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import streamlit as st

# Authentication and session management
from auth_manager import AuthenticationManager
from session_manager import SessionManager
from auth_ui import AuthInterface
from auth_guard import AuthGuard, RouteProtection

# Chat functionality
from chat_manager import ChatManager
from message_store import Message
from message_store_optimized import OptimizedMessageStore

# UI components
from theme_manager import ThemeManager
from chat_interface import ChatInterface, inject_chat_css
from chat_interface_optimized import OptimizedChatInterface, inject_optimized_chat_css
from performance_optimizer import performance_optimizer, LoadingStateManager

# RAG and model components
try:
    from rag_orchestrator_optimized import RAGOrchestrator
except ImportError:
    try:
        from rag_orchestrator import RAGOrchestrator
    except ImportError:
        # Fallback if no RAG orchestrator is available
        class RAGOrchestrator:
            def __init__(self, *args, **kwargs):
                pass
            
            def stream_query(self, *args, **kwargs):
                yield "RAG system temporarily unavailable"
                return None

from model_manager import ModelManager
from database_init import check_and_initialize_database, render_database_setup_instructions

# Supabase client for main app (uses anon key)
def get_supabase_client():
    """Get Supabase client for main application using anon key"""
    from supabase import create_client
    from deployment_config import deployment_config
    
    db_config = deployment_config.get_database_config()
    return create_client(db_config["url"], db_config["anon_key"])

def get_authenticated_supabase_client(auth_manager):
    """Get Supabase client with authenticated user context"""
    try:
        # Use the auth manager's client directly since it has the authenticated session
        return auth_manager.supabase
    except Exception as e:
        print(f"Warning: Could not get authenticated client: {e}")
        # Fallback to anonymous client
        from supabase import create_client
        from deployment_config import deployment_config
        db_config = deployment_config.get_database_config()
        return create_client(db_config["url"], db_config["anon_key"])

# Legacy RAG components (fallback)
from langchain_supabase_utils import get_supabase_client as get_legacy_supabase_client, get_vectorstore, upsert_documents
from ingestion import create_documents_from_uploads, extract_text_from_url
from embeddings import get_embeddings
from groq_llm import generate_completion_stream, FAST_MODE, PREMIUM_MODE
from prompts import get_rag_enhanced_prompt, pharmacology_system_prompt

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(
    page_title="🧬 Pharmacology Chat Assistant", 
    page_icon="🧬",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ----------------------------
# Application Class
# ----------------------------
class PharmacologyChat:
    """Main application class with integrated authentication and chat"""
    
    def __init__(self):
        """Initialize the application"""
        self.initialize_managers()
        self.initialize_ui_components()
        self.initialize_legacy_components()
    
    def initialize_managers(self):
        """Initialize authentication and core managers"""
        try:
            # Authentication and session management
            self.auth_manager = AuthenticationManager()
            self.session_manager = SessionManager(self.auth_manager)
            self.auth_guard = AuthGuard(self.auth_manager, self.session_manager)
            
            # Store session manager in session state for access by other components
            st.session_state.session_manager = self.session_manager
            
            # Theme management
            self.theme_manager = ThemeManager()
            
            # Database client (anonymous for basic operations)
            self.supabase_client = get_supabase_client()
            
            # Authenticated database client (for user-specific operations)
            self.auth_supabase_client = get_authenticated_supabase_client(self.auth_manager)
            
            # Chat management (only if authenticated)
            self.chat_manager = None
            self.model_manager = None
            self.rag_orchestrator = None
            
            if self.session_manager.is_authenticated():
                self._initialize_chat_components()
                
        except Exception as e:
            st.error(f"Failed to initialize application: {e}")
            st.stop()
    
    def initialize_ui_components(self):
        """Initialize UI components"""
        self.auth_interface = AuthInterface(self.auth_manager, self.session_manager)
        
        # Initialize optimized message store if available (use authenticated client)
        self.optimized_message_store = None
        if self.auth_supabase_client:
            try:
                self.optimized_message_store = OptimizedMessageStore(self.auth_supabase_client)
            except Exception as e:
                logger.warning(f"Failed to initialize optimized message store: {e}")
        
        # Use optimized chat interface if available
        if self.optimized_message_store:
            self.chat_interface = OptimizedChatInterface(self.theme_manager, self.optimized_message_store)
        else:
            self.chat_interface = ChatInterface(self.theme_manager)
    
    def initialize_legacy_components(self):
        """Initialize legacy RAG components for fallback"""
        try:
            # Use deployment configuration
            from deployment_config import deployment_config
            
            db_config = deployment_config.get_database_config()
            self.supabase_url = db_config["url"]
            self.supabase_anon_key = db_config["anon_key"]
            
            model_config = deployment_config.get_model_config()
            self.groq_api_key = model_config["groq_api_key"]
            
            if not (self.supabase_url and self.supabase_anon_key and self.groq_api_key):
                st.error("Please configure SUPABASE_URL, SUPABASE_ANON_KEY and GROQ_API_KEY in Streamlit secrets.")
                st.stop()
            
            # Legacy components
            self.legacy_supabase = get_legacy_supabase_client(self.supabase_url, self.supabase_anon_key)
            self.embeddings = get_embeddings()
            self.vectorstore = get_vectorstore(supabase_client=self.legacy_supabase, embedding_fn=self.embeddings)
            
        except Exception as e:
            st.warning(f"Legacy components initialization failed: {e}")
            # Log error for monitoring
            from health_check import error_monitor
            error_monitor.log_error(e, "legacy_components_initialization")
            
            self.legacy_supabase = None
            self.embeddings = None
            self.vectorstore = None
    
    def _initialize_chat_components(self):
        """Initialize chat-related components for authenticated users"""
        try:
            # Use authenticated client for chat operations
            self.chat_manager = ChatManager(self.auth_supabase_client, self.session_manager)
            self.model_manager = ModelManager()
            self.rag_orchestrator = RAGOrchestrator()
        except Exception as e:
            st.warning(f"Chat components initialization failed: {e}")
            self.chat_manager = None
            self.model_manager = None
            self.rag_orchestrator = None

    def run(self):
        """Main application entry point"""
        # Check for health check page
        if st.query_params.get("page") == "health":
            from health_check import render_health_check_page
            render_health_check_page()
            return
        
        # Check database initialization
        if self.supabase_client:
            db_initializer = check_and_initialize_database(self.supabase_client)
            if not db_initializer.schema_status.get('initialized', False):
                st.title("🧬 Pharmacology Chat Assistant")
                render_database_setup_instructions(db_initializer)
                return
        
        # Apply current theme and chat CSS
        self.theme_manager.apply_theme()
        if isinstance(self.chat_interface, OptimizedChatInterface):
            inject_optimized_chat_css()
        else:
            inject_chat_css()
        
        # Check authentication status and route accordingly
        if not self.session_manager.validate_session():
            self.render_authentication_page()
        else:
            self.render_protected_chat_interface()
    
    def render_authentication_page(self):
        """Render authentication page for unauthenticated users"""
        # Clear any existing chat data
        self._clear_chat_session_data()
        
        # Render authentication interface
        self.auth_interface.render_auth_page()
    
    def render_protected_chat_interface(self):
        """Render the main chat interface for authenticated users"""
        # Validate session and protect route
        if not RouteProtection.protect_chat_interface(self.auth_guard):
            return
        
        # Initialize chat components if needed
        if self.chat_manager is None:
            self._initialize_chat_components()
        
        # Render main interface
        self._render_chat_header()
        self._render_sidebar()
        self._render_main_chat_area()
    
    def _render_chat_header(self):
        """Render the chat interface header with enhanced model indicator"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.title("🧬 Pharmacology Chat Assistant")
        
        with col2:
            # Enhanced model indicator
            if self.model_manager:
                from model_ui import render_header_model_indicator
                model_display = render_header_model_indicator()
                st.markdown(model_display)
            else:
                model_pref = self.session_manager.get_model_preference()
                model_display = "🚀 Fast" if model_pref == "fast" else "⭐ Premium"
                st.markdown(f"**{model_display}**")
        
        with col3:
            # Connection status
            if self.supabase_client:
                st.markdown("🟢 **Online**")
            else:
                st.markdown("🔴 **Offline**")
    
    def _render_sidebar(self):
        """Render sidebar with user profile and controls"""
        with st.sidebar:
            # User profile and logout
            self.auth_interface.render_user_profile()
            
            # Chat controls
            self._render_chat_controls()
            
            # Performance dashboard (if using optimized interface)
            if isinstance(self.chat_interface, OptimizedChatInterface):
                with st.expander("📊 Performance", expanded=False):
                    self.chat_interface.render_performance_dashboard()
            
            # Legacy document ingestion (if available)
            if self.vectorstore:
                self._render_legacy_document_ingestion()
    
    def _render_chat_controls(self):
        """Render chat control section in sidebar"""
        st.markdown("---")
        
        user_id = self.session_manager.get_user_id()
        if user_id and self.chat_manager:
            # Render enhanced model settings in sidebar
            if self.model_manager:
                from model_ui import render_model_settings_sidebar
                render_model_settings_sidebar(self.model_manager)
                st.markdown("---")
            
            # Render conversation controls (optimized if available)
            if isinstance(self.chat_interface, OptimizedChatInterface):
                controls = self.chat_interface.render_conversation_controls_optimized(user_id, self.chat_manager)
                
                # Render page size selector for pagination
                self.chat_interface.render_page_size_selector()
            else:
                controls = self.chat_interface.render_conversation_controls(user_id, self.chat_manager)
                
                # Render chat statistics for non-optimized interface
                stats = self.chat_manager.get_user_message_stats(user_id)
                self.chat_interface.render_chat_statistics(stats)
            
            # Handle clear conversation
            if controls.get('clear_confirmed'):
                with LoadingStateManager.show_loading_spinner("Clearing conversation..."):
                    if self.chat_manager.clear_conversation(user_id):
                        st.success("Conversation cleared!")
                        st.session_state.conversation_history = []
                        # Clear pagination state
                        st.session_state.chat_current_page = 1
                        st.rerun()
                    else:
                        st.error("Failed to clear conversation")
            
            # Handle export conversation
            if controls.get('export'):
                self._handle_conversation_export(user_id)
    
    def _render_legacy_document_ingestion(self):
        """Render legacy document ingestion interface"""
        st.markdown("---")
        st.subheader("📚 Document Ingestion")
        
        upload_files = st.file_uploader(
            "Upload documents", 
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'md']
        )
        
        url_to_ingest = st.text_input("Or paste a URL")
        
        if st.button("Process Documents"):
            self._process_document_ingestion(upload_files, url_to_ingest)
    
    def _process_document_ingestion(self, upload_files, url_to_ingest):
        """Process document ingestion"""
        if not self.vectorstore:
            st.error("Document ingestion not available")
            return
        
        docs_to_upsert = []
        
        if upload_files:
            try:
                docs_to_upsert += create_documents_from_uploads(
                    upload_files, chunk_size=500, chunk_overlap=100
                )
                st.success(f"Processed {len(docs_to_upsert)} chunks from uploads")
            except Exception as e:
                st.error(f"Failed to process uploads: {e}")
        
        if url_to_ingest:
            try:
                txt = extract_text_from_url(url_to_ingest)
                fake_file = type("U", (), {
                    "name": url_to_ingest, 
                    "read": lambda: txt.encode("utf-8"),
                    "getvalue": lambda: txt.encode("utf-8")
                })()
                docs_to_upsert += create_documents_from_uploads(
                    [fake_file], chunk_size=500, chunk_overlap=100
                )
                st.success(f"Processed URL content")
            except Exception as e:
                st.error(f"Failed to process URL: {e}")
        
        if docs_to_upsert:
            try:
                upsert_documents(
                    docs_to_upsert, 
                    supabase_client=self.legacy_supabase, 
                    embedding_fn=self.embeddings
                )
                st.success("Documents ingested successfully!")
            except Exception as e:
                st.error(f"Ingestion failed: {e}")
    
    def _render_main_chat_area(self):
        """Render the main chat area"""
        user_id = self.session_manager.get_user_id()
        
        if not user_id:
            st.error("Invalid user session. Please refresh the page and sign in again.")
            return
        
        # Debug: Test GROQ API availability
        with st.expander("🔍 Debug Info", expanded=False):
            try:
                from deployment_config import deployment_config
                model_config = deployment_config.get_model_config()
                groq_key = model_config.get("groq_api_key")
                
                if groq_key:
                    st.success("✅ GROQ API key is configured")
                else:
                    st.error("❌ GROQ API key is missing - add GROQ_API_KEY to Streamlit secrets")
                    
                st.write(f"User ID: {user_id}")
                st.write(f"Chat manager available: {self.chat_manager is not None}")
                
            except Exception as e:
                st.error(f"Configuration error: {e}")
        
        # Initialize conversation history
        if 'conversation_history' not in st.session_state:
            if self.chat_manager:
                messages = self.chat_manager.get_conversation_history(user_id, limit=50)
                st.session_state.conversation_history = messages
            else:
                st.session_state.conversation_history = []
        
        # Display chat history (optimized if available)
        if isinstance(self.chat_interface, OptimizedChatInterface):
            # Use paginated chat history
            self.chat_interface.render_paginated_chat_history(user_id, show_pagination=True)
        else:
            # Use traditional chat history
            self.chat_interface.render_chat_history(
                st.session_state.get('conversation_history', [])
            )
        
        # Enhanced chat input with file attachments and loading states
        if isinstance(self.chat_interface, OptimizedChatInterface):
            input_data = self.chat_interface.render_loading_message_input(
                placeholder="Ask about pharmacology...",
                enable_attachments=True
            )
        else:
            input_data = self.chat_interface.render_message_input_with_attachments(
                placeholder="Ask about pharmacology...",
                enable_attachments=True
            )
        
        if input_data:
            self._process_user_message_with_attachments(user_id, input_data)
    

    

    
    def _handle_model_change(self, new_model: str):
        """Handle model selection change with persistence"""
        self.session_manager.update_model_preference(new_model)
        
        # Update model manager if available
        if self.model_manager:
            from model_manager import ModelTier
            tier = ModelTier.PREMIUM if new_model == 'premium' else ModelTier.FAST
            self.model_manager.set_current_model(tier)
        
        st.success(f"✅ Switched to {'Fast' if new_model == 'fast' else 'Premium'} mode - preference saved!")
    
    def _handle_conversation_export(self, user_id: str):
        """Handle conversation export"""
        if not self.chat_manager:
            st.error("Chat manager not available")
            return
        
        messages = self.chat_manager.get_conversation_history(user_id, limit=1000)
        if not messages:
            st.warning("No conversation history to export")
            return
        
        # Export options
        export_format = st.selectbox(
            "Export format:",
            options=["txt", "json", "csv"],
            key="export_format"
        )
        
        try:
            exported_data = self.chat_interface.export_conversation(messages, export_format)
            filename = f"pharmacology_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
            
            st.download_button(
                label=f"Download {export_format.upper()}",
                data=exported_data,
                file_name=filename,
                mime=f"text/{export_format}" if export_format != "json" else "application/json"
            )
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    def _process_user_message_with_attachments(self, user_id: str, input_data: Dict[str, Any]):
        """Process user message with file attachments"""
        message_content = input_data.get('message', '')
        uploaded_files = input_data.get('files', [])
        
        # Process file attachments if any
        if uploaded_files:
            self._process_file_attachments(uploaded_files)
            
            # Add file info to message if no text message
            if not message_content:
                file_names = [f.name for f in uploaded_files]
                message_content = f"I've uploaded these files: {', '.join(file_names)}. Please analyze them."
        
        if message_content:
            self._process_user_message_with_streaming(user_id, message_content)
    
    def _process_file_attachments(self, uploaded_files: List[Any]):
        """Process uploaded file attachments"""
        try:
            # This would integrate with document processing
            # For now, show processing status
            with st.spinner("Processing uploaded files..."):
                time.sleep(1)  # Simulate processing
                st.success(f"Processed {len(uploaded_files)} file(s)")
                
                # Here you would:
                # 1. Extract text from files
                # 2. Create document chunks
                # 3. Generate embeddings
                # 4. Store in vector database with user_id
                
        except Exception as e:
            st.error(f"File processing failed: {e}")
    
    def _process_user_message_with_streaming(self, user_id: str, message_content: str):
        """Process user message with streaming response"""
        try:
            model_preference = self.session_manager.get_model_preference()
            
            # Set loading state for optimized interface
            if isinstance(self.chat_interface, OptimizedChatInterface):
                self.chat_interface.set_loading_state("processing_message", True)
            
            # Save user message
            if self.chat_manager:
                with st.spinner("Saving message..."):
                    user_response = self.chat_manager.send_message(
                        user_id=user_id,
                        message_content=message_content,
                        model_type=model_preference
                    )
                
                if user_response.success:
                    # Add to session history
                    if 'conversation_history' not in st.session_state:
                        st.session_state.conversation_history = []
                    st.session_state.conversation_history.append(user_response.message)
                    
                    # Invalidate cache for optimized message store
                    if self.optimized_message_store:
                        performance_optimizer.invalidate_user_cache(user_id)
                else:
                    # Handle authentication/RLS errors
                    if "row-level security policy" in user_response.error_message.lower() or "database security policy" in user_response.error_message.lower():
                        st.error("🔒 **Database Security Policy Issue**")
                        st.markdown("""
                        **Quick Fix Needed:**
                        
                        1. **Go to your Supabase Dashboard**
                        2. **Navigate to SQL Editor**
                        3. **Run this command:**
                        ```sql
                        ALTER TABLE messages DISABLE ROW LEVEL SECURITY;
                        ```
                        4. **Refresh this app and try again**
                        
                        **Why this happens:**
                        - Row-Level Security (RLS) is blocking message saves
                        - The authentication session isn't properly maintained
                        - Disabling RLS temporarily allows messages to save
                        
                        **Alternative:** Check the QUICK_FIX_INSTRUCTIONS.md file in your repository.
                        """)
                        
                        # Suggest re-authentication as backup
                        if st.button("🔄 Try Re-authenticating First"):
                            self.session_manager.clear_session()
                            st.rerun()
                        return
                    else:
                        st.error(f"Failed to save message: {user_response.error_message}")
                        return
            else:
                st.error("Chat system not available. Please refresh the page.")
                return
            
            # Start streaming response
            self.chat_interface.start_streaming_response()
            
            # Generate AI response with streaming and error handling
            try:
                self._generate_streaming_response(user_id, message_content, model_preference)
            except Exception as e:
                # Fallback to simple response if RAG fails
                st.error(f"AI processing error: {e}")
                fallback_response = f"I apologize, but I encountered an error processing your question about '{message_content}'. This might be due to API configuration issues. Please check that your GROQ_API_KEY is properly configured in Streamlit secrets."
                
                # Save fallback response
                if self.chat_manager:
                    assistant_response = self.chat_manager.save_assistant_response(
                        user_id=user_id,
                        response_content=fallback_response,
                        model_used="error_fallback",
                        metadata={"error": str(e)}
                    )
                    
                    if assistant_response.success:
                        st.session_state.conversation_history.append(assistant_response.message)
                
                st.rerun()
            
        except Exception as e:
            st.error(f"Error processing message: {e}")
            import traceback
            st.code(traceback.format_exc())
            self.chat_interface.complete_streaming_message()
        finally:
            # Clear loading state
            if isinstance(self.chat_interface, OptimizedChatInterface):
                self.chat_interface.set_loading_state("processing_message", False)
    
    def _generate_streaming_response(self, user_id: str, message_content: str, model_preference: str):
        """Generate streaming AI response"""
        try:
            st.write(f"🔍 DEBUG: Starting response generation...")
            st.write(f"🔍 DEBUG: RAG orchestrator available: {self.rag_orchestrator is not None}")
            
            # Temporarily bypass RAG orchestrator and use legacy system
            st.write("🔍 DEBUG: Bypassing RAG orchestrator, using legacy system...")
            self._generate_streaming_legacy_response(user_id, message_content, model_preference)
            
        except Exception as e:
            st.error(f"Streaming response generation failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            self.chat_interface.complete_streaming_message()
    
    def _generate_streaming_rag_response(self, user_id: str, message_content: str, model_preference: str):
        """Generate streaming response using new RAG orchestrator"""
        try:
            st.write("🔍 DEBUG: Getting conversation context...")
            context = self.chat_manager.get_conversation_context(user_id, limit=10)
            st.write(f"🔍 DEBUG: Got context with {len(context.messages)} messages")
            
            # Create placeholder for streaming
            response_placeholder = st.empty()
            collected_response = ""
            
            st.write("🔍 DEBUG: Starting RAG orchestrator stream_query...")
            
            # Stream response
            try:
                for response_chunk in self.rag_orchestrator.stream_query(
                    query=message_content,
                    user_id=user_id,
                    model_type=model_preference,
                    conversation_history=[{"role": msg.role, "content": msg.content} for msg in context.messages[-4:]]
                ):
                    collected_response += response_chunk
                    self.chat_interface.update_streaming_message(response_chunk)
                    
                    # Update display
                    response_placeholder.markdown(collected_response + "▌")
                
                st.write("🔍 DEBUG: RAG streaming completed successfully")
            except Exception as e:
                st.write(f"🔍 DEBUG: RAG streaming failed: {e}")
                import traceback
                st.code(traceback.format_exc())
                
                # Fallback to simple response
                collected_response = f"I apologize, but I encountered an error processing your question about '{message_content}'. The RAG system failed with: {str(e)}"
            
            # Complete streaming
            final_response = self.chat_interface.complete_streaming_message()
            if not final_response:
                final_response = collected_response
                
            response_placeholder.markdown(final_response)
            
            # Save assistant response
            if self.chat_manager and final_response:
                assistant_response = self.chat_manager.save_assistant_response(
                    user_id=user_id,
                    response_content=final_response,
                    model_used=f"{model_preference}_model",
                    metadata={"streaming": True}
                )
                
                if assistant_response.success:
                    st.session_state.conversation_history.append(assistant_response.message)
                    st.write("🔍 DEBUG: RAG response saved successfully")
                else:
                    st.write(f"🔍 DEBUG: Failed to save RAG response: {assistant_response.error_message}")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"RAG streaming response failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            self.chat_interface.complete_streaming_message()
    
    def _generate_streaming_legacy_response(self, user_id: str, message_content: str, model_preference: str):
        """Generate streaming response using legacy RAG system"""
        try:
            st.write("🔍 DEBUG: Starting legacy response generation...")
            
            # Use legacy RAG system with streaming
            selected_model = PREMIUM_MODE if model_preference == "premium" else FAST_MODE
            st.write(f"🔍 DEBUG: Selected model: {selected_model}")
            
            # Retrieve context
            docs = []
            if self.vectorstore:
                st.write("🔍 DEBUG: Vectorstore available, retrieving documents...")
                retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
                try:
                    docs = retriever.invoke(message_content) if hasattr(retriever, "invoke") else retriever.get_relevant_documents(message_content)
                except Exception as e:
                    st.write(f"🔍 DEBUG: Document retrieval failed: {e}")
                    docs = []
            else:
                st.write("🔍 DEBUG: No vectorstore available, using empty context")
            
            st.write(f"🔍 DEBUG: Retrieved {len(docs)} documents")
            
            # Build context
            retrieved_texts = []
            for d in docs:
                text = getattr(d, "page_content", None) or d.get("content", "") if isinstance(d, dict) else str(d)
                retrieved_texts.append(text)
            
            context = "\n\n---\n\n".join(retrieved_texts)[:50000] if retrieved_texts else ""
            st.write(f"🔍 DEBUG: Context length: {len(context)}")
            
            # Generate response with streaming
            try:
                system_prompt = get_rag_enhanced_prompt(user_question=message_content, context=context)
                st.write("🔍 DEBUG: System prompt created")
            except Exception as e:
                st.write(f"🔍 DEBUG: System prompt creation failed: {e}")
                # Fallback to simple prompt
                system_prompt = f"You are a helpful pharmacology assistant. Answer this question: {message_content}"
            
            messages_for_model = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content}
            ]
            
            st.write("🔍 DEBUG: Starting streaming response...")
            
            # Stream response
            response_placeholder = st.empty()
            collected_response = ""
            
            try:
                for chunk in generate_completion_stream(messages=messages_for_model, model=selected_model):
                    collected_response += chunk
                    self.chat_interface.update_streaming_message(chunk)
                    response_placeholder.markdown(collected_response + "▌")
                
                st.write("🔍 DEBUG: Streaming completed successfully")
            except Exception as e:
                st.write(f"🔍 DEBUG: Streaming failed: {e}")
                # Fallback to non-streaming
                try:
                    collected_response = generate_completion(messages=messages_for_model, model=selected_model)
                    st.write("🔍 DEBUG: Fallback to non-streaming successful")
                except Exception as e2:
                    st.write(f"🔍 DEBUG: Non-streaming also failed: {e2}")
                    collected_response = "I apologize, but I'm having trouble generating a response right now. Please try again."
            
            # Complete streaming
            final_response = self.chat_interface.complete_streaming_message()
            if not final_response:
                final_response = collected_response
                
            response_placeholder.markdown(final_response)
            
            # Save response
            if self.chat_manager:
                assistant_response = self.chat_manager.save_assistant_response(
                    user_id=user_id,
                    response_content=final_response,
                    model_used=selected_model,
                    metadata={"sources_used": len(docs), "streaming": True}
                )
                
                if assistant_response.success:
                    st.session_state.conversation_history.append(assistant_response.message)
                    st.write("🔍 DEBUG: Response saved successfully")
                else:
                    st.write(f"🔍 DEBUG: Failed to save response: {assistant_response.error_message}")
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Legacy streaming response failed: {e}")
            import traceback
            st.code(traceback.format_exc())
            self.chat_interface.complete_streaming_message()
    
    def _clear_chat_session_data(self):
        """Clear chat-related session data"""
        keys_to_clear = ['conversation_history', 'last_message_id', 'chat_context', 'streaming_message', 'show_typing_indicator']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# ----------------------------
# Main Application Entry Point
# ----------------------------
def main():
    """Main application entry point"""
    app = PharmacologyChat()
    app.run()


if __name__ == "__main__":
    main()


