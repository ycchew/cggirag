# CGGI RAG System - End-to-End Docker Test

This document explains how to run the end-to-end test for the CGGI RAG system Docker implementation.

## About the Test Script

The `test_e2e_docker.py` script provides comprehensive testing for the CGGI RAG system in its Docker deployment. It verifies:
- All containers start and remain healthy
- API endpoints respond correctly
- UI is accessible
- Data flows properly between services
- Worker functionality is available
- Overall system integration works as expected

## Test Components

The test validates:

1. **Service Startup**: Ensures all Docker containers start successfully
2. **Container Health**: Verifies all required services are running
3. **API Connectivity**: Tests API endpoints for health and functionality
4. **Query Processing**: Validates search/retrieval/generation functionality
5. **UI Accessibility**: Confirms UI is responsive and working
6. **Backend Integration**: Tests integration between components

## Prerequisites

Before running the test, ensure you have:

- Docker Desktop installed and running
- Docker Compose installed
- Sufficient system resources (recommended: 8GB+ RAM)
- Python 3.9+ installed (for running the test script)

## Execution Steps

### 1. Navigate to the Project Directory
```bash
cd /path/to/cggi-rag-system
```

### 2. Prepare Environment (if not done already)
```bash
# Copy example environment file
cp .env.example .env

# Add your Alibaba Cloud API key to .env if available
# Or ensure the system runs without an API key (mock responses will be used)
```

### 3. Run the End-to-End Test
```bash
python test_e2e_docker.py
```

The script will prompt for confirmation before starting Docker containers:
```
🚀 Proceed with Docker deployment test? (y/N):
```

Type `y` and press Enter to proceed.

### 4. Monitor Test Progress
The test will:
- Start all Docker services via `docker-compose up -d --build`
- Wait for services to become available
- Execute individual test validations
- Show real-time results
- Automatically shut down services when complete

### 5. Review Results
At the end of execution, the test will display:
- Pass/fail status for each test component
- Count of total tests and passes
- Overall success/failure status
- Any specific errors encountered

## Expected Results

Under normal conditions, all 7-8 individual tests should pass:
- ✅ Container_cggg-postgres
- ✅ Container_cggg-redis
- ✅ Container_cggg-api
- ✅ Container_cggg-ui
- ✅ Container_cggg-worker
- ✅ API_health
- ✅ Root_endpoint
- ✅ Query_functionality
- ✅ UI_accessibility
- ✅ Worker_functionality

Note: The vector store might be empty in a new installation, so the query test might return mock responses rather than actual retrieved content. This is acceptable and will still pass validation.

## Troubleshooting

### Test Fails to Start Services
- Verify Docker is running
- Check if ports 8000, 3000, 5432, 6379 are available
- Review `docker-compose.yml` for any syntax issues

### API Responses Time Out
- Wait longer for all services to fully initialize
- Check that your vector store is properly mounted if populated

### UI Not Accessible
- Verify the UI service is building successfully
- Check for any frontend build errors in the docker logs

## Logging and Diagnostics

For troubleshooting, you can check Docker container logs:
```bash
# View all container logs
docker-compose -f docker-compose.yml logs

# View specific service logs
docker-compose -f docker-compose.yml logs api
docker-compose -f docker-compose.yml logs ui
docker-compose -f docker-compose.yml logs worker
```

## Test Architecture

The test script follows this execution flow:
1. **Setup Phase**: Starts Docker services with `--build` option
2. **Waiting Phase**: Waits up to 3 minutes for all services to be ready
3. **Validation Phase**: Runs individual tests for each component
4. **Teardown Phase**: Stops all services and cleans up

Each test is atomic, meaning a failure in one won't stop execution of others. At the end, you get both granular results and a summary.