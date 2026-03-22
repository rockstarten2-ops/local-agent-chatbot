"""Markdown document agent API."""
from typing import Dict, Any
from Agents.apis.base_api import BaseAgentAPI

class MarkdownAgentAPI(BaseAgentAPI):
    """API for Markdown document agents."""
    
    def search(self, query: str, use_llm: bool = True, top_k: int = 5) -> Dict[str, Any]:
        """Search in Markdown documents."""
        if use_llm:
            return self.agent.search_with_llm_response(query, top_k=top_k)
        else:
            return self.agent.search(query, top_k=top_k)
    
    def get_info(self) -> Dict[str, Any]:
        """Get Markdown agent information."""
        stats = self.agent.get_stats()
        return {
            "type": "markdown_agent",
            "description": "Agent for searching and analyzing Markdown documents",
            "stats": stats,
            "capabilities": [
                "semantic_search",
                "section_search",
                "question_answering",
                "context_retrieval"
            ]
        }
