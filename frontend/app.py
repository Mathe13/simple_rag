import streamlit as st
import requests
import os
import uuid

# Configuration
# BACKEND_API_URL is injected via docker-compose
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
SSO_URL = os.getenv("SSO_URL", "http://localhost:8001/sso/token")
CHAT_ENDPOINT = f"{BACKEND_API_URL}/api/chat"

# Page Configuration
st.set_page_config(
    page_title="HP Technical Support Agent",
    page_icon="💻",
    layout="centered"
)

st.title("💻 HP Technical Support Agent")
st.markdown("Ask me anything about hp products.")

# ==========================================
# Session State Initialization
# ==========================================
if "token" not in st.session_state:
    # Auto-login to SSO Mock on session start
    try:
        login_resp = requests.post(SSO_URL, json={"username": "tech-support-agent", "password": "password"})
        login_resp.raise_for_status()
        st.session_state.token = login_resp.json().get("access_token")
    except Exception as e:
        st.error(f"Failed to authenticate with Enterprise SSO: {e}")
        st.session_state.token = None

if "conversation_id" not in st.session_state:
    # Initially None, will be populated by the backend after the first message
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    # Start with a greeting from the AI
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! How can I help you with your HP devices today?"}
    ]

# ==========================================
# UI Rendering: Chat History
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# User Interaction
# ==========================================
if prompt := st.chat_input("Type your question here..."):
    # 1. Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call the FastAPI Backend
    with st.chat_message("assistant"):
        with st.spinner("Searching HP documentation..."):
            payload = {
                "conversation_id": st.session_state.conversation_id,
                "query": prompt
            }
            
            headers = {}
            if st.session_state.token:
                headers["Authorization"] = f"Bearer {st.session_state.token}"
            
            try:
                response = requests.post(CHAT_ENDPOINT, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                assistant_response = data.get("answer", "Error: No answer returned.")
                
                # Update the conversation ID if it was just created
                if not st.session_state.conversation_id:
                    st.session_state.conversation_id = data.get("conversation_id")
                    
                st.markdown(assistant_response)
                
                # Append assistant response to session state
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Failed to connect to the backend: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})