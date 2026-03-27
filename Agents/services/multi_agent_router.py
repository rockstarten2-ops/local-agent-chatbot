"""Multi-agent routing and decision making service."""
import re
import requests
from typing import Dict, Any, List
from Agents.config import LLM_SERVER_URL, LLM_MODEL, LLM_TIMEOUT, LLM_MAX_TOKENS
from Agents.services.document_parsers import extract_chapter_targets, find_best_document_match
from Agents.services.llm_response_parser import extract_chat_completion_text

class MultiAgentRouter:
    """Routes queries to appropriate agents based on relevance and intent."""

    def __init__(self, llm_url: str = LLM_SERVER_URL):
        self.llm_url = llm_url
        self.summary_keywords = [
            "summary", "summarize", "overview", "brief", "abstract",
            "sum up", "main points", "key points", "outline", "gist"
        ]
        self.chapter_keywords = ["chapter", "section", "part"]
        self.all_docs_keywords = [
            "all documents", "all docs", "across documents",
            "everything", "entire set", "all files"
        ]
        self.web_keywords = [
            "latest", "today", "current", "news", "online", "internet",
            "web", "google", "what happened", "recent", "trend", "update",
            "stock price", "weather", "live"
        ]

    @staticmethod
    def _tokenize_words(text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_]+", text.lower())

    def check_query_relevance(self, query: str, document_names: List[str]) -> Dict[str, Any]:
        """Check if query is relevant to loaded documents."""
        if not document_names:
            return {"is_relevant": False, "confidence": 0.0, "reason": "No documents loaded"}

        query_lower = query.lower()
        query_words = set(self._tokenize_words(query_lower))
        doc_words = set(self._tokenize_words(" ".join(document_names)))
        overlap = len(query_words & doc_words) / len(query_words) if query_words else 0.0

        has_summary_keyword = any(keyword in query_lower for keyword in self.summary_keywords)
        has_chapter_keyword = any(keyword in query_lower for keyword in self.chapter_keywords)
        is_relevant = has_summary_keyword or has_chapter_keyword or overlap > 0.08

        return {
            "is_relevant": is_relevant,
            "confidence": min(max(overlap, 0.35 if (has_summary_keyword or has_chapter_keyword) else 0.05), 1.0),
            "reason": (
                "Summary request" if has_summary_keyword else
                ("Chapter-focused request" if has_chapter_keyword else
                 ("Keyword overlap with filenames" if overlap > 0.08 else "Different topic"))
            )
        }

    def determine_query_intent(self, query: str) -> Dict[str, Any]:
        """Determine query intent and route category."""
        query_lower = query.lower()
        chapter_targets = extract_chapter_targets(query)
        has_summary_keyword = any(keyword in query_lower for keyword in self.summary_keywords)
        has_all_docs_keyword = any(keyword in query_lower for keyword in self.all_docs_keywords)

        if chapter_targets:
            route_type = "chapter_summary"
        elif has_summary_keyword and has_all_docs_keyword:
            route_type = "all_documents_summary"
        elif has_summary_keyword:
            route_type = "single_document_summary"
        else:
            route_type = "document_retriever"

        return {
            "route_type": route_type,
            "chapter_targets": chapter_targets,
            "is_summarization": route_type in {
                "all_documents_summary",
                "single_document_summary",
                "chapter_summary",
            },
        }

    def route_query(
        self,
        query: str,
        document_names: List[str],
        has_documents: bool,
        force_web_search: bool = False,
        web_search_top_k: int = 5,
    ) -> Dict[str, Any]:
        """Route query to an execution plan with structured metadata."""
        steps: List[Dict[str, str]] = []
        steps.append({"step": "query_received", "description": "Received user query"})
        safe_web_top_k = max(1, min(int(web_search_top_k), 10))

        if force_web_search:
            steps.append({"step": "routing_decision", "description": "Forced internet search from UI toggle"})
            return {
                "agent": "internet_search",
                "route_type": "internet_search",
                "reason": "Forced web search from UI",
                "should_search": True,
                "search_strategy": "internet_search",
                "top_k": safe_web_top_k,
                "relevance": {"is_relevant": False, "confidence": 1.0, "reason": "Forced web route"},
                "confidence": 1.0,
                "target_documents": [],
                "target_chapters": [],
                "steps": steps,
            }

        relevance = self.check_query_relevance(query, document_names)
        steps.append({
            "step": "relevance_check",
            "description": f"Relevance={relevance['confidence']:.2f} ({relevance['reason']})"
        })

        query_lower = query.lower()
        doc_reference_keywords = [
            "document", "doc", "file", "pdf", "upload", "uploaded",
            "filename", "file name", "name", "name of", "title", "chapter", "section",
            "this", "that", "it",
        ]
        chit_chat_keywords = [
            "hello", "hi", "hey", "thanks", "thank you", "how are you",
            "who are you", "your name",
        ]
        has_doc_reference = any(keyword in query_lower for keyword in doc_reference_keywords)
        is_chit_chat = any(keyword in query_lower for keyword in chit_chat_keywords)

        if not has_documents:
            steps.append({"step": "routing_decision", "description": "No documents available, route to general LLM"})
            return {
                "agent": "general_llm",
                "route_type": "general_llm",
                "reason": "No documents loaded",
                "should_search": False,
                "relevance": relevance,
                "confidence": relevance["confidence"],
                "target_documents": [],
                "target_chapters": [],
                "top_k": 0,
                "steps": steps,
            }

        if has_documents and not relevance["is_relevant"]:
            if has_doc_reference and not is_chit_chat:
                steps.append({
                    "step": "routing_decision",
                    "description": "Low lexical match but document-reference detected, route to document retriever"
                })
                return {
                    "agent": "document_retriever",
                    "route_type": "document_retriever",
                    "reason": "Follow-up appears to reference uploaded documents",
                    "should_search": True,
                    "search_strategy": "topic_search",
                    "top_k": 5,
                    "relevance": relevance,
                    "confidence": max(relevance["confidence"], 0.45),
                    "target_documents": [],
                    "target_chapters": [],
                    "steps": steps,
                }
            steps.append({"step": "routing_decision", "description": "Query not document-relevant, route to general LLM"})
            return {
                "agent": "general_llm",
                "route_type": "general_llm",
                "reason": "Query not relevant to loaded documents",
                "should_search": False,
                "relevance": relevance,
                "confidence": relevance["confidence"],
                "target_documents": [],
                "target_chapters": [],
                "top_k": 0,
                "steps": steps,
            }

        intent = self.determine_query_intent(query)
        best_match = find_best_document_match(query, document_names)
        target_document = best_match if best_match else ""
        target_documents = [target_document] if target_document else []

        steps.append({
            "step": "intent_detection",
            "description": f"Detected route candidate: {intent['route_type']}"
        })
        if target_document:
            steps.append({
                "step": "document_targeting",
                "description": f"Matched target document: {target_document}"
            })

        route_type = intent["route_type"]
        if route_type == "single_document_summary" and not target_documents:
            route_type = "all_documents_summary"
            steps.append({
                "step": "document_targeting",
                "description": "No specific file detected, switched to all-documents summary"
            })

        if route_type == "chapter_summary" and not target_documents:
            # Chapter request without explicit file defaults to all documents.
            target_documents = list(document_names)

        if route_type in {"all_documents_summary", "single_document_summary", "chapter_summary"}:
            top_k = 12 if route_type == "chapter_summary" else 10
            reason = {
                "all_documents_summary": "Summarize all loaded documents",
                "single_document_summary": "Summarize a selected document",
                "chapter_summary": "Summarize requested chapters/sections",
            }[route_type]
            steps.append({"step": "routing_decision", "description": f"Routed to {route_type}"})
            return {
                "agent": route_type,
                "route_type": route_type,
                "reason": reason,
                "should_search": True,
                "search_strategy": "summarization",
                "top_k": top_k,
                "relevance": relevance,
                "confidence": relevance["confidence"],
                "target_documents": target_documents,
                "target_chapters": intent["chapter_targets"],
                "steps": steps,
            }

        steps.append({"step": "routing_decision", "description": "Routed to document retriever"})
        return {
            "agent": "document_retriever",
            "route_type": "document_retriever",
            "reason": "Topic search in documents",
            "should_search": True,
            "search_strategy": "topic_search",
            "top_k": 5,
            "relevance": relevance,
            "confidence": relevance["confidence"],
            "target_documents": target_documents,
            "target_chapters": [],
            "steps": steps,
        }

    def _call_llm(self, prompt: str) -> str:
        """Call LLM for decision making with fallback."""
        try:
            response = requests.post(
                f"{self.llm_url}/v1/chat/completions",
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": LLM_MAX_TOKENS,
                },
                timeout=LLM_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return extract_chat_completion_text(data)
        except Exception as e:
            raise Exception(f"LLM call failed: {str(e)}")

    def generate_answer(self, query: str, context: str) -> str:
        """Generate answer using LLM with fallback."""
        prompt = f"""Based on the following context from documents, answer the question concisely and accurately.

Context:
{context}

Question: {query}

Answer:"""
        try:
            return self._call_llm(prompt)
        except Exception:
            sentences = context.split(". ")
            return ' '.join(sentences[:3]) if sentences else "Unable to generate answer."

    def generate_summary(self, context: str, document_name: str, instructions: str = "") -> str:
        """Generate summary of document/chapter content with fallback."""
        prompt = f"""Please provide a concise summary of the following content from '{document_name}'.
{instructions}

{context}

Summary:"""
        try:
            return self._call_llm(prompt)
        except Exception:
            sentences = context.split(". ")
            summary = ". ".join(sentences[:2]) + "."
            return summary if len(summary) > 10 else "Summary could not be generated."


# Singleton instance
_router = None

def get_router() -> MultiAgentRouter:
    """Get or create the router instance."""
    global _router
    if _router is None:
        _router = MultiAgentRouter()
    return _router
