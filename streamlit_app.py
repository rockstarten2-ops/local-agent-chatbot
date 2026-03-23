import streamlit as st
import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
LLM_SERVER_URL = os.getenv("LLM_SERVER", "http://localhost:1234")
LLM_MODEL = os.getenv("LLM_MODEL", "local-model")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api/agents")

# Initialize session state FIRST - required by Streamlit before page config
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "files_processed" not in st.session_state:
    st.session_state.files_processed = []

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
                "model": LLM_MODEL,
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

def should_search_documents(query: str, loaded_documents: dict) -> bool:
    """Check if query should search documents. Always search when documents are loaded."""
    if not loaded_documents:
        return False
    
    # Simply return True if we have documents - let the semantic search 
    # and LLM decide relevance based on similarity scores
    return True

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

# Clean file upload section at top
st.markdown("### 📁 Upload Documents")
uploaded_file = st.file_uploader(
    "Select a file to analyze",
    type=["txt", "pdf", "csv", "json", "md"],
    label_visibility="collapsed",
    key="file_uploader"
)

if uploaded_file is not None:
    col_upload_status, col_upload_action = st.columns([3, 1])
    with col_upload_status:
        st.info(f"📄 Ready to upload: **{uploaded_file.name}**")
    with col_upload_action:
        if st.button("Upload", key="upload_button"):
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
                        st.error(f"❌ Upload failed: {response.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}\n\nMake sure the backend is running:\n`python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000`")

st.markdown("---")

# Chat input area
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
    retrieved_chunks = []
    
    # Process query
    with st.chat_message("assistant", avatar="🤖"):
        # If no agents loaded, provide guidance
        if not st.session_state.agents:
            response_text = ("👋 Hello! I'm your AI assistant. To get started, please:\n\n"
                           "1. **Upload a document** using the file upload above\n"
                           "2. Supported formats: PDF, TXT, CSV, JSON, Markdown\n"
                           "3. After uploading, I can answer questions about the document!\n\n"
                           "📝 Once you upload a file, your questions will be answered using semantic search.")
            st.write(response_text)
        else:
            # Search across all loaded agents
            with st.spinner("🔍 Searching documents..."):
                try:
                    all_results = []
                    search_debug_info = []
                    
                    # Search each agent
                    for collection_name, agent_info in st.session_state.agents.items():
                        payload = {
                            "query": user_input,
                            "use_llm": False,  # We'll use LLM once for final answer
                            "top_k": 5
                        }
                        
                        response = requests.post(
                            f"{BACKEND_API_URL}/search/{collection_name}",
                            json=payload,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            search_debug_info.append({
                                "file": agent_info["name"],
                                "results_found": len(data.get("search_results", [])),
                                "status": "✅ Found results" if data.get("search_results") else "⚠️ No results"
                            })
                            
                            if data.get("search_results"):
                                for result in data["search_results"]:
                                    all_results.append({
                                        "document": agent_info["name"],
                                        "content": result["content"],
                                        "similarity": result.get("similarity", 0),
                                        "metadata": result.get("metadata", {})
                                    })
                        else:
                            search_debug_info.append({
                                "file": agent_info["name"],
                                "results_found": 0,
                                "status": "❌ API error"
                            })
                    
                    # Sort by similarity
                    all_results.sort(key=lambda x: x["similarity"], reverse=True)
                    retrieved_chunks = all_results
                    
                    if all_results:
                        # Generate LLM response with context
                        context = "\n\n".join([
                            f"[{r['document']}] {r['content']}"
                            for r in all_results[:5]
                        ])
                        
                        response_text = generate_llm_response(user_input, context)
                        
                        st.markdown(response_text)
                        
                        # Show retrieved documents in dropdown with better formatting
                        with st.expander(f"📚 Retrieved Documents ({len(all_results)} chunks found)", expanded=False):
                            st.markdown("**Documents and chunks used for this answer:**")
                            st.divider()
                            
                            for i, result in enumerate(all_results[:10], 1):
                                # Document header with similarity score
                                col_header, col_score = st.columns([4, 1])
                                with col_header:
                                    st.markdown(f"**{i}. {result['document']}**")
                                    st.caption(f"🎯 Relevance: {result['similarity']:.1%}")
                                with col_score:
                                    st.metric("Score", f"{result['similarity']:.0%}", label_visibility="collapsed")
                                
                                # Content preview with expander
                                with st.expander("📋 View content"):
                                    st.markdown(result['content'])
                                    if result['metadata']:
                                        st.divider()
                                        st.caption("**Metadata:**")
                                        st.json(result['metadata'])
                                
                                st.divider()
                    else:
                        response_text = "❓ No relevant information found in loaded documents."
                        
                        st.error(response_text)
                        
                        # Show debug info in expander
                        with st.expander("🔍 Search Debug Info"):
                            st.write("**Search Results by Document:**")
                            for debug in search_debug_info:
                                st.write(f"- {debug['file']}: {debug['status']} ({debug['results_found']} chunks)")
                            
                            st.write("\n**Troubleshooting Tips:**")
                            tips = [
                                "1. Make sure documents are uploaded (check sidebar)",
                                "2. Try simpler, shorter queries",
                                "3. Check if backend is running: `curl http://localhost:8000/health`",
                                "4. Ensure ChromaDB is properly persisting data"
                            ]
                            for tip in tips:
                                st.write(tip)
                
                except Exception as e:
                    response_text = f"⚠️ Search error: {str(e)}"
                    
                    st.error(response_text)
                    
                    with st.expander("📋 Error Details"):
                        st.code(str(e))
    
    # Add assistant response to history if we have one
    if response_text:
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text
        })

