"""Agent factory for creating type-specific agents."""
from typing import Dict, Any
from Agents.services.semantic_search import SemanticSearchAgent
from Agents.services.file_processor import FileProcessor
from Agents.config import CHROMA_COLLECTION_PREFIX

class AgentFactory:
    """Factory for creating file-type-specific agents."""
    
    AGENT_TYPES = {
        "txt": "text_agent",
        "pdf": "pdf_agent",
        "csv": "csv_agent",
        "json": "json_agent",
        "md": "markdown_agent",
    }
    
    _agents: Dict[str, SemanticSearchAgent] = {}
    
    @classmethod
    def get_agent(cls, file_type: str, collection_name: str = None) -> SemanticSearchAgent:
        """Get or create agent for file type."""
        if collection_name is None:
            collection_name = f"{CHROMA_COLLECTION_PREFIX}_{file_type}s"
        
        if collection_name not in cls._agents:
            cls._agents[collection_name] = SemanticSearchAgent(collection_name)
        
        return cls._agents[collection_name]
    
    @classmethod
    def create_agent_for_file(cls, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """Create and initialize agent for a file."""
        if file_type is None:
            file_type = FileProcessor.get_file_type(file_path)
        
        # Process file
        chunks, metadata = FileProcessor.process_file(file_path, file_type)
        
        # Create agent
        collection_name = f"{CHROMA_COLLECTION_PREFIX}_{file_type}_{metadata['filename'].replace('.', '_')}"
        agent = cls.get_agent(file_type, collection_name)
        
        # Add documents with metadata
        metadata_list = [
            {**metadata, "chunk_index": i}
            for i in range(len(chunks))
        ]
        agent.add_documents(chunks, metadata_list)
        
        return {
            "collection_name": collection_name,
            "agent": agent,
            "file_type": file_type,
            "metadata": metadata,
            "chunks_count": len(chunks)
        }
    
    @classmethod
    def list_agents(cls) -> list:
        """List all active agents."""
        return list(cls._agents.keys())
    
    @classmethod
    def remove_agent(cls, collection_name: str) -> None:
        """Remove an agent."""
        if collection_name in cls._agents:
            agent = cls._agents[collection_name]
            from Agents.services.chroma_vector_store import get_vector_store
            get_vector_store().delete_collection(collection_name)
            del cls._agents[collection_name]
    
    @classmethod
    def get_supported_types(cls) -> list:
        """Get list of supported file types."""
        return list(cls.AGENT_TYPES.keys())
