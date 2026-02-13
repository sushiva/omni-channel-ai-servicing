#!/bin/bash
# Launcher script for email polling service (30s intervals)
# Activates venv and runs the poller

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

# Check if API server is running
if ! curl -s http://localhost:8001/docs > /dev/null 2>&1; then
    echo "⚠️  Warning: API server doesn't seem to be running on port 8000"
    echo "Please start it first with: ./run_api.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run email poller
echo "🚀 Starting Email Poller (30s intervals)..."
echo "Press Ctrl+C to stop"
echo ""
python -m omni_channel_ai_servicing.services.email_poller
