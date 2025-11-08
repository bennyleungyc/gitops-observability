#!/bin/bash
# Build all exchange listener images using the unified build system

set -e

export VERSION="${VERSION:-latest}"
# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Building all exchange listener images...${NC}"
echo -e "${BLUE}========================================${NC}"

# List of all available listeners
LISTENERS=("crypto" "binance")

# Build each listener
for listener in "${LISTENERS[@]}"; do
    echo ""
    echo -e "${BLUE}Building ${listener}...${NC}"
    ./control/build_listener.sh "$listener"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All images built successfully!${NC}"
echo -e "${GREEN}========================================${NC}"

# Show all built images
echo ""
echo "Built images:"
docker images | grep -E "(crypto-ws|binance-ws)" | head -10