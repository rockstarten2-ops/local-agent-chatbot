#!/bin/bash

# Quick Start Script for Local Agent Chatbot
# This script sets up and runs the complete system

set -e

echo "🚀 Local Agent Chatbot - Quick Start"
echo "="

# Check Python
echo "✓ Checking Python..."
python --version

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Create data directories
echo ""
echo "📁 Creating data directories..."
mkdir -p data/uploaded_files
mkdir -p data/chroma_db
echo "✓ Directories created"

# Start backend
echo ""
echo "🔧 Starting FastAPI backend..."
echo "   API will be available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
python -m uvicorn backend:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit
echo ""
echo "🎨 Starting Streamlit UI..."
echo "   UI will be available at: http://localhost:8501"
streamlit run streamlit_app.py

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
