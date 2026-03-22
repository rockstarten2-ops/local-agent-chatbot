"""JSON data agent API."""
from typing import Dict, Any
from Agents.apis.base_api import BaseAgentAPI

class JSONAgentAPI(BaseAgentAPI):
    """API for JSON data agents."""
    
    def search(self, query: str, use_llm: bool = True, top_k: int = 5) -> Dict[str, Any]:
        """Search in JSON data."""
        if use_llm:
            return self.agent.search_with_llm_response(query, top_k=top_k)
        else:
            return self.agent.search(query, top_k=top_k)
    
    def get_info(self) -> Dict[str, Any]:
        """Get JSON agent information."""
        stats = self.agent.get_stats()
        return {
            "type": "json_agent",
            "description": "Agent for searching and analyzing JSON structured data",
            "stats": stats,
            "capabilities": [
                "semantic_search",
                "structured_data_retrieval",
                "nested_object_search",
                "question_answering"
            ]
        }
