#!/bin/bash
# Advanced build script using build-config.yml
# Usage: ./control/build_advanced.sh [target] [options]

set -e

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

resolve_login_registry() {
    local primary="$1"
    local fallback="$2"
    local candidate="${primary:-$fallback}"

    if [ -z "$candidate" ]; then
        echo "docker.io"
        return
    fi

    candidate="${candidate#*://}"
    if [[ "$candidate" == */* ]]; then
        candidate="${candidate%%/*}"
    fi

    echo "$candidate"
}

DOCKER_LOGIN_STATE="not_attempted"

ensure_docker_login() {
    local registry_host="$1"

    case "$DOCKER_LOGIN_STATE" in
        success) return 0 ;;
        failed) return 1 ;;
    esac

    local username="${DOCKER_USERNAME:-${CI_REGISTRY_USER:-}}"
    local password="${DOCKER_PASSWORD:-${CI_REGISTRY_PASSWORD:-}}"

    if [ -z "$username" ] || [ -z "$password" ]; then
        print_error "Docker credentials not provided. Expected DOCKER_USERNAME/DOCKER_PASSWORD or CI_REGISTRY_USER/CI_REGISTRY_PASSWORD."
        DOCKER_LOGIN_STATE="failed"
        return 1
    fi

    print_status "Logging in to Docker registry: $registry_host"
    if login_output=$(echo "$password" | docker login "$registry_host" --username "$username" --password-stdin 2>&1); then
        DOCKER_LOGIN_STATE="success"
        return 0
    else
        DOCKER_LOGIN_STATE="failed"
        print_error "Docker login failed for registry $registry_host"
        echo "$login_output"
        return 1
    fi
}

validate_push_reference() {
    local image_ref="$1"

    if [[ "$image_ref" != */* ]]; then
        print_error "Cannot push image '$image_ref'. Provide a registry or namespace (e.g. --registry docker.io/username or set CI_REGISTRY_IMAGE)."
        return 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [target] [options]"
    echo ""
    echo "Targets:"
    echo "  all           Build all listeners (default)"
    echo "  binance       Build only Binance listener"
    echo "  crypto        Build only Crypto.com listener"
    echo "  binance-only  Build only Binance listener"
    echo "  crypto-only   Build only Crypto.com listener"
    echo ""
    echo "Options:"
    echo "  --tag <tag>        Custom image tag (default: latest)"
    echo "  --registry <url>   Override registry (default: docker.io)"
    echo "  --no-cache         Build without cache"
    echo "  --push             Push images to registry after build"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all"
    echo "  $0 binance --tag v1.0.0"
    echo "  $0 all --registry docker.io/myorg --push"
}

# Check if yq is available for YAML parsing
check_yq() {
    if ! command -v yq &> /dev/null; then
        print_error "yq is required but not installed."
        echo "Install with: brew install yq (macOS) or apt install yq (Ubuntu)"
        echo "Or download from: https://github.com/mikefarah/yq/releases"
        exit 1
    fi
}

# Parse YAML config
parse_config() {
    local config_file="build-config.yml"
    if [ ! -f "$config_file" ]; then
        print_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    # Get available targets
    TARGETS=$(yq '.targets | keys | .[]' "$config_file" 2>/dev/null || echo "all")
    
    # Get available listeners
    LISTENERS=$(yq '.listeners | keys | .[]' "$config_file" 2>/dev/null || echo "binance crypto")
}

# Get listeners for target
get_listeners_for_target() {
    local target="$1"
    local config_file="build-config.yml"
    
    if [ "$target" = "all" ]; then
        echo "binance crypto"
    else
        yq ".targets.$target.listeners[]" "$config_file" 2>/dev/null || echo "$target"
    fi
}

# Get listener config
get_listener_config() {
    local listener="$1"
    local key="$2"
    local config_file="build-config.yml"
    
    yq ".listeners.$listener.$key" "$config_file" 2>/dev/null
}

# Parse arguments
TARGET="all"
TAG="latest"
REGISTRY=""
NO_CACHE=""
PUSH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        --push)
            PUSH="true"
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
            TARGET="$1"
            shift
            ;;
    esac
done

# Check dependencies
check_yq
parse_config

# Validate target
if [ "$TARGET" != "all" ] && ! echo "$TARGETS" | grep -q "^$TARGET$"; then
    print_error "Unknown target: '$TARGET'"
    echo "Available targets: $TARGETS"
    exit 1
fi

# Get listeners to build
LISTENERS_TO_BUILD=$(get_listeners_for_target "$TARGET")

print_status "Building target: $TARGET"
print_status "Listeners to build: $LISTENERS_TO_BUILD"
print_status "Tag: $TAG"
if [ -n "$REGISTRY" ]; then
    print_status "Registry: $REGISTRY"
fi

LOGIN_REGISTRY_HOST=$(resolve_login_registry "$REGISTRY" "${CI_REGISTRY:-}")

# Build each listener
for listener in $LISTENERS_TO_BUILD; do
    print_status "Building $listener listener..."
    
    # Get listener configuration
    MODULE=$(get_listener_config "$listener" "module")
    IMAGE=$(get_listener_config "$listener" "image")
    
    if [ -z "$MODULE" ] || [ -z "$IMAGE" ]; then
        print_error "Invalid configuration for listener: $listener"
        exit 1
    fi
    
    # Build image name
    if [ -n "$REGISTRY" ]; then
        FULL_IMAGE_NAME="$REGISTRY/$IMAGE:$TAG"
    else
        FULL_IMAGE_NAME="$IMAGE:$TAG"
    fi
    
    print_status "Module: $MODULE"
    print_status "Image: $FULL_IMAGE_NAME"
    
    # Build command
    BUILD_CMD="docker build \
        --build-arg LISTENER_MODULE=\"$MODULE\" \
        -t \"$FULL_IMAGE_NAME\" \
        -f dockerfile \
        $NO_CACHE \
        ."
    
    # Execute build
    if eval $BUILD_CMD; then
        print_success "$listener listener built successfully: $FULL_IMAGE_NAME"
        
        # Push if requested
        if [ "$PUSH" = "true" ]; then
            print_status "Pushing $FULL_IMAGE_NAME..."
            if ! validate_push_reference "$FULL_IMAGE_NAME"; then
                exit 1
            fi

            if ! ensure_docker_login "$LOGIN_REGISTRY_HOST"; then
                exit 1
            fi

            if push_output=$(docker push "$FULL_IMAGE_NAME" 2>&1); then
                print_success "Pushed $FULL_IMAGE_NAME"
            else
                print_error "Failed to push $FULL_IMAGE_NAME"
                echo "$push_output"
                exit 1
            fi
        fi
    else
        print_error "Failed to build $listener listener"
        exit 1
    fi
done

print_success "All builds completed successfully!"

# Show built images
print_status "Built images:"
docker images | grep -E "($(echo $LISTENERS_TO_BUILD | tr ' ' '|'))-ws" | head -10
