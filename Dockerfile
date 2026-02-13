# Dockerfile for HuggingFace Spaces
# Multi-stage build for efficient deployment

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt requirements_streamlit.txt ./

# Install Python dependencies (Streamlit version includes extra UI packages)
RUN pip install --no-cache-dir -r requirements_streamlit.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p faiss_index knowledge_base evaluation_results .embedding_cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose ports
EXPOSE 7860 8000

# Make startup script executable
RUN chmod +x start.sh

# Run startup script
CMD ["./start.sh"]
