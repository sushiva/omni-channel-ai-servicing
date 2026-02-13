#!/bin/bash
# Startup script for HuggingFace Spaces
# Starts both the FastAPI backend and Streamlit frontend

# Start FastAPI backend in background
echo "Starting FastAPI backend..."
cd /app
uvicorn omni_channel_ai_servicing.app.api.main:app --host 0.0.0.0 --port 8000 &

# Wait for backend to be ready
echo "Waiting for backend to start..."
sleep 10

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0
