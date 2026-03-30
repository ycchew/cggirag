import asyncio
import logging
from typing import List, Dict, Any, Optional
import json
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """
    A simple vector store implementation using TF-IDF and cosine similarity
    This is a simplified version that doesn't require FAISS or sentence transformers
    """

    def __init__(self):
        self.documents = []  # Stores document metadata
        self.contents = []  # Stores document text content
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=10000)
        self.tfidf_matrix = None
        logger.info("Simple vector store initialized")

    def add_documents(self, texts: List[str], metadatas: List[Dict[str, Any]] = None):
        """Add documents to the vector store"""
        if not texts:
            logger.warning("No texts provided to add_documents")
            return

        self.contents.extend(texts)

        # Add metadata
        if metadatas:
            self.documents.extend(metadatas)
        else:
            self.documents.extend([{}] * len(texts))

        # Fit/update the TF-IDF matrix
        self.tfidf_matrix = self.vectorizer.fit_transform(self.contents)
        logger.info(f"Added {len(texts)} documents to vector store")

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search in the vector store"""
        if not self.contents or self.tfidf_matrix is None:
            logger.warning("Vector store is empty")
            return []

        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([query])

        # Calculate cosine similarities
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()

        # Get top-k results
        top_indices = similarities.argsort()[-k:][::-1]

        # Format results
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only include if similarity > 0
                result = {
                    "id": f"doc_{idx}",
                    "content": self.contents[idx],
                    "metadata": self.documents[idx],
                    "similarity_score": float(similarities[idx]),
                }
                results.append(result)

        return results

    def save(self, filepath: str):
        """Save the vector store to disk"""
        data = {
            "contents": self.contents,
            "documents": self.documents,
            "vectorizer": self.vectorizer,
            "tfidf_matrix": self.tfidf_matrix,
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Vector store saved to {filepath}")

    def load(self, filepath: str):
        """Load the vector store from disk"""
        if not os.path.exists(filepath):
            logger.error(f"Vector store file does not exist: {filepath}")
            return

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.contents = data["contents"]
        self.documents = data["documents"]
        self.vectorizer = data["vectorizer"]
        self.tfidf_matrix = data["tfidf_matrix"]

        logger.info(f"Vector store loaded from {filepath}")


# Example usage
async def main():
    # Create vector store
    vs = SimpleVectorStore()

    # Sample documents
    documents = [
        "The Chandler Good Government Index measures government effectiveness.",
        "CGGI evaluates countries across seven pillars of good governance.",
        "Singapore consistently ranks among the top performers in CGGI.",
        "The index includes pillars like leadership, institutions, and financial stewardship.",
        "CGGI was launched in 2021 by the Chandler Institute of Governance.",
    ]

    # Metadata for each document
    metadatas = [
        {"source": "cggi_faq.pdf", "year": 2025, "topic": "overview"},
        {"source": "cggi_methodology.pdf", "year": 2025, "topic": "pillars"},
        {"source": "cggi_rankings_2025.pdf", "year": 2025, "topic": "rankings"},
        {"source": "cggi_framework.pdf", "year": 2025, "topic": "framework"},
        {"source": "cggi_about.pdf", "year": 2021, "topic": "history"},
    ]

    # Add documents
    vs.add_documents(documents, metadatas)

    # Search
    results = vs.similarity_search("Which country performs best in CGGI?", k=2)

    for result in results:
        print(f"Score: {result['similarity_score']:.3f}")
        print(f"Content: {result['content'][:100]}...")
        print(f"Metadata: {result['metadata']}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
