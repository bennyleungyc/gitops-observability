"""Unit tests for CryptoListener."""

import asyncio
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import yaml

from src.crypto_com_listener.crypto_listener import CryptoListener


class TestCryptoListener:
    """Test suite for CryptoListener."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.module_dir = Path(self.temp_dir)
        self.config_dir = self.module_dir / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Create default config
        default_config = {
            "connection": {"endpoint": "wss://stream.crypto.com/v2/market"},
            "instruments": [
                {"instrument": "BTC_USDT", "depth": 150, "enabled": True}
            ],
            "default_depth": 150,
            "server": {"host": "0.0.0.0", "port": 8001},
            "logging": {"level": "INFO", "format": "text"}
        }
        with open(self.config_dir / "default.yml", "w") as f:
            yaml.dump(default_config, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test CryptoListener initialization."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()

            assert listener.get_exchange_name() == "crypto.com"
            assert listener.config is not None

    def test_get_exchange_name(self):
        """Test getting exchange name."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            assert listener.get_exchange_name() == "crypto.com"

    def test_get_default_config_single_instrument(self):
        """Test getting default config with single instrument."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            config = listener.get_default_config()

            assert config["endpoint"] == "wss://stream.crypto.com/v2/market"
            assert len(config["instruments"]) == 1
            assert config["instruments"][0] == "BTC_USDT"
            assert len(config["channels"]) == 1
            assert config["channels"][0] == "book.BTC_USDT.150"

    def test_get_default_config_multiple_instruments(self):
        """Test getting default config with multiple instruments."""
        config = {
            "connection": {"endpoint": "wss://stream.crypto.com/v2/market"},
            "instruments": [
                {"instrument": "BTC_USDT", "depth": 150, "enabled": True},
                {"instrument": "SOL_USDT", "depth": 200, "enabled": True}
            ],
            "default_depth": 150,
            "server": {"host": "0.0.0.0", "port": 8001},
            "logging": {"level": "INFO", "format": "text"}
        }
        with open(self.config_dir / "default.yml", "w") as f:
            yaml.dump(config, f)

        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            config_result = listener.get_default_config()

            assert len(config_result["instruments"]) == 2
            assert len(config_result["channels"]) == 2
            assert "book.BTC_USDT.150" in config_result["channels"]
            assert "book.SOL_USDT.200" in config_result["channels"]

    def test_subscription_message(self):
        """Test creating subscription message."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            channels = ["book.BTC_USDT.150", "book.SOL_USDT.150"]
            msg = listener._subscription_message(channels)

            assert msg["method"] == "subscribe"
            assert msg["id"] == 3217
            assert "params" in msg
            assert msg["params"]["channels"] == channels
            assert "nonce" in msg["params"]

    def test_process_book_data(self):
        """Test processing book data from Crypto.com."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            result = {
                "data": [{
                    "bids": [["50000", "1.0", "1"], ["49999", "2.0", "2"]],
                    "asks": [["51000", "1.0", "1"], ["51001", "2.0", "2"]],
                    "t": int(time.time() * 1000)
                }]
            }

            with patch("asyncio.create_task"):
                listener._process_book_data(result, "book.BTC_USDT.150")

            assert listener.latest_market_data is not None
            assert listener.latest_market_data["symbol"] == "BTC_USDT"
            assert listener.latest_market_data["subscription"] == "book.BTC_USDT.150"
            assert listener.latest_market_data["best_bid"] == ["50000", "1.0", "1"]
            assert listener.latest_market_data["best_ask"] == ["51000", "1.0", "1"]
            assert listener.latest_market_data["bid_count"] == 2
            assert listener.latest_market_data["ask_count"] == 2

    def test_process_book_data_empty_data(self):
        """Test processing book data with empty data array."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            result = {"data": []}

            listener._process_book_data(result, "book.BTC_USDT.150")

            # Should not update latest_market_data if data is empty
            # (The method returns early, so latest_market_data might be None or unchanged)
            # This depends on implementation - checking that it doesn't crash

    def test_process_book_data_empty_bids_asks(self):
        """Test processing book data with empty bids/asks."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            result = {
                "data": [{
                    "bids": [],
                    "asks": [],
                    "t": int(time.time() * 1000)
                }]
            }

            with patch("asyncio.create_task"):
                listener._process_book_data(result, "book.BTC_USDT.150")

            assert listener.latest_market_data["best_bid"] is None
            assert listener.latest_market_data["best_ask"] is None
            assert listener.latest_market_data["bid_count"] == 0
            assert listener.latest_market_data["ask_count"] == 0

    def test_process_book_data_limits_bids_asks(self):
        """Test that only first 5 bids/asks are stored."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            result = {
                "data": [{
                    "bids": [[f"{50000-i}", "1.0", "1"] for i in range(10)],
                    "asks": [[f"{51000+i}", "1.0", "1"] for i in range(10)],
                    "t": int(time.time() * 1000)
                }]
            }

            with patch("asyncio.create_task"):
                listener._process_book_data(result, "book.BTC_USDT.150")

            assert len(listener.latest_market_data["bids"]) == 5
            assert len(listener.latest_market_data["asks"]) == 5
            assert listener.latest_market_data["bid_count"] == 10

    @pytest.mark.asyncio
    async def test_connect_and_subscribe(self):
        """Test connecting and subscribing."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                json.dumps({
                    "result": {
                        "subscription": "book.BTC_USDT.150",
                        "data": [{
                            "bids": [["50000", "1.0", "1"]],
                            "asks": [["51000", "1.0", "1"]],
                            "t": int(time.time() * 1000)
                        }]
                    }
                }),
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with patch("asyncio.sleep", return_value=None):
                    with pytest.raises(asyncio.CancelledError):
                        await listener.connect_and_subscribe()

            assert listener.connection_status["connected"] is True
            assert mock_ws.send.called  # Subscription message sent

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_heartbeat(self):
        """Test handling heartbeat messages."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                json.dumps({
                    "method": "public/heartbeat",
                    "id": 12345
                }),
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with patch("asyncio.sleep", return_value=None):
                    with pytest.raises(asyncio.CancelledError):
                        await listener.connect_and_subscribe()

            # Should have sent heartbeat response
            from unittest.mock import call
            send_calls = [str(call_args[0][0]) for call_args in mock_ws.send.call_args_list]
            heartbeat_responses = [c for c in send_calls if "public/respond-heartbeat" in c]
            assert len(heartbeat_responses) > 0

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_invalid_json(self):
        """Test handling of invalid JSON messages."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()
            
            mock_ws = AsyncMock()
            mock_ws.recv = AsyncMock(side_effect=[
                "invalid json",
                asyncio.CancelledError()
            ])

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_ws)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            
            with patch("websockets.connect", return_value=mock_context):
                with patch("asyncio.sleep", return_value=None):
                    with pytest.raises(asyncio.CancelledError):
                        await listener.connect_and_subscribe()

            assert listener.connection_status["error_count"] > 0

    @pytest.mark.asyncio
    async def test_connect_and_subscribe_connection_error(self):
        """Test handling of connection errors."""
        with patch("src.crypto_com_listener.crypto_listener.Path") as mock_path:
            mock_path.return_value.parent = self.module_dir
            mock_path.return_value = self.module_dir / "crypto_listener.py"
            
            listener = CryptoListener()

            with patch("websockets.connect", side_effect=Exception("Connection failed")):
                with pytest.raises(Exception, match="Connection failed"):
                    await listener.connect_and_subscribe()

            assert listener.connection_status["connected"] is False
            assert listener.connection_status["error_count"] > 0

