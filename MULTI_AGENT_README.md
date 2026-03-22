# Multi-Agent Document Chat System

A modern, intelligent document chat system with 3 specialized agents working together to answer your questions effectively.

## Architecture

### Three Intelligent Agents

1. **Query Router (Main Agent)**
   - Analyzes incoming queries
   - Determines relevance to loaded documents
   - Routes to appropriate secondary agent
   - Handles edge cases and fallbacks

2. **Document Retriever Agent**
   - Searches documents using semantic similarity
   - Returns relevant chunks with similarity scores
   - Generates answers based on document content
   - Best for: Specific information, fact-finding, topic searches

3. **Summarizer Agent**
   - Generates concise summaries of documents
   - Extracts key points and main ideas
   - Uses LLM for synthesis
   - Best for: Quick overviews, understanding content at a glance

4. **General LLM Agent** (Fallback)
   - Answers general knowledge questions
   - Used when query isn't related to documents
   - Provides standalone responses
   - Best for: General knowledge, creative tasks, explanations

## Smart Query Routing

The system intelligently determines how to answer your question:

```
User Query
    ↓
[Query Router]
    ├─ Documents loaded?
    │   ├─ No → [General LLM Agent]
    │   └─ Yes ↓
    │
    └─ Query relevant to documents?
        ├─ No → [General LLM Agent]
        └─ Yes ↓
        
    ├─ Summarization request?
    │   ├─ Yes → [Summarizer Agent] (retrieves many chunks)
    │   └─ No → [Document Retriever Agent] (targeted search)
    │
    └─ [Generate Answer] → Return to User
```

## File Structure

```
local-agent-chatbot/
├── index.html              # Web UI
├── style.css              # Styling
├── script.js              # Frontend logic
├── backend.py             # FastAPI server
├── Agents/
│   ├── services/
│   │   ├── multi_agent_router.py    # Agent routing logic ⭐ NEW
│   │   ├── agent_factory.py
│   │   ├── semantic_search.py
│   │   └── ...
│   ├── routes/
│   │   └── agent_router.py   # API endpoints (with /query endpoint) ⭐ UPDATED
│   └── ...
├── data/
│   └── chroma_db/          # Document embeddings
└── ...
```

## Getting Started

### 1. Start the Backend
```bash
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### 2. Open the Web UI
Navigate to `http://localhost:8000` in your browser

### 3. Upload Documents
- Click the upload area or drag files
- Supported: PDF, TXT, CSV, JSON, Markdown

### 4. Ask Questions
- Ask about your documents (will use Document Retriever)
- Ask for summaries (will use Summarizer)
- Ask general questions (will use General LLM)

## API Endpoints

### Core Endpoints

- `POST /api/agents/upload` - Upload a document
- `GET /api/agents` - List loaded documents
- `DELETE /api/agents/agent/{collection_name}` - Delete a document

### Smart Query Endpoint ⭐

```bash
POST /api/agents/query

{
    "query": "Your question here",
    "use_llm": true
}

Response:
{
    "success": true,
    "agent": "document_retriever|summarizer|general_llm",
    "answer": "The answer...",
    "results": [...],
    "routing": {
        "agent": "document_retriever",
        "should_search": true,
        ...
    }
}
```

## Example Queries

### For Document Retriever
- "What are the key safety features?"
- "How do I charge the battery?"
- "Find information about installation"

### For Summarizer
- "Summarize this document"
- "Give me an overview"
- "What are the main points?"

### For General LLM
- "What is machine learning?"
- "Explain quantum computing"
- "How do I cook pasta?"

## Key Features

✅ **Intelligent Routing** - Automatically chooses the best agent
✅ **No Nested Searches** - Flat data flow, no UI nesting issues
✅ **Clean API** - Simple `/query` endpoint handles everything
✅ **Smart Context** - Limits context to what's actually needed
✅ **Source Attribution** - Shows which documents provided answers
✅ **Modern UI** - Clean, responsive HTML/CSS interface
✅ **Drag & Drop** - Easy file uploading

## Configuration

### LLM Server
Edit `Agents/config.py`:
```python
LLM_SERVER_URL = "http://localhost:1234"  # Your local LLM
```

### Backend Port
Edit `Agents/config.py`:
```python
API_PORT = 8000
API_HOST = "0.0.0.0"
```

## Troubleshooting

### Query not using documents?
- Ensure documents are uploaded (check sidebar)
- Try different phrasing
- Check backend logs for routing decisions

### Documents not loading?
```bash
# Check backend logs
curl http://localhost:8000/health

# List agents
curl http://localhost:8000/api/agents
```

### LLM integration issues?
- Verify LLM server is running
- Check `LLM_SERVER_URL` in config
- Test with curl:
  ```bash
  curl -X POST http://localhost:1234/v1/chat/completions \
    -H "Content-Type: application/json" \
    -d '{"model":"local-model","messages":[{"role":"user","content":"test"}]}'
  ```

## Performance Tips

1. **Chunk Size** - Larger chunks = less context but more relevant results
2. **Top-K** - Retriever uses `top_k=5`, Summarizer uses `top_k=10`
3. **Similarity Threshold** - Results below 0.2 similarity are filtered
4. **Context Limit** - Max 3 chunks used for answer generation

## Future Enhancements

- [ ] Multi-turn conversations
- [ ] Document versioning
- [ ] Query caching & history
- [ ] Advanced analytics
- [ ] Custom agent creation
- [ ] Batch processing

## Support

For issues or questions, check the logs:
```bash
# Backend logs show routing decisions
# Frontend console (F12) shows API responses
```
