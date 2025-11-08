#!/bin/bash
# Build all services using Docker Compose (same as CI integration test)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building with Docker Compose${NC}"
echo -e "${BLUE}========================================${NC}"

echo ""
echo -e "${YELLOW}This builds all services as defined in docker-compose.yml${NC}"
echo -e "${YELLOW}Same approach used in CI integration tests${NC}"
echo ""

# Build using docker compose
echo -e "${BLUE}Running: docker compose build${NC}"
docker compose build --progress=plain

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All services built successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show built images
echo ""
echo "Built images:"
docker compose images

echo ""
echo -e "${BLUE}To start services:${NC}"
echo "  docker compose up -d"
echo ""
echo -e "${BLUE}To test integration (like CI):${NC}"
echo "  ./control/test_integration.sh"

