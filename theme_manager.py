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
    """Manages permanent dark theme for the application."""
    
    def __init__(self):
        # Enhanced dark theme configuration for better readability and contrast
        self.dark_theme = ThemeConfig(
            name="dark",
            primary_color="#4fc3f7",
            background_color="#0e1117",
            secondary_background_color="#262730",
            text_color="#ffffff",  # Pure white for maximum contrast
            accent_color="#ff6b6b",
            user_message_bg="#1e3a8a",
            ai_message_bg="#374151",
            border_color="#4b5563",
            shadow_color="rgba(0, 0, 0, 0.4)"  # Slightly stronger shadow
        )
        
        # Force dark theme in session state (if available)
        try:
            st.session_state.theme = "dark"
        except (AttributeError, RuntimeError):
            # Session state not available in testing or non-streamlit context
            pass
    
    def get_current_theme(self) -> str:
        """Get the current theme name - always returns 'dark'."""
        return "dark"
    
    def get_theme_config(self, theme_name: str = None) -> ThemeConfig:
        """Get theme configuration - always returns dark theme."""
        return self.dark_theme
    
    def apply_theme(self, theme_name: str = None) -> None:
        """Apply the permanent dark theme to the Streamlit app."""
        css = self._generate_css(self.dark_theme)
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
        
        /* Main app styling - Enhanced for dark theme */
        .stApp {{
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }}
        
        /* Sidebar styling - Enhanced for dark theme */
        .css-1d391kg {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        /* Ensure all text elements use high contrast */
        .stMarkdown, .stText, p, span, div {{
            color: var(--text-color) !important;
        }}
        
        /* Headers with enhanced contrast */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-color) !important;
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
        
        /* Input area - Enhanced for dark theme */
        .stTextInput > div > div > input {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
            border-radius: 0.5rem !important;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.2) !important;
        }}
        
        /* Buttons - Enhanced for dark theme */
        .stButton > button {{
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: 0.5rem !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.3s ease !important;
            font-weight: 600 !important;
        }}
        
        .stButton > button:hover {{
            background-color: var(--accent-color) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px var(--shadow-color) !important;
        }}
        
        /* Theme toggle removed - permanent dark theme */
        
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
        
        /* Additional dark theme enforcement */
        .stSelectbox > div > div > select {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
        }}
        
        .stTextArea > div > div > textarea {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
        }}
        
        /* Streamlit specific dark theme overrides */
        .stApp > header {{
            background-color: var(--background-color) !important;
        }}
        
        .main .block-container {{
            background-color: var(--background-color) !important;
        }}
        
        /* Force dark theme on all elements */
        * {{
            scrollbar-color: var(--border-color) var(--secondary-bg);
        }}
        
        ::-webkit-scrollbar {{
            background-color: var(--secondary-bg);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background-color: var(--border-color);
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background-color: var(--primary-color);
        }}
        
        /* Enhanced dark theme enforcement for all Streamlit components */
        .stSelectbox > div > div > div {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        .stMultiSelect > div > div > div {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        .stNumberInput > div > div > input {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
        }}
        
        .stDateInput > div > div > input {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
        }}
        
        .stTimeInput > div > div > input {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
        }}
        
        /* File uploader dark theme */
        .stFileUploader > div > div {{
            background-color: var(--secondary-bg) !important;
            border: 2px dashed var(--border-color) !important;
        }}
        
        .stFileUploader > div > div > div {{
            color: var(--text-color) !important;
        }}
        
        /* Expander dark theme */
        .streamlit-expanderHeader {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        .streamlit-expanderContent {{
            background-color: var(--background-color) !important;
            border: 1px solid var(--border-color) !important;
        }}
        
        /* Tabs dark theme */
        .stTabs > div > div > div > div {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        /* Metric dark theme */
        .metric-container {{
            background-color: var(--secondary-bg) !important;
            border: 1px solid var(--border-color) !important;
        }}
        
        /* Alert/info boxes dark theme */
        .stAlert {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border-left: 4px solid var(--primary-color) !important;
        }}
        
        .stSuccess {{
            background-color: color-mix(in srgb, #4caf50 20%, var(--secondary-bg)) !important;
            color: var(--text-color) !important;
        }}
        
        .stError {{
            background-color: color-mix(in srgb, #f44336 20%, var(--secondary-bg)) !important;
            color: var(--text-color) !important;
        }}
        
        .stWarning {{
            background-color: color-mix(in srgb, #ff9800 20%, var(--secondary-bg)) !important;
            color: var(--text-color) !important;
        }}
        
        .stInfo {{
            background-color: color-mix(in srgb, var(--primary-color) 20%, var(--secondary-bg)) !important;
            color: var(--text-color) !important;
        }}
        
        /* Code blocks dark theme */
        .stCode {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 1px solid var(--border-color) !important;
        }}
        
        /* JSON viewer dark theme */
        .stJson {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        /* DataFrame dark theme */
        .stDataFrame {{
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
        }}
        
        /* Progress bar dark theme */
        .stProgress > div > div > div {{
            background-color: var(--primary-color) !important;
        }}
        
        /* Spinner dark theme */
        .stSpinner > div {{
            border-color: var(--primary-color) !important;
        }}
        
        /* Ensure all text elements have proper contrast */
        label, .stMarkdown, .stText, .stCaption {{
            color: var(--text-color) !important;
        }}
        
        /* High contrast for links */
        a {{
            color: var(--primary-color) !important;
        }}
        
        a:hover {{
            color: var(--accent-color) !important;
        }}
        
        /* Ensure proper contrast for form labels */
        .stFormSubmitButton > button {{
            background-color: var(--primary-color) !important;
            color: white !important;
        }}
        
        /* Dark theme for radio buttons and checkboxes */
        .stRadio > div {{
            color: var(--text-color) !important;
        }}
        
        .stCheckbox > div {{
            color: var(--text-color) !important;
        }}
        </style>
        """
    
    def render_theme_toggle(self) -> None:
        """Theme toggle removed - permanent dark theme enforced."""
        # No theme toggle functionality - dark theme is permanent
        pass