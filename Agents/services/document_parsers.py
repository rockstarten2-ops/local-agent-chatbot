"""Document parsers for different file types."""
import json
import csv
import io
from typing import List, Tuple
from pathlib import Path

class DocumentParser:
    """Base document parser."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse document and return chunks."""
        raise NotImplementedError

class TextParser(DocumentParser):
    """Parser for plain text files."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return [content]

class MarkdownParser(DocumentParser):
    """Parser for markdown files."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        # Split by headers for better chunking
        chunks = content.split('\n# ')
        return [chunk.strip() for chunk in chunks if chunk.strip()]

class CSVParser(DocumentParser):
    """Parser for CSV files."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse CSV file."""
        chunks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_text = " | ".join(f"{k}: {v}" for k, v in row.items())
                chunks.append(row_text)
        return chunks

class JSONParser(DocumentParser):
    """Parser for JSON files."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        chunks = []
        
        def flatten_json(obj, prefix=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    flatten_json(value, new_prefix)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_prefix = f"{prefix}[{i}]"
                    flatten_json(item, new_prefix)
            else:
                chunks.append(f"{prefix}: {obj}")
        
        flatten_json(data)
        return chunks if chunks else [json.dumps(data)]

class PDFParser(DocumentParser):
    """Parser for PDF files."""
    
    @staticmethod
    def parse(file_path: str) -> List[str]:
        """Parse PDF file."""
        try:
            import PyPDF2
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF parsing. Install with: pip install PyPDF2")
        
        chunks = []
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    chunks.append(f"Page {page_num + 1}:\n{text}")
        
        return chunks if chunks else [""]

class ParserFactory:
    """Factory for creating appropriate parser."""
    
    PARSERS = {
        ".txt": TextParser,
        ".md": MarkdownParser,
        ".csv": CSVParser,
        ".json": JSONParser,
        ".pdf": PDFParser,
    }
    
    @classmethod
    def get_parser(cls, file_path: str):
        """Get parser for file type."""
        ext = Path(file_path).suffix.lower()
        parser_class = cls.PARSERS.get(ext)
        
        if parser_class is None:
            raise ValueError(f"Unsupported file type: {ext}")
        
        return parser_class
    
    @classmethod
    def parse(cls, file_path: str) -> List[str]:
        """Parse file using appropriate parser."""
        parser_class = cls.get_parser(file_path)
        return parser_class.parse(file_path)
    
    @classmethod
    def supported_types(cls) -> List[str]:
        """Get list of supported file types."""
        return list(cls.PARSERS.keys())
