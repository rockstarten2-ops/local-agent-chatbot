"""Base API class for agents."""
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseAgentAPI(ABC):
    """Base class for agent APIs."""
    
    def __init__(self, agent):
        """Initialize with agent."""
        self.agent = agent
    
    @abstractmethod
    def search(self, query: str, use_llm: bool = True, top_k: int = 5) -> Dict[str, Any]:
        """Search method."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        pass
