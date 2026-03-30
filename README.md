# CGGI RAG-Based Q&A System

A high-performance and accurate RAG (Retrieval-Augmented Generation) system for querying Chandler Good Government Index (CGGI) information using Alibaba Cloud's international coding plan API for LLM models, with a modern UI.

## Overview

This system provides natural language Q&A capabilities over CGGI reports from 2021-2025, leveraging:
- Vector databases for efficient document retrieval
- Alibaba Cloud's Qwen API for response generation
- Modern React/Next.js UI for intuitive interaction
- Comprehensive data pipeline for processing CGGI reports

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User UI       │────│   API Service    │────│  Vector Store   │
│ (Next.js)       │    │   (FastAPI)      │    │ (TF-IDF/FAISS)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                     ┌────────┴────────┐
                     │                 │
              ┌──────────────┐  ┌──────────────────┐
              │   Worker     │  │   LLM Service    │
              │  (Celery)    │  │ (Alibaba Qwen)   │
              └──────────────┘  └──────────────────┘
                     │
              ┌──────────────┐
              │ Data Pipeline│
              │(PDF Process) │
              └──────────────┘
```

## Prerequisites

Before setting up the system, ensure you have the following prerequisites installed:

### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: At least 8GB RAM (16GB recommended)
- **Disk Space**: At least 2GB free space

### Software Dependencies
- **Python 3.9 or higher**
- **Node.js 18.x or higher**
- **npm 8.x or higher**
- **Docker Desktop** (if using containerized deployment)
- **Docker Compose**

## Setup Instructions

### Option 1: Docker Setup (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd cggi-rag-system
   ```

2. **Create a Python Virtual Environment (Optional but Recommended):**
   ```bash
   # Windows
   python -m venv cggi-env
   cggi-env\Scripts\activate
   
   # macOS/Linux
   python3 -m venv cggi-env
   source cggi-env/bin/activate
   ```

3. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit the .env file to add your Alibaba Cloud API key
   # You can use any text editor like nano, vim, or VS Code
   nano .env
   # or
   code .env
   ```

4. **Build and start the system:**
   ```bash
   docker-compose up --build
   ```

5. **The system will be available at:**
   - UI: http://localhost:3000
   - API: http://localhost:8000
   - Worker: Background Celery worker for async tasks

### Option 2: Manual Setup (Development)

1. **Create a Python Virtual Environment:**
   ```bash
   # Windows
   python -m venv cggi-env
   cggi-env\Scripts\activate
   
   # macOS/Linux
   python3 -m venv cggi-env
   source cggi-env/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd ../ui
   npm install
   ```

4. **Set up environment variables:**
   ```bash
   # Create .env file in the api directory
   cd ../api
   # Add your environment variables to config/.env or system environment
   ```

5. **Process CGGI documents:**
   ```bash
   cd etl
   python ingest_documents.py
   ```

6. **Start the API service:**
   ```bash
   cd ../api
   uvicorn main:app --reload
   ```

7. **In a new terminal, start the UI:**
   ```bash
   cd ../ui
   npm run dev
   ```

## Environment Variables Configuration

Create a `.env` file in the `api/` directory with the following variables:

```bash
# Alibaba Cloud API Configuration
ALIBABA_API_KEY=your_alibaba_cloud_api_key_here
ALIBABA_BASE_URL=https://dashscope.aliyuncs.com/api/v1

# Database Configuration
POSTGRES_URL=postgresql://user:password@localhost:5432/cggi_db
REDIS_URL=redis://localhost:6379

# Application Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Vector Database Configuration
VECTOR_DB_URL=http://localhost:8001
VECTOR_EMBEDDING_DIMENSION=1536

# Document Processing Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Search Configuration
TOP_K=5
SEARCH_THRESHOLD=0.7

# LLM Parameters
MAX_TOKENS=1000
TEMPERATURE=0.7
```

## Database Setup

### PostgreSQL Database

The system uses PostgreSQL for storing structured CGGI data and metadata. To set up the database:

1. **For Docker setup**, PostgreSQL is automatically deployed via docker-compose.yml
2. **For manual setup**, you need to install PostgreSQL separately:
   - Download PostgreSQL from https://www.postgresql.org/download/
   - Follow the installation instructions for your OS
   - Create a database named `cggi_db` and a user with appropriate permissions

3. **Database Schema:**
   The system expects the following tables:
   - `countries`: Contains country information and metadata
   - `cggi_reports`: Stores CGGI report data
   - `pillars`: CGGI pillars information
   - `indicators`: CGGI indicators data
   - `metrics`: Individual metric values

### Vector Database

The system uses a vector database for document retrieval:
- **Production**: FAISS or Pinecone
- **Development**: Simple TF-IDF-based vector store (included in the codebase)

## Document Processing Pipeline

### Data Sources

The system processes CGGI reports from a source directory containing PDF files for years 2021-2025. Configure the source path in your environment variables or `ingest_documents.py`.

### Processing Steps

1. **Document Ingestion**: Extracts text and metadata from PDF files
2. **Text Chunking**: Splits documents into manageable chunks with overlap
3. **Embedding Generation**: Creates vector embeddings using Alibaba Cloud API
4. **Indexing**: Stores embeddings in the vector database with metadata
5. **Metadata Enrichment**: Adds source information, publication year, etc.

### Chunking Configuration

- **Chunk Size**: 512 tokens (adjustable via CHUNK_SIZE environment variable)
- **Overlap**: 50 tokens (to maintain context continuity)
- **Strategy**: Semantic chunking to preserve meaning boundaries

### Embedding Configuration

- **Model**: Alibaba Cloud's text embedding model via API
- **Dimension**: 1536-dimensional vectors
- **Normalization**: Cosine similarity with L2 normalization

## API Endpoints

### Core Endpoints

- `GET /` - Health check and system status
- `GET /health` - Detailed health status
- `POST /query` - Submit a natural language query and receive a response
- `GET /documents` - List available documents
- `GET /stats` - System statistics and performance metrics

### Query Endpoint

**URL**: `POST /query`

**Request Body**:
```json
{
  "query": "Your natural language question about CGGI",
  "top_k": 5,
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response**:
```json
{
  "query": "Your question",
  "answer": "Generated response based on CGGI data",
  "documents": [
    {
      "content": "Relevant document snippet",
      "source": "Source document",
      "page_number": 1,
      "metadata": {}
    }
  ],
  "confidence_score": 0.85
}
```

## Development Workflow

### Setting Up Development Environment

1. **Python Virtual Environment**:
   ```bash
   python -m venv cggi-dev
   source cggi-dev/bin/activate  # Linux/macOS
   # or
   cggi-dev\Scripts\activate  # Windows
   ```

2. **Install Development Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8  # Development tools
   ```

3. **Environment Variables**:
   Set up the .env file with development-specific configurations

### Running Tests

```bash
# Run API tests
cd api
pytest tests/

# Run linting
flake8 .
black --check .
```

### Adding New Features

1. Create a new branch for your feature
2. Make changes following the existing code style
3. Write tests for new functionality
4. Run all tests to ensure nothing is broken
5. Submit a pull request

## Deployment

### Local Deployment

For local deployment with Docker:
```bash
docker-compose up -d --build
```

### Production Deployment

1. **Environment Setup**:
   - Use production-grade database (managed service)
   - Set DEBUG=False
   - Configure SSL certificates

2. **Configuration**:
   - Update docker-compose.prod.yml with production settings
   - Set up proper logging and monitoring
   - Configure backup and recovery

3. **Security**:
   - Use environment variables for secrets
   - Implement proper authentication
   - Set up HTTPS/SSL

## Troubleshooting

### Common Issues

1. **API Connection Errors**:
   - Verify Alibaba Cloud API key is correct
   - Check internet connectivity
   - Ensure rate limits are not exceeded

2. **Database Connection Errors**:
   - Verify PostgreSQL is running
   - Check connection string in .env
   - Confirm database permissions

3. **Document Processing Failures**:
   - Ensure PDF files are accessible
   - Check document processing logs
   - Verify sufficient memory allocation

### Debugging

Enable debug mode by setting `DEBUG=True` in .env to get more detailed error messages.

### Docker Build Issues

1. **`npm ci` fails in UI build**:
   - Ensure `package-lock.json` exists in the `ui/` directory
   - Run `npm install` locally in the `ui/` directory before building Docker images
   - The UI uses a multi-stage Docker build that requires all dependencies for building, then only production dependencies for runtime

2. **Python package version not found**:
   - Check `requirements.txt` for valid package versions
   - Some packages may have been updated; use `pip search <package>` or check PyPI for current versions

3. **Build context too large**:
   - Ensure `node_modules/` is excluded via `.dockerignore`
   - Clean up unnecessary files before building

## Performance Tuning

### Caching Strategy

- Query result caching using Redis
- Embedding caching for frequently accessed documents
- API response caching

### Scalability

- Horizontal scaling of API services
- Database read replicas for heavy read loads
- CDN for static assets

## Features

- Natural language Q&A interface
- Document retrieval from CGGI reports (2021-2025)
- Confidence scoring for responses
- Source citations
- Modern, responsive UI
- Fast search and response times

## Project Structure

```
cggi-rag-system/
├── api/                 # FastAPI backend
│   ├── main.py          # Main application
│   ├── rag_service.py   # RAG service implementation
│   ├── llm_service.py   # LLM integration
│   ├── config/          # Configuration files
│   └── Dockerfile       # API container configuration
├── ui/                  # Next.js frontend
│   ├── pages/           # React pages
│   ├── components/      # UI components
│   ├── package.json     # Node.js dependencies
│   ├── package-lock.json # Dependency lock file (required for Docker build)
│   └── Dockerfile       # Multi-stage UI container configuration
├── worker/              # Celery worker service
│   └── Dockerfile       # Worker container configuration
├── vector-db/           # Vector store implementations
│   └── vector_store_simple.py # TF-IDF vector store
├── etl/                 # Data processing pipelines
│   ├── document_processor.py # PDF processing
│   └── ingest_documents.py   # Document ingestion script
├── config/              # Configuration files
├── docs/                # Documentation
├── docker-compose.yml   # Docker orchestration
├── requirements.txt     # Python dependencies (unified)
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.