#!/bin/bash
# Start both mock services and API server

cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing
source .venv/bin/activate

# Kill any existing servers
pkill -f "uvicorn mock_services.main"
pkill -f "uvicorn omni_channel_ai_servicing.app.main"

sleep 2

# Start mock services
echo "Starting mock services on port 9000..."
uvicorn mock_services.main:app --host 127.0.0.1 --port 9000 > /tmp/mock_services.log 2>&1 &
MOCK_PID=$!
echo "Mock services PID: $MOCK_PID"

sleep 3

# Start API server
echo "Starting API server on port 8000..."
uvicorn omni_channel_ai_servicing.app.main:app --host 127.0.0.1 --port 8000 > /tmp/api_server.log 2>&1 &
API_PID=$!
echo "API server PID: $API_PID"

sleep 3

# Verify both are running
echo ""
echo "Verifying services..."
curl -s http://localhost:9000/ && echo " ✅ Mock services running"
curl -s http://localhost:8000/health && echo " ✅ API server running"

echo ""
echo "Both services are ready!"
echo "Mock services: http://localhost:9000"
echo "API server: http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "To stop: pkill -f 'uvicorn mock_services.main' && pkill -f 'uvicorn omni_channel_ai_servicing.app.main'"
