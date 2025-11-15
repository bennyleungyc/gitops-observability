"""Unit tests for BaseExchangeListener."""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import make_mocked_request

from src.common.base_listener import BaseExchangeListener


class ConcreteListener(BaseExchangeListener):
    """Concrete implementation for testing."""

    def get_exchange_name(self):
        """Return exchange name."""
        return "test_exchange"

    def get_default_config(self):
        """Return default config."""
        return {
            "server": {"host": "0.0.0.0", "port": 8000},
            "redis": {"host": "localhost", "port": 6379}
        }

    async def connect_and_subscribe(self):
        """Mock implementation."""
        pass


class TestBaseExchangeListener:
    """Test suite for BaseExchangeListener."""

    def setup_method(self):
        """Set up test fixtures."""
        self.listener = ConcreteListener()

    def test_init(self):
        """Test listener initialization."""
        assert self.listener.connection_status["connected"] is False
        assert self.listener.connection_status["exchange"] == "test_exchange"
        assert self.listener.connection_status["message_count"] == 0
        assert self.listener.connection_status["error_count"] == 0
        assert self.listener.latest_market_data is None
        assert self.listener.logger is None
        assert self.listener.redis_client is None

    def test_get_exchange_name(self):
        """Test getting exchange name."""
        assert self.listener.get_exchange_name() == "test_exchange"

    def test_update_connection_status_connected(self):
        """Test updating connection status when connected."""
        self.listener._update_connection_status(connected=True)

        assert self.listener.connection_status["connected"] is True
        assert self.listener.connection_status["last_error"] is None

    def test_update_connection_status_disconnected_with_error(self):
        """Test updating connection status when disconnected with error."""
        self.listener._update_connection_status(connected=False, error="Connection failed")

        assert self.listener.connection_status["connected"] is False
        assert self.listener.connection_status["error_count"] == 1
        assert self.listener.connection_status["last_error"] == "Connection failed"

    def test_update_message_received(self):
        """Test updating status when message is received."""
        initial_count = self.listener.connection_status["message_count"]
        self.listener._update_message_received()

        assert self.listener.connection_status["message_count"] == initial_count + 1
        assert self.listener.connection_status["last_message_time"] is not None

    @pytest.mark.asyncio
    async def test_send_json(self):
        """Test sending JSON to WebSocket."""
        ws = AsyncMock()
        payload = {"method": "subscribe", "params": {"channels": ["test"]}}

        await self.listener._send_json(ws, payload)

        ws.send.assert_called_once_with(json.dumps(payload))

    @pytest.mark.asyncio
    async def test_initialize_redis(self):
        """Test Redis initialization."""
        config = {
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        }

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)

        with patch("src.common.base_listener.redis.Redis", return_value=mock_redis):
            await self.listener._initialize_redis(config)

        assert self.listener.redis_client is not None

    @pytest.mark.asyncio
    async def test_store_orderbook_to_redis(self):
        """Test storing orderbook to Redis."""
        mock_redis = AsyncMock()
        self.listener.redis_client = mock_redis

        orderbook_data = {
            "symbol": "btcusdt",
            "timestamp": int(time.time() * 1000),
            "bids": [["50000", "1.0"]],
            "asks": [["51000", "1.0"]]
        }

        await self.listener._store_orderbook_to_redis(orderbook_data)

        assert mock_redis.setex.call_count == 2  # Full key + latest key

    @pytest.mark.asyncio
    async def test_store_orderbook_to_redis_no_client(self):
        """Test storing orderbook when Redis client is not available."""
        self.listener.redis_client = None

        orderbook_data = {"symbol": "btcusdt"}

        # Should not raise an error
        await self.listener._store_orderbook_to_redis(orderbook_data)

    @pytest.mark.asyncio
    async def test_cleanup_redis(self):
        """Test Redis cleanup."""
        mock_redis = AsyncMock()
        self.listener.redis_client = mock_redis

        await self.listener._cleanup_redis()

        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_redis_no_client(self):
        """Test Redis cleanup when client is not available."""
        self.listener.redis_client = None

        # Should not raise an error
        await self.listener._cleanup_redis()

    @pytest.mark.asyncio
    async def test_handle_health_healthy(self):
        """Test health check endpoint when healthy."""
        self.listener.connection_status["connected"] = True
        self.listener.connection_status["last_message_time"] = time.time()
        self.listener.redis_client = AsyncMock()
        self.listener.redis_client.ping = AsyncMock(return_value=True)

        request = make_mocked_request("GET", "/health")

        with patch("psutil.cpu_percent", return_value=50), \
             patch("psutil.virtual_memory", return_value=MagicMock(percent=50, total=8*1024**3, available=4*1024**3)), \
             patch("psutil.disk_usage", return_value=MagicMock(percent=50, total=100*1024**3, free=50*1024**3)):
            response = await self.listener.handle_health(request)

        assert response.status == 200
        data = json.loads(response.text)
        assert data["status"] == "healthy"
        assert data["exchange"] == "test_exchange"
        assert data["websocket"]["connected"] is True

    @pytest.mark.asyncio
    async def test_handle_health_unhealthy_websocket(self):
        """Test health check endpoint when WebSocket is unhealthy."""
        self.listener.connection_status["connected"] = False
        self.listener.redis_client = AsyncMock()
        self.listener.redis_client.ping = AsyncMock(return_value=True)

        request = make_mocked_request("GET", "/health")

        with patch("psutil.cpu_percent", return_value=50), \
             patch("psutil.virtual_memory", return_value=MagicMock(percent=50, total=8*1024**3, available=4*1024**3)), \
             patch("psutil.disk_usage", return_value=MagicMock(percent=50, total=100*1024**3, free=50*1024**3)):
            response = await self.listener.handle_health(request)

        assert response.status == 503
        data = json.loads(response.text)
        assert data["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_handle_health_stale_message(self):
        """Test health check endpoint when last message is stale."""
        self.listener.connection_status["connected"] = True
        self.listener.connection_status["last_message_time"] = time.time() - 60  # 60 seconds ago
        self.listener.redis_client = AsyncMock()
        self.listener.redis_client.ping = AsyncMock(return_value=True)

        request = make_mocked_request("GET", "/health")

        with patch("psutil.cpu_percent", return_value=50), \
             patch("psutil.virtual_memory", return_value=MagicMock(percent=50, total=8*1024**3, available=4*1024**3)), \
             patch("psutil.disk_usage", return_value=MagicMock(percent=50, total=100*1024**3, free=50*1024**3)):
            response = await self.listener.handle_health(request)

        assert response.status == 503
        data = json.loads(response.text)
        assert data["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_handle_health_unhealthy_redis(self):
        """Test health check endpoint when Redis is unhealthy."""
        self.listener.connection_status["connected"] = True
        self.listener.connection_status["last_message_time"] = time.time()
        self.listener.redis_client = AsyncMock()
        self.listener.redis_client.ping = AsyncMock(side_effect=Exception("Redis error"))

        request = make_mocked_request("GET", "/health")

        with patch("psutil.cpu_percent", return_value=50), \
             patch("psutil.virtual_memory", return_value=MagicMock(percent=50, total=8*1024**3, available=4*1024**3)), \
             patch("psutil.disk_usage", return_value=MagicMock(percent=50, total=100*1024**3, free=50*1024**3)):
            response = await self.listener.handle_health(request)

        assert response.status == 503
        data = json.loads(response.text)
        assert data["status"] == "unhealthy"
        assert data["redis"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_handle_market_data_available(self):
        """Test market data endpoint when data is available."""
        self.listener.latest_market_data = {
            "symbol": "btcusdt",
            "price": 50000,
            "received_at": time.time()
        }

        request = make_mocked_request("GET", "/market")
        response = await self.listener.handle_market_data(request)

        assert response.status == 200
        data = json.loads(response.text)
        assert data["symbol"] == "btcusdt"

    @pytest.mark.asyncio
    async def test_handle_market_data_not_available(self):
        """Test market data endpoint when data is not available."""
        self.listener.latest_market_data = None

        request = make_mocked_request("GET", "/market")
        response = await self.listener.handle_market_data(request)

        assert response.status == 503
        data = json.loads(response.text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_handle_market_data_stale(self):
        """Test market data endpoint when data is stale."""
        self.listener.latest_market_data = {
            "symbol": "btcusdt",
            "price": 50000,
            "received_at": time.time() - 120  # 120 seconds ago
        }

        request = make_mocked_request("GET", "/market")
        response = await self.listener.handle_market_data(request)

        assert response.status == 503
        data = json.loads(response.text)
        assert "error" in data
        assert "stale" in data["error"].lower()

    def test_create_app(self):
        """Test creating aiohttp application."""
        app = self.listener.create_app()

        assert isinstance(app, web.Application)
        # Check that health and market routes exist
        routes = list(app.router.routes())
        route_paths = [str(route.resource.canonical) for route in routes if hasattr(route.resource, 'canonical')]
        assert "/health" in route_paths
        assert "/market" in route_paths

