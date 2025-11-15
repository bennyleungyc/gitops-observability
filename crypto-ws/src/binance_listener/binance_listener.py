"""Binance exchange WebSocket listener implementation."""

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


class BinanceListener(BaseExchangeListener):
    """WebSocket listener for Binance exchange."""

    def __init__(self, custom_config_path: str = None):
        """
        Initialize Binance listener with configuration.
        
        Args:
            custom_config_path: Optional path to custom config file
        """
        super().__init__()
        
        # Initialize config loader
        module_dir = Path(__file__).parent
        self.config_loader = ConfigLoader(module_dir, "binance")
        self.custom_config_path = custom_config_path
        
        # Load configuration
        self.config = self.config_loader.load(custom_config_path)
        
        # Setup logger
        self.logger = setup_logger(__name__, self.config, exchange_name="binance")

    def get_exchange_name(self) -> str:
        """Return exchange name."""
        return "binance"

    def get_default_config(self) -> Dict[str, Any]:
        """
        Return Binance specific configuration.
        
        Loads from YAML files with environment variable overrides.
        Priority: ENV vars > custom config > local config > env config > default config
        """
        # Get symbols configuration
        symbols_config = self.config_loader.get_symbols_config(self.config)
        
        # Get connection settings
        connection = self.config.get("connection", {})
        endpoint = connection.get("endpoint", "wss://stream.binance.com:9443/ws")
        
        # Build streams from symbol configs
        symbols = []
        streams = []
        for sym_cfg in symbols_config:
            symbol = sym_cfg["symbol"]
            depth = sym_cfg["depth"]
            symbols.append(symbol)
            streams.append(f"{symbol}@depth{depth}")
        
        return {
            "endpoint": endpoint,
            "symbols": symbols,
            "streams": streams,
            "connection": connection,
            "server": self.config.get("server", {}),
            "logging": self.config.get("logging", {})
        }

    async def connect_and_subscribe(self) -> None:
        """
        Connect to Binance WebSocket and subscribe to market data.
        
        Binance uses a different model - you connect to a specific stream URL,
        no explicit subscribe message needed for individual streams.
        For multiple streams, use combined stream endpoint.
        """
        cfg = self.get_default_config()
        endpoint = cfg["endpoint"]
        streams = cfg["streams"]
        
        # Construct full WebSocket URL
        # Single stream: ws://host/ws/<streamName>
        # Multiple streams: ws://host/stream?streams=<stream1>/<stream2>/<stream3>
        if len(streams) == 1:
            ws_url = f"{endpoint}/{streams[0]}"
        else:
            combined_streams = "/".join(streams)
            ws_url = f"{endpoint.replace('/ws', '/stream')}?streams={combined_streams}"
        
        self.logger.info(f"Connecting to {ws_url}")
        self.logger.info(f"Subscribing to streams: {', '.join(streams)}")
        
        try:
            async with websockets.connect(ws_url) as ws:
                self._update_connection_status(connected=True)
                self.logger.info(f"Connected to Binance - monitoring {len(streams)} stream(s)")

                # Binance doesn't require explicit subscription
                # It streams data immediately after connection
                
                while True:
                    raw = await ws.recv()
                    self._update_message_received()

                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError as e:
                        self._update_connection_status(connected=True, error=str(e))
                        self.logger.warning(f"Non-JSON message: {raw}")
                        continue

                    # For combined streams, msg has format: {"stream": "btcusdt@depth10", "data": {...}}
                    # For single stream, msg is just the data: {"lastUpdateId": ..., "bids": ...}
                    if "stream" in msg and "data" in msg:
                        # Combined stream format
                        stream_name = msg["stream"]
                        data = msg["data"]
                        if "lastUpdateId" in data:
                            self._process_depth_update(data, stream_name)
                    elif "lastUpdateId" in msg:
                        # Single stream format
                        self._process_depth_update(msg, streams[0])

        except Exception as e:
            self._update_connection_status(connected=False, error=str(e))
            self.logger.error(f"WebSocket connection error: {e}", exc_info=True)
            raise

    def _process_depth_update(self, msg: Dict[str, Any], stream: str) -> None:
        """
        Process depth update from Binance.
        
        Binance partial book depth message format:
        {
            "lastUpdateId": 160,
            "bids": [["0.0024", "10"]],  # [price, quantity]
            "asks": [["0.0026", "100"]]
        }
        """
        # Extract symbol from stream name (e.g., "btcusdt@depth10" -> "btcusdt")
        symbol = stream.split("@")[0] if "@" in stream else stream
        
        bids = msg.get("bids", [])
        asks = msg.get("asks", [])
        last_update_id = msg.get("lastUpdateId")
        
        best_bid = bids[0] if bids else None
        best_ask = asks[0] if asks else None

        self.latest_market_data = {
            "exchange": self.get_exchange_name(),
            "symbol": symbol,
            "stream": stream,
            "last_update_id": last_update_id,
            "timestamp": int(time.time() * 1000),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "bid_count": len(bids),
            "ask_count": len(asks),
            "bids": bids[:5],
            "asks": asks[:5],
            "received_at": time.time()
        }

        # Store orderbook data to Redis if enabled
        asyncio.create_task(self._store_orderbook_to_redis(self.latest_market_data))

        self.logger.debug(
            f"{stream} update_id={last_update_id} best_bid={best_bid} best_ask={best_ask} "
            f"bids={len(bids)} asks={len(asks)}"
        )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Binance WebSocket Listener with YAML configuration")
    parser.add_argument("--config", type=str, help="Path to custom configuration file")
    args = parser.parse_args()
    
    listener = BinanceListener(custom_config_path=args.config)
    listener.main()

