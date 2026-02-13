#!/bin/bash
# Launcher script for API server
# Activates venv and runs uvicorn

set -e

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found at .venv"
    echo "Please create it first with: python3 -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Run API server
echo "🚀 Starting API server on port 8000..."
echo "API docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""
uvicorn omni_channel_ai_servicing.app.main:app --host 0.0.0.0 --port 8000 --reload
