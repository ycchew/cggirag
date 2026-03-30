FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy config, api, and vector-db directories
COPY config/ ./config/
COPY api/ ./
COPY vector-db/ ./vector-db/

# Set PYTHONPATH to include /app and /app/vector-db
ENV PYTHONPATH=/app:/app/vector-db

EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]