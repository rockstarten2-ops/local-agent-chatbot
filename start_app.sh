#!/bin/bash

echo "🚀 Starting AI Document Assistant..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo ""
echo "=========================================="
echo "🤖 AI Document Assistant (Multi-Agent)"
echo "=========================================="
echo ""
echo "Available endpoints:"
echo "  • Web UI:     http://localhost:8000"
echo "  • API Docs:   http://localhost:8000/docs"
echo "  • Health:     http://localhost:8000/health"
echo ""
echo "Backend endpoints:"
echo "  • List docs:     GET /api/agents"
echo "  • Upload doc:    POST /api/agents/upload"
echo "  • Smart query:   POST /api/agents/query ⭐ NEW"
echo "  • Search docs:   POST /api/agents/search/{collection}"
echo ""
echo "Query routing logic:"
echo "  1. Check if query is relevant to documents"
echo "  2. Determine query type (summary vs search)"
echo "  3. Route to: Summarizer, Retriever, or General LLM"
echo ""
echo "=========================================="
echo ""

# Start the backend
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000
