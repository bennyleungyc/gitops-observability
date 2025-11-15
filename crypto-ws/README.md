# WebSocket Exchange Listeners

[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/websocket-trial/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/websocket-trial/actions/workflows/ci.yml)
[![Security Scanning](https://github.com/YOUR_USERNAME/websocket-trial/actions/workflows/security.yml/badge.svg)](https://github.com/YOUR_USERNAME/websocket-trial/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Industry-standard WebSocket listeners for cryptocurrency exchanges with unified Docker build system and automated CI/CD.

## 🚀 Features

- **Unified Build System**: Single dockerfile for all exchange listeners
- **Multi-Stage Builds**: Optimized images with minimal attack surface
- **Security Hardened**: Non-root user, health checks, and security best practices
- **Configuration-Driven**: YAML-based configuration with environment overrides
- **Docker Compose Ready**: Development and production configurations
- **Scalable Architecture**: Easy to add new exchanges
- **Redis Integration**: Automatic orderbook data storage with configurable TTL
- **Real-time Data**: WebSocket streams with HTTP API endpoints
- **CI/CD Pipeline**: Automated builds, tests, and security scanning with GitHub Actions
- **Automated Security**: Trivy scanning, CodeQL analysis, and Dependabot updates

## 📁 Project Structure

```
websocket-trial/
├── dockerfile                    # Unified multi-stage dockerfile
├── build-config.yml             # Build configuration
├── docker-compose.yml           # Development setup
├── docker-compose.prod.yml      # Production configuration
├── requirements.txt             # Python dependencies
├── redis-example.yml            # Redis configuration example
├── REDIS_INTEGRATION.md         # Redis integration documentation
├── src/
│   ├── common/                  # Shared base classes
│   ├── binance_listener/        # Binance WebSocket listener
│   └── crypto_com_listener/     # Crypto.com WebSocket listener
├── web_socket_implementation/   # Standalone WebSocket implementation
├── control/                     # Build and run scripts
│   ├── build_listener.sh        # Build individual listener (fast)
│   ├── build_all.sh             # Build all listeners individually
│   ├── build_compose.sh         # Build using docker-compose.yml
│   ├── test_integration.sh      # Integration test (mirrors CI)
│   └── build_advanced.sh        # Configuration-driven build
└── .github/workflows/           # CI/CD pipelines
    ├── ci.yml                   # Main CI/CD pipeline
    ├── security.yml             # Security scanning
    └── deploy.yml               # Production deployment
```

## 🏗️ Build System

The project supports **three build approaches** for different use cases:

### 1️⃣ Individual Builds (Quick Iteration)

**Use case:** Fast local development, testing individual services

```bash
# Build all listeners individually
./control/build_all.sh

# Build specific listener
./control/build_listener.sh binance
./control/build_listener.sh crypto

# Build with custom tag
./control/build_listener.sh binance --tag v1.0.0
```

**Pros:** Fast, simple, good for quick iteration
**When:** During active development of a single service

---

### 2️⃣ Docker Compose Build (Integration Testing)

**Use case:** Test all services together, validate docker-compose.yml

```bash
# Build all services using docker-compose.yml
./control/build_compose.sh

# Run full integration test (mirrors CI)
./control/test_integration.sh
```

**What it does:**
- Builds all services as defined in `docker-compose.yml`
- Same approach used in CI integration tests
- Validates service orchestration

**Pros:** Tests complete system, validates compose configuration
**When:** Before committing, testing multi-service interactions

---

### 3️⃣ Docker Compose Up (Development)

**Use case:** Run services for local development

```bash
# Development mode
docker compose up -d

# Production mode
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose logs -f binance
docker compose logs -f crypto

# Stop services
docker compose down
```

**Pros:** Easy to manage multiple services, automatic networking
**When:** Daily development, debugging multiple services

---

### 📊 Build Strategy Comparison

| Method | Speed | Use Case | CI Equivalent |
|--------|-------|----------|---------------|
| `build_listener.sh` | ⚡ Fastest | Quick iteration | Individual matrix builds |
| `build_compose.sh` | 🐢 Slower | Integration test | `docker-compose-test` job |
| `docker compose up` | 🐢 Slower | Run services | Not in CI (deployment only) |

---

### Advanced Build (Configuration-Driven)

```bash
# Requires yq: brew install yq (macOS) or apt install yq (Ubuntu)

# Build all listeners
./control/build_advanced.sh all

# Build specific target
./control/build_advanced.sh binance-only

# Build and push to registry
./control/build_advanced.sh all --registry gcr.io/myproject --push
```

## 🔧 Configuration

### Environment Variables

#### Redis Configuration
- `REDIS_HOST` - Redis server host (default: `localhost`)
- `REDIS_PORT` - Redis server port (default: `6379`)
- `REDIS_PASSWORD` - Redis password (optional)
- `REDIS_DB` - Redis database number (default: `0`)
- `REDIS_ENABLED` - Enable Redis storage (default: `false`)

#### Binance Listener
- `BINANCE_SYMBOLS` - Comma-separated symbols (default: `btcusdt`)
- `BINANCE_DEPTH` - Order book depth (default: `10`)
- `BINANCE_WS_ENDPOINT` - WebSocket endpoint

#### Crypto.com Listener
- `CRYPTO_INSTRUMENTS` - Comma-separated instruments (default: `BTC_USDT`)
- `CRYPTO_DEPTH` - Order book depth (default: `10`)
- `CRYPTO_WS_ENDPOINT` - WebSocket endpoint

### YAML Configuration

Each listener supports YAML configuration files with priority-based merging:

1. Environment variables (highest priority)
2. Custom config file (`--config` flag)
3. Local config (`config/local.yml` - gitignored)
4. Environment config (`config/prod.yml`, `config/dev.yml`)
5. Default config (`config/default.yml` - lowest priority)

### Example Configurations

```bash
# Single symbol
BINANCE_SYMBOLS=btcusdt ./control/build_listener.sh binance

# Multiple symbols with custom depth
BINANCE_SYMBOLS=btcusdt,ethusdt,bnbusdt BINANCE_DEPTH=20 ./control/build_listener.sh binance

# Custom config file
docker run -v $(pwd)/my-config.yml:/app/config.yml:ro \
  -e CONFIG_FILE=/app/config.yml \
  binance-ws:latest
```

## 🐳 Docker Usage

### Build Images

```bash
# Build all listeners
./control/build_all.sh

# Build specific listener
./control/build_listener.sh binance

# Build with no cache
./control/build_listener.sh binance --no-cache
```

### Run Containers

```bash
# Run Binance listener with Redis
docker run -d -p 8002:8000 \
  -e BINANCE_SYMBOLS=btcusdt,ethusdt \
  -e BINANCE_DEPTH=20 \
  -e REDIS_HOST=redis-server \
  -e REDIS_PORT=6379 \
  -e REDIS_ENABLED=true \
  binance-ws:latest

# Run Crypto.com listener with Redis
docker run -d -p 8001:8000 \
  -e CRYPTO_INSTRUMENTS=BTC_USDT,ETH_USDT \
  -e CRYPTO_DEPTH=20 \
  -e REDIS_HOST=redis-server \
  -e REDIS_PORT=6379 \
  -e REDIS_ENABLED=true \
  crypto-ws:latest
```

### Docker Compose

```bash
# Development setup
docker compose up -d

# Production setup
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop all services
docker compose down
```

## 📊 API Endpoints

Each listener exposes HTTP endpoints:

- **Health Check**: `http://localhost:PORT/health`
  - Returns connection status, message count, uptime, system metrics
  
- **Market Data**: `http://localhost:PORT/market`
  - Returns latest order book data

Default ports:
- Crypto.com: `8001`
- Binance: `8002`

## 🔴 Redis Integration

The listeners automatically store orderbook data to Redis when enabled, providing persistent storage and easy access to historical market data.

### Redis Configuration

Enable Redis by setting environment variables:

```bash
# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password  # Optional
REDIS_DB=0                    # Optional, defaults to 0

# Enable Redis storage
REDIS_ENABLED=true
```

### Redis Data Structure

Orderbook data is stored with the following key patterns:

```
# Historical data (expires after 1 hour)
orderbook:{exchange}:{symbol}:{timestamp}

# Latest data (expires after 1 minute)
orderbook:{exchange}:{symbol}:latest
```

**Examples:**
```
orderbook:crypto.com:SOL_USDT:1761390673060
orderbook:crypto.com:SOL_USDT:latest
orderbook:binance:btcusdt:1761390673060
orderbook:binance:btcusdt:latest
```

### Redis Data Format

Each Redis key contains JSON data with the following structure:

```json
{
  "exchange": "crypto.com",
  "symbol": "SOL_USDT",
  "subscription": "book.SOL_USDT.150",
  "timestamp": 1761390673060,
  "best_bid": ["191.98", "13.713", "8"],
  "best_ask": ["191.99", "0.007", "1"],
  "bid_count": 150,
  "ask_count": 150,
  "bids": [["191.98", "13.713", "8"], ...],
  "asks": [["191.99", "0.007", "1"], ...],
  "received_at": 1703521873.456
}
```

### Redis Usage Examples

```bash
# Connect to Redis
redis-cli

# Get latest orderbook for SOL_USDT on Crypto.com
GET orderbook:crypto.com:SOL_USDT:latest

# Get all keys for a specific symbol
KEYS orderbook:crypto.com:SOL_USDT:*

# Get all latest orderbooks
KEYS orderbook:*:latest

# Monitor Redis commands in real-time
MONITOR
```

### Docker Compose with Redis

```yaml
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  binance:
    build: .
    ports:
      - "8002:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_ENABLED=true
      - BINANCE_SYMBOLS=btcusdt,ethusdt
    depends_on:
      - redis

  crypto:
    build: .
    ports:
      - "8001:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_ENABLED=true
      - CRYPTO_INSTRUMENTS=BTC_USDT,ETH_USDT
    depends_on:
      - redis

volumes:
  redis_data:
```

### Redis Performance

- **Automatic TTL**: Historical data expires after 1 hour, latest data after 1 minute
- **Efficient Storage**: Only top 5 bids/asks stored to minimize memory usage
- **Async Operations**: Redis writes don't block WebSocket processing
- **Error Handling**: Graceful fallback if Redis is unavailable

## 🧪 Local Development

### Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (optional, for data persistence)
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Run Locally

```bash
# Run Binance listener with Redis
REDIS_ENABLED=true REDIS_HOST=localhost REDIS_PORT=6379 \
BINANCE_SYMBOLS=btcusdt,ethusdt,bnbusdt \
BINANCE_DEPTH=20 \
python -m src.binance_listener.binance_listener

# Run Crypto.com listener with Redis
REDIS_ENABLED=true REDIS_HOST=localhost REDIS_PORT=6379 \
CRYPTO_INSTRUMENTS=BTC_USDT,ETH_USDT,SOL_USDT \
CRYPTO_DEPTH=20 \
python -m src.crypto_com_listener.crypto_listener

# Run with custom config
python -m src.binance_listener.binance_listener \
  --config src/binance_listener/config/examples/multi-symbol.yml
```

## 🏭 Production Deployment

### Docker Compose Production

```bash
# Deploy to production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale binance=2
```

### Kubernetes

```yaml
# Example Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: binance-ws
spec:
  replicas: 2
  selector:
    matchLabels:
      app: binance-ws
  template:
    metadata:
      labels:
        app: binance-ws
    spec:
      containers:
      - name: binance-ws
        image: binance-ws:latest
        ports:
        - containerPort: 8000
        env:
        - name: BINANCE_SYMBOLS
          value: "btcusdt,ethusdt,bnbusdt"
        - name: BINANCE_DEPTH
          value: "20"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
```

## 🔒 Security Features

- **Non-root User**: Containers run as user `appuser` (UID 1000)
- **Multi-stage Builds**: Minimal runtime image without build tools
- **Health Checks**: Built-in health monitoring
- **Resource Limits**: Configurable CPU and memory limits
- **Security Scanning**: Compatible with Trivy, Snyk, etc.

## 📈 Performance

- **Optimized Images**: ~157MB (vs ~200MB+ with old system)
- **Layer Caching**: Efficient Docker layer caching
- **Multi-stage Builds**: Faster builds and smaller images
- **Resource Efficient**: Low CPU and memory usage

## 🧪 Testing

```bash
# Run tests
pytest

# Test specific listener
pytest tests/test_binance_listener.py

# Test with Docker
docker run --rm binance-ws:latest python -m pytest
```

## 🔧 Adding New Exchanges

1. Create new listener in `src/new_exchange_listener/`
2. Extend `BaseExchangeListener`
3. Add configuration to `build-config.yml`
4. Update build scripts

Example:
```yaml
# In build-config.yml
listeners:
  new_exchange:
    module: src.new_exchange_listener.new_exchange_listener
    image: new-exchange-ws
    port: 8003
    description: "New Exchange WebSocket listener"
```

## 🔄 CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline using GitHub Actions:

### **Automated Workflows**

#### 1. **CI/CD Pipeline** (`ci.yml`)
- Automatic builds on push and PR
- Python linting (flake8) and formatting (black)
- Automated testing with pytest
- Docker image building (matrix strategy)
- Security scanning with Trivy
- Integration testing with Docker Compose
- Push to GitHub Container Registry

#### 2. **Security Scanning** (`security.yml`)
- Daily vulnerability scans
- CodeQL static analysis
- Dependency review
- Container security scanning
- Secret detection with TruffleHog

#### 3. **Production Deployment** (`deploy.yml`)
- Manual deployment workflow
- Environment selection (staging/production)
- Version control
- Health checks

### **Getting Started with CI/CD**

```bash
# 1. Fork/clone the repository
git clone https://github.com/YOUR_USERNAME/websocket-trial.git

# 2. Enable GitHub Actions in repository settings

# 3. Update badge URLs in README with your username

# 4. Push changes to trigger CI
git add .
git commit -m "feat: enable CI/CD"
git push
```

### **Viewing Build Status**

- Check **Actions** tab in GitHub
- View security alerts in **Security** tab
- See build badges in README

### **Container Registry**

Images are automatically pushed to GitHub Container Registry:
```bash
# Pull images
docker pull ghcr.io/YOUR_USERNAME/binance-ws:latest
docker pull ghcr.io/YOUR_USERNAME/crypto-ws:latest
```

For detailed CI/CD documentation, see [CI/CD Guide](.github/CICD_GUIDE.md).

## 📚 Documentation

- [CI/CD Guide](.github/CICD_GUIDE.md) - Complete CI/CD pipeline documentation
- [Cleanup Summary](CLEANUP_SUMMARY.md) - Project cleanup and optimization details
- [Redis Integration](REDIS_INTEGRATION.md) - Detailed Redis integration guide
- [Build System Design](BUILD_SYSTEM_DESIGN.md) - Build system architecture and design

## 🎯 Industry Best Practices

This project implements industry-standard practices:

- ✅ **DRY Principle**: Single dockerfile for all listeners
- ✅ **Security First**: Non-root user, minimal attack surface, automated scanning
- ✅ **Configuration-Driven**: YAML-based configuration management
- ✅ **Multi-stage Builds**: Optimized Docker images
- ✅ **Health Monitoring**: Built-in health checks
- ✅ **Scalable Architecture**: Easy to add new exchanges
- ✅ **Production Ready**: Resource limits, logging, monitoring
- ✅ **CI/CD Automation**: Automated builds, tests, and deployments
- ✅ **Security Scanning**: Trivy, CodeQL, dependency review, secret detection

## 📄 License

MIT

---

**Built with industry best practices for production-ready WebSocket exchange listeners.**