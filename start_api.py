#!/usr/bin/env python3
"""
Start script for the CGGI RAG API
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def start_api():
    """Start the FastAPI application"""
    print("Starting CGGI RAG API...")

    # Change to the API directory
    api_dir = project_root / "api"
    os.chdir(api_dir)

    # Set environment variables
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "8000")
    os.environ.setdefault("DEBUG", "True")

    # Import and run the app
    import uvicorn
    from api.main import app

    print("CGGI RAG API is starting on http://0.0.0.0:8000")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "api.main:app",
        host=os.environ.get("API_HOST", "0.0.0.0"),
        port=int(os.environ.get("API_PORT", "8000")),
        reload=os.environ.get("DEBUG", "False").lower() == "true",
    )


if __name__ == "__main__":
    start_api()
