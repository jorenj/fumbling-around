#!/bin/bash

# Master Dev Script for Cribbage Tournament Engine
# This script starts both the backend API and the frontend dashboard.

# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Cribbage Tournament Engine...${NC}"

# --- Dependency Checks ---
echo -e "${PURPLE}Checking system requirements...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[Error] python3 is not installed. Please install Python 3.9 or newer.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}[Error] npm is not installed. Please install Node.js and npm.${NC}"
    exit 1
fi

# --- Port Checks ---
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 1 # Port is in use
    else
        return 0 # Port is free
    fi
}

if ! check_port 8000; then
    echo -e "${YELLOW}[Warning] Port 8000 (Backend) is already in use. The server might fail to start.${NC}"
fi

if ! check_port 5173; then
    echo -e "${YELLOW}[Warning] Port 5173 (Frontend) is already in use. The server might fail to start.${NC}"
fi

# --- Backend Setup ---
echo -e "${PURPLE}[Backend] Preparing environment...${NC}"
cd "CribbageBots/backend"

if [ ! -d ".venv" ]; then
    echo -e "${PURPLE}[Backend] Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

source .venv/bin/activate

# Ensure core dependencies are installed
echo -e "${PURPLE}[Backend] Upgrading pip/setuptools and installing dependencies...${NC}"
python3 -m pip install --upgrade pip setuptools wheel
if ! pip install -e . ; then
    echo -e "${RED}[Backend] Failed to install dependencies. Please check your internet connection.${NC}"
    exit 1
fi

# --- Frontend Setup ---
echo -e "${BLUE}[Frontend] Preparing environment...${NC}"
cd "$SCRIPT_DIR/CribbageBots/frontend"

if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}[Frontend] node_modules not found. Running npm install...${NC}"
    if ! npm install; then
        echo -e "${RED}[Frontend] npm install failed. Please check your internet connection.${NC}"
        exit 1
    fi
fi

# --- Start Services ---

# Function to stop background processes on exit
cleanup() {
    echo -e "\n${BLUE}Stopping all services...${NC}"
    # Kill the process groups to ensure children die too
    if [ ! -z "$BACKEND_PID" ]; then kill $BACKEND_PID 2>/dev/null; fi
    if [ ! -z "$FRONTEND_PID" ]; then kill $FRONTEND_PID 2>/dev/null; fi
    exit
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${PURPLE}[Backend] Starting FastAPI server on http://localhost:8000...${NC}"
cd "$SCRIPT_DIR/CribbageBots/backend"
source .venv/bin/activate
# Run uvicorn as a background process
python3 -m uvicorn cribbage.api:app --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to initialize
sleep 2

# Start Frontend
echo -e "${BLUE}[Frontend] Starting Vite server on http://localhost:5173...${NC}"
cd "$SCRIPT_DIR/CribbageBots/frontend"
npm run dev &
FRONTEND_PID=$!

echo -e "${PURPLE}All services are running.${NC}"
echo -e "Press ${BLUE}Ctrl+C${NC} to stop."

# Wait for background processes
wait
