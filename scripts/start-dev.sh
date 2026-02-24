#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  SkinCare AI - Development Startup"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker is not running!${NC}"
    echo "Please start Docker and try again."
    exit 1
fi

echo -e "${BLUE}[1/4] Starting Backend Services (Docker)...${NC}"
echo ""
cd backend
docker-compose up -d
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to start backend services!${NC}"
    exit 1
fi
cd ..

echo ""
echo -e "${BLUE}[2/4] Waiting for backend to be ready...${NC}"
sleep 5

echo ""
echo -e "${BLUE}[3/4] Installing Frontend Dependencies...${NC}"
echo ""
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install frontend dependencies!${NC}"
        cd ..
        exit 1
    fi
else
    echo "Dependencies already installed, skipping..."
fi

echo ""
echo -e "${BLUE}[4/4] Starting Frontend Development Server...${NC}"
echo ""
echo "========================================"
echo "  Services Starting:"
echo "========================================"
echo -e "  ${GREEN}Backend API:${NC}  http://localhost:8000"
echo -e "  ${GREEN}Frontend:${NC}     http://localhost:8081"
echo -e "  ${GREEN}Docs:${NC}         http://localhost:8000/docs"
echo "========================================"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Stopping backend services...${NC}"
    cd ../backend
    docker-compose down
    cd ..
    echo -e "${GREEN}All services stopped.${NC}"
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT TERM

# Start frontend
npm start

# If npm start exits normally, cleanup
cleanup
