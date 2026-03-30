import asyncio
import logging
import httpx
from typing import List, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)


class AlibabaLLMService:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_API_URL.rstrip("/")
        self.model = getattr(settings, "LLM_MODEL", "qwen-max")
        logger.info(f"LLM Service initialized with model: {self.model}")

    async def generate_response(
        self,
        prompt: str,
        context_documents: List[Dict[str, Any]],
        max_tokens: int = 1000,
        temperature: float = 0.7,
        enable_web_search: bool = False,
    ) -> str:
        """
        Generate response using Alibaba Cloud Anthropic-compatible API

        Args:
            prompt: User query
            context_documents: Retrieved documents from vector store
            max_tokens: Maximum response tokens
            temperature: Response temperature
            enable_web_search: Enable web search when vector store has poor results
        """
        if not self.api_key:
            logger.warning("Alibaba API key not configured, returning mock response")
            return self._mock_response(prompt, context_documents)

        try:
            # Prepare the context from retrieved documents
            context_text = self._prepare_context(context_documents)

            # Construct the full prompt
            full_prompt = self._construct_prompt(
                prompt, context_text, enable_web_search
            )

            # Make the API call with optional web search
            response_text = await self._call_alibaba_api(
                full_prompt, max_tokens, temperature, enable_web_search
            )
            return response_text

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return self._fallback_response(prompt)

    def _prepare_context(self, documents: List[Dict[str, Any]]) -> str:
        """Prepare context text from retrieved documents"""
        context_parts = []

        for doc in documents:
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source_file", "Unknown")
            year = doc.get("metadata", {}).get("year", "Unknown")

            context_parts.append(f"[From: {source}, Year: {year}]\n{content}\n")

        return "\n".join(context_parts)

    def _construct_prompt(
        self, user_query: str, context: str, enable_web_search: bool = False
    ) -> str:
        """Construct the full prompt with context"""
        web_search_instruction = ""
        if enable_web_search:
            web_search_instruction = """
WEB SEARCH ENABLED: The vector store did not return sufficient context for this query.
You should search for information from https://chandlergovernmentindex.com/ and other authoritative sources
to provide an accurate answer. Cite the web sources you used."""

        prompt = f"""Based on the following CGGI (Chandler Good Government Index) information, please answer the user's question.

CONTEXT INFORMATION:
{context}
{web_search_instruction}

USER QUESTION:
{user_query}

INSTRUCTIONS:
1. Provide a direct and accurate answer based on the CGGI information provided.
2. Cite the specific documents and years when possible.
3. If the information is not available in the provided context, clearly state that.
4. Be concise but comprehensive in your response.
5. Maintain objectivity and stick to facts from the CGGI reports."""
        return prompt.strip()

    async def _call_alibaba_api(
        self,
        user_message: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        enable_web_search: bool = False,
    ) -> str:
        """
        Make the actual call to Alibaba Cloud DashScope API (Anthropic compatible)

        When enable_web_search is True, the API will search the web for information.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "system": "You are an expert assistant specializing in the Chandler Good Government Index (CGGI). Answer questions based on the provided CGGI information. Be precise, factual, and cite sources when possible.",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": user_message}],
        }

        if enable_web_search:
            payload["enable_search"] = True

        url = f"{self.base_url}/apps/anthropic/v1/messages"
        logger.info(f"Calling Alibaba API: {url} (web_search={enable_web_search})")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    data = response.json()

                    for block in data.get("content", []):
                        if block.get("type") == "text":
                            text = block.get("text", "")
                            usage = data.get("usage", {})
                            logger.info(
                                f"Qwen response generated successfully, tokens used: {usage}"
                            )
                            return text

                    logger.error(f"No text content in response: {data}")
                    return self._fallback_response(user_message)
                else:
                    logger.error(
                        f"Qwen API error: {response.status_code} - {response.text}"
                    )
                    return self._fallback_response(user_message)

        except httpx.TimeoutException:
            logger.error("Qwen API request timed out")
            return self._fallback_response(user_message)
        except Exception as e:
            logger.error(f"Error calling Qwen API: {str(e)}")
            return self._fallback_response(user_message)

    def _mock_response(
        self, prompt: str, context_documents: List[Dict[str, Any]]
    ) -> str:
        """Generate a mock response when API key is not configured"""
        return f"MOCK RESPONSE: Based on CGGI information, here's an answer to your query: '{prompt}'. This is a simulated response since the Alibaba Cloud API key is not configured. In the full implementation, this would be generated by the Qwen model using the provided context from {len(context_documents)} documents."

    def _fallback_response(self, prompt: str) -> str:
        """Provide a fallback response in case of errors"""
        return f"FALLBACK RESPONSE: Could not generate a response for your query. Please check API connectivity and configuration."


# Example usage
async def main():
    llm_service = AlibabaLLMService()
    response = await llm_service.generate_response(
        prompt="What are the top 3 countries in CGGI 2025?",
        context_documents=[
            {
                "content": "Singapore, Denmark, and Norway are the top 3 countries in CGGI 2025.",
                "metadata": {"source_file": "cggi_2025_report.pdf", "year": 2025},
            }
        ],
    )
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
