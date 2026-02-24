#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "  SkinCare AI - Stopping Services"
echo "========================================"
echo ""

echo -e "${BLUE}Stopping Backend Services...${NC}"
cd backend
docker-compose down
cd ..

echo ""
echo -e "${GREEN}All services stopped successfully!${NC}"
echo ""
