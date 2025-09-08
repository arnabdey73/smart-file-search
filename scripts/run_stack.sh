#!/bin/bash
# Start the complete smart-file-search stack

set -e

echo "Starting Smart File Search Stack..."

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "Warning: .env file not found. Copying from .env.example"
    cp .env.example .env
    echo "Please edit .env with your configuration before running again."
    exit 1
fi

# Load environment variables
source .env

# Create required directories
mkdir -p data logs ui/frontend/dist

# Activate virtual environment if it exists
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
fi

# Function to start service in background
start_service() {
    local name=$1
    local command=$2
    local port=$3
    
    echo "Starting $name on port $port..."
    
    # Kill existing process on port if it exists
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Killing existing process on port $port"
        kill $(lsof -Pi :$port -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 2
    fi
    
    # Start the service
    eval "$command" &
    local pid=$!
    echo "$name started with PID $pid"
    
    # Store PID for cleanup
    echo $pid >> .pids
}

# Clean up existing PID file
rm -f .pids

# Trap to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    if [[ -f ".pids" ]]; then
        while read pid; do
            kill $pid 2>/dev/null || true
        done < .pids
        rm -f .pids
    fi
    echo "Cleanup completed"
}
trap cleanup EXIT

# Start MCP Server
start_service "MCP Server" "python -m mcp_server.server" ${MCP_PORT:-9000}

# Wait for MCP server to be ready
echo "Waiting for MCP server to be ready..."
sleep 3

# Start UI Backend
start_service "UI Backend" "cd ui/backend && python api.py" ${UI_BACKEND_PORT:-8081}

# Wait for backend to be ready
echo "Waiting for UI backend to be ready..."
sleep 3

# Check if frontend needs to be built
if [[ ! -d "ui/frontend/dist" ]] || [[ ! "$(ls -A ui/frontend/dist)" ]]; then
    echo "Building frontend..."
    cd ui/frontend
    if [[ ! -d "node_modules" ]]; then
        npm install
    fi
    npm run build
    cd ../..
fi

# Start Frontend (if using vite preview)
start_service "UI Frontend" "cd ui/frontend && npm run preview -- --port ${UI_FRONTEND_PORT:-8080} --host 0.0.0.0" ${UI_FRONTEND_PORT:-8080}

echo ""
echo "🚀 Smart File Search Stack is running!"
echo ""
echo "Services:"
echo "  - Frontend: http://localhost:${UI_FRONTEND_PORT:-8080}"
echo "  - Backend API: http://localhost:${UI_BACKEND_PORT:-8081}"
echo "  - Health Check: http://localhost:${UI_BACKEND_PORT:-8081}/healthz"
echo "  - MCP Server: http://localhost:${MCP_PORT:-9000}"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait
