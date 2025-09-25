"""
Theme Manager for handling light/dark mode switching and UI styling.
"""
import streamlit as st
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ThemeConfig:
    """Configuration for theme settings."""
    name: str
    primary_color: str
    background_color: str
    secondary_background_color: str
    text_color: str
    accent_color: str
    user_message_bg: str
    ai_message_bg: str
    border_color: str
    shadow_color: str


class ThemeManager:
    """Manages theme switching and CSS generation for the application."""
    
    def __init__(self):
        self.themes = {
            "light": ThemeConfig(
                name="light",
                primary_color="#1f77b4",
                background_color="#ffffff",
                secondary_background_color="#f8f9fa",
                text_color="#262730",
                accent_color="#ff6b6b",
                user_message_bg="#e3f2fd",
                ai_message_bg="#f5f5f5",
                border_color="#e0e0e0",
                shadow_color="rgba(0, 0, 0, 0.1)"
            ),
            "dark": ThemeConfig(
                name="dark",
                primary_color="#4fc3f7",
                background_color="#0e1117",
                secondary_background_color="#262730",
                text_color="#fafafa",
                accent_color="#ff6b6b",
                user_message_bg="#1e3a8a",
                ai_message_bg="#374151",
                border_color="#4b5563",
                shadow_color="rgba(0, 0, 0, 0.3)"
            )
        }
        
        # Initialize theme in session state if not present
        if "theme" not in st.session_state:
            st.session_state.theme = "light"
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return st.session_state.get("theme", "light")
    
    def toggle_theme(self) -> str:
        """Toggle between light and dark themes."""
        current = self.get_current_theme()
        new_theme = "dark" if current == "light" else "light"
        st.session_state.theme = new_theme
        return new_theme
    
    def set_theme(self, theme_name: str) -> None:
        """Set a specific theme."""
        if theme_name in self.themes:
            st.session_state.theme = theme_name
    
    def get_theme_config(self, theme_name: str = None) -> ThemeConfig:
        """Get theme configuration for specified theme or current theme."""
        if theme_name is None:
            theme_name = self.get_current_theme()
        return self.themes.get(theme_name, self.themes["light"])
    
    def apply_theme(self, theme_name: str = None) -> None:
        """Apply the specified theme or current theme to the Streamlit app."""
        config = self.get_theme_config(theme_name)
        css = self._generate_css(config)
        st.markdown(css, unsafe_allow_html=True)
    
    def _generate_css(self, config: ThemeConfig) -> str:
        """Generate CSS styles based on theme configuration."""
        return f"""
        <style>
        /* Global theme variables */
        :root {{
            --primary-color: {config.primary_color};
            --background-color: {config.background_color};
            --secondary-bg: {config.secondary_background_color};
            --text-color: {config.text_color};
            --accent-color: {config.accent_color};
            --user-msg-bg: {config.user_message_bg};
            --ai-msg-bg: {config.ai_message_bg};
            --border-color: {config.border_color};
            --shadow-color: {config.shadow_color};
        }}
        
        /* Main app styling */
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        
        /* Sidebar styling */
        .css-1d391kg {{
            background-color: var(--secondary-bg);
        }}
        
        /* Chat container */
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
        }}
        
        /* Message bubbles */
        .message-bubble {{
            margin: 1rem 0;
            padding: 1rem;
            border-radius: 1rem;
            box-shadow: 0 2px 4px var(--shadow-color);
            animation: fadeIn 0.3s ease-in;
        }}
        
        .user-message {{
            background-color: var(--user-msg-bg);
            margin-left: 2rem;
            border-bottom-right-radius: 0.3rem;
        }}
        
        .ai-message {{
            background-color: var(--ai-msg-bg);
            margin-right: 2rem;
            border-bottom-left-radius: 0.3rem;
        }}
        
        /* Message content */
        .message-content {{
            margin: 0;
            line-height: 1.6;
        }}
        
        .message-role {{
            font-weight: bold;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            opacity: 0.8;
        }}
        
        /* Input area */
        .stTextInput > div > div > input {{
            background-color: var(--secondary-bg);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
        }}
        
        /* Buttons */
        .stButton > button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }}
        
        .stButton > button:hover {{
            background-color: var(--accent-color);
            transform: translateY(-1px);
            box-shadow: 0 4px 8px var(--shadow-color);
        }}
        
        /* Theme toggle button */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 1000;
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 50%;
            width: 3rem;
            height: 3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            background-color: var(--primary-color);
            color: white;
        }}
        
        /* Responsive design */
        @media (max-width: 768px) {{
            .chat-container {{
                padding: 0.5rem;
            }}
            
            .user-message {{
                margin-left: 1rem;
            }}
            
            .ai-message {{
                margin-right: 1rem;
            }}
            
            .message-bubble {{
                padding: 0.75rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .user-message {{
                margin-left: 0.5rem;
            }}
            
            .ai-message {{
                margin-right: 0.5rem;
            }}
            
            .theme-toggle {{
                width: 2.5rem;
                height: 2.5rem;
                top: 0.5rem;
                right: 0.5rem;
            }}
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(10px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        /* Loading animation */
        .loading-dots {{
            display: inline-block;
        }}
        
        .loading-dots::after {{
            content: '';
            animation: dots 1.5s steps(5, end) infinite;
        }}
        
        @keyframes dots {{
            0%, 20% {{
                color: rgba(0,0,0,0);
                text-shadow:
                    .25em 0 0 rgba(0,0,0,0),
                    .5em 0 0 rgba(0,0,0,0);
            }}
            40% {{
                color: var(--text-color);
                text-shadow:
                    .25em 0 0 rgba(0,0,0,0),
                    .5em 0 0 rgba(0,0,0,0);
            }}
            60% {{
                text-shadow:
                    .25em 0 0 var(--text-color),
                    .5em 0 0 rgba(0,0,0,0);
            }}
            80%, 100% {{
                text-shadow:
                    .25em 0 0 var(--text-color),
                    .5em 0 0 var(--text-color);
            }}
        }}
        
        /* Model selector styling */
        .model-selector {{
            background-color: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.5rem;
            margin: 1rem 0;
        }}
        
        /* Status indicators */
        .status-indicator {{
            display: inline-block;
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            margin-right: 0.5rem;
        }}
        
        .status-online {{
            background-color: #4caf50;
        }}
        
        .status-offline {{
            background-color: #f44336;
        }}
        
        .status-loading {{
            background-color: #ff9800;
            animation: pulse 1s infinite;
        }}
        
        @keyframes pulse {{
            0% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.5;
            }}
            100% {{
                opacity: 1;
            }}
        }}
        </style>
        """
    
    def render_theme_toggle(self) -> None:
        """Render a theme toggle button in the UI."""
        current_theme = self.get_current_theme()
        icon = "🌙" if current_theme == "light" else "☀️"
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col3:
            if st.button(icon, key="theme_toggle", help="Toggle theme"):
                self.toggle_theme()
                st.rerun()