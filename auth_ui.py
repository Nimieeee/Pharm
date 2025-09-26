"""
Authentication UI Components for Pharmacology Chat App
Provides login and registration forms with Streamlit
"""

import streamlit as st
import time
from typing import Optional, Tuple
from auth_manager import AuthenticationManager, AuthResult
from session_manager import SessionManager

class AuthInterface:
    """Authentication user interface components"""
    
    def __init__(self, auth_manager: AuthenticationManager, session_manager: SessionManager):
        """
        Initialize authentication interface
        
        Args:
            auth_manager: Authentication manager instance
            session_manager: Session manager instance
        """
        self.auth_manager = auth_manager
        self.session_manager = session_manager
    
    def render_login_form(self) -> Optional[AuthResult]:
        """
        Render login form
        
        Returns:
            AuthResult if login attempted, None otherwise
        """
        st.subheader("🔐 Sign In")
        
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="Enter your email address",
                help="Use the email address you registered with"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Enter your account password"
            )
            
            col1, col2 = st.columns([1, 1])
            with col1:
                login_button = st.form_submit_button(
                    "Sign In",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                forgot_password = st.form_submit_button(
                    "Forgot Password?",
                    use_container_width=True
                )
            
            if login_button:
                if not email or not password:
                    st.error("Please enter both email and password.")
                    return None
                
                if not self._is_valid_email(email):
                    st.error("Please enter a valid email address.")
                    return None
                
                with st.spinner("Signing in..."):
                    result = self.auth_manager.sign_in(email, password)
                    
                if result.success:
                    st.success("Successfully signed in!")
                    self.session_manager.initialize_session(
                        user_id=result.user_id,
                        email=result.email,
                        preferences=result.user_data or {}
                    )
                    st.rerun()
                else:
                    st.error(result.error_message)
                
                return result
            
            if forgot_password:
                st.info("Password reset functionality will be available soon.")
        
        return None
    
    def render_registration_form(self) -> Optional[AuthResult]:
        """
        Render registration form
        
        Returns:
            AuthResult if registration attempted, None otherwise
        """
        st.subheader("📝 Create Account")
        
        with st.form("registration_form"):
            email = st.text_input(
                "Email",
                placeholder="Enter your email address",
                help="This will be your username for signing in"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password",
                help="Password should be at least 8 characters long"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm your password",
                help="Re-enter your password to confirm"
            )
            
            # Terms and conditions
            terms_accepted = st.checkbox(
                "I agree to the Terms of Service and Privacy Policy",
                help="You must accept the terms to create an account"
            )
            
            register_button = st.form_submit_button(
                "Create Account",
                use_container_width=True,
                type="primary"
            )
            
            if register_button:
                # Validation
                if not email or not password or not confirm_password:
                    st.error("Please fill in all fields.")
                    return None
                
                if not self._is_valid_email(email):
                    st.error("Please enter a valid email address.")
                    return None
                
                if len(password) < 8:
                    st.error("Password must be at least 8 characters long.")
                    return None
                
                if password != confirm_password:
                    st.error("Passwords do not match.")
                    return None
                
                if not terms_accepted:
                    st.error("Please accept the Terms of Service and Privacy Policy.")
                    return None
                
                with st.spinner("Creating account..."):
                    result = self.auth_manager.sign_up(email, password)
                
                if result.success:
                    st.success("Account created successfully! Please check your email for verification.")
                    st.info("You can now sign in with your credentials.")
                else:
                    st.error(result.error_message)
                
                return result
        
        return None
    
    def render_auth_page(self) -> None:
        """Render complete authentication page with tabs for login and registration"""
        st.title("🧬 Pharmacology Chat Assistant")
        st.markdown("---")
        
        # Welcome message
        st.markdown("""
        Welcome to your AI-powered pharmacology assistant! Get expert answers to your 
        pharmacology questions with our advanced RAG-powered chatbot.
        
        **Features:**
        - 🤖 Two AI model tiers (Fast & Premium)
        - 🔒 Private, secure conversations
        - 📚 Comprehensive pharmacology knowledge base
        - 🌓 Light & dark theme support
        """)
        
        st.markdown("---")
        
        # Authentication tabs
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            self.render_login_form()
        
        with tab2:
            self.render_registration_form()
        
        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: gray;'>"
            "Secure authentication powered by Supabase"
            "</div>",
            unsafe_allow_html=True
        )
    
    def render_user_profile(self) -> None:
        """Render user profile section in sidebar"""
        user_session = self.session_manager.get_user_session()
        if not user_session:
            return
        
        with st.sidebar:
            st.markdown("---")
            st.subheader("👤 User Profile")
            
            # User info
            st.write(f"**Email:** {user_session.email}")
            st.write(f"**Plan:** {user_session.preferences.get('subscription_tier', 'Free').title()}")
            
            # Model preference
            current_model = self.session_manager.get_model_preference()
            model_options = ["fast", "premium"]
            model_labels = ["🚀 Fast (Gemma2-9B)", "⭐ Premium (Qwen3-32B)"]
            
            selected_model = st.selectbox(
                "AI Model",
                options=model_options,
                format_func=lambda x: model_labels[model_options.index(x)],
                index=model_options.index(current_model),
                help="Choose between fast responses or premium quality"
            )
            
            if selected_model != current_model:
                self.session_manager.update_model_preference(selected_model)
                st.rerun()
            
            # Theme toggle
            current_theme = self.session_manager.get_theme()
            theme_options = ["light", "dark"]
            theme_labels = ["☀️ Light", "🌙 Dark"]
            
            selected_theme = st.selectbox(
                "Theme",
                options=theme_options,
                format_func=lambda x: theme_labels[theme_options.index(x)],
                index=theme_options.index(current_theme),
                help="Choose your preferred theme"
            )
            
            if selected_theme != current_theme:
                self.session_manager.update_theme(selected_theme)
                st.rerun()
            
            # Sign out button
            st.markdown("---")
            if st.button("🚪 Sign Out", use_container_width=True):
                self._handle_sign_out()
    
    def _handle_sign_out(self) -> None:
        """Handle user sign out"""
        success = self.auth_manager.sign_out()
        if success:
            self.session_manager.clear_session()
            st.success("Successfully signed out!")
            st.rerun()
        else:
            st.error("Error signing out. Please try again.")
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Basic email validation
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


def require_authentication(session_manager: SessionManager) -> bool:
    """
    Decorator-like function to require authentication
    
    Args:
        session_manager: Session manager instance
        
    Returns:
        True if authenticated, False otherwise
    """
    if not session_manager.is_authenticated():
        st.warning("Please sign in to access the chat interface.")
        return False
    
    # Validate session
    if not session_manager.validate_session():
        st.error("Your session has expired. Please sign in again.")
        return False
    
    return True