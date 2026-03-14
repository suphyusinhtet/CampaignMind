# rag/knowledge_manager.py
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Optional
import uuid
import logging
from pathlib import Path

from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeManager:
    """
    Manages document ingestion, embedding, and retrieval for CampaignMind AI.
    Uses ChromaDB for vector storage and LangChain for text processing.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the knowledge manager.
        
        Args:
            persist_directory: Where to store ChromaDB data. Defaults to settings.VECTOR_DB_PATH
        """
        self.persist_directory = persist_directory or settings.VECTOR_DB_PATH
        
        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create collections for different knowledge types
        self.collections = {
            "trends": self._get_or_create_collection("trends"),
            "case_studies": self._get_or_create_collection("case_studies"),
            "market_research": self._get_or_create_collection("market_research"),
            "brand_guidelines": self._get_or_create_collection("brand_guidelines"),
        }
        
        # Initialize embeddings (using OpenAI-compatible endpoint with Gemini won't work for embeddings)
        # For now we'll use ChromaDB's default embeddings (sentence transformers)
        # In production, you'd use Google's embedding API or OpenAI embeddings
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        
        logger.info(f"KnowledgeManager initialized with {len(self.collections)} collections")
        logger.info(f"Persist directory: {self.persist_directory}")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a ChromaDB collection."""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def ingest_document(
        self,
        content: str,
        doc_type: str,
        metadata: Dict[str, str]
    ) -> int:
        """
        Ingest a document into the knowledge base.
        
        Args:
            content: Document text content
            doc_type: One of 'trends', 'case_studies', 'market_research', 'brand_guidelines'
            metadata: Dict with keys like:
                - source: Source name/title
                - industry: Industry category
                - geography: Geographic region
                - audience: Target audience
                - campaign_type: Campaign type
                - date: Publication date
                - author: Author name (optional)
        
        Returns:
            Number of chunks created
        """
        if doc_type not in self.collections:
            raise ValueError(
                f"Invalid doc_type: {doc_type}. "
                f"Must be one of {list(self.collections.keys())}"
            )
        
        # Chunk the document
        chunks = self.text_splitter.split_text(content)
        
        if not chunks:
            logger.warning(f"No chunks created from document: {metadata.get('source', 'unknown')}")
            return 0
        
        # Generate IDs and prepare data
        collection = self.collections[doc_type]
        
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{metadata.get('source', 'unknown')}_{uuid.uuid4().hex[:8]}"
            chunk_metadata = {
                **metadata,
                "chunk_index": str(i),
                "total_chunks": str(len(chunks)),
                "doc_type": doc_type
            }
            
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)
            chunk_metadatas.append(chunk_metadata)
        
        # Add to collection
        collection.add(
            documents=chunk_texts,
            metadatas=chunk_metadatas,
            ids=chunk_ids
        )
        
        logger.info(
            f"Ingested {len(chunks)} chunks from '{metadata.get('source', 'unknown')}' "
            f"into {doc_type} collection"
        )
        
        return len(chunks)
    
    def query(
        self,
        query_text: str,
        doc_type: str,
        filters: Optional[Dict[str, str]] = None,
        n_results: int = None
    ) -> List[Dict]:
        """
        Query the knowledge base.
        
        Args:
            query_text: Search query
            doc_type: Collection to search ('trends', 'case_studies', etc.)
            filters: Metadata filters (e.g., {"industry": "tech", "geography": "US"})
            n_results: Number of results to return (defaults to settings.RAG_TOP_K)
        
        Returns:
            List of dicts with keys: content, metadata, distance
        """
        if doc_type not in self.collections:
            raise ValueError(
                f"Invalid doc_type: {doc_type}. "
                f"Must be one of {list(self.collections.keys())}"
            )
        
        n_results = n_results or settings.RAG_TOP_K
        collection = self.collections[doc_type]
        
        # Build where clause for filters
        where = filters if filters else None
        
        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
        
        # Format results
        formatted_results = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        logger.info(f"Query returned {len(formatted_results)} results from {doc_type}")
        
        return formatted_results
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get document counts for all collections."""
        stats = {}
        for name, collection in self.collections.items():
            stats[name] = collection.count()
        return stats
    
    def reset_collection(self, doc_type: str) -> None:
        """Delete all documents from a collection."""
        if doc_type not in self.collections:
            raise ValueError(f"Invalid doc_type: {doc_type}")
        
        collection_name = doc_type
        self.client.delete_collection(name=collection_name)
        self.collections[doc_type] = self._get_or_create_collection(collection_name)
        logger.info(f"Reset collection: {doc_type}")
    
    def reset_all(self) -> None:
        """Delete all collections and data. Use with caution!"""
        for doc_type in list(self.collections.keys()):
            self.reset_collection(doc_type)
        logger.warning("All collections have been reset")


# Singleton instance
_knowledge_manager = None


def get_knowledge_manager() -> KnowledgeManager:
    """Get or create the global KnowledgeManager instance."""
    global _knowledge_manager
    if _knowledge_manager is None:
        _knowledge_manager = KnowledgeManager()
    return _knowledge_manager