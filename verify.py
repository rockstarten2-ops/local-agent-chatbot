#!/usr/bin/env python3
"""
Verification script to check if all components are properly set up.
Run this to verify the complete installation.
"""

import os
import sys
from pathlib import Path

def check_marker(condition, item):
    """Print check status."""
    status = "✅" if condition else "❌"
    print(f"{status} {item}")
    return condition

def check_file(path, description):
    """Check if file exists."""
    exists = Path(path).exists()
    return check_marker(exists, f"{description}: {path}")

def check_directory(path, description):
    """Check if directory exists."""
    exists = Path(path).is_dir()
    return check_marker(exists, f"{description}: {path}")

def main():
    """Run verification checks."""
    print("\n" + "="*60)
    print("  Local Agent Chatbot - Verification Checklist")
    print("="*60 + "\n")
    
    checks_passed = 0
    checks_total = 0
    
    # Core files
    print("📄 Core Files:")
    core_files = [
        ("backend.py", "FastAPI backend"),
        ("streamlit_app.py", "Streamlit UI"),
        ("requirements.txt", "Dependencies"),
        ("start.sh", "Startup script"),
    ]
    
    for file, desc in core_files:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Agent services
    print("\n🤖 Agent Services:")
    services = [
        ("Agents/services/chroma_vector_store.py", "Vector store"),
        ("Agents/services/document_parsers.py", "Document parsers"),
        ("Agents/services/file_processor.py", "File processor"),
        ("Agents/services/semantic_search.py", "Semantic search"),
        ("Agents/services/agent_factory.py", "Agent factory"),
    ]
    
    for file, desc in services:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Agent APIs
    print("\n🔌 Agent APIs:")
    apis = [
        ("Agents/apis/base_api.py", "Base API"),
        ("Agents/apis/text_agent_api.py", "Text agent API"),
        ("Agents/apis/pdf_agent_api.py", "PDF agent API"),
        ("Agents/apis/csv_agent_api.py", "CSV agent API"),
        ("Agents/apis/json_agent_api.py", "JSON agent API"),
        ("Agents/apis/markdown_agent_api.py", "Markdown agent API"),
    ]
    
    for file, desc in apis:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Routes
    print("\n📍 Routes:")
    checks_total += 1
    if check_file("Agents/routes/agent_router.py", "Agent router"):
        checks_passed += 1
    
    # Documentation
    print("\n📚 Documentation:")
    docs = [
        ("README.md", "Main documentation"),
        ("ARCHITECTURE.md", "Architecture guide"),
        ("QUICKSTART.md", "Quick start guide"),
        ("PROJECT_SUMMARY.md", "Project summary"),
    ]
    
    for file, desc in docs:
        checks_total += 1
        if check_file(file, desc):
            checks_passed += 1
    
    # Directories
    print("\n📁 Directories Structure:")
    dirs = [
        ("Agents", "Agents module"),
        ("Agents/services", "Services"),
        ("Agents/apis", "APIs"),
        ("Agents/routes", "Routes"),
    ]
    
    for dir, desc in dirs:
        checks_total += 1
        if check_directory(dir, desc):
            checks_passed += 1
    
    # Configuration
    print("\n⚙️  Configuration:")
    checks_total += 1
    if check_file("Agents/config.py", "Config"):
        checks_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"  Status: {checks_passed}/{checks_total} checks passed")
    print("="*60 + "\n")
    
    if checks_passed == checks_total:
        print("🎉 All checks passed! System is ready.")
        print("\n📖 Next steps:")
        print("  1. Read: ./QUICKSTART.md")
        print("  2. Install: pip install -r requirements.txt")
        print("  3. Start: ./start.sh")
        print("  4. Open: http://localhost:8501\n")
        return 0
    else:
        print(f"⚠️  {checks_total - checks_passed} check(s) failed.")
        print("Please verify your installation.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
