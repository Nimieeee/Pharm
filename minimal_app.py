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

# Simple dark styling
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
    
    # Generate response with visible streaming
    def stream_response() -> Generator[str, None, None]:
        """Reliable streaming generator"""
        # Get full response first
        full_response = st.session_state.model_manager.generate_response(
            message=prompt,
            stream=False
        )
        
        # Stream character by character for smooth effect
        for i, char in enumerate(full_response):
            yield char
            if i % 3 == 0:  # Add delay every few characters
                time.sleep(0.02)
    
    # Display streaming response
    with st.chat_message("assistant"):
        response = st.write_stream(stream_response())
    
    # Save response
    if response:
        st.session_state.messages.append({"role": "assistant", "content": response})