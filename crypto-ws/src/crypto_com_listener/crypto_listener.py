"""Crypto.com exchange WebSocket listener implementation."""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import websockets

from src.common.base_listener import BaseExchangeListener
from src.common.config_loader import ConfigLoader
from src.common.logger import setup_logger


class CryptoListener(BaseExchangeListener):
    """WebSocket listener for Crypto.com exchange."""

    def __init__(self, custom_config_path: str = None):
        """
        Initialize Crypto.com listener with configuration.
        
        Args:
            custom_config_path: Optional path to custom config file
        """
        super().__init__()
        
        # Initialize config loader
        module_dir = Path(__file__).parent
        self.config_loader = ConfigLoader(module_dir, "crypto")
        self.custom_config_path = custom_config_path
        
        # Load configuration
        self.config = self.config_loader.load(custom_config_path)
        
        # Setup logger
        self.logger = setup_logger(__name__, self.config, exchange_name="crypto")

    def get_exchange_name(self) -> str:
        """Return exchange name."""
        return "crypto.com"

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return Crypto.com specific configuration.
        
        Loads from YAML files with environment variable overrides.
        Priority: ENV vars > custom config > local config > env config > default config
        """
        # Get instruments configuration
        instruments_config = self.config_loader.get_instruments_config(self.config)
        
        # Get connection settings
        connection = self.config.get("connection", {})
        endpoint = connection.get("endpoint", "wss://stream.crypto.com/v2/market")
        
        # Build channels from instrument configs
        instruments = []
        channels = []
        for inst_cfg in instruments_config:
            instrument = inst_cfg["instrument"]
            depth = inst_cfg["depth"]
            instruments.append(instrument)
            channels.append(f"book.{instrument}.{depth}")
        
        return {
            "endpoint": endpoint,
            "instruments": instruments,
            "channels": channels,
            "connection": connection,
            "server": self.config.get("server", {}),
            "logging": self.config.get("logging", {})
        }

    def _subscription_message(self, channels: list) -> Dict[str, Any]:
        """Create Crypto.com subscription message for multiple channels."""
        return {
            "id": 3217,
            "method": "subscribe",
            "params": {
                "channels": channels,
                "nonce": int(time.time() * 1000)
            }
        }

    async def connect_and_subscribe(self) -> None:
        """Connect to Crypto.com WebSocket and subscribe to market data."""
        cfg = self.get_default_config()
        endpoint = cfg["endpoint"]
        channels = cfg["channels"]

        self.logger.info(f"Connecting to {endpoint}")
        self.logger.info(f"Subscribing to channels: {', '.join(channels)}")
        
        try:
            async with websockets.connect(endpoint) as ws:
                self._update_connection_status(connected=True)

                # Wait ~1s after connect to avoid pro-rated rate limits
                await asyncio.sleep(1.0)

                sub = self._subscription_message(channels)
                self.logger.info(f"Subscribing to {len(channels)} channel(s)")
                await self._send_json(ws, sub)

                # Handle messages and heartbeats
                while True:
                    raw = await ws.recv()
                    self._update_message_received()

                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError as e:
                        self._update_connection_status(connected=True, error=str(e))
                        self.logger.warning(f"Non-JSON message: {raw}")
                        continue

                    # Handle heartbeat
                    method = msg.get("method")
                    if method == "public/heartbeat":
                        hb_id = msg.get("id")
                        if hb_id is not None:
                            response = {"id": hb_id, "method": "public/respond-heartbeat"}
                            await self._send_json(ws, response)
                        continue

                    # Handle market data
                    if "result" in msg:
                        result = msg.get("result", {})
                        subscription = result.get("subscription", "")
                        if subscription.startswith("book."):
                            self._process_book_data(result, subscription)

        except Exception as e:
            self._update_connection_status(connected=False, error=str(e))
            self.logger.error(f"WebSocket connection error: {e}", exc_info=True)
            raise

    def _process_book_data(self, result: Dict[str, Any], subscription: str) -> None:
        """Process order book data from Crypto.com."""
        data = result.get("data", [])
        if not data:
            return

        book = data[0]
        bids = book.get("bids", [])
        asks = book.get("asks", [])
        ts = book.get("t")
        
        best_bid = bids[0] if bids else None
        best_ask = asks[0] if asks else None

        # Extract symbol from subscription (e.g., "book.SOL_USDT.150" -> "SOL_USDT")
        symbol = "unknown"
        if subscription.startswith("book."):
            parts = subscription.split(".")
            if len(parts) >= 2:
                symbol = parts[1]

        self.latest_market_data = {
            "exchange": self.get_exchange_name(),
            "subscription": subscription,
            "symbol": symbol,
            "timestamp": ts,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bid_count": len(bids),
            "ask_count": len(asks),
            "bids": bids[:5],
            "asks": asks[:5],
            "received_at": time.time()
        }

        self.logger.debug(
            f"{subscription} t={ts} best_bid={best_bid} best_ask={best_ask} "
            f"bids={len(bids)} asks={len(asks)}"
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto.com WebSocket Listener with YAML configuration")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    args = parser.parse_args()
    
    listener = CryptoListener(custom_config_path=args.config)
    listener.main()

