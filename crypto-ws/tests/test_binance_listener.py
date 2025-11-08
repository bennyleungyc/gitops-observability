"""Unit tests for BinanceListener."""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from src.binance_listener.binance_listener import BinanceListener


class TestBinanceListener:
    """Test suite for BinanceListener."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.module_dir = Path(self.temp_dir)
        self.config_dir = self.module_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create default config
        default_config = {
            "connection": {"endpoint": "wss://stream.binance.com:9443/ws"},
            "symbols": [
                {"symbol": "btcusdt", "depth": 10, "enabled": True}
            ],
            "default_depth": 10,
            "server": {"host": "0.0.0.0", "port": 8000},
            "logging": {"level": "INFO", "format": "text"}
        }
        with open(self.config_dir / "default.yml", "w") as f:
            yaml.dump(default_config, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test BinanceListener initialization."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()

            assert listener.get_exchange_name() == "binance"
            assert listener.config is not None

    def test_get_exchange_name(self):
        """Test getting exchange name."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            assert listener.get_exchange_name() == "binance"

    def test_get_default_config_single_symbol(self):
        """Test getting default config with single symbol."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            config = listener.get_default_config()

            assert config["endpoint"] == "wss://stream.binance.com:9443/ws"
            assert len(config["symbols"]) == 1
            assert config["symbols"][0] == "btcusdt"
            assert len(config["streams"]) == 1
            assert config["streams"][0] == "btcusdt@depth10"

    def test_get_default_config_multiple_symbols(self):
        """Test getting default config with multiple symbols."""
        config = {
            "connection": {"endpoint": "wss://stream.binance.com:9443/ws"},
            "symbols": [
                {"symbol": "btcusdt", "depth": 10, "enabled": True},
                {"symbol": "ethusdt", "depth": 20, "enabled": True}
            ],
            "default_depth": 10,
            "server": {"host": "0.0.0.0", "port": 8000},
            "logging": {"level": "INFO", "format": "text"}
        }
        with open(self.config_dir / "default.yml", "w") as f:
            yaml.dump(config, f)

        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            config_result = listener.get_default_config()

            assert len(config_result["symbols"]) == 2
            assert len(config_result["streams"]) == 2
            assert "btcusdt@depth10" in config_result["streams"]
            assert "ethusdt@depth20" in config_result["streams"]

    def test_process_depth_update_single_stream(self):
        """Test processing depth update from single stream."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            msg = {
                "lastUpdateId": 12345,
                "bids": [["50000", "1.0"], ["49999", "2.0"]],
                "asks": [["51000", "1.0"], ["51001", "2.0"]]
            }

            with patch("asyncio.create_task"):
                listener._process_depth_update(msg, "btcusdt@depth10")

            assert listener.latest_market_data is not None
            assert listener.latest_market_data["symbol"] == "btcusdt"
            assert listener.latest_market_data["last_update_id"] == 12345
            assert listener.latest_market_data["best_bid"] == ["50000", "1.0"]
            assert listener.latest_market_data["best_ask"] == ["51000", "1.0"]
            assert listener.latest_market_data["bid_count"] == 2
            assert listener.latest_market_data["ask_count"] == 2

    def test_process_depth_update_empty_bids_asks(self):
        """Test processing depth update with empty bids/asks."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            msg = {
                "lastUpdateId": 12345,
                "bids": [],
                "asks": []
            }

            with patch("asyncio.create_task"):
                listener._process_depth_update(msg, "btcusdt@depth10")

            assert listener.latest_market_data["best_bid"] is None
            assert listener.latest_market_data["best_ask"] is None
            assert listener.latest_market_data["bid_count"] == 0
            assert listener.latest_market_data["ask_count"] == 0

    def test_process_depth_update_limits_bids_asks(self):
        """Test that only first 5 bids/asks are stored."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            msg = {
                "lastUpdateId": 12345,
                "bids": [[f"{50000-i}", "1.0"] for i in range(10)],
                "asks": [[f"{51000+i}", "1.0"] for i in range(10)]
            }

            with patch("asyncio.create_task"):
                listener._process_depth_update(msg, "btcusdt@depth10")

            assert len(listener.latest_market_data["bids"]) == 5
            assert len(listener.latest_market_data["asks"]) == 5
            assert listener.latest_market_data["bid_count"] == 10

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_single_stream(self):
        """Test connecting and subscribing to single stream."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                json.dumps({
                    "lastUpdateId": 12345,
                    "bids": [["50000", "1.0"]],
                    "asks": [["51000", "1.0"]]
                }),
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with pytest.raises(asyncio.CancelledError):
                    await listener.connect_and_subscribe()

            assert listener.connection_status["connected"] is True
            assert listener.connection_status["message_count"] > 0

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_combined_stream(self):
        """Test connecting and subscribing to combined stream."""
        config = {
            "connection": {"endpoint": "wss://stream.binance.com:9443/ws"},
            "symbols": [
                {"symbol": "btcusdt", "depth": 10, "enabled": True},
                {"symbol": "ethusdt", "depth": 10, "enabled": True}
            ],
            "default_depth": 10,
            "server": {"host": "0.0.0.0", "port": 8000},
            "logging": {"level": "INFO", "format": "text"}
        }
        with open(self.config_dir / "default.yml", "w") as f:
            yaml.dump(config, f)

        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                json.dumps({
                    "stream": "btcusdt@depth10",
                    "data": {
                        "lastUpdateId": 12345,
                        "bids": [["50000", "1.0"]],
                        "asks": [["51000", "1.0"]]
                    }
                }),
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with pytest.raises(asyncio.CancelledError):
                    await listener.connect_and_subscribe()

            assert listener.connection_status["connected"] is True

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_invalid_json(self):
        """Test handling of invalid JSON messages."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                "invalid json",
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with pytest.raises(asyncio.CancelledError):
                    await listener.connect_and_subscribe()

            assert listener.connection_status["error_count"] > 0

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_connection_error(self):
        """Test handling of connection errors."""
        with patch("src.binance_listener.binance_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "binance_listener.py"
            
            listener = BinanceListener()

            with patch("websockets.connect", side_effect=Exception("Connection failed")):
                with pytest.raises(Exception, match="Connection failed"):
                    await listener.connect_and_subscribe()

            assert listener.connection_status["connected"] is False
            assert listener.connection_status["error_count"] > 0

