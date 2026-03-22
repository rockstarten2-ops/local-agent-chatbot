import streamlit as st
import requests
import json

# Configuration
LLM_SERVER_URL = "https://medium-helps-justin-hub.trycloudflare.com"
API_ENDPOINT = f"{LLM_SERVER_URL}/v1/chat/completions"

# Page configuration
st.set_page_config(
    page_title="LM Studio Chatbot",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.title("🤖 LM Studio Chatbot")
st.markdown("Chat with Gemma 3.1B powered by LM Studio")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function to get response from LM Studio
def get_llm_response(user_message):
    """Send message to LM Studio and get response"""
    try:
        # Prepare the conversation history for the API
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.messages
        ]
        messages.append({"role": "user", "content": user_message})
        
        # Make request to LM Studio
        response = requests.post(
            API_ENDPOINT,
            json={
                "model": "local-model",  # LM Studio uses this generic name
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 512,
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Extract the assistant's response
        assistant_message = data["choices"][0]["message"]["content"]
        return assistant_message
        
    except requests.exceptions.ConnectionError:
        return "❌ Connection Error: Unable to connect to LM Studio server. Make sure it's running at " + LLM_SERVER_URL
    except requests.exceptions.Timeout:
        return "❌ Timeout: The LM Studio server took too long to respond."
    except requests.exceptions.HTTPError as e:
        return f"❌ HTTP Error: {e.response.status_code} - {e.response.text}"
    except json.JSONDecodeError:
        return "❌ Error: Invalid response from LM Studio server."
    except KeyError:
        return "❌ Error: Unexpected response format from LM Studio server."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_llm_response(prompt)
        st.write(response)
    
    # Add assistant response to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

# Sidebar controls
with st.sidebar:
    st.markdown("### Controls")
    if st.button("🔄 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Server Info")
    st.code(f"Server: {LLM_SERVER_URL}\nModel: Gemma 3.1B", language="text")

