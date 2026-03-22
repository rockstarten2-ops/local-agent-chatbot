# 🚀 Quick Start Guide

Get up and running with the Local Agent Chatbot in 5 minutes!

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements.txt
```

### Step 2: Start Backend (1 min)

```bash
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
Uvicorn running on http://0.0.0.0:8000
Press CTRL+C to quit
```

### Step 3: Start Streamlit (in new terminal, 1 min)

```bash
streamlit run streamlit_app.py
```

You should see:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

### Step 4: Open UI (1 min)

Visit: **http://localhost:8501** in your browser

### Step 5: Upload and Search (1 min)

1. Use the sidebar to upload a document (TXT, PDF, CSV, JSON, or MD)
2. Wait for the agent to be created
3. Enter a search query in the main area
4. Toggle "Use LLM" to get AI-powered answers
5. View search results and chat history

## 📚 Full Setup with One Command

For bash/zsh:
```bash
chmod +x start.sh && ./start.sh
```

This will:
- Install dependencies
- Create data directories  
- Start backend on port 8000
- Start Streamlit UI
- Keep both running

Press Ctrl+C to stop.

## 🧪 Test the System

In a third terminal, run the example:
```bash
python example_usage.py
```

This demonstrates:
- Uploading files
- Creating agents
- Searching documents
- Listing active agents

## 📝 Create Sample Files to Test

### Sample Text File
```bash
cat > sample.txt << 'EOF'
The Local Agent Chatbot system uses ChromaDB for semantic search.
It supports multiple file types including text, PDF, CSV, and JSON.
Each file type has a specialized agent optimized for that format.
EOF
```

### Sample JSON File
```bash
cat > sample.json << 'EOF'
{
  "name": "Local Agent Chatbot",
  "version": "1.0.0",
  "features": ["semantic search", "multi-agent", "file upload"],
  "supported_types": ["txt", "pdf", "csv", "json", "md"]
}
EOF
```

### Sample CSV File
```bash
cat > sample.csv << 'EOF'
Name,Topic,Status
Document1,ML,complete
Document2,AI,active
Document3,GenAI,planned
EOF
```

Then upload these in the UI!

## 🔍 Understanding File Collections

When you upload a file, the system:

1. **Detects file type** → Selects appropriate parser
2. **Parses document** → Extracts meaningful content
3. **Creates chunks** → Splits into 500-token pieces with 50-token overlap
4. **Embeds chunks** → Uses sentence-transformers
5. **Stores in ChromaDB** → Creates searchable collection

Example collection name: `semantic_search_txt_sample_txt`

## 📊 Search Examples

### Basic Search
```
Query: "What is in the document?"
Returns: Top 5 most similar chunks with similarity scores
```

### LLM-Enhanced Search
```
Query: "Summarize the main points"
Returns: 
- Top 5 chunks (with similarity)
- AI-generated summary using those chunks as context
```

### Type-Specific Search
```
CSV: "Show me active projects" → Searches row-by-row content
JSON: "Find all API endpoints" → Searches nested structures
PDF: "What's on page 3?" → Page-aware extraction
```

## 🛠️ Common Tasks

### View API Documentation
Visit: http://localhost:8000/docs

Interactive Swagger documentation for all endpoints.

### List All Active Agents
```bash
curl http://localhost:8000/api/agents/agents
```

### Delete an Agent
```bash
curl -X DELETE http://localhost:8000/api/agents/agent/COLLECTION_NAME
```

### Clear All Agents
```bash
curl -X POST http://localhost:8000/api/agents/clear-all
```

### Check API Health
```bash
curl http://localhost:8000/health
```

## 🐛 Quick Troubleshooting

### Port Already in Use
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process (if needed)
kill -9 PID
```

### Dependencies Error
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

### ChromaDB Issues
```bash
# Reset database (WARNING: deletes all data)
rm -rf data/chroma_db/
```

### Streamlit Connection Error
- Make sure backend is running on port 8000
- Check: `curl http://localhost:8000/health`
- Verify `BACKEND_API_URL` in streamlit_app.py is correct

## 📱 UI Overview

### Left Sidebar
- **File upload** → Upload documents
- **Agent selection** → Choose which agent to query
- **Agent management** → View agent stats, delete agents
- **Control buttons** → Clear conversation, delete agent

### Main Area
- **Search input** → Enter your query
- **LLM toggle** → Enable AI response generation
- **Search button** → Execute semantic search
- **Results** → View chunks with similarity scores
- **AI Response** → LLM-generated answer

### Right Sidebar
- **Chat history** → View past queries and responses
- **Clear history** → Reset conversation

## 📖 Next Steps

1. **Read** [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
2. **Explore** [README.md](README.md) for full documentation  
3. **Try** different file types (PDF, CSV, JSON)
4. **Customize** in [Agents/config.py](Agents/config.py):
   - Chunk size
   - Embedding model
   - LLM parameters

## 🚀 Advanced Usage

### Using the API Directly
```python
import requests

# Upload file
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/api/agents/upload', files=files)
collection = response.json()['collection_name']

# Search
query = {"query": "What is this about?", "use_llm": True}
results = requests.post(f'http://localhost:8000/api/agents/search/{collection}', json=query)
print(results.json())
```

### Custom Configuration
Edit [Agents/config.py](Agents/config.py):
```python
CHUNK_SIZE = 1000          # Larger chunks  
CHROMA_EMBEDDING_MODEL = "..." # Different embeddings
LLM_SERVER_URL = "https://your-server.com"  # Different LLM
```

## 💡 Pro Tips

1. **Similarity Threshold**: Results show similarity % - aim for 0.7+
2. **Chunk Size**: Smaller chunks (200) for precision, larger (1000) for context
3. **Top-K**: More results (10+) for better LLM context
4. **Temperature**: Lower LLM temperature (0.1) for factual answers

## 🎯 Commands Cheat Sheet

```bash
# Install
pip install -r requirements.txt

# Run backend
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000

# Run frontend
streamlit run streamlit_app.py

# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/docs

# List agents
curl http://localhost:8000/api/agents/agents

# Example script
python example_usage.py

# Reset database
rm -rf data/chroma_db/

# One-command start
./start.sh
```

## 📞 Need Help?

1. Check logs:
   - Backend logs in terminal
   - Streamlit logs in terminal
   
2. Check health:
   - `curl http://localhost:8000/health`
   - Open http://localhost:8501

3. Reset everything:
   - `rm -rf data/`
   - Restart backend and frontend

4. Read documentation:
   - [README.md](README.md)
   - [ARCHITECTURE.md](ARCHITECTURE.md)

---

🎉 **That's it!** You're ready to use the Local Agent Chatbot system!
