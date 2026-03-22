import streamlit as st
import requests
import json
from datetime import datetime
from pathlib import Path

# Configuration
LLM_SERVER_URL = "https://medium-helps-justin-hub.trycloudflare.com"
BACKEND_API_URL = "http://localhost:8000/api/agents"

# Helper function
def generate_llm_response(query: str, context: str) -> str:
    """Generate LLM response using context."""
    try:
        prompt = f"""Based on the following context from documents, answer the question concisely and accurately.

Context:
{context}

Question: {query}

Answer:"""
        
        response = requests.post(
            f"{LLM_SERVER_URL}/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that answers questions based on provided document context. Be concise and accurate."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 512,
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
    except Exception as e:
        return f"⚠️ Could not generate AI response: {str(e)}"

# Page configuration
st.set_page_config(
    page_title="AI Chat with Document Search",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better chat UI
st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 2rem;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "files_processed" not in st.session_state:
    st.session_state.files_processed = []

# Page Title
st.title("💬 AI Chat Assistant")
st.caption("Chat with AI • Upload documents • Semantic search")

# Sidebar for agent management
with st.sidebar:
    st.header("📚 Loaded Documents")
    
    if st.session_state.agents:
        for collection_name, agent_info in st.session_state.agents.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {agent_info['name']}")
                st.caption(f"Type: {agent_info['type'].upper()} | Chunks: {agent_info['chunks']}")
            with col2:
                if st.button("❌", key=f"delete_{collection_name}", help="Delete this document"):
                    try:
                        requests.delete(f"{BACKEND_API_URL}/agent/{collection_name}")
                        del st.session_state.agents[collection_name]
                        st.rerun()
                    except:
                        st.error("Failed to delete")
            st.divider()
        
        if st.button("🗑️ Clear All Documents", use_container_width=True):
            try:
                requests.post(f"{BACKEND_API_URL}/clear-all")
                st.session_state.agents = {}
                st.session_state.messages = []
                st.rerun()
            except:
                st.error("Failed to clear")
    else:
        st.info("📭 No documents loaded\nUpload files in chat to get started!")

# Main chat area
st.markdown("---")

# Display chat messages
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])
            if "file_info" in message:
                st.caption(f"📤 Uploaded: {message['file_info']}")
    else:
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message["content"])

# Chat input area with file upload
col1, col2 = st.columns([0.9, 0.1])

with col2:
    # File upload button (+ icon)
    uploaded_file = st.file_uploader(
        "Upload file",
        type=["txt", "pdf", "csv", "json", "md"],
        label_visibility="collapsed",
        key=f"uploader_{len(st.session_state.messages)}"
    )
    
    if uploaded_file is not None:
        # Process file upload
        with st.spinner("🔄 Processing file..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(f"{BACKEND_API_URL}/upload", files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    collection_name = data['collection_name']
                    file_type = data['file_type']
                    chunks_count = data['chunks_count']
                    
                    # Store agent info
                    st.session_state.agents[collection_name] = {
                        "name": uploaded_file.name,
                        "type": file_type,
                        "chunks": chunks_count
                    }
                    
                    # Add to chat history
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"📤 Uploaded file: {uploaded_file.name}",
                        "file_info": f"{uploaded_file.name} ({file_type.upper()}) - {chunks_count} chunks"
                    })
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"✅ **{uploaded_file.name}** loaded successfully!\n\n"
                                 f"📊 Details:\n"
                                 f"- Type: {file_type.upper()}\n"
                                 f"- Chunks: {chunks_count}\n"
                                 f"- Agent: **{file_type.capitalize()} Agent**\n\n"
                                 f"💬 You can now ask questions about this document!"
                    })
                    
                    st.rerun()
                else:
                    st.error(f"❌ Upload failed: {response.json()['detail']}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}\n\nMake sure the backend is running:\n`python -m uvicorn backend:app --reload`")

with col1:
    # Chat input
    user_input = st.chat_input("Ask me anything or upload a file...")
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)
        
        # Initialize response text
        response_text = ""
        
        # Process query
        with st.chat_message("assistant", avatar="🤖"):
            # If no agents loaded, provide guidance
            if not st.session_state.agents:
                response_text = ("👋 Hello! I'm your AI assistant. To get started, please:\n\n"
                               "1. **Upload a document** using the **+** button below\n"
                               "2. Supported formats: PDF, TXT, CSV, JSON, Markdown\n"
                               "3. After uploading, I can answer questions about the document!\n\n"
                               "📝 Once you upload a file, your questions will be answered using semantic search.")
                st.write(response_text)
            else:
                # Search across all loaded agents
                with st.spinner("🔍 Searching documents..."):
                    try:
                        all_results = []
                        
                        # Search each agent
                        for collection_name, agent_info in st.session_state.agents.items():
                            payload = {
                                "query": user_input,
                                "use_llm": False,  # We'll use LLM once for final answer
                                "top_k": 3
                            }
                            
                            response = requests.post(
                                f"{BACKEND_API_URL}/search/{collection_name}",
                                json=payload
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                if data.get("search_results"):
                                    for result in data["search_results"]:
                                        all_results.append({
                                            "document": agent_info["name"],
                                            "content": result["content"],
                                            "similarity": result["similarity"]
                                        })
                        
                        # Sort by similarity
                        all_results.sort(key=lambda x: x["similarity"], reverse=True)
                        
                        if all_results:
                            # Build context from top results
                            context = "\n\n".join([
                                f"[{r['document']}] {r['content']}"
                                for r in all_results[:5]
                            ])
                            
                            # Generate LLM response with context
                            response_text = generate_llm_response(user_input, context)
                            
                            # Display response with sources
                            st.markdown(response_text)
                            
                            # Show sources
                            with st.expander("📚 Sources"):
                                for i, result in enumerate(all_results[:3], 1):
                                    st.caption(f"**{i}. {result['document']}** (Similarity: {result['similarity']:.0%})")
                                    st.text(result['content'][:200] + "...")
                        else:
                            response_text = "❓ No relevant information found in loaded documents. Try uploading more files or rephrase your question."
                            st.write(response_text)
                        
                    except Exception as e:
                        response_text = f"⚠️ Search error: {str(e)}"
                        st.error(response_text)
        
        # Add assistant response to history if we have one
        if response_text:
            st.session_state.messages.append({
                "role": "assistant",
                "content": response_text
            })

