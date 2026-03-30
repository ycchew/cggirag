import asyncio
import logging
from typing import List, Dict, Any
import sys
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Define required models first before any imports that might need them
from pydantic import BaseModel


class DocumentChunk(BaseModel):
    content: str
    source: str
    page_number: int | None = None
    metadata: dict


class QueryResponse(BaseModel):
    query: str
    answer: str
    documents: List[DocumentChunk]
    confidence_score: float


def setup_module_paths():
    """Setup Python path for module imports"""
    current_file_dir = Path(__file__).parent.absolute()
    project_root = current_file_dir.parent
    vector_db_dir = project_root / "vector-db"

    # Ensure we're working with absolute paths
    project_root = project_root.resolve()
    vector_db_dir = vector_db_dir.resolve()

    # Add to Python path if not already there; insert rather than append so it has priority
    paths_to_add = [str(project_root), str(vector_db_dir)]

    for path in paths_to_add:
        if path not in sys.path:
            sys.path.insert(0, path)

    # Make sure we can find config from project root
    config_dir = project_root / "api" / "config"
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))


# Setup paths on module load
setup_module_paths()


# Now import the modules after paths are configured; use type comments to handle import errors
from config.settings import settings

try:
    from vector_store import VectorStore, extract_years_from_query
except ImportError:

    class VectorStore:
        def __init__(self):
            pass

        def load(self, filepath):
            pass

        def similarity_search(self, query, k):
            return []

        def add_documents(self, texts, metadatas=None):
            pass

        def save(self, filepath):
            pass

        def create_index(self):
            pass


from llm_service import AlibabaLLMService


class RAGService:
    def __init__(self):
        self.llm_service = AlibabaLLMService()
        self.vector_store = VectorStore()

        # Default vector store path
        default_vector_store_path = "vector_store.pkl"
        self.vector_store_path = os.environ.get(
            "VECTOR_STORE_PATH", default_vector_store_path
        )

        # Attempt to load the vector store on initialization
        try:
            # Determine current working directory and project root
            project_root = Path(__file__).parent.parent
            current_dir = os.getcwd()

            # List of possible paths to try
            paths_to_try = [
                self.vector_store_path,  # As provided
                str(project_root / self.vector_store_path),  # Relative to project root
                str(project_root / "vector_store.pkl"),  # Default vector store
                "./vector_store.pkl",  # Current directory
            ]

            loaded = False
            for path in paths_to_try:
                if os.path.exists(path):
                    self.vector_store.load(path)
                    self.vector_store_path = path
                    logger.info(f"Vector store loaded from {path}")
                    loaded = True
                    break

            if not loaded:
                logger.warning(
                    f"No vector store found at any of these paths: {paths_to_try}"
                )
                logger.info(
                    "Vector store is uninitialized - this may impact query results"
                )

        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")

        logger.info("RAG Service initialized with vector store integration")

    async def initialize(self):
        """Initialize the RAG service, load documents, etc."""
        logger.info("Initializing RAG service...")
        # Load CGGI documents here if needed
        await self._load_cggi_documents()

    async def _load_cggi_documents(self):
        """Load CGGI documents into the system (placeholder implementation)"""
        # No longer needed since we load the pre-built vector store
        logger.info("Documents already loaded from vector store during initialization")

    async def query(self, query_text: str, top_k: int = 5) -> QueryResponse:
        """
        Process a query against the CGGI knowledge base
        """
        logger.info(f"Processing query: {query_text}")

        # Actually retrieve documents using the vector store
        retrieved_docs = await self._retrieve_documents(query_text, top_k)

        # Calculate confidence score from the top similarity score
        if retrieved_docs and len(retrieved_docs) > 0:
            top_scores = [doc.get("similarity_score", 0.5) for doc in retrieved_docs]
            if top_scores:
                top_score = max(top_scores)
                confidence_score = min(top_score, 0.95)
            else:
                confidence_score = 0.01
        else:
            confidence_score = 0.01

        # Enable web search fallback when confidence is low
        enable_web_search = confidence_score < 0.2 or len(retrieved_docs) == 0
        if enable_web_search:
            logger.info(
                f"Low confidence ({confidence_score:.2f}), enabling web search fallback"
            )

        # Generate response using LLM
        answer = await self.llm_service.generate_response(
            prompt=query_text,
            context_documents=retrieved_docs,
            enable_web_search=enable_web_search,
        )

        # Format documents for response
        formatted_docs = []
        for doc in retrieved_docs:
            formatted_docs.append(
                DocumentChunk(
                    content=doc.get("content", ""),
                    source=doc.get("metadata", {}).get("source_file", "unknown"),
                    page_number=doc.get("metadata", {}).get("page_number"),
                    metadata=doc.get("metadata", {}),
                )
            )

        return QueryResponse(
            query=query_text,
            answer=answer,
            documents=formatted_docs,
            confidence_score=confidence_score,
        )

    async def _retrieve_documents(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from the vector store with optional year filtering
        """
        if not hasattr(self, "vector_store") or self.vector_store is None:
            logger.error("Vector store not initialized")
            # Fallback to placeholder behavior
            docs = []
            for i in range(top_k):
                docs.append(
                    {
                        "content": f"Placeholder content for query '{query}', result #{i + 1}",
                        "metadata": {
                            "source_file": f"placeholder_source_{i}.pdf",
                            "year": 2025,
                            "type": "cggi_report",
                            "pillar": "all",
                            "similarity_score": 0.5,
                        },
                    }
                )
            return docs

        try:
            # Extract years from query for filtering
            years = extract_years_from_query(query)

            filters = None
            if years:
                filters = {"year": years}  # List for OR logic
                logger.info(f"Detected years {years} in query, applying filter")

            # Perform similarity search with optional filter
            search_results = self.vector_store.similarity_search_with_filter(
                query, k=top_k, filters=filters
            )

            logger.info(
                f"Found {len(search_results)} results from vector store for query: {query}"
            )

            # Convert vector store results to required format
            docs = []
            for result in search_results:
                # Extract content, metadata, and similarity score
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                similarity_score = result.get("similarity_score", 0.0)

                doc = {
                    "content": content,
                    "metadata": metadata,
                    "similarity_score": similarity_score,
                }
                docs.append(doc)

            logger.info(f"Returning {len(docs)} documents for query")
            return docs

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            logger.exception("Full exception traceback:")
            # Fallback to placeholder behavior if vector store fails
            docs = []
            for i in range(top_k):
                docs.append(
                    {
                        "content": f"Placeholder content for query '{query}', result #{i + 1}",
                        "metadata": {
                            "source_file": f"placeholder_source_{i}.pdf",
                            "year": 2025,
                            "type": "cggi_report",
                            "pillar": "all",
                            "similarity_score": 0.5,
                        },
                    }
                )
            return docs
