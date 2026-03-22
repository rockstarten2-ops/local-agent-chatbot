"""
Example usage of the Local Agent Chatbot system.
This script demonstrates how to use the agent system programmatically.
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000/api/agents"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_health():
    """Check if API is running."""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def upload_file(file_path):
    """Upload a file and create an agent."""
    print(f"📤 Uploading: {file_path}")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Collection: {data['collection_name']}")
        print(f"   File Type: {data['file_type']}")
        print(f"   Chunks: {data['chunks_count']}")
        return data['collection_name']
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def search(collection_name, query, use_llm=True):
    """Search in a collection."""
    print(f"\n🔍 Searching: '{query}'")
    
    payload = {
        "query": query,
        "use_llm": use_llm,
        "top_k": 5
    }
    
    response = requests.post(
        f"{BASE_URL}/search/{collection_name}",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n📊 Results found: {data.get('total_sources', 0)}")
        
        if 'search_results' in data:
            for i, result in enumerate(data['search_results'], 1):
                print(f"\n   [{i}] Similarity: {result['similarity']:.2%}")
                print(f"       Content: {result['content'][:100]}...")
        
        if 'llm_response' in data:
            print(f"\n🤖 AI Response:")
            print(f"   {data['llm_response']}")
        
        return data
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def list_agents():
    """List all active agents."""
    response = requests.get(f"{BASE_URL}/agents")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📋 Active Agents: {data['total_agents']}")
        
        for agent in data['agents']:
            print(f"\n  • {agent['filename']}")
            print(f"    Type: {agent['file_type']}")
            print(f"    Chunks: {agent['chunks_count']}")
            print(f"    Collection: {agent['collection_name']}")
        
        return data
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def get_agent_info(collection_name):
    """Get information about an agent."""
    response = requests.get(f"{BASE_URL}/agent-info/{collection_name}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 Agent Information:")
        print(f"  Type: {data['type']}")
        print(f"  Description: {data['description']}")
        print(f"  Capabilities:")
        for cap in data['capabilities']:
            print(f"    - {cap}")
        print(f"  Stats: {data['stats']}")
        return data
    else:
        print(f"❌ Failed: {response.json()}")
        return None

def delete_agent(collection_name):
    """Delete an agent."""
    print(f"🗑️  Deleting agent: {collection_name}")
    
    response = requests.delete(f"{BASE_URL}/agent/{collection_name}")
    
    if response.status_code == 200:
        print(f"✅ Deleted successfully")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False

def main():
    """Run example usage."""
    print_header("Local Agent Chatbot - Example Usage")
    
    # Check if API is running
    print("🔍 Checking API health...")
    if not check_health():
        print("❌ API is not running!")
        print("   Start it with: python -m uvicorn backend:app --reload")
        return
    
    print("✅ API is running!")
    
    # Get supported types
    response = requests.get(f"{BASE_URL}/supported-types")
    if response.status_code == 200:
        types = response.json()['supported_types']
        print(f"📁 Supported file types: {', '.join(types)}")
    
    print_header("Example: Creating Agents and Searching")
    
    # Create sample files for demonstration
    sample_files = {
        'sample.txt': 'This is a sample text document. It contains information about various topics.',
        'sample.json': json.dumps({"name": "John", "age": 30, "city": "New York"}),
        'sample.csv': "Name,Age,City\nJohn,30,New York\nJane,25,Boston",
    }
    
    agents = {}
    
    # Upload sample files
    for filename, content in sample_files.items():
        filepath = Path(f'/tmp/{filename}')
        filepath.write_text(content)
        
        print_header(f"Uploading {filename}")
        collection_name = upload_file(str(filepath))
        
        if collection_name:
            agents[filename] = collection_name
            time.sleep(1)
    
    # List agents
    print_header("Listing All Agents")
    list_agents()
    
    # Get agent info
    if agents:
        first_agent = list(agents.values())[0]
        print_header(f"Getting Agent Information")
        get_agent_info(first_agent)
    
    # Search examples
    if agents:
        print_header("Search Examples")
        
        # Text search
        txt_agent = agents.get('sample.txt')
        if txt_agent:
            print("\n📄 Searching in text document:")
            search(txt_agent, "Tell me about the sample document", use_llm=True)
    
    # Cleanup
    print_header("Cleanup")
    
    for filename, collection_name in agents.items():
        print(f"Deleting agent for {filename}...")
        delete_agent(collection_name)
        time.sleep(0.5)
    
    print_header("Example completed!")
    print("✅ All operations completed successfully!")

if __name__ == "__main__":
    main()
