"""Multi-agent routing and decision making service."""
import requests
from typing import Dict, Any, List, Optional
from Agents.config import LLM_SERVER_URL

class MultiAgentRouter:
    """Routes queries to appropriate agents based on relevance and type."""
    
    def __init__(self, llm_url: str = LLM_SERVER_URL):
        self.llm_url = llm_url
    
    def check_query_relevance(self, query: str, document_names: List[str]) -> Dict[str, Any]:
        """Check if query is relevant to loaded documents."""
        if not document_names:
            return {"is_relevant": False, "confidence": 0.0, "reason": "No documents loaded"}
        
        # Fallback: keyword matching (fast, reliable, no LLM needed)
        query_lower = query.lower()
        doc_text_lower = ' '.join(document_names).lower()
        
        # Simple keyword overlap
        query_words = set(query_lower.split())
        doc_words = set(doc_text_lower.split())
        overlap = len(query_words & doc_words) / len(query_words) if query_words else 0
        
        # Also check for summarization keywords
        summarize_keywords = ['summary', 'summarize', 'overview', 'brief', 'abstract', 'sum up']
        has_summary_keyword = any(kw in query_lower for kw in summarize_keywords)
        
        # If has summary keyword, always search documents
        is_relevant = has_summary_keyword or overlap > 0.1  # Lower threshold for better recall
        
        return {
            "is_relevant": is_relevant,
            "confidence": min(max(overlap, 0.3 if has_summary_keyword else 0.0), 1.0),
            "reason": "Summary request" if has_summary_keyword else ("Keyword match" if overlap > 0.1 else "Different topic")
        }
    
    def determine_query_type(self, query: str) -> Dict[str, Any]:
        """Determine if query is asking for summary or topic search."""
        query_lower = query.lower()
        
        # Keywords for different query types
        summarize_keywords = [
            'summary', 'summarize', 'overview', 'brief', 'abstract',
            'sum up', 'main points', 'key points', 'outline', 'gist',
            'what is', 'tell me about', 'describe', 'explain'
        ]
        
        is_summarization = any(kw in query_lower for kw in summarize_keywords)
        
        return {
            "query_type": "summarization" if is_summarization else "topic_search",
            "is_summarization": is_summarization,
            "keywords": summarize_keywords if is_summarization else []
        }
    
    def route_query(self, query: str, document_names: List[str], has_documents: bool) -> Dict[str, Any]:
        """Route query to appropriate agent."""
        
        # Step 1: Check relevance
        relevance = self.check_query_relevance(query, document_names)
        
        if has_documents and not relevance["is_relevant"]:
            # Not relevant to documents - use general LLM
            return {
                "agent": "general_llm",
                "reason": "Query not relevant to loaded documents",
                "should_search": False,
                "relevance": relevance
            }
        
        if not has_documents:
            # No documents - use general LLM
            return {
                "agent": "general_llm",
                "reason": "No documents loaded",
                "should_search": False,
                "relevance": relevance
            }
        
        # Step 2: Determine query type
        query_type = self.determine_query_type(query)
        
        if query_type["is_summarization"]:
            return {
                "agent": "summarizer",
                "reason": query_type["keywords"],
                "should_search": True,
                "search_strategy": "summarization",
                "top_k": 10,  # Get more chunks for summary
                "query_type": query_type
            }
        
        # Step 3: Topic search
        return {
            "agent": "document_retriever",
            "reason": "Topic search in documents",
            "should_search": True,
            "search_strategy": "topic_search",
            "top_k": 5,  # Fewer chunks for specific topic
            "query_type": query_type
        }
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM for decision making with fallback."""
        try:
            response = requests.post(
                f"{self.llm_url}/v1/chat/completions",
                json={
                    "model": "local-model",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 200,
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"⚠️ LLM call failed (will use fallback): {str(e)}")
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
        except:
            # Fallback: extract key sentences from context
            sentences = context.split('. ')
            return ' '.join(sentences[:3]) if sentences else "Unable to generate answer."
    
    def generate_summary(self, context: str, document_name: str) -> str:
        """Generate summary of document with fallback."""
        prompt = f"""Please provide a concise summary of the following content from '{document_name}':

{context}

Summary:"""
        try:
            return self._call_llm(prompt)
        except:
            # Fallback: extract first few sentences
            sentences = context.split('. ')
            summary = '. '.join(sentences[:2]) + '.'
            return summary if len(summary) > 10 else "Summary could not be generated."


# Singleton instance
_router = None

def get_router() -> MultiAgentRouter:
    """Get or create the router instance."""
    global _router
    if _router is None:
        _router = MultiAgentRouter()
    return _router
