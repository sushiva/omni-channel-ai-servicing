#!/bin/bash
# Launcher script for mock CRM/banking services
# Activates venv and runs mock services on port 9000

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

# Run mock services
echo "🚀 Starting Mock CRM/Banking Services on port 9000..."
echo "Press Ctrl+C to stop"
echo ""
uvicorn mock_services.main:app --host 127.0.0.1 --port 9000 --reload
