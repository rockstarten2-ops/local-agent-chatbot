import streamlit as st
import requests
import json
import io
from pathlib import Path

# Configuration
LLM_SERVER_URL = "https://medium-helps-justin-hub.trycloudflare.com"
BACKEND_API_URL = "http://localhost:8000/api/agents"

# Page configuration
st.set_page_config(
    page_title="Multi-Agent Document Search",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Multi-Agent Document Search System")
st.markdown("Upload documents and chat using semantic search with ChromaDB")

# Initialize session state
if "agents" not in st.session_state:
    st.session_state.agents = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None

# ============================================================================
# SIDEBAR - AGENT MANAGEMENT
# ============================================================================

with st.sidebar:
    st.header("📁 Agent Management")
    
    # File upload
    st.subheader("Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a file to analyze",
        type=["txt", "pdf", "csv", "json", "md"],
        help="Supported formats: TXT, PDF, CSV, JSON, Markdown"
    )
    
    if uploaded_file is not None:
        if st.button("📤 Upload and Create Agent", use_container_width=True):
            with st.spinner("Processing file..."):
                try:
                    # Upload file to backend
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(f"{BACKEND_API_URL}/upload", files=files)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.agents[data['collection_name']] = {
                            "name": uploaded_file.name,
                            "type": data['file_type'],
                            "chunks": data['chunks_count']
                        }
                        st.session_state.current_agent = data['collection_name']
                        st.success(f"✅ Agent created! Processed {data['chunks_count']} chunks")
                        st.rerun()
                    else:
                        st.error(f"❌ Upload failed: {response.json()}")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    # Agent selection
    if st.session_state.agents:
        st.divider()
        st.subheader("Active Agents")
        
        agent_names = list(st.session_state.agents.keys())
        display_names = [
            f"{st.session_state.agents[a]['name']} ({st.session_state.agents[a]['type'].upper()})"
            for a in agent_names
        ]
        
        selected_idx = st.selectbox(
            "Select agent",
            range(len(agent_names)),
            format_func=lambda i: display_names[i],
            key="agent_selector"
        )
        
        st.session_state.current_agent = agent_names[selected_idx]
        
        # Display agent info
        agent_name = st.session_state.current_agent
        agent_info = st.session_state.agents[agent_name]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", agent_info['type'].upper())
        with col2:
            st.metric("Chunks", agent_info['chunks'])
        with col3:
            st.metric("File", agent_info['name'].split('/')[-1][:15])
        
        # Delete agent
        if st.button("🗑️ Delete Agent", use_container_width=True, type="secondary"):
            try:
                response = requests.delete(f"{BACKEND_API_URL}/agent/{agent_name}")
                if response.status_code == 200:
                    del st.session_state.agents[agent_name]
                    if st.session_state.current_agent == agent_name:
                        st.session_state.current_agent = None
                    st.success("✅ Agent deleted")
                    st.rerun()
                else:
                    st.error("❌ Failed to delete agent")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    
    # Clear all
    if st.button("🔄 Clear All Agents", use_container_width=True, type="secondary"):
        try:
            response = requests.post(f"{BACKEND_API_URL}/clear-all")
            if response.status_code == 200:
                st.session_state.agents = {}
                st.session_state.current_agent = None
                st.session_state.chat_history = {}
                st.success("✅ All agents cleared")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ============================================================================
# MAIN CONTENT
# ============================================================================

if st.session_state.current_agent:
    agent_name = st.session_state.current_agent
    agent_info = st.session_state.agents[agent_name]
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"🔍 Searching: {agent_info['name']}")
    with col2:
        st.caption(f"Type: {agent_info['type'].upper()}")
    
    # Chat area
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown("### Search Results")
        
        # Search input
        query = st.text_input(
            "Enter your search query",
            placeholder="What would you like to know?",
            key=f"search_{agent_name}"
        )
        
        search_options = st.columns([1, 1])
        with search_options[0]:
            use_llm = st.checkbox("Use LLM", value=True, help="Generate AI response from search results")
        
        if query:
            if st.button("🔎 Search", use_container_width=True, type="primary"):
                with st.spinner("Searching..."):
                    try:
                        payload = {
                            "query": query,
                            "use_llm": use_llm,
                            "top_k": 5
                        }
                        response = requests.post(
                            f"{BACKEND_API_URL}/search/{agent_name}",
                            json=payload
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            
                            # Store in chat history
                            if agent_name not in st.session_state.chat_history:
                                st.session_state.chat_history[agent_name] = []
                            
                            st.session_state.chat_history[agent_name].append({
                                "query": query,
                                "result": result
                            })
                            
                            # Display search results
                            if "search_results" in result and result["search_results"]:
                                st.success(f"✅ Found {len(result['search_results'])} relevant results")
                                
                                for i, item in enumerate(result["search_results"], 1):
                                    with st.expander(f"📄 Result {i} (Similarity: {item['similarity']:.2%})"):
                                        st.write(item['content'])
                                        if item['metadata']:
                                            st.caption(f"Metadata: {item['metadata']}")
                            
                            # Display LLM response
                            if use_llm and "llm_response" in result:
                                st.divider()
                                st.markdown("### 🤖 AI Response")
                                st.info(result['llm_response'])
                        else:
                            st.error(f"❌ Search failed: {response.json()}")
                            
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with col_right:
        st.markdown("### 📋 Chat History")
        
        if agent_name in st.session_state.chat_history:
            history = st.session_state.chat_history[agent_name]
            
            if history:
                for i, item in enumerate(reversed(history), 1):
                    with st.expander(f"Query {len(history) - i + 1}: {item['query'][:50]}..."):
                        st.write(f"**Query:** {item['query']}")
                        st.divider()
                        
                        if "search_results" in item["result"]:
                            st.write(f"**Found:** {len(item['result']['search_results'])} results")
                        
                        if "llm_response" in item["result"]:
                            st.write(f"**Response:** {item['result']['llm_response']}")
                
                if st.button("🗑️ Clear History", use_container_width=True, type="secondary"):
                    st.session_state.chat_history[agent_name] = []
                    st.rerun()
            else:
                st.info("No search history yet")
        else:
            st.info("No search history yet")

else:
    st.info(
        "👈 **Get started by uploading a document in the sidebar!**\n\n"
        "Supported formats:\n"
        "- 📄 **TXT**: Plain text documents\n"
        "- 📕 **PDF**: PDF documents\n"
        "- 📊 **CSV**: Spreadsheet data\n"
        "- 📦 **JSON**: Structured data\n"
        "- 📝 **MD**: Markdown documents"
    )

