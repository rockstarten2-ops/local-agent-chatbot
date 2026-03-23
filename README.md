# 🤖 Local Agent Chatbot - Multi-Agent Semantic Search System

A comprehensive multi-agent system with ChromaDB vector store for semantic document search and analysis. Different agents are created for different file types (PDF, TXT, CSV, JSON, Markdown).

## 📋 Overview

This system provides:
- **Multi-Agent Architecture**: Different specialized agents for different file types
- **Query Router Modes**: All-doc summary, single-doc summary, chapter summary, and retrieval fallback
- **Semantic Search**: Vector-based search using ChromaDB with sentence-transformers
- **LLM Integration**: Question answering using your local LLM Studio server
- **Realtime Trace Streaming**: SSE timeline of routing and agent execution flow
- **File Upload Interface**: Easy upload and management of documents
- **REST API**: FastAPI backend for programmatic access
- **Vanilla Web UI + Streamlit UI**: Two client options

## 📁 Project Structure

```
local-agent-chatbot/
├── Agents/
│   ├── __init__.py
│   ├── config.py                 # Configuration for agents and vector store
│   ├── services/                 # Core services
│   │   ├── chroma_vector_store.py    # ChromaDB wrapper
│   │   ├── document_parsers.py       # File type parsers
│   │   ├── file_processor.py         # File processing and chunking
│   │   ├── semantic_search.py        # Semantic search agent
│   │   └── agent_factory.py          # Agent factory
│   ├── apis/                     # API layers for different file types
│   │   ├── base_api.py               # Base API class
│   │   ├── text_agent_api.py         # Text document API
│   │   ├── pdf_agent_api.py          # PDF document API
│   │   ├── csv_agent_api.py          # CSV data API
│   │   ├── json_agent_api.py         # JSON data API
│   │   ├── markdown_agent_api.py     # Markdown document API
│   │   └── agent_api_factory.py      # API factory
│   └── routes/
│       └── agent_router.py           # FastAPI routes
├── data/                         # Data directory (created at runtime)
│   ├── uploaded_files/          # Uploaded documents
│   └── chroma_db/               # ChromaDB vector store
├── streamlit_app.py             # Streamlit UI
├── backend.py                   # FastAPI backend server
├── requirements.txt             # Python dependencies
└── README.md                    # This file

```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure LM Studio / Qwen

Start LM Studio's local server and load your model (for example `qwen-3.5-vl-9b`) first.

Set environment variables before starting the app:

```bash
# macOS/Linux
export LLM_SERVER="http://localhost:1234"
export LLM_MODEL="qwen-3.5-vl-9b"
```

```powershell
# Windows PowerShell
$env:LLM_SERVER="http://localhost:1234"
$env:LLM_MODEL="qwen-3.5-vl-9b"
```

### 3. Start the Backend API

In terminal 1:

```bash
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Open the Vanilla Web UI (recommended)

Open `http://localhost:8000/static/index.html` in your browser.

This UI now includes:
- live SSE routing timeline,
- selected route badge,
- persisted query history.

### 5. Optional: Start the Streamlit UI

In terminal 2:

```bash
streamlit run streamlit_app.py
```

The Streamlit UI will be available at: http://localhost:8501

## 📄 Supported File Types

| Format | Agent | Features |
|--------|-------|----------|
| **TXT** | Text Agent | Full document search |
| **PDF** | PDF Agent | Page-aware extraction, multi-page analysis |
| **CSV** | CSV Agent | Row-level semantic search |
| **JSON** | JSON Agent | Nested structure search |
| **MD** | Markdown Agent | Section-aware extraction |

## 🔧 How It Works

### File Upload Flow

1. User uploads a document via Streamlit UI
2. File is processed based on its type
3. Document is parsed into semantic chunks
4. Agent is created with a dedicated ChromaDB collection
5. Chunks are indexed in the vector store

### Search Flow

1. User enters a search query
2. Query is sent to the appropriate agent API
3. ChromaDB performs semantic search (returns top-k similar chunks)
4. (Optional) LLM generates a response using search results as context
5. Results and response are displayed in UI

## 🔌 API Endpoints

### Agent Management

- `POST /api/agents/upload` - Upload and create an agent
- `GET /api/agents/agents` - List all active agents
- `GET /api/agents/agent-info/{collection_name}` - Get agent information
- `DELETE /api/agents/agent/{collection_name}` - Delete an agent
- `POST /api/agents/clear-all` - Clear all agents

### Search

- `POST /api/agents/search/{collection_name}` - Search with specific agent
  - Body: `{"query": "string", "use_llm": bool, "top_k": int}`
- `POST /api/agents/query` - Multi-agent query (JSON response)
- `POST /api/agents/query/stream` - Multi-agent query (SSE realtime events)
- `GET /api/agents/history` - Recent multi-agent traces and outputs

### System

- `GET /api/agents/supported-types` - Get supported file types
- `GET /api/agents/health` - Health check

## 💡 Example Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/agents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Search in a Document

```bash
curl -X POST "http://localhost:8000/api/agents/search/semantic_search_pdf_document_pdf" \
  -H "Content-Type: application/json" \
  -d {
    "query": "What is in this document?",
    "use_llm": true,
    "top_k": 5
  }
```

## 🎯 Agent Types

### TextAgentAPI
- **Purpose**: Search and analyze plain text documents
- **Capabilities**: Full semantic search, question answering
- **Ideal for**: Articles, notes, logs

### PDFAgentAPI
- **Purpose**: Extract and search PDF documents
- **Capabilities**: Page-aware extraction, multi-page analysis
- **Ideal for**: Reports, papers, books

### CSVAgentAPI
- **Purpose**: Search and analyze tabular data
- **Capabilities**: Row-level semantic matching
- **Ideal for**: Spreadsheets, data exports

### JSONAgentAPI
- **Purpose**: Search structured JSON data
- **Capabilities**: Nested structure search
- **Ideal for**: API responses, configuration files

### MarkdownAgentAPI
- **Purpose**: Search and analyze markdown documents
- **Capabilities**: Section-aware extraction
- **Ideal for**: Documentation, wikis, notes

## 🛠️ Configuration

Set these environment variables to customize runtime configuration:

```bash
LLM_SERVER=http://localhost:1234
LLM_MODEL=qwen-3.5-vl-9b
BACKEND_API_URL=http://localhost:8000/api/agents  # Streamlit client only
API_HOST=0.0.0.0
API_PORT=8000
```

## 📊 Performance Tips

1. **Chunk Size**: Larger chunks for broader context, smaller for precise matching
2. **Embedding Model**: Lighter models (MiniLM) for speed, larger for accuracy
3. **Top-K Results**: Increase for more results, useful for LLM context
4. **LLM Temperature**: 0.1-0.3 for precise answers, 0.7+ for creative responses

## 🐛 Troubleshooting

### Backend Won't Start
- Check if port 8000 is in use: `lsof -i :8000`
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Streamlit Won't Connect to Backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check BACKEND_API_URL in streamlit_app.py

### PDF Parsing Issues
- Ensure PyPDF2 is installed: `pip install PyPDF2`
- Check PDF file is not encrypted

### ChromaDB Issues
- Delete the `data/chroma_db/` directory to reset: `rm -rf data/chroma_db/`
- Ensure write permissions in the data directory

## 📝 License

Open source - feel free to use and modify!

## 🚀 Future Enhancements

- [ ] Support for additional file types (DOCX, PPTX, EPUB)
- [ ] Advanced filtering and metadata search
- [ ] Document versioning and tracking
- [ ] Multi-document cross-search
- [ ] Export search results
- [ ] Batch file upload
- [ ] Advanced analytics and usage statistics
