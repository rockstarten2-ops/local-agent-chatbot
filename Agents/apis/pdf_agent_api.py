"""PDF document agent API."""
from typing import Dict, Any
from Agents.apis.base_api import BaseAgentAPI

class PDFAgentAPI(BaseAgentAPI):
    """API for PDF document agents."""
    
    def search(self, query: str, use_llm: bool = True) -> Dict[str, Any]:
        """Search in PDF documents."""
        if use_llm:
            return self.agent.search_with_llm_response(query, top_k=5)
        else:
            return self.agent.search(query, top_k=5)
    
    def get_info(self) -> Dict[str, Any]:
        """Get PDF agent information."""
        stats = self.agent.get_stats()
        return {
            "type": "pdf_agent",
            "description": "Agent for searching and analyzing PDF documents",
            "stats": stats,
            "capabilities": [
                "semantic_search",
                "question_answering",
                "multiple_page_analysis",
                "context_retrieval"
            ]
        }
