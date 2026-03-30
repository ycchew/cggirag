from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import logging
from config.settings import settings
from rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CGGI RAG API",
    description="API for CGGI RAG-based question answering system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class DocumentChunk(BaseModel):
    content: str
    source: str
    page_number: Optional[int] = None
    metadata: dict


class QueryResponse(BaseModel):
    query: str
    answer: str
    documents: List[DocumentChunk]
    confidence_score: float


# Initialize RAG service
rag_service = RAGService()


@app.get("/")
async def root():
    return {"message": "Welcome to CGGI RAG API", "version": "1.0.0"}


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Process a natural language query and return an answer based on CGGI information
    """
    try:
        logger.info(f"Processing query: {request.query}")
        top_k = request.top_k or 5  # Use default if None
        response = await rag_service.query(request.query, top_k)
        return response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "cggi-rag-api"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
