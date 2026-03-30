#!/usr/bin/env python3
"""
Document ingestion script for CGGI RAG system.
This script processes CGGI PDF reports and loads them into the vector store.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any
import pickle

# Add project root to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from document_processor import CGGIDocumentProcessor

# Import the vector store from the correct location
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "vector-db"))
from vector_store import VectorStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("ingestion.log")],
)
logger = logging.getLogger(__name__)


class DocumentIngestor:
    def __init__(self, source_dir: str, vector_store_path: str = "vector_store.pkl"):
        self.source_dir = Path(source_dir)
        self.vector_store_path = vector_store_path
        self.processor = CGGIDocumentProcessor(source_dir)
        self.vector_store = VectorStore()
        self.vector_store.create_index()

    async def ingest_documents(self):
        """Main ingestion workflow"""
        logger.info(f"Starting document ingestion from {self.source_dir}")

        # Process PDF documents
        logger.info("Processing CGGI reports...")
        chunks = await self.processor.process_cggi_reports()
        logger.info(f"Processed {len(chunks)} document chunks")

        # Prepare data for vector store
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Add documents to vector store
        logger.info("Adding documents to vector store...")
        self.vector_store.add_documents(texts, metadatas)

        # Save vector store
        logger.info(f"Saving vector store to {self.vector_store_path}...")
        self.vector_store.save(self.vector_store_path)

        logger.info(f"Successfully ingested {len(chunks)} document chunks")
        return len(chunks)

    def load_vector_store(self):
        """Load the vector store from disk"""
        if self.vector_store_path and Path(self.vector_store_path).exists():
            self.vector_store.load(self.vector_store_path)
            logger.info(f"Loaded vector store from {self.vector_store_path}")
        else:
            logger.warning(f"Vector store file not found: {self.vector_store_path}")

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the vector store"""
        return self.vector_store.similarity_search(query, k)


async def main():
    # Define source directory containing CGGI PDFs
    source_dir = "D:\\dev\\CGGI\\docs\\source\\"

    # Create ingestor
    ingestor = DocumentIngestor(source_dir)

    # Ingest documents
    num_ingested = await ingestor.ingest_documents()
    print(f"Ingested {num_ingested} document chunks")

    # Test search functionality
    print("\nTesting search functionality:")
    test_queries = [
        "top countries in CGGI 2025",
        "seven pillars of good governance",
        "Singapore performance in CGGI",
    ]

    for query in test_queries:
        results = ingestor.search(query, k=2)
        print(f"\nQuery: {query}")
        for i, result in enumerate(results):
            print(f"  Result {i + 1}: Score {result['similarity_score']:.3f}")
            print(f"    Content preview: {result['content'][:100]}...")
            print(f"    Source: {result['metadata'].get('source_file', 'Unknown')}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
