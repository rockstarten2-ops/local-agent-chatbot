"""Agent routes for FastAPI."""
import asyncio
import inspect
import io
import json
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Callable, Awaitable, Optional

from Agents.services.agent_factory import AgentFactory
from Agents.apis.agent_api_factory import AgentAPIFactory
from Agents.services.file_processor import FileProcessor
from Agents.services.multi_agent_router import get_router
from Agents.services.document_parsers import chunk_matches_chapter
from Agents.services.internet_search_service import InternetSearchService

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Store active agents
active_agents: Dict[str, Dict[str, Any]] = {}
processing_history: List[Dict[str, Any]] = []
MAX_HISTORY_ITEMS = 100

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
        processing_history.clear()
        
        return {"message": "All agents cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Clear failed: {str(e)}")


class MultiAgentQuery(BaseModel):
    """Multi-agent query model."""
    query: str
    use_llm: bool = True
    force_web_search: bool = False
    web_search_top_k: int = 5
    web_search_provider: str = "auto"


def _utc_now_iso() -> str:
    """Return UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _append_history(entry: Dict[str, Any]) -> None:
    """Append processing history with max length cap."""
    processing_history.append(entry)
    if len(processing_history) > MAX_HISTORY_ITEMS:
        del processing_history[:-MAX_HISTORY_ITEMS]


def _format_sse(event_name: str, payload: Dict[str, Any]) -> str:
    """Format event payload as SSE frame."""
    return f"event: {event_name}\ndata: {json.dumps(payload)}\n\n"


async def _emit_event(
    collector: List[Dict[str, Any]],
    event_handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
    event_name: str,
    payload: Dict[str, Any],
) -> None:
    """Record event and forward to streaming handler."""
    event = {
        "event": event_name,
        "timestamp": _utc_now_iso(),
        "payload": payload,
    }
    collector.append(event)
    if event_handler:
        maybe_awaitable = event_handler(event)
        if inspect.isawaitable(maybe_awaitable):
            await maybe_awaitable


def _resolve_target_collections(target_documents: List[str]) -> Dict[str, Dict[str, Any]]:
    """Return active agents limited to target documents when provided."""
    if not target_documents:
        return dict(active_agents)

    target_set = {target.lower() for target in target_documents}
    filtered = {}
    for collection_name, agent_info in active_agents.items():
        filename = agent_info["metadata"].get("filename", "unknown")
        if filename.lower() in target_set:
            filtered[collection_name] = agent_info
    return filtered if filtered else dict(active_agents)


async def _execute_multi_agent_query(
    request: MultiAgentQuery,
    event_handler: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
) -> Dict[str, Any]:
    """Shared execution logic for JSON and streaming endpoints."""
    trace_id = str(uuid4())
    started_at = _utc_now_iso()
    events: List[Dict[str, Any]] = []
    router_service = get_router()

    try:
        await _emit_event(events, event_handler, "query_received", {
            "trace_id": trace_id,
            "query": request.query,
            "started_at": started_at,
        })

        document_names = [
            agent_info["metadata"].get("filename", "unknown")
            for agent_info in active_agents.values()
        ]
        has_documents = len(active_agents) > 0

        routing_info = router_service.route_query(
            request.query,
            document_names,
            has_documents,
            force_web_search=request.force_web_search,
            web_search_top_k=request.web_search_top_k,
        )
        await _emit_event(events, event_handler, "routing_decision", {
            "trace_id": trace_id,
            "route_type": routing_info.get("route_type", routing_info.get("agent")),
            "agent": routing_info.get("agent"),
            "reason": routing_info.get("reason"),
            "confidence": routing_info.get("confidence", 0.0),
            "target_documents": routing_info.get("target_documents", []),
            "target_chapters": routing_info.get("target_chapters", []),
            "steps": routing_info.get("steps", []),
        })

        route_type = routing_info.get("route_type", routing_info.get("agent", "general_llm"))

        if route_type == "internet_search":
            await _emit_event(events, event_handler, "agent_started", {
                "trace_id": trace_id,
                "agent": "internet_search",
                "message": "Searching the internet",
            })
            await _emit_event(events, event_handler, "web_search_started", {
                "trace_id": trace_id,
                "query": request.query,
                "top_k": routing_info.get("top_k", request.web_search_top_k),
                "provider_preference": request.web_search_provider,
            })

            web_result = InternetSearchService.search(
                request.query,
                top_k=routing_info.get("top_k", request.web_search_top_k),
                preferred_provider=request.web_search_provider,
            )
            web_results = web_result.get("results", [])
            await _emit_event(events, event_handler, "web_search_completed", {
                "trace_id": trace_id,
                "result_count": len(web_results),
                "success": web_result.get("success", False),
                "error": web_result.get("error", ""),
                "provider_used": web_result.get("provider_used", ""),
                "fallback_used": web_result.get("fallback_used", False),
                "fallback_reason": web_result.get("fallback_reason", ""),
            })

            if web_results:
                web_context = InternetSearchService.build_context(web_results)
                answer_prompt = (
                    "Answer the user query using these web search results. "
                    "If uncertain, acknowledge uncertainty and cite likely sources.\n\n"
                    f"User query: {request.query}\n\n"
                    f"Web results:\n{web_context}\n\n"
                    "Answer:"
                )
                try:
                    answer = router_service._call_llm(answer_prompt)
                except Exception:
                    answer = web_results[0].get("snippet", "Web results found but answer synthesis failed.")
            else:
                fallback_error = web_result.get("error", "No internet results found.")
                answer = f"Unable to find useful web results. {fallback_error}"

            response_payload = {
                "success": True,
                "trace_id": trace_id,
                "agent": "internet_search",
                "answer": answer,
                "web_results": web_results[:10],
                "web_provider": web_result.get("provider_used", "none"),
                "web_fallback_used": web_result.get("fallback_used", False),
                "web_fallback_reason": web_result.get("fallback_reason", ""),
                "routing": routing_info,
            }
            await _emit_event(events, event_handler, "agent_completed", {
                "trace_id": trace_id,
                "agent": "internet_search",
            })
            await _emit_event(events, event_handler, "final_response", {
                "trace_id": trace_id,
                "agent": "internet_search",
                "response": response_payload,
            })
        elif route_type == "general_llm":
            await _emit_event(events, event_handler, "agent_started", {
                "trace_id": trace_id,
                "agent": "general_llm",
                "message": "Generating response without document context",
            })
            try:
                answer = router_service._call_llm(request.query)
            except Exception:
                answer = f"I could not generate a response right now. Query: {request.query[:120]}"
            response_payload = {
                "success": True,
                "trace_id": trace_id,
                "agent": "general_llm",
                "answer": answer,
                "routing": routing_info,
            }
            await _emit_event(events, event_handler, "agent_completed", {
                "trace_id": trace_id,
                "agent": "general_llm",
            })
            await _emit_event(events, event_handler, "final_response", {
                "trace_id": trace_id,
                "agent": "general_llm",
                "response": response_payload,
            })
        elif route_type in {"all_documents_summary", "single_document_summary", "chapter_summary"}:
            selected_agents = _resolve_target_collections(routing_info.get("target_documents", []))
            chapter_targets = routing_info.get("target_chapters", [])
            summaries = []

            for collection_name, agent_info in selected_agents.items():
                filename = agent_info["metadata"].get("filename", "Document")
                api = agent_info["api"]

                await _emit_event(events, event_handler, "agent_started", {
                    "trace_id": trace_id,
                    "agent": route_type,
                    "document": filename,
                    "collection": collection_name,
                })

                result = api.search(
                    request.query,
                    use_llm=False,
                    top_k=routing_info.get("top_k", 10),
                )
                search_results = result.get("search_results", [])

                await _emit_event(events, event_handler, "retrieval_completed", {
                    "trace_id": trace_id,
                    "document": filename,
                    "result_count": len(search_results),
                })

                filtered_results = search_results
                chapter_fallback_used = False
                if route_type == "chapter_summary":
                    chapter_hits = [item for item in search_results if chunk_matches_chapter(item.get("content", ""), chapter_targets)]
                    if chapter_hits:
                        filtered_results = chapter_hits
                        await _emit_event(events, event_handler, "chapter_resolution", {
                            "trace_id": trace_id,
                            "document": filename,
                            "matched_chapters": chapter_targets,
                            "mode": "heading_detected",
                            "matched_chunks": len(chapter_hits),
                        })
                    else:
                        chapter_fallback_used = True
                        filtered_results = search_results[: max(1, min(5, len(search_results)))]
                        await _emit_event(events, event_handler, "chapter_resolution", {
                            "trace_id": trace_id,
                            "document": filename,
                            "matched_chapters": chapter_targets,
                            "mode": "semantic_fallback",
                            "matched_chunks": len(filtered_results),
                        })

                if not filtered_results:
                    continue

                context = "\n\n".join([item.get("content", "") for item in filtered_results[:5]])
                summary_instructions = ""
                if route_type == "chapter_summary" and chapter_targets:
                    summary_instructions = (
                        f"Focus only on these chapter/section targets: {', '.join(chapter_targets)}. "
                        "If exact headings are missing, summarize the closest relevant sections."
                    )
                summary_text = router_service.generate_summary(
                    context,
                    filename,
                    instructions=summary_instructions,
                )
                summary_item = {
                    "document": filename,
                    "summary": summary_text,
                }
                if route_type == "chapter_summary":
                    summary_item["chapters"] = chapter_targets
                    summary_item["chapter_fallback_used"] = chapter_fallback_used
                summaries.append(summary_item)

                await _emit_event(events, event_handler, "summary_partial", {
                    "trace_id": trace_id,
                    "document": filename,
                    "agent": route_type,
                    "chapter_fallback_used": chapter_fallback_used,
                })
                await _emit_event(events, event_handler, "agent_completed", {
                    "trace_id": trace_id,
                    "agent": route_type,
                    "document": filename,
                })

            if not summaries:
                fallback_message = "No documents matched your request."
                if route_type == "chapter_summary":
                    fallback_message = "No chapter-relevant content was found."
                summaries = [{
                    "document": "No matches",
                    "summary": fallback_message,
                }]

            response_payload = {
                "success": True,
                "trace_id": trace_id,
                "agent": route_type,
                "summaries": summaries,
                "routing": routing_info,
            }
            await _emit_event(events, event_handler, "final_response", {
                "trace_id": trace_id,
                "agent": route_type,
                "response": response_payload,
            })
        else:
            selected_agents = _resolve_target_collections(routing_info.get("target_documents", []))
            merged_results = []

            for collection_name, agent_info in selected_agents.items():
                filename = agent_info["metadata"].get("filename", "Document")
                api = agent_info["api"]

                await _emit_event(events, event_handler, "agent_started", {
                    "trace_id": trace_id,
                    "agent": "document_retriever",
                    "document": filename,
                    "collection": collection_name,
                })

                result = api.search(
                    request.query,
                    use_llm=False,
                    top_k=routing_info.get("top_k", 5),
                )
                search_results = result.get("search_results", [])
                await _emit_event(events, event_handler, "retrieval_completed", {
                    "trace_id": trace_id,
                    "document": filename,
                    "result_count": len(search_results),
                })

                for item in search_results:
                    if item.get("similarity", 0) > 0.2:
                        merged_results.append({
                            "document": filename,
                            "content": item.get("content", ""),
                            "similarity": item.get("similarity", 0),
                        })
                await _emit_event(events, event_handler, "agent_completed", {
                    "trace_id": trace_id,
                    "agent": "document_retriever",
                    "document": filename,
                })

            if not merged_results:
                response_payload = {
                    "success": True,
                    "trace_id": trace_id,
                    "agent": "document_retriever",
                    "answer": "No relevant information found in your documents.",
                    "results": [],
                    "routing": routing_info,
                }
            else:
                merged_results.sort(key=lambda item: item["similarity"], reverse=True)
                context = "\n\n".join([
                    f"[{item['document']}] {item['content']}"
                    for item in merged_results[:3]
                ])
                answer = router_service.generate_answer(request.query, context)
                response_payload = {
                    "success": True,
                    "trace_id": trace_id,
                    "agent": "document_retriever",
                    "answer": answer,
                    "results": merged_results[:5],
                    "routing": routing_info,
                }

            await _emit_event(events, event_handler, "final_response", {
                "trace_id": trace_id,
                "agent": response_payload["agent"],
                "response": response_payload,
            })

        completed_at = _utc_now_iso()
        history_entry = {
            "trace_id": trace_id,
            "query": request.query,
            "started_at": started_at,
            "completed_at": completed_at,
            "routing": response_payload.get("routing", {}),
            "events": events,
            "response": response_payload,
        }
        _append_history(history_entry)
        return response_payload
    except Exception as exc:
        error_payload = {
            "success": False,
            "trace_id": trace_id,
            "agent": "error",
            "answer": f"Error processing query: {str(exc)}",
            "routing": {},
        }
        await _emit_event(events, event_handler, "error", {
            "trace_id": trace_id,
            "message": str(exc),
        })
        await _emit_event(events, event_handler, "final_response", {
            "trace_id": trace_id,
            "agent": "error",
            "response": error_payload,
        })
        _append_history({
            "trace_id": trace_id,
            "query": request.query,
            "started_at": started_at,
            "completed_at": _utc_now_iso(),
            "routing": {},
            "events": events,
            "response": error_payload,
        })
        return error_payload


@router.post("/query")
async def multi_agent_query(request: MultiAgentQuery) -> Dict[str, Any]:
    """Process query using multi-agent routing system."""
    return await _execute_multi_agent_query(request)


@router.post("/query/stream")
async def multi_agent_query_stream(request: MultiAgentQuery) -> StreamingResponse:
    """Stream multi-agent processing events via SSE."""
    queue: asyncio.Queue = asyncio.Queue()
    completion_marker = object()

    async def event_handler(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def run_query() -> None:
        try:
            await _execute_multi_agent_query(request, event_handler=event_handler)
        finally:
            await queue.put(completion_marker)

    async def event_generator():
        task = asyncio.create_task(run_query())
        try:
            while True:
                item = await queue.get()
                if item is completion_marker:
                    break
                event_name = item.get("event", "message")
                yield _format_sse(event_name, item)
        finally:
            await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history")
async def get_processing_history(limit: int = 20) -> Dict[str, Any]:
    """Return recent processing traces."""
    safe_limit = max(1, min(limit, MAX_HISTORY_ITEMS))
    recent_items = processing_history[-safe_limit:]
    return {
        "total": len(processing_history),
        "history": list(reversed(recent_items)),
    }
