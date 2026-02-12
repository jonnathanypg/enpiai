"""
RAG Service - Vector memory with Pinecone
"""
import os
import hashlib
from typing import List, Dict, Optional, Any
from flask import current_app


# Global cache
_pinecone_client = None

class RAGService:
    """RAG service for vector memory operations"""
    
    def __init__(self, company=None):
        self.company = company
        self._index = None
        self._llm_service = None
    
    @property
    def llm_service(self):
        """Lazy load LLM service"""
        if not self._llm_service:
            from services.llm_service import LLMService
            self._llm_service = LLMService(self.company)
        return self._llm_service
    
    def _get_pinecone_client(self):
        """Initialize Pinecone client (singleton)"""
        global _pinecone_client
        if _pinecone_client:
            return _pinecone_client
            
        try:
            from pinecone import Pinecone
            
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                return None
            
            _pinecone_client = Pinecone(api_key=api_key)
            return _pinecone_client
        except ImportError:
            return None
    
    def _get_index(self):
        """Get or create Pinecone index"""
        if self._index:
            return self._index
        
        pc = self._get_pinecone_client()
        if not pc:
            return None
        
        # Determine index name
        if self.company and self.company.pinecone_index:
            index_name = self.company.pinecone_index
        else:
            index_name = os.getenv('PINECONE_INDEX_NAME', 'onepunch-rag')
        
        try:
            self._index = pc.Index(index_name)
            return self._index
        except Exception:
            return None
    
    def _get_namespace(self) -> str:
        """Get namespace for current company"""
        if self.company and self.company.pinecone_namespace:
            return self.company.pinecone_namespace
        if self.company:
            return f"company_{self.company.id}"
        return "default"
    
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return [c for c in chunks if c]
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for texts"""
        return self.llm_service.get_embeddings(texts)
    
    def generate_chunk_id(self, document_id: int, chunk_index: int, content: str) -> str:
        """Generate unique ID for a chunk"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"doc_{document_id}_chunk_{chunk_index}_{content_hash}"
    
    def index_document(
        self,
        document_id: int,
        content: str,
        metadata: Optional[Dict] = None
    ) -> List[str]:
        """
        Index a document into Pinecone
        
        Args:
            document_id: Database document ID
            content: Text content to index
            metadata: Additional metadata
        
        Returns:
            List of vector IDs created
        """
        index = self._get_index()
        if not index:
            raise ValueError("Pinecone index not available")
        
        # Chunk the content
        chunks = self.chunk_text(content)
        if not chunks:
            return []
        
        # Create embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Prepare vectors
        vectors = []
        vector_ids = []
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = self.generate_chunk_id(document_id, i, chunk)
            vector_ids.append(vector_id)
            
            chunk_metadata = {
                'document_id': document_id,
                'chunk_index': i,
                'content': chunk[:1000],  # Truncate for metadata limit
                'company_id': self.company.id if self.company else None,
                **(metadata or {})
            }
            
            vectors.append({
                'id': vector_id,
                'values': embedding,
                'metadata': chunk_metadata
            })
        
        # Upsert to Pinecone
        namespace = self._get_namespace()
        index.upsert(vectors=vectors, namespace=namespace)
        
        return vector_ids
    
    def delete_document(self, document_id: int):
        """Delete all vectors for a document"""
        index = self._get_index()
        if not index:
            return
        
        namespace = self._get_namespace()
        
        # Delete by metadata filter
        index.delete(
            filter={'document_id': document_id},
            namespace=namespace
        )
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the vector store
        
        Args:
            query_text: Text to search for
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
        
        Returns:
            List of results with content and metadata
        """
        index = self._get_index()
        if not index:
            return []
        
        # Create query embedding
        query_embedding = self.create_embeddings([query_text])[0]
        
        namespace = self._get_namespace()
        
        # Build filter
        query_filter = {}
        if self.company:
            query_filter['company_id'] = self.company.id
        if filter_metadata:
            query_filter.update(filter_metadata)
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            filter=query_filter if query_filter else None,
            include_metadata=True
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                'id': match.id,
                'score': match.score,
                'content': match.metadata.get('content', ''),
                'document_id': match.metadata.get('document_id'),
                'metadata': match.metadata
            })
        
        return formatted_results
    
    def get_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = 5
    ) -> str:
        """
        Get relevant context for a query
        
        Args:
            query: User query
            max_tokens: Approximate max tokens for context
            top_k: Number of chunks to retrieve
        
        Returns:
            Combined context string
        """
        results = self.query(query, top_k=top_k)
        
        if not results:
            return ""
        
        # Combine results
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Rough char to token ratio
        
        for result in results:
            content = result.get('content', '')
            if total_chars + len(content) > max_chars:
                break
            context_parts.append(content)
            total_chars += len(content)
        
        return "\n\n---\n\n".join(context_parts)
