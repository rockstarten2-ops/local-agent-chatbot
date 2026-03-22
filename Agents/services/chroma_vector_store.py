"""ChromaDB vector store for semantic search."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from Agents.config import CHROMA_DB_DIR, CHROMA_COLLECTION_PREFIX
import hashlib

class ChromaVectorStore:
    """Manages ChromaDB for semantic search."""
    
    def __init__(self):
        """Initialize ChromaDB client."""
        settings = Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=str(CHROMA_DB_DIR),
            anonymized_telemetry=False,
        )
        self.client = chromadb.Client(settings)
        self.collections = {}
    
    def get_or_create_collection(self, collection_name: str) -> Any:
        """Get or create a collection."""
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self.collections[collection_name]
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add documents to a collection."""
        collection = self.get_or_create_collection(collection_name)
        
        if ids is None:
            ids = [hashlib.md5(f"{doc}_{i}".encode()).hexdigest() for i, doc in enumerate(documents)]
        
        if metadata is None:
            metadata = [{} for _ in documents]
        
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadata
        )
    
    def search(
        self,
        collection_name: str,
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """Semantic search in a collection."""
        collection = self.get_or_create_collection(collection_name)
        
        results = collection.query(
            query_texts=[query],
            n_results=num_results
        )
        
        return results
    
    def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        self.client.delete_collection(name=collection_name)
        if collection_name in self.collections:
            del self.collections[collection_name]
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        return [col.name for col in self.client.list_collections()]
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        collection = self.get_or_create_collection(collection_name)
        count = collection.count()
        
        return {
            "name": collection_name,
            "document_count": count,
            "metadata": collection.metadata
        }

# Global instance
_vector_store = None

def get_vector_store() -> ChromaVectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store
