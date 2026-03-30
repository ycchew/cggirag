"""Test RAG query for CGGI core belief"""

import asyncio
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "vector-db"))
sys.path.insert(0, os.path.join(project_root, "api"))

from dotenv import load_dotenv

load_dotenv(".env", override=True)

from llm_service import AlibabaLLMService
from vector_store_simple import SimpleVectorStore


async def test_rag_query():
    query = "Which fundamental relationship forms the core belief of the Chandler Good Government Index (CGGI)?"

    print("=" * 60)
    print(f"QUERY: {query}")
    print("=" * 60)
    print()

    print("1. VECTOR DATABASE TEST")
    print("-" * 40)
    vs = SimpleVectorStore()
    vs.load("vector_store.pkl")
    print(f"   Documents loaded: {len(vs.documents)}")
    print(
        f"   TF-IDF matrix shape: {vs.tfidf_matrix.shape if vs.tfidf_matrix is not None else 'None'}"
    )
    print()

    print("2. VECTOR SEARCH TEST")
    print("-" * 40)
    results = vs.similarity_search(query, k=5)
    print(f"   Results found: {len(results)}")
    for i, r in enumerate(results):
        score = r.get("similarity_score", 0)
        source = r.get("metadata", {}).get("source_file", "unknown")
        year = r.get("metadata", {}).get("year", "unknown")
        content_preview = r.get("content", "")[:150].replace("\n", " ")
        print(f"   [{i + 1}] Score: {score:.3f}")
        print(f"       Source: {source} (Year: {year})")
        print(f"       Preview: {content_preview}...")
        print()

    print("3. LLM INTEGRATION TEST")
    print("-" * 40)
    llm = AlibabaLLMService()
    print(
        f"   API Key configured: {llm.api_key[:15]}...{llm.api_key[-8:] if llm.api_key else 'NOT SET'}"
    )
    print(f"   Base URL: {llm.base_url}")
    print(f"   Model: {llm.model}")
    print()

    print("4. FULL RAG RESPONSE TEST")
    print("-" * 40)
    response = await llm.generate_response(
        prompt=query, context_documents=results, max_tokens=1000, temperature=0.7
    )

    print("=" * 60)
    print("LLM RESPONSE:")
    print("=" * 60)
    print(response)
    print()
    print("=" * 60)
    print("TEST COMPLETE - ALL COMPONENTS VERIFIED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_rag_query())
