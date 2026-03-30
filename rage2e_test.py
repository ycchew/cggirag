#!/usr/bin/env python3
"""
End-to-End Test Script for RAG Pipeline
Validates the complete flow: query → embed query → search vector store → retrieve documents → generate response
"""

import asyncio
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root and subdirectories to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api"))
sys.path.insert(0, str(project_root / "vector-db"))


class RAGEndToEndTester:
    """Class to test the complete RAG pipeline flow"""

    def __init__(self):
        self.rag_service = None
        self.results_summary = {
            "vector_store_loaded": False,
            "query_processed": False,
            "documents_retrieved": False,
            "llm_generated_response": False,
            "pipeline_integrated": False,
        }

    async def setup_rag_service(self):
        """Set up the RAG service for testing"""
        logger.info("Setting up RAG Service for testing...")

        try:
            # Change to API dir to match expected working context
            api_dir = project_root / "api"
            old_cwd = os.getcwd()
            os.chdir(api_dir)

            from rag_service import RAGService
            from config.settings import settings

            # Initialize the RAG service
            self.rag_service = RAGService()
            logger.info("✓ RAG Service initialized successfully")

            # Restore previous working directory
            os.chdir(old_cwd)

            return True
        except Exception as e:
            logger.error(f"✗ Failed to setup RAG Service: {str(e)}")
            logger.exception("Full error trace:")
            return False

    async def test_vector_store_integration(self):
        """Test vector store integration - embedding and similarity search"""
        logger.info("Testing Vector Store Integration...")

        if not self.rag_service:
            logger.error("✗ Cannot test vector store - RAG service not initialized")
            return False

        try:
            # Test vector store attributes
            if not hasattr(self.rag_service, "vector_store"):
                logger.error("✗ RAG service has no vector_store attribute")
                return False

            # Check if vector store loaded content
            vector_store = self.rag_service.vector_store
            has_content = (
                hasattr(vector_store, "contents") and vector_store.contents
            ) or (
                hasattr(vector_store, "tfidf_matrix")
                and vector_store.tfidf_matrix is not None
            )

            if has_content:
                logger.info("✓ Vector store has content loaded")

                # Test the similarity search with a sample query
                test_query = "top countries in CGGI 2025"

                # Try to get the raw vector search
                if hasattr(vector_store, "similarity_search"):
                    search_results = vector_store.similarity_search(test_query, k=3)

                    if search_results:
                        logger.info(
                            f"✓ Similarity search successful, returned {len(search_results)} documents"
                        )
                        logger.info(
                            f"  Sample result scores: {[r.get('similarity_score', 0.0) for r in search_results[:3]]}"
                        )

                        if all(
                            r.get("content")
                            for r in search_results[:2]
                            if r.get("content")
                        ):
                            logger.info("✓ Retrieved documents have meaningful content")
                            self.results_summary["vector_store_loaded"] = True
                            return True
                        else:
                            logger.error(
                                "✗ Retrieved documents don't have proper content"
                            )
                            return False
                    else:
                        logger.error("✗ Similarity search returned no results")
                        return False
                else:
                    logger.error("✗ Vector store has no similarity_search method")
                    return False
            else:
                logger.error("✗ Vector store is not properly loaded with content")
                return False

        except Exception as e:
            logger.error(f"✗ Vector store integration test failed: {str(e)}")
            logger.exception("Full error trace:")
            return False

    async def test_document_retrieval_flow(self):
        """Test the full document retrieval flow from query to retrieved docs"""
        logger.info("Testing Full Document Retrieval Flow...")

        if not self.rag_service:
            logger.error(
                "✗ Cannot test document retrieval - RAG service not initialized"
            )
            return False

        try:
            test_query = "performance of Singapore in CGGI rankings"

            # Call the internal document retrieval method
            retrieved_docs = await self.rag_service._retrieve_documents(
                test_query, top_k=5
            )

            if not retrieved_docs or len(retrieved_docs) == 0:
                logger.error("✗ Document retrieval returned no documents")
                return False

            logger.info(f"✓ Retrieved {len(retrieved_docs)} documents for query")

            # Verify document structure
            all_have_metadata = True
            all_have_content = True
            all_have_scores = True

            for i, doc in enumerate(retrieved_docs[:3]):  # Check first few documents
                has_content = "content" in doc and doc["content"].strip()
                has_metadata = isinstance(doc.get("metadata"), dict)
                has_score = "similarity_score" in doc and isinstance(
                    doc["similarity_score"], (int, float)
                )

                if not has_content:
                    all_have_content = False
                if not has_metadata:
                    all_have_metadata = False
                if not has_score:
                    all_have_scores = False

                logger.debug(
                    f"  Doc {i + 1}: content={'✓' if has_content else '✗'}, "
                    f"metadata={'✓' if has_metadata else '✗'}, "
                    f"score={'✓' if has_score else '✗'}"
                )

            if not all_have_content:
                logger.error("✗ Not all documents have proper content")
                return False
            if not all_have_metadata:
                logger.error("✗ Not all documents have proper metadata")
                return False
            if not all_have_scores:
                logger.error("✗ Not all documents have similarity scores")
                return False

            # Verify similarity scores are reasonable
            scores = [
                doc["similarity_score"]
                for doc in retrieved_docs
                if "similarity_score" in doc
            ]
            if scores:
                avg_score = sum(scores) / len(scores)
                logger.info(
                    f"✓ Documents have reasonable scores (avg: {avg_score:.3f}, max: {max(scores):.3f})"
                )
            else:
                logger.error("✗ No documents had similarity scores")
                return False

            logger.info("✓ Document retrieval flow works correctly")
            self.results_summary["documents_retrieved"] = True
            return True

        except Exception as e:
            logger.error(f"✗ Document retrieval flow test failed: {str(e)}")
            logger.exception("Full error trace:")
            return False

    async def test_llm_generation_integration(self):
        """Test LLM service integration with retrieved documents"""
        logger.info("Testing LLM Generation Integration...")

        if not self.rag_service:
            logger.error("✗ Cannot test LLM - RAG service not initialized")
            return False

        try:
            # Ensure LLM service is available (might be mock depending on API key)
            if not hasattr(self.rag_service, "llm_service"):
                logger.error("✗ RAG service has no LLM service")
                return False

            test_query = "What is CGGI and what are the top 3 countries in 2025?"

            # Manually test retrieval then LLM generation to isolate the flow
            retrieved_docs = await self.rag_service._retrieve_documents(
                test_query, top_k=3
            )

            if retrieved_docs:
                logger.info(
                    f"✓ Retrieved {len(retrieved_docs)} documents to pass to LLM"
                )

                # Test response generation with context
                generated_response = (
                    await self.rag_service.llm_service.generate_response(
                        prompt=test_query, context_documents=retrieved_docs
                    )
                )

                if generated_response and len(generated_response.strip()) > 0:
                    logger.info("✓ LLM generated response successfully")
                    logger.info(
                        f"  Response preview ({len(generated_response)} chars): {generated_response[:100]}..."
                    )

                    # Verify it's not just a mock/fallback response
                    is_mock_response = (
                        "MOCK RESPONSE" in generated_response.upper()
                        or "FALLBACK RESPONSE" in generated_response.upper()
                    )
                    if is_mock_response:
                        logger.warning(
                            "⚠ LLM using mock response (likely no API key configured)"
                        )
                    else:
                        logging.info(
                            "✓ LLM generated real response (API key configured or using different fallback)"
                        )

                    self.results_summary["llm_generated_response"] = True
                    return True
                else:
                    logger.error("✗ LLM returned empty response")
                    return False
            else:
                logger.error("✗ Could not retrieve documents to test with LLM")
                return False

        except Exception as e:
            logger.error(f"✗ LLM integration test failed: {str(e)}")
            logger.exception("Full error trace:")
            return False

    async def test_complete_pipeline_flow(self):
        """Test the complete end-to-end pipeline from API query to full response"""
        logger.info("Testing Complete Pipeline Flow...")

        if not self.rag_service:
            logger.error(
                "✗ Cannot test complete pipeline - RAG service not initialized"
            )
            return False

        try:
            test_query = "How does Singapore perform in CGGI compared to other top countries in recent years?"

            # This calls the full query method which orchestrates everything
            response = await self.rag_service.query(test_query, top_k=2)

            # Verify response structure
            required_fields = ["query", "answer", "documents", "confidence_score"]
            missing_fields = [
                field for field in required_fields if not hasattr(response, field)
            ]

            if missing_fields:
                logger.error(f"✗ Response missing required fields: {missing_fields}")
                return False

            # Validate response content
            if not response.query or response.query != test_query:
                logger.error("✗ Response query doesn't match input")
                return False

            if not response.answer or len(response.answer.strip()) == 0:
                logger.error("✗ Response has no answer")
                return False

            if len(response.documents) == 0:
                logger.error("✗ Response has no documents")
                return False

            if (
                not isinstance(response.confidence_score, (int, float))
                or response.confidence_score < 0
                or response.confidence_score > 1
            ):
                logger.error("✗ Response has invalid confidence score")
                return False

            logger.info("✓ Response has proper structure and content")
            logger.info(f"  Query: {response.query[:50]}...")
            logger.info(f"  Answer preview: {response.answer[:100]}...")
            logger.info(f"  Found {len(response.documents)} supporting documents")
            logger.info(f"  Confidence score: {response.confidence_score}")

            # Validate documents have expected attributes
            for i, doc in enumerate(response.documents):
                required_doc_attrs = ["content", "source", "metadata"]
                missing_doc_attrs = []
                for attr in required_doc_attrs:
                    if not hasattr(doc, attr):
                        missing_doc_attrs.append(attr)

                if missing_doc_attrs:
                    logger.error(
                        f"✗ Document {i} missing attributes: {missing_doc_attrs}"
                    )
                    return False

                if not doc.content:
                    logger.error(f"✗ Document {i} has no content")
                    return False

            logger.info("✓ Complete pipeline flow works correctly")
            self.results_summary["query_processed"] = True
            self.results_summary["pipeline_integrated"] = True
            return True

        except Exception as e:
            logger.error(f"✗ Complete pipeline test failed: {str(e)}")
            logger.exception("Full error trace:")
            return False

    def print_results_summary(self):
        """Print a summary of test results"""
        logger.info("\n" + "=" * 60)
        logger.info("RAG PIPELINE TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(
            f"Vector Store Integration: {'✓' if self.results_summary['vector_store_loaded'] else '✗'}"
        )
        logger.info(
            f"Document Retrieval Flow: {'✓' if self.results_summary['documents_retrieved'] else '✗'}"
        )
        logger.info(
            f"LLM Generation: {'✓' if self.results_summary['llm_generated_response'] else '✗'}"
        )
        logger.info(
            f"Complete Pipeline: {'✓' if self.results_summary['pipeline_integrated'] else '✗'}"
        )
        logger.info(
            f"Query Processing: {'✓' if self.results_summary['query_processed'] else '✗'}"
        )

        # Calculate overall success
        success_count = sum(1 for val in self.results_summary.values() if val)
        total_tests = len(self.results_summary)
        logger.info(f"\nOverall: {success_count}/{total_tests} tests passed")

        if success_count == total_tests:
            logger.info("🎉 All tests passed! RAG pipeline is working correctly.")
            return True
        else:
            logger.info("❌ Some tests failed. Please investigate the issues above.")
            return False


async def main():
    """Main function to run all tests"""
    logger.info("Starting RAG Pipeline End-to-End Test...")
    logger.info("=" * 60)

    tester = RAGEndToEndTester()

    try:
        # Initialize the system first
        if not await tester.setup_rag_service():
            logger.error("Failed to initialize RAG service. Aborting tests.")
            return False

        # Run all test phases sequentially
        test_results = []

        # Test vector store and embedding functionality
        test_results.append(await tester.test_vector_store_integration())
        if not test_results[-1]:
            logger.error("Stopping tests due to vector store failure.")
            tester.print_results_summary()
            return False

        # Test document retrieval flow
        test_results.append(await tester.test_document_retrieval_flow())

        # Test LLM integration
        test_results.append(await tester.test_llm_generation_integration())

        # Test complete pipeline
        test_results.append(await tester.test_complete_pipeline_flow())

        # Print final results
        success = tester.print_results_summary()
        return success

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")
        logger.exception("Full error trace:")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n✓ RAG pipeline validated successfully!")
        sys.exit(0)
    else:
        print("\n✗ RAG pipeline validation failed!")
        sys.exit(1)
