"""
Integration example showing how MessageStore and ChatManager work with the existing authentication system.
This demonstrates the complete flow for user-scoped message storage and retrieval.
"""

import streamlit as st
from supabase import create_client
from auth_manager import AuthenticationManager
from session_manager import SessionManager
from chat_manager import ChatManager
from message_store import MessageStore

def initialize_chat_system():
    """Initialize the chat system with authentication and session management"""
    
    # Initialize authentication manager
    auth_manager = AuthenticationManager()
    
    # Initialize session manager
    session_manager = SessionManager(auth_manager)
    
    # Get Supabase client from auth manager
    supabase_client = auth_manager.supabase
    
    # Initialize chat manager
    chat_manager = ChatManager(supabase_client, session_manager)
    
    return auth_manager, session_manager, chat_manager

def example_chat_flow():
    """Example of a complete chat flow with user authentication and message persistence"""
    
    st.title("Pharmacology Chat App - Message Storage Demo")
    
    # Initialize systems
    auth_manager, session_manager, chat_manager = initialize_chat_system()
    
    # Check authentication status
    if not session_manager.is_authenticated():
        st.warning("Please log in to use the chat functionality")
        
        # Simple login form (in real app, this would be in auth_ui.py)
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted and email and password:
                result = auth_manager.sign_in(email, password)
                if result.success:
                    session_manager.initialize_session(
                        user_id=result.user_id,
                        email=result.email,
                        preferences=result.user_data or {}
                    )
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error(result.error_message)
        return
    
    # User is authenticated - show chat interface
    user_session = session_manager.get_user_session()
    st.success(f"Welcome, {user_session.email}!")
    
    # Display conversation history
    st.subheader("Conversation History")
    
    history = chat_manager.get_conversation_history(user_session.user_id, limit=10)
    
    if history:
        for message in history:
            if message.role == "user":
                st.chat_message("user").write(message.content)
            else:
                st.chat_message("assistant").write(f"{message.content} (Model: {message.model_used})")
    else:
        st.info("No conversation history yet. Start chatting below!")
    
    # Chat input
    st.subheader("Send Message")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_message = st.text_input("Your message:", key="user_input")
    
    with col2:
        # Use toggle switch for model selection
        current_model = st.session_state.get("demo_model", "fast")
        is_premium = current_model == "premium"
        
        toggle_html = f"""
        <div style="margin-bottom: 1rem;">
            <label style="font-weight: 500; margin-bottom: 0.5rem; display: block;">Model:</label>
            <div class="model-toggle-labels">
                <span class="toggle-label {'active' if not is_premium else ''}">⚡ Fast</span>
                <div class="toggle-switch-wrapper">
                    <label class="toggle-switch">
                        <input type="checkbox" {'checked' if is_premium else ''} onchange="
                            const checkbox = document.querySelector('[data-testid=\\'stCheckbox\\']:last-of-type input');
                            if (checkbox) checkbox.click();
                        ">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <span class="toggle-label {'active' if is_premium else ''}">🎯 Premium</span>
            </div>
        </div>
        """
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Handle toggle
        demo_toggle_key = "demo_model_toggle"
        if demo_toggle_key not in st.session_state:
            st.session_state[demo_toggle_key] = is_premium
        
        new_state = st.checkbox(
            "Demo Model Toggle",
            value=st.session_state[demo_toggle_key],
            key=f"{demo_toggle_key}_checkbox",
            label_visibility="collapsed"
        )
        
        if new_state != st.session_state[demo_toggle_key]:
            st.session_state[demo_toggle_key] = new_state
            st.session_state["demo_model"] = "premium" if new_state else "fast"
            st.rerun()
        
        model_type = st.session_state.get("demo_model", "fast")
    
    if st.button("Send Message") and user_message:
        # Send user message
        response = chat_manager.send_message(
            user_id=user_session.user_id,
            message_content=user_message,
            model_type=model_type
        )
        
        if response.success:
            st.success("Message sent!")
            
            # Simulate AI response (in real app, this would call the AI model)
            ai_response = f"This is a simulated response to: '{user_message}'"
            model_used = "gemma2-9b-it" if model_type == "fast" else "qwen3-32b"
            
            # Save AI response
            ai_response_result = chat_manager.save_assistant_response(
                user_id=user_session.user_id,
                response_content=ai_response,
                model_used=model_used,
                metadata={"response_type": "simulated"}
            )
            
            if ai_response_result.success:
                st.success("AI response saved!")
                st.rerun()  # Refresh to show new messages
            else:
                st.error(f"Failed to save AI response: {ai_response_result.error_message}")
        else:
            st.error(f"Failed to send message: {response.error_message}")
    
    # User statistics
    st.subheader("Your Chat Statistics")
    stats = chat_manager.get_user_message_stats(user_session.user_id)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Messages", stats["total_messages"])
    with col2:
        st.metric("Recent Messages (24h)", stats["recent_messages"])
    
    # Clear conversation option
    st.subheader("Conversation Management")
    if st.button("Clear Conversation History", type="secondary"):
        if chat_manager.clear_conversation(user_session.user_id):
            st.success("Conversation history cleared!")
            st.rerun()
        else:
            st.error("Failed to clear conversation history")
    
    # Logout option
    if st.button("Logout"):
        auth_manager.sign_out()
        session_manager.clear_session()
        st.success("Logged out successfully!")
        st.rerun()

if __name__ == "__main__":
    # This would be called from the main Streamlit app
    example_chat_flow()