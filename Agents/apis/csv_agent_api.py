"""CSV data agent API."""
from typing import Dict, Any
from Agents.apis.base_api import BaseAgentAPI

class CSVAgentAPI(BaseAgentAPI):
    """API for CSV data agents."""
    
    def search(self, query: str, use_llm: bool = True) -> Dict[str, Any]:
        """Search in CSV data."""
        if use_llm:
            return self.agent.search_with_llm_response(query, top_k=10)
        else:
            return self.agent.search(query, top_k=10)
    
    def get_info(self) -> Dict[str, Any]:
        """Get CSV agent information."""
        stats = self.agent.get_stats()
        return {
            "type": "csv_agent",
            "description": "Agent for searching and analyzing CSV data",
            "stats": stats,
            "capabilities": [
                "semantic_search",
                "data_analysis",
                "row_matching",
                "aggregation_queries"
            ]
        }
