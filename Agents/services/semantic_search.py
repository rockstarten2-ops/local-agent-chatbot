"""Semantic search service."""
import requests
import json
from typing import List, Dict, Any
from Agents.config import LLM_API_ENDPOINT, LLM_MODEL
from Agents.services.chroma_vector_store import get_vector_store

class SemanticSearchAgent:
    """Agent for semantic search and LLM-based Q&A."""
    
    def __init__(self, collection_name: str):
        """Initialize with collection name."""
        self.collection_name = collection_name
        self.vector_store = get_vector_store()
    
    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Perform semantic search."""
        results = self.vector_store.search(
            collection_name=self.collection_name,
            query=query,
            num_results=top_k
        )
        
        # Format results
        formatted_results = []
        if results and results.get('documents') and results['documents'][0]:
            for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                formatted_results.append({
                    "rank": i + 1,
                    "content": doc,
                    "similarity": 1 - distance,  # Convert distance to similarity
                    "metadata": results['metadatas'][0][i] if results.get('metadatas') else {}
                })
        
        return {
            "query": query,
            "search_results": formatted_results,  # Changed from "results" to "search_results"
            "total_results": len(formatted_results)
        }
    
    def search_with_llm_response(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Perform semantic search and generate LLM response."""
        search_results = self.search(query, top_k)
        
        # Build context from search results
        context = "\n".join([
            f"Source {i+1}: {result['content']}"
            for i, result in enumerate(search_results['search_results'])
        ])
        
        # Generate LLM response
        llm_response = self._generate_llm_response(query, context)
        
        return {
            "query": query,
            "search_results": search_results['search_results'],
            "llm_response": llm_response,
            "total_sources": len(search_results['search_results'])
        }
    
    @staticmethod
    def _generate_llm_response(query: str, context: str) -> str:
        """Generate response from LLM using search context."""
        try:
            prompt = f"""Based on the following context, answer the question concisely.

Context:
{context}

Question: {query}

Answer:"""
            
            response = requests.post(
                LLM_API_ENDPOINT,
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 512,
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def add_documents(self, documents: List[str], metadata_list: List[Dict[str, Any]] = None) -> None:
        """Add documents to the vector store."""
        if metadata_list is None:
            metadata_list = [{} for _ in documents]
        
        self.vector_store.add_documents(
            collection_name=self.collection_name,
            documents=documents,
            metadata=metadata_list
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return self.vector_store.get_collection_stats(self.collection_name)
