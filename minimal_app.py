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
    
    # Generate response with smart streaming
    def stream_response() -> Generator[str, None, None]:
        """Smart streaming - faster for tables and long content"""
        # Get full response first
        full_response = st.session_state.model_manager.generate_response(
            message=prompt,
            stream=False
        )
        
        # Check if response contains tables or structured content
        has_table = '|' in full_response and '---' in full_response
        has_code = '```' in full_response
        
        if has_table or has_code or len(full_response) > 500:
            # Fast streaming for tables/code/long content - by chunks
            chunk_size = 50
            for i in range(0, len(full_response), chunk_size):
                chunk = full_response[i:i + chunk_size]
                yield chunk
                time.sleep(0.01)  # Faster for structured content
        else:
            # Normal streaming for regular text - by words
            words = full_response.split()
            for i, word in enumerate(words):
                if i == 0:
                    yield word
                else:
                    yield " " + word
                time.sleep(0.05)  # Moderate speed for readability
    
    # Display streaming response with pill cursor
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response())
    
    # Save response
    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})