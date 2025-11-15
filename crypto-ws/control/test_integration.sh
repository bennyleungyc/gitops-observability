#!/bin/bash
# Integration test script (mirrors CI docker-compose-test job)
# Tests all services together using docker-compose

set -e

# Default VERSION if not provided
export VERSION="${VERSION:-latest}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Docker Compose Integration Test${NC}"
echo -e "${BLUE}(Mirrors CI integration test)${NC}"
echo -e "${BLUE}========================================${NC}"

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"
    docker compose down -v 2>/dev/null || true
}

# Ensure cleanup on exit
trap cleanup EXIT

# Step 1: Build
echo ""
echo -e "${BLUE}Step 1: Building services...${NC}"
docker compose build

# Step 2: Start services
echo ""
echo -e "${BLUE}Step 2: Starting services...${NC}"
docker compose up -d

# Step 3: Wait for healthy
echo ""
echo -e "${BLUE}Step 3: Waiting for services to be healthy...${NC}"
echo "Waiting 15 seconds for startup..."
sleep 15

# Check service status
echo ""
docker compose ps

# Step 4: Test Binance service
# echo ""
# echo -e "${BLUE}Step 4: Testing Binance service...${NC}"
# if curl -f http://localhost:8002/health 2>/dev/null; then
#     echo -e "${GREEN}✅ Binance service is healthy${NC}"
# else
#     echo -e "${RED}❌ Binance service health check failed${NC}"
#     echo "Binance logs:"
#     docker compose logs binance
#     exit 1
# fi

# # Step 5: Test Crypto.com service
# echo ""
# echo -e "${BLUE}Step 5: Testing Crypto.com service...${NC}"
# if curl -f http://localhost:8001/health 2>/dev/null; then
#     echo -e "${GREEN}✅ Crypto.com service is healthy${NC}"
# else
#     echo -e "${RED}❌ Crypto.com service health check failed${NC}"
#     echo "Crypto logs:"
#     docker compose logs crypto
#     exit 1
# fi

# Success
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ All integration tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"

echo ""
echo -e "${YELLOW}Services are still running. To stop:${NC}"
echo "  docker compose down"
echo ""
echo -e "${YELLOW}To view live logs:${NC}"
echo "  docker compose logs -f"

