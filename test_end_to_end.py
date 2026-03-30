#!/usr/bin/env python3
"""
Test script to verify end-to-end functionality of RAG system
after connecting components together
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_end_to_end():
    """Test the end-to-end functionality of the RAG system"""
    print("=" * 60)
    print("TESTING END-TO-END RAG SYSTEM FUNCTIONALITY")
    print("=" * 60)

    # Test 1: Check if vector store file exists
    print("\n1. CHECKING VECTOR STORE FILE...")
    vector_store_path = project_root / "vector_store.pkl"
    if vector_store_path.exists():
        print(f"SUCCESS: Vector store file found: {vector_store_path}")
        print(f"   File size: {vector_store_path.stat().st_size} bytes")
    else:
        print(f"ERROR: Vector store file NOT FOUND at {vector_store_path}")
        return False

    # Test 2: Test the RAG Service initialization
    print("\n2. TESTING RAG SERVICE INITIALIZATION...")
    try:
        api_dir = project_root / "api"
        vector_db_dir = project_root / "vector-db"

        for path in [str(project_root), str(api_dir), str(vector_db_dir)]:
            if path not in sys.path:
                sys.path.insert(0, path)

        old_cwd = os.getcwd()
        os.chdir(api_dir)

        print("Attempting to import modules...")
        from config.settings import settings

        print("Config settings imported")

        import rag_service

        os.chdir(old_cwd)

        print("SUCCESS: RAG Service module imported successfully")

        rag_service_instance = rag_service.RAGService()
        print("SUCCESS: RAG Service initialized successfully")

        if (
            hasattr(rag_service_instance, "vector_store")
            and rag_service_instance.vector_store
        ):
            if (
                hasattr(rag_service_instance.vector_store, "contents")
                and rag_service_instance.vector_store.contents
            ):
                print(
                    f"SUCCESS: Vector store loaded with {len(rag_service_instance.vector_store.contents)} documents"
                )
            elif (
                hasattr(rag_service_instance.vector_store, "tfidf_matrix")
                and rag_service_instance.vector_store.tfidf_matrix is not None
            ):
                print(
                    f"SUCCESS: Vector store loaded with TF-IDF matrix shape: {rag_service_instance.vector_store.tfidf_matrix.shape}"
                )
            else:
                print(
                    "WARNING: Vector store is initialized but appears to have no content"
                )
        else:
            print("ERROR: Vector store is not properly initialized")

    except Exception as e:
        print(f"ERROR: Error initializing RAG service: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    # Test 3: Test actual search functionality
    print("\n3. TESTING DOCUMENT RETRIEVAL...")
    try:
        test_query = "top countries in CGGI 2025"
        retrieved_docs = await rag_service_instance._retrieve_documents(
            test_query, top_k=3
        )

        print(
            f"SUCCESS: Retrieved {len(retrieved_docs)} documents for query: '{test_query}'"
        )

        for i, doc in enumerate(retrieved_docs, 1):
            content_preview = (
                doc.get("content", "")[:100] + "..."
                if len(doc.get("content", "")) > 100
                else doc.get("content", "")
            )
            similarity_score = doc.get("similarity_score", "N/A")
            source_file = doc.get("metadata", {}).get("source_file", "Unknown")
            print(f"   Document {i}: Score={similarity_score}, Source={source_file}")
            print(f"   Content preview: {content_preview}")

    except Exception as e:
        print(f"ERROR: Error during document retrieval: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    # Test 4: Test full query functionality
    print("\n4. TESTING FULL QUERY FLOW...")
    try:
        test_query = "Top performing countries in CGGI"
        response = await rag_service_instance.query(test_query, top_k=2)

        print(f"SUCCESS: RAG query executed successfully")
        print(f"   Query: {test_query}")
        print(
            f"   Answer preview: {response.answer[:100] if response.answer else 'None'}..."
        )
        print(f"   Number of supporting documents: {len(response.documents)}")
        print(f"   Confidence score: {response.confidence_score}")

        for i, doc in enumerate(response.documents, 1):
            content_preview = (
                doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
            )
            print(f"   Doc {i} source: {doc.source}, preview: {content_preview}")

    except Exception as e:
        print(f"ERROR: Error during full query flow: {str(e)}")
        import traceback

        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("ALL END-TO-END TESTS PASSED!")
    print("The RAG system is functioning correctly with connected components.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_end_to_end())
    if not success:
        print("\nSome tests failed. Please check the logs above.")
        sys.exit(1)
    else:
        print("\nRAG system is fully operational!")
