"""File processing and chunking service."""
from typing import List, Tuple, Dict, Any
from pathlib import Path
from Agents.config import CHUNK_SIZE, CHUNK_OVERLAP, UPLOAD_DIR
from Agents.services.document_parsers import ParserFactory

class FileProcessor:
    """Process files and create semantic chunks."""
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start += chunk_size - overlap
        
        return chunks if chunks else [text] if text.strip() else []
    
    @staticmethod
    def process_file(file_path: str, file_type: str = None) -> Tuple[List[str], Dict[str, Any]]:
        """Process file and return chunks and metadata."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type if not provided
        if file_type is None:
            file_type = path.suffix.lower().lstrip('.')
        
        # Parse document
        parsed_chunks = ParserFactory.parse(file_path)
        
        # Create chunks with overlap
        all_chunks = []
        for parsed_chunk in parsed_chunks:
            chunks = FileProcessor.chunk_text(parsed_chunk)
            all_chunks.extend(chunks)
        
        # Create metadata
        metadata = {
            "filename": path.name,
            "file_type": file_type,
            "total_chunks": len(all_chunks),
            "file_size": path.stat().st_size,
        }
        
        return all_chunks, metadata
    
    @staticmethod
    def process_uploaded_file(file_obj, filename: str) -> Tuple[str, Dict[str, Any]]:
        """Process uploaded file and save it."""
        # Save uploaded file
        file_path = UPLOAD_DIR / filename
        
        # Handle different file object types
        if hasattr(file_obj, 'read'):
            content = file_obj.read()
            if isinstance(content, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                with open(file_path, 'wb') as f:
                    f.write(content)
        else:
            with open(file_path, 'wb') as f:
                f.write(file_obj)
        
        # Process the file
        chunks, metadata = FileProcessor.process_file(str(file_path))
        
        return str(file_path), chunks, metadata
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """Get file type from filename."""
        return Path(filename).suffix.lower().lstrip('.')
