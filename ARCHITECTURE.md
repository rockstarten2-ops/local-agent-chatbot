# Local Agent Chatbot - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SINGLE PAGE APP (Streamlit)              │
│                   streamlit_app.py                          │
│                                                              │
│  • File Upload Interface                                     │
│  • Agent Management                                          │
│  • Search Query Input                                        │
│  • Results Display                                           │
│  • Chat History                                              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests/JSON
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (backend.py)                   │
│                                                              │
│  Routes (Agents/routes/agent_router.py)                     │
│  ├── POST /api/agents/upload                                │
│  ├── POST /api/agents/search/{collection}                   │
│  ├── GET /api/agents/agents                                 │
│  ├── GET /api/agents/agent-info/{collection}                │
│  └── DELETE /api/agents/agent/{collection}                  │
└─────────────────┬──────────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
┌──────────────────┐  ┌──────────────────────┐
│  API Factories   │  │  Service Layer       │
│  (Agents/apis)   │  │                      │
│                  │  │  • FileProcessor     │
│ • TextAPI        │  │  • DocumentParsers   │
│ • PDFAPI         │  │  • AgentFactory      │
│ • CSVAPI         │  │  • SemanticSearch    │
│ • JSONAPI        │  │  • ChromaVectorStore │
│ • MarkdownAPI    │  │                      │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
        ┌────────────────────────────┐
        │   ChromaDB Vector Store    │
        │   (data/chroma_db)         │
        │                            │
        │  Collections:              │
        │  • semantic_search_txts    │
        │  • semantic_search_pdfs    │
        │  • semantic_search_csvs    │
        │  • semantic_search_jsons   │
        │  • semantic_search_mds     │
        └────────────────────────────┘
```

## 📊 Data Flow

### Upload Flow
```
User Upload → FileProcessor → DocumentParsers → Chunking → AgentFactory → 
ChromaDB Vector Store → Collection Created
```

### Search Flow
```
Search Query → Agent API → SemanticSearch → ChromaDB Query → 
Results + LLM Response → JSON Response → UI Display
```

## 🔄 Agent Lifecycle

### 1. File Upload
- User selects file via Streamlit
- File sent to backend via `/api/agents/upload`

### 2. File Processing
- FileProcessor validates file
- Appropriate Parser selected based on extension
- Document parsed into chunks

### 3. Agent Creation
- AgentFactory creates agent with unique collection name
- ChromaDB collection created
- Chunks indexed with embeddings

### 4. Search Operations
- Query receives through API
- SemanticSearch agent performs vector search
- (Optional) LLM generates response using context
- Results returned to UI

### 5. Agent Cleanup
- Agent deleted via `/api/agents/agent/{collection_name}`
- ChromaDB collection removed
- Agent instance deleted from memory

## 📦 Module Organization

```
Agents/
├── config.py                      # Global configuration
├── services/
│   ├── chroma_vector_store.py     # ChromaDB wrapper
│   ├── document_parsers.py        # File type parsers
│   ├── file_processor.py          # File chunking
│   ├── semantic_search.py         # Search agent
│   └── agent_factory.py           # Agent creation
├── apis/
│   ├── base_api.py                # Base class
│   ├── text_agent_api.py          # Text-specific API
│   ├── pdf_agent_api.py           # PDF-specific API
│   ├── csv_agent_api.py           # CSV-specific API
│   ├── json_agent_api.py          # JSON-specific API
│   ├── markdown_agent_api.py      # Markdown-specific API
│   └── agent_api_factory.py       # API factory
└── routes/
    └── agent_router.py            # FastAPI routes
```

## 🎯 Key Features

### 1. Multi-File Type Support
- PDF: Page-aware extraction
- JSON: Nested structure handling
- CSV: Row-based semantic search
- TXT: Full document search
- Markdown: Section-aware extraction

### 2. Semantic Search
- Uses sentence-transformers for embeddings
- ChromaDB for vector similarity
- Configurable chunk size and overlap

### 3. LLM Integration
- Uses local LLM Studio server
- Context-aware question answering
- Configurable temperature and token limits

### 4. Session Management
- Unique collections per uploaded file
- In-memory agent tracking
- Chat history per collection

## 🔌 API Request/Response Examples

### Upload File
```
POST /api/agents/upload
Content-Type: multipart/form-data

file: <binary>

Response:
{
  "collection_name": "semantic_search_txt_sample_txt",
  "file_type": "txt",
  "filename": "sample.txt",
  "chunks_count": 10,
  "message": "File uploaded successfully..."
}
```

### Search
```
POST /api/agents/search/semantic_search_txt_sample_txt
Content-Type: application/json

{
  "query": "What is in this document?",
  "use_llm": true,
  "top_k": 5
}

Response:
{
  "query": "What is in this document?",
  "search_results": [
    {
      "rank": 1,
      "content": "...",
      "similarity": 0.95,
      "metadata": {...}
    }
  ],
  "llm_response": "Based on the document...",
  "total_sources": 5,
  "agent_type": "txt"
}
```

## 🚀 Performance Considerations

### Chunking
- Default: 500 tokens per chunk, 50 token overlap
- Smaller chunks: Better precision
- Larger chunks: Better context retention

### Embedding Model
- Default: all-MiniLM-L6-v2 (22MB)
- Fast inference, good for semantic search
- Alternative: larger models for better accuracy

### ChromaDB
- In-memory + persistent storage
- Cosine distance for similarity
- Automatic HNSW indexing

### LLM Integration
- Optional: can search without LLM
- Context-aware responses
- Configurable max tokens

## 🛠️ Configuration Points

Edit `Agents/config.py`:
```python
CHUNK_SIZE = 500              # Document chunk size
CHUNK_OVERLAP = 50            # Overlap between chunks
CHROMA_EMBEDDING_MODEL = "..."# Embedding model
LLM_SERVER_URL = "..."        # Your LM Studio URL
LLM_MODEL = "..."             # Model name
API_PORT = 8000               # API port
```

## 📈 Scalability

### Current Design
- Single-process backend
- In-memory agent storage
- Local ChromaDB

### Future Enhancements
- Distributed processing
- Redis backend for session management
- PostgreSQL for metadata
- Elasticsearch for large-scale search
