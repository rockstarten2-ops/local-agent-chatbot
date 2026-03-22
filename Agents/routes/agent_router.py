"""Agent routes for FastAPI."""
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import io
from pathlib import Path

from Agents.services.agent_factory import AgentFactory
from Agents.apis.agent_api_factory import AgentAPIFactory
from Agents.services.file_processor import FileProcessor
from Agents.services.multi_agent_router import get_router

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Store active agents
active_agents: Dict[str, Dict[str, Any]] = {}

class SearchQuery(BaseModel):
    """Search query model."""
    query: str
    use_llm: bool = True
    top_k: int = 5

class UploadResponse(BaseModel):
    """Upload response model."""
    collection_name: str
    file_type: str
    filename: str
    chunks_count: int
    message: str

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a file and create an agent."""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename
        
        # Determine file type
        file_type = FileProcessor.get_file_type(filename)
        
        # Save and process file
        file_path, chunks, metadata = FileProcessor.process_uploaded_file(
            io.BytesIO(content),
            filename
        )
        
        # Create agent
        agent_info = AgentFactory.create_agent_for_file(file_path, file_type)
        collection_name = agent_info['collection_name']
        
        # Store agent info
        active_agents[collection_name] = {
            "agent": agent_info['agent'],
            "api": AgentAPIFactory.create_api(file_type, agent_info['agent']),
            "file_type": file_type,
            "metadata": metadata,
            "chunks_count": agent_info['chunks_count']
        }
        
        return {
            "collection_name": collection_name,
            "file_type": file_type,
            "filename": filename,
            "chunks_count": agent_info['chunks_count'],
            "message": f"File uploaded successfully. Created agent for {file_type} file."
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")

@router.post("/search/{collection_name}")
async def search_agent(
    collection_name: str,
    query: SearchQuery
) -> Dict[str, Any]:
    """Search using a specific agent."""
    if collection_name not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {collection_name}")
    
    try:
        agent_info = active_agents[collection_name]
        api = agent_info['api']
        
        result = api.search(query.query, use_llm=query.use_llm)
        result['agent_type'] = agent_info['file_type']
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")

@router.get("/agents")
async def list_agents() -> Dict[str, Any]:
    """List all active agents."""
    agents_list = []
    
    for collection_name, agent_info in active_agents.items():
        agents_list.append({
            "collection_name": collection_name,
            "file_type": agent_info['file_type'],
            "filename": agent_info['metadata'].get('filename', 'unknown'),
            "chunks_count": agent_info['chunks_count']
        })
    
    return {
        "total_agents": len(active_agents),
        "agents": agents_list
    }

@router.get("/agent-info/{collection_name}")
async def get_agent_info(collection_name: str) -> Dict[str, Any]:
    """Get information about a specific agent."""
    if collection_name not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {collection_name}")
    
    try:
        agent_info = active_agents[collection_name]
        api = agent_info['api']
        
        return {
            "collection_name": collection_name,
            **api.get_info(),
            "metadata": agent_info['metadata']
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get agent info: {str(e)}")

@router.delete("/agent/{collection_name}")
async def delete_agent(collection_name: str) -> Dict[str, str]:
    """Delete an agent."""
    if collection_name not in active_agents:
        raise HTTPException(status_code=404, detail=f"Agent not found: {collection_name}")
    
    try:
        AgentFactory.remove_agent(collection_name)
        del active_agents[collection_name]
        
        return {"message": f"Agent {collection_name} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")

@router.get("/supported-types")
async def get_supported_types() -> Dict[str, List[str]]:
    """Get supported file types."""
    return {
        "supported_types": AgentAPIFactory.get_supported_types()
    }

@router.post("/clear-all")
async def clear_all() -> Dict[str, str]:
    """Clear all agents."""
    try:
        for collection_name in list(active_agents.keys()):
            AgentFactory.remove_agent(collection_name)
        active_agents.clear()
        
        return {"message": "All agents cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clear failed: {str(e)}")


class MultiAgentQuery(BaseModel):
    """Multi-agent query model."""
    query: str
    use_llm: bool = True


@router.post("/query")
async def multi_agent_query(request: MultiAgentQuery) -> Dict[str, Any]:
    """Process query using multi-agent routing system."""
    try:
        router = get_router()
        
        # Get document info
        document_names = [
            agent_info['metadata'].get('filename', 'unknown')
            for agent_info in active_agents.values()
        ]
        has_documents = len(active_agents) > 0
        
        # Route the query
        routing_info = router.route_query(request.query, document_names, has_documents)
        
        # Execute based on routing decision
        if routing_info["agent"] == "general_llm":
            # General LLM mode - answer without document context
            try:
                answer = router._call_llm(request.query)
            except Exception as e:
                print(f"⚠️ LLM failed, using fallback: {e}")
                answer = f"I couldn't generate a response, but here's what I Know: {request.query[:100]}..."
            
            return {
                "success": True,
                "agent": "general_llm",
                "answer": answer,
                "routing": routing_info
            }
        
        elif routing_info["agent"] == "summarizer":
            # Summarization mode
            summaries = []
            
            try:
                for collection_name, agent_info in active_agents.items():
                    api = agent_info['api']
                    # Get top chunks for summary
                    result = api.search(
                        request.query,
                        use_llm=False,
                        top_k=routing_info.get("top_k", 10)
                    )
                    
                    if result.get("search_results"):
                        context = "\n\n".join([
                            r["content"] for r in result["search_results"][:5]
                        ])
                        try:
                            summary = router.generate_summary(context, agent_info['metadata'].get('filename', 'Document'))
                        except Exception as e:
                            print(f"Summary generation failed: {e}")
                            summary = context[:200] + "..."
                        
                        summaries.append({
                            "document": agent_info['metadata'].get('filename', 'Document'),
                            "summary": summary
                        })
            except Exception as e:
                print(f"Summarization error: {e}")
            
            if not summaries:
                return {
                    "success": True,
                    "agent": "summarizer",
                    "summaries": [{
                        "document": "No documents",
                        "summary": "No documents loaded to summarize."
                    }],
                    "routing": routing_info
                }
            
            return {
                "success": True,
                "agent": "summarizer",
                "summaries": summaries,
                "routing": routing_info
            }
        
        else:  # document_retriever
            # Topic search mode
            results = []
            
            try:
                for collection_name, agent_info in active_agents.items():
                    api = agent_info['api']
                    result = api.search(
                        request.query,
                        use_llm=False,
                        top_k=routing_info.get("top_k", 5)
                    )
                    
                    if result.get("search_results"):
                        for search_result in result["search_results"]:
                            if search_result.get("similarity", 0) > 0.2:  # Only high relevance
                                results.append({
                                    "document": agent_info['metadata'].get('filename', 'Document'),
                                    "content": search_result["content"],
                                    "similarity": search_result.get("similarity", 0)
                                })
            except Exception as e:
                print(f"Search error: {e}")
            
            if not results:
                return {
                    "success": True,
                    "agent": "document_retriever",
                    "answer": "❓ No relevant information found in your documents.",
                    "results": [],
                    "routing": routing_info
                }
            
            # Sort by similarity
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Generate answer using top results
            context = "\n\n".join([
                f"[{r['document']}] {r['content']}"
                for r in results[:3]
            ])
            
            try:
                answer = router.generate_answer(request.query, context)
            except Exception as e:
                print(f"Answer generation failed: {e}")
                answer = context[:300] + "..."
            
            return {
                "success": True,
                "agent": "document_retriever",
                "answer": answer,
                "results": results[:5],  # Return top 5 for UI display
                "routing": routing_info
            }
            
    except Exception as e:
        print(f"Query processing error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "agent": "error",
            "answer": f"Error processing query: {str(e)}",
            "routing": {}
        }
