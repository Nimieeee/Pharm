"""
Comprehensive styling system for the pharmacology chat application.
Provides theme-aware, responsive CSS styles.
"""
from typing import Dict, Any
from theme_manager import ThemeConfig


class StyleGenerator:
    """Generates comprehensive CSS styles for the application."""
    
    @staticmethod
    def generate_base_styles(theme_config: ThemeConfig) -> str:
        """Generate base application styles."""
        return f"""
        <style>
        /* CSS Custom Properties for Theme */
        :root {{
            --primary-color: {theme_config.primary_color};
            --background-color: {theme_config.background_color};
            --secondary-bg: {theme_config.secondary_background_color};
            --text-color: {theme_config.text_color};
            --accent-color: {theme_config.accent_color};
            --user-msg-bg: {theme_config.user_message_bg};
            --ai-msg-bg: {theme_config.ai_message_bg};
            --border-color: {theme_config.border_color};
            --shadow-color: {theme_config.shadow_color};
        }}
        
        /* Global Styles */
        * {{
            box-sizing: border-box;
        }}
        
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--secondary-bg);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--primary-color);
        }}
        </style>
        """
    
    @staticmethod
    def generate_chat_styles() -> str:
        """Generate chat interface specific styles."""
        return """
        <style>
        /* Chat Container */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
            min-height: 60vh;
        }
        
        /* Message Bubbles */
        .message-bubble {
            margin: 1rem 0;
            padding: 1rem 1.25rem;
            border-radius: 1.25rem;
            box-shadow: 0 2px 8px var(--shadow-color);
            animation: slideIn 0.3s ease-out;
            position: relative;
            word-wrap: break-word;
            max-width: 85%;
        }
        
        .user-message {
            background: linear-gradient(135deg, var(--user-msg-bg), color-mix(in srgb, var(--user-msg-bg) 90%, white));
            margin-left: auto;
            margin-right: 0;
            border-bottom-right-radius: 0.5rem;
            text-align: right;
        }
        
        .ai-message {
            background: linear-gradient(135deg, var(--ai-msg-bg), color-mix(in srgb, var(--ai-msg-bg) 95%, white));
            margin-left: 0;
            margin-right: auto;
            border-bottom-left-radius: 0.5rem;
        }
        
        /* Message Content */
        .message-role {
            font-weight: 600;
            font-size: 0.85rem;
            margin-bottom: 0.5rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .message-content {
            margin: 0;
            line-height: 1.6;
            font-size: 0.95rem;
        }
        
        .message-content p {
            margin: 0.5rem 0;
        }
        
        .message-content ul, .message-content ol {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        
        .message-content code {
            background-color: color-mix(in srgb, var(--border-color) 30%, transparent);
            padding: 0.2rem 0.4rem;
            border-radius: 0.3rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.85rem;
        }
        
        .message-content pre {
            background-color: var(--secondary-bg);
            padding: 1rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        
        /* Animations */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Typing Indicator */
        .typing-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .typing-dots {
            display: flex;
            gap: 0.25rem;
        }
        
        .typing-dot {
            width: 0.5rem;
            height: 0.5rem;
            background-color: var(--primary-color);
            border-radius: 50%;
            animation: typingBounce 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        .typing-dot:nth-child(3) { animation-delay: 0s; }
        
        @keyframes typingBounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }
        </style>
        """
    
    @staticmethod
    def generate_form_styles() -> str:
        """Generate form and input styles."""
        return """
        <style>
        /* Input Fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div > select {
            background-color: var(--secondary-bg) !important;
            color: var(--text-color) !important;
            border: 2px solid var(--border-color) !important;
            border-radius: 0.75rem !important;
            padding: 0.75rem 1rem !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
        }
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary-color) 20%, transparent) !important;
            outline: none !important;
        }
        
        /* Buttons */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color), color-mix(in srgb, var(--primary-color) 80%, black)) !important;
            color: white !important;
            border: none !important;
            border-radius: 0.75rem !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            cursor: pointer !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, var(--accent-color), color-mix(in srgb, var(--accent-color) 80%, black)) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px var(--shadow-color) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Secondary Buttons */
        .stButton > button[kind="secondary"] {
            background: transparent !important;
            color: var(--primary-color) !important;
            border: 2px solid var(--primary-color) !important;
        }
        
        .stButton > button[kind="secondary"]:hover {
            background: var(--primary-color) !important;
            color: white !important;
        }
        </style>
        """
    
    @staticmethod
    def generate_layout_styles() -> str:
        """Generate layout and component styles."""
        return """
        <style>
        /* Sidebar */
        .css-1d391kg {
            background-color: var(--secondary-bg) !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        /* Main content area */
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        /* Model Selector */
        .model-selector {
            background: linear-gradient(135deg, var(--secondary-bg), color-mix(in srgb, var(--secondary-bg) 95%, white));
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px var(--shadow-color);
        }
        
        .model-selector h4 {
            margin: 0 0 0.5rem 0;
            color: var(--primary-color);
            font-size: 1rem;
        }
        
        /* Status Indicators */
        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 2rem;
            font-size: 0.85rem;
            font-weight: 500;
            margin: 0.5rem 0;
        }
        
        .status-online {
            background-color: color-mix(in srgb, #4caf50 20%, transparent);
            color: #2e7d32;
            border: 1px solid color-mix(in srgb, #4caf50 40%, transparent);
        }
        
        .status-offline {
            background-color: color-mix(in srgb, #f44336 20%, transparent);
            color: #c62828;
            border: 1px solid color-mix(in srgb, #f44336 40%, transparent);
        }
        
        .status-loading {
            background-color: color-mix(in srgb, #ff9800 20%, transparent);
            color: #ef6c00;
            border: 1px solid color-mix(in srgb, #ff9800 40%, transparent);
        }
        
        .status-dot {
            width: 0.5rem;
            height: 0.5rem;
            border-radius: 50%;
            background-color: currentColor;
        }
        
        .status-loading .status-dot {
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Theme Toggle */
        .theme-toggle {
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 1000;
            background: var(--secondary-bg);
            border: 2px solid var(--border-color);
            border-radius: 50%;
            width: 3rem;
            height: 3rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 1.2rem;
            box-shadow: 0 2px 8px var(--shadow-color);
        }
        
        .theme-toggle:hover {
            background: var(--primary-color);
            color: white;
            transform: scale(1.1);
        }
        
        /* Cards and Containers */
        .info-card {
            background: var(--secondary-bg);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 8px var(--shadow-color);
        }
        
        .info-card h3 {
            margin: 0 0 1rem 0;
            color: var(--primary-color);
        }
        
        /* Welcome Message */
        .welcome-container {
            text-align: center;
            padding: 2rem;
            background: linear-gradient(135deg, var(--secondary-bg), color-mix(in srgb, var(--secondary-bg) 95%, var(--primary-color)));
            border-radius: 1.5rem;
            margin: 2rem 0;
            border: 1px solid var(--border-color);
        }
        
        .welcome-container h2 {
            color: var(--primary-color);
            margin-bottom: 1rem;
        }
        
        .welcome-container p {
            opacity: 0.8;
            line-height: 1.6;
        }
        </style>
        """
    
    @staticmethod
    def generate_responsive_styles() -> str:
        """Generate responsive design styles for different screen sizes."""
        return """
        <style>
        /* Responsive Design */
        
        /* Large screens (desktops) */
        @media (min-width: 1200px) {
            .chat-container {
                max-width: 900px;
            }
            
            .message-bubble {
                max-width: 80%;
            }
        }
        
        /* Medium screens (tablets) */
        @media (max-width: 1024px) {
            .chat-container {
                max-width: 100%;
                padding: 1rem;
            }
            
            .message-bubble {
                max-width: 90%;
                padding: 1rem;
            }
            
            .theme-toggle {
                width: 2.75rem;
                height: 2.75rem;
            }
        }
        
        /* Small screens (mobile landscape) */
        @media (max-width: 768px) {
            .chat-container {
                padding: 0.75rem;
            }
            
            .message-bubble {
                max-width: 95%;
                margin: 0.75rem 0;
                padding: 0.875rem 1rem;
                font-size: 0.9rem;
            }
            
            .user-message {
                margin-left: 1rem;
            }
            
            .ai-message {
                margin-right: 1rem;
            }
            
            .main .block-container {
                padding-top: 1rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            
            .model-selector {
                padding: 0.75rem;
                margin: 0.75rem 0;
            }
        }
        
        /* Extra small screens (mobile portrait) */
        @media (max-width: 480px) {
            .chat-container {
                padding: 0.5rem;
            }
            
            .message-bubble {
                max-width: 100%;
                margin: 0.5rem 0;
                padding: 0.75rem;
                font-size: 0.875rem;
            }
            
            .user-message {
                margin-left: 0.5rem;
            }
            
            .ai-message {
                margin-right: 0.5rem;
            }
            
            .message-role {
                font-size: 0.75rem;
            }
            
            .theme-toggle {
                width: 2.5rem;
                height: 2.5rem;
                top: 0.5rem;
                right: 0.5rem;
                font-size: 1rem;
            }
            
            .stButton > button {
                padding: 0.625rem 1rem !important;
                font-size: 0.875rem !important;
            }
            
            .stTextInput > div > div > input {
                font-size: 16px !important; /* Prevent zoom on iOS */
                padding: 0.625rem 0.875rem !important;
            }
            
            /* Stack columns on mobile */
            .stColumns > div {
                min-width: 100% !important;
                margin-bottom: 0.5rem;
            }
            
            /* Hide sidebar on mobile by default */
            .css-1d391kg {
                transform: translateX(-100%);
                transition: transform 0.3s ease;
            }
            
            .css-1d391kg.show {
                transform: translateX(0);
            }
        }
        
        /* High DPI displays */
        @media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
            .message-bubble {
                box-shadow: 0 1px 4px var(--shadow-color);
            }
            
            .stButton > button {
                box-shadow: 0 2px 6px var(--shadow-color);
            }
        }
        
        /* Dark mode specific responsive adjustments */
        @media (prefers-color-scheme: dark) {
            .message-bubble {
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
            }
        }
        
        /* Reduced motion preferences */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.01ms !important;
            }
        }
        
        /* High contrast mode */
        @media (prefers-contrast: high) {
            .message-bubble {
                border: 2px solid var(--border-color);
            }
            
            .stButton > button {
                border: 2px solid currentColor;
            }
        }
        </style>
        """
    
    @staticmethod
    def generate_accessibility_styles() -> str:
        """Generate accessibility-focused styles."""
        return """
        <style>
        /* Accessibility Improvements */
        
        /* Focus indicators */
        *:focus {
            outline: 2px solid var(--primary-color) !important;
            outline-offset: 2px !important;
        }
        
        /* Skip link for keyboard navigation */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--primary-color);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 1000;
        }
        
        .skip-link:focus {
            top: 6px;
        }
        
        /* Screen reader only content */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            .message-bubble {
                border: 2px solid;
            }
            
            .user-message {
                border-color: var(--primary-color);
            }
            
            .ai-message {
                border-color: var(--text-color);
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .message-bubble {
                animation: none;
            }
            
            .typing-dot {
                animation: none;
            }
            
            .theme-toggle:hover {
                transform: none;
            }
        }
        
        /* Large text support */
        @media (min-resolution: 120dpi) {
            .message-content {
                font-size: 1rem;
            }
            
            .message-role {
                font-size: 0.9rem;
            }
        }
        </style>
        """