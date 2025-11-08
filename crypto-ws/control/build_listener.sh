#!/bin/bash
# Parameterized build script for WebSocket exchange listeners
# Usage: ./control/build_listener.sh <listener_name>

set -e

# Configuration mapping - using functions for compatibility
get_listener_module() {
    case "$1" in
        "binance") echo "src.binance_listener.binance_listener" ;;
        "crypto") echo "src.crypto_com_listener.crypto_listener" ;;
        *) echo "" ;;
    esac
}

get_listener_image() {
    case "$1" in
        "binance") echo "binance-ws" ;;
        "crypto") echo "crypto-ws" ;;
        *) echo "" ;;
    esac
}

get_available_listeners() {
    echo "binance crypto"
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 <listener_name> [options]"
    echo ""
    echo "Available listeners:"
    for listener in $(get_available_listeners); do
        echo "  - $listener"
    done
    echo ""
    echo "Options:"
    echo "  --tag <tag>     Custom image tag (default: latest)"
    echo "  --no-cache      Build without cache"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 binance"
    echo "  $0 crypto --tag v1.0.0"
    echo "  $0 binance --no-cache"
}

# Parse arguments
LISTENER=""
TAG="latest"
NO_CACHE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        -*)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [ -z "$LISTENER" ]; then
                LISTENER="$1"
            else
                print_error "Multiple listeners specified. Only one allowed."
                show_usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate listener
if [ -z "$LISTENER" ]; then
    print_error "No listener specified"
    show_usage
    exit 1
fi

MODULE=$(get_listener_module "$LISTENER")
if [ -z "$MODULE" ]; then
    print_error "Unknown listener: '$LISTENER'"
    echo "Available listeners: $(get_available_listeners)"
    exit 1
fi

# Get configuration
IMAGE=$(get_listener_image "$LISTENER")
FULL_IMAGE_NAME="${IMAGE}:${TAG}"

# Build the image
print_status "Building ${LISTENER} listener..."
print_status "Module: ${MODULE}"
print_status "Image: ${FULL_IMAGE_NAME}"

# Check if dockerfile exists
if [ ! -f "dockerfile" ]; then
    print_error "dockerfile not found in current directory"
    exit 1
fi

# Build command
BUILD_CMD="docker build \
    --build-arg LISTENER_MODULE=\"${MODULE}\" \
    -t \"${FULL_IMAGE_NAME}\" \
    -f dockerfile \
    ${NO_CACHE} \
    ."

print_status "Executing: ${BUILD_CMD}"

# Execute build
if eval $BUILD_CMD; then
    print_success "${LISTENER} listener built successfully: ${FULL_IMAGE_NAME}"
    
    # Show image info
    print_status "Image details:"
    docker images "${IMAGE}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
else
    print_error "Failed to build ${LISTENER} listener"
    exit 1
fi
