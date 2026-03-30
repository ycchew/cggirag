import asyncio
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import faiss
import os
import re


def extract_years_from_query(query: str) -> List[int]:
    """Extract all explicit 4-digit years from query (2021 onwards)

    Examples:
        "top countries 2023" → [2023]
        "compare 2021 and 2024" → [2021, 2024]
        "What is CGGI?" → []
    """
    # Matches 2021-2029, 2030-2099 (future reports)
    matches = re.findall(r"\b(202[1-9]|20[3-9]\d)\b", query)
    return [int(m) for m in matches]


logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(embedding_model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.documents = []  # Stores document metadata
        self.contents = []  # Stores document text content
        self.doc_ids = []  # Stores document IDs
        logger.info(f"Initialized vector store with dimension: {self.dimension}")

    def create_index(self):
        """Create a FAISS index for similarity search"""
        # Use FAISS IndexFlatIP (Inner Product) which is equivalent to cosine similarity
        # when vectors are normalized
        self.index = faiss.IndexFlatIP(self.dimension)
        logger.info("FAISS index created")

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
        ids: List[str] = None,
    ):
        """Add documents to the vector store"""
        if not texts:
            logger.warning("No texts provided to add_documents")
            return

        # Store text content
        self.contents.extend(texts)

        # Generate embeddings
        embeddings = self.model.encode(texts)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add to index
        self.index.add(embeddings.astype("float32"))

        # Store metadata
        if metadatas:
            self.documents.extend(metadatas)
        else:
            self.documents.extend([{}] * len(texts))

        # Store IDs
        if ids:
            self.doc_ids.extend(ids)
        else:
            start_id = len(self.doc_ids)
            self.doc_ids.extend([f"doc_{start_id + i}" for i in range(len(texts))])

        logger.info(f"Added {len(texts)} documents to vector store")

    def similarity_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search in the vector store"""
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []

        # Generate embedding for query
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)

        # Perform search
        scores, indices = self.index.search(query_embedding.astype("float32"), k)

        # Format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:  # Valid index
                result = {
                    "id": self.doc_ids[idx],
                    "content": self.contents[idx],
                    "metadata": self.documents[idx],
                    "similarity_score": float(score),
                }
                results.append(result)

        return results

    def similarity_search_with_filter(
        self, query: str, k: int = 5, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search with metadata filtering applied post-retrieval

        Args:
            query: Search query text
            k: Number of results to return
            filters: Dict of metadata filters, e.g., {"year": [2021, 2024]}
                     Uses OR logic for list values (match ANY)

        Returns:
            Filtered results if matches found, else unfiltered fallback
        """

        # Get more candidates for filtering (k × 10 ensures year-specific matches)
        candidates = self.similarity_search(query, k=k * 10)

        if not filters:
            return candidates[:k]

        # Filter by metadata with OR logic for list values
        filtered = []
        for doc in candidates:
            match = True
            for key, value in filters.items():
                doc_value = doc.get("metadata", {}).get(key)

                # OR logic: if value is list, match ANY
                if isinstance(value, list):
                    if doc_value not in value:
                        match = False
                        break
                else:
                    if doc_value != value:
                        match = False
                        break

            if match:
                filtered.append(doc)

        # Fallback: if filtering returns empty, return unfiltered results
        return filtered[:k] if filtered else candidates[:k]

    def save(self, filepath: str):
        """Save the vector store to disk"""
        import faiss

        # Save FAISS index separately (required for proper serialization)
        index_path = filepath.replace(".pkl", ".index")
        faiss.write_index(self.index, index_path)

        # Save metadata separately with pickle
        data = {
            "documents": self.documents,
            "contents": self.contents,
            "doc_ids": self.doc_ids,
            "dimension": self.dimension,
            "index_path": index_path,
        }

        with open(filepath, "wb") as f:
            pickle.dump(data, f)

        logger.info(f"Vector store saved to {filepath}")

    def load(self, filepath: str):
        """Load the vector store from disk"""
        import faiss

        if not os.path.exists(filepath):
            logger.error(f"Vector store file does not exist: {filepath}")
            return

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.contents = data["contents"]
        self.doc_ids = data["doc_ids"]
        self.dimension = data["dimension"]

        # Load FAISS index from separate file
        index_path = data.get("index_path", filepath.replace(".pkl", ".index"))
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            logger.info(
                f"Vector store loaded from {filepath} with {self.index.ntotal} vectors"
            )
        else:
            logger.error(f"FAISS index file not found: {index_path}")
            self.index = None


# Example usage
async def main():
    # Create vector store
    vs = VectorStore()
    vs.create_index()

    # Sample documents
    documents = [
        "The Chandler Good Government Index measures government effectiveness.",
        "CGGI evaluates countries across seven pillars of good governance.",
        "Singapore consistently ranks among the top performers in CGGI.",
        "The index includes pillars like leadership, institutions, and financial stewardship.",
    ]

    # Add documents
    vs.add_documents(documents)

    # Search
    results = vs.similarity_search("Which country performs best in CGGI?", k=2)

    for result in results:
        print(f"Score: {result['similarity_score']:.3f}")
        print(f"Content: {result['content'][:100]}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())
