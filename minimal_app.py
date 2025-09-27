"""
Minimal Streaming Chatbot
Simple, clean interface with visible streaming
"""

import streamlit as st
import time
from typing import Generator

# Import models
try:
    from models import ModelManager
except ImportError as e:
    st.error(f"Cannot import ModelManager: {e}")
    st.stop()

# Page config
st.set_page_config(
    page_title="Minimal Chat",
    page_icon="💬",
    layout="centered"
)

# Simple dark styling with pulsing pill indicator
st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: white;
}
.stChatMessage {
    background-color: #262730;
    border-radius: 10px;
    padding: 10px;
    margin: 5px 0;
}
.streaming-indicator {
    font-size: 1.5rem;
    animation: pill-pulse 1.5s ease-in-out infinite;
    display: inline-block;
}
@keyframes pill-pulse {
    0%, 100% { 
        opacity: 0.4;
        transform: scale(1);
    }
    50% { 
        opacity: 1;
        transform: scale(1.1);
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize
if 'model_manager' not in st.session_state:
    st.session_state.model_manager = ModelManager()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Title
st.title("💬 Minimal Streaming Chat")

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate response with pill cursor streaming
    def stream_response() -> Generator[str, None, None]:
        """Streaming generator with pill emoji cursor"""
        # Get full response first
        full_response = st.session_state.model_manager.generate_response(
            message=prompt,
            stream=False
        )
        
        # Build response progressively with pill cursor
        current_text = ""
        for i, char in enumerate(full_response):
            current_text += char
            # Show current text with pill cursor (except for last character)
            if i < len(full_response) - 1:
                yield current_text + "💊"
            else:
                yield current_text
            time.sleep(0.02)
    
    # Display streaming response with pill cursor
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response())
    
    # Save response
    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})