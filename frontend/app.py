import streamlit as st
import requests
import os
import uuid

# Configuration
# BACKEND_API_URL is injected via docker-compose
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
SSO_URL = os.getenv("SSO_URL", "http://localhost:8001/sso/token")
CHAT_ENDPOINT = f"{BACKEND_API_URL}/api/chat"

def fetch_conversations(token):
    try:
        resp = requests.get(f"{BACKEND_API_URL}/api/conversations", headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

def fetch_messages(token, conv_id):
    try:
        resp = requests.get(f"{BACKEND_API_URL}/api/conversations/{conv_id}/messages", headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

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
    st.session_state.token = None

if not st.session_state.token:
    st.subheader("Login to Access the Agent")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.warning("Please enter both username and password.")
            else:
                try:
                    login_resp = requests.post(SSO_URL, json={"username": username, "password": password})
                    login_resp.raise_for_status()
                    st.session_state.token = login_resp.json().get("access_token")
                    st.rerun()
                except Exception as e:
                    st.error(f"Authentication failed. Please check your credentials and try again.")
    
    # Halt execution here if not logged in so we don't render the chat UI
    st.stop()
    
# User is logged in, show logout button in sidebar
with st.sidebar:
    st.header("Chat History")
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your HP devices today?"}]
        st.rerun()
        
    st.divider()
    
    # Render past conversations
    conversations = fetch_conversations(st.session_state.token)
    if not conversations:
        st.info("No past chats.")
    else:
        for conv in conversations:
            # Format datetime or fallback to ID
            created = conv.get("created_at", "")[:10]
            label = f"Chat {conv['id'][:8]} ({created})"
            if st.button(label, key=conv['id'], use_container_width=True):
                st.session_state.conversation_id = conv['id']
                msgs = fetch_messages(st.session_state.token, conv['id'])
                if msgs:
                    st.session_state.messages = [
                        {"role": m["role"], "content": m["content"]} for m in msgs
                    ]
                else:
                    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you with your HP devices today?"}]
                st.rerun()
                
    st.divider()
    
    if st.button("Logout", type="primary", use_container_width=True):
        st.session_state.token = None
        st.session_state.conversation_id = None
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! How can I help you with your HP devices today?"}
        ]
        st.rerun()

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