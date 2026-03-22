"""Agent API factory."""
from typing import Dict, Any
from Agents.apis.text_agent_api import TextAgentAPI
from Agents.apis.pdf_agent_api import PDFAgentAPI
from Agents.apis.csv_agent_api import CSVAgentAPI
from Agents.apis.json_agent_api import JSONAgentAPI
from Agents.apis.markdown_agent_api import MarkdownAgentAPI

class AgentAPIFactory:
    """Factory for creating agent APIs."""
    
    API_MAPPING = {
        "txt": TextAgentAPI,
        "pdf": PDFAgentAPI,
        "csv": CSVAgentAPI,
        "json": JSONAgentAPI,
        "md": MarkdownAgentAPI,
    }
    
    @classmethod
    def create_api(cls, file_type: str, agent) -> Any:
        """Create API for file type."""
        api_class = cls.API_MAPPING.get(file_type)
        
        if api_class is None:
            raise ValueError(f"Unsupported file type: {file_type}. Supported types: {list(cls.API_MAPPING.keys())}")
        
        return api_class(agent)
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get supported file types."""
        return list(cls.API_MAPPING.keys())
