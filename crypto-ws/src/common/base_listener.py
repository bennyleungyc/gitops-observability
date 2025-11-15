"""Abstract base class for exchange WebSocket listeners."""

import asyncio
import json
import logging
import signal
import sys
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import psutil
from aiohttp import web

from src.common.logger import setup_logger


class BaseExchangeListener(ABC):
    """
    Abstract base class for exchange WebSocket listeners.
    Provides common functionality for HTTP server, health checks, and message handling.
    Subclasses implement exchange-specific WebSocket connection logic.
    """

    def __init__(self):
        self.connection_status: Dict[str, Any] = {
            "connected": False,
            "exchange": self.get_exchange_name(),
            "last_message_time": None,
            "message_count": 0,
            "error_count": 0,
            "last_error": None,
            "start_time": time.time()
        }
        self.latest_market_data: Optional[Dict[str, Any]] = None
        self.logger: Optional[logging.Logger] = None

    @abstractmethod
    def get_exchange_name(self) -> str:
        """Return the exchange name (e.g., 'crypto', 'binance')."""
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, str]:
        """Return exchange-specific default configuration."""
        pass

    @abstractmethod
    async def connect_and_subscribe(self) -> None:
        """
        Implement exchange-specific WebSocket connection and subscription logic.
        This method should update self.connection_status and self.latest_market_data.
        """
        pass

    async def _send_json(self, ws, payload: Dict[str, Any]) -> None:
        """Send JSON payload to WebSocket."""
        await ws.send(json.dumps(payload))

    def _update_connection_status(self, connected: bool, error: Optional[str] = None) -> None:
        """Update connection status uniformly."""
        self.connection_status["connected"] = connected
        if error:
            self.connection_status["error_count"] += 1
            self.connection_status["last_error"] = error
        else:
            self.connection_status["last_error"] = None

    def _update_message_received(self) -> None:
        """Update status when message received."""
        self.connection_status["last_message_time"] = time.time()
        self.connection_status["message_count"] += 1


    async def handle_health(self, request: web.Request) -> web.Response:
        """Comprehensive health check endpoint."""
        current_time = time.time()
        uptime = current_time - self.connection_status["start_time"]

        # Check WebSocket health
        ws_healthy = self.connection_status["connected"]
        last_message_age = None
        if self.connection_status["last_message_time"]:
            last_message_age = current_time - self.connection_status["last_message_time"]
            ws_healthy = ws_healthy and last_message_age < 30

        # System metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            system_healthy = (
                cpu_percent < 90 and
                memory.percent < 90 and
                disk.percent < 90
            )
        except Exception:
            system_healthy = False
            cpu_percent = None
            memory = None
            disk = None

        overall_healthy = ws_healthy and system_healthy 

        health_data = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "exchange": self.get_exchange_name(),
            "timestamp": current_time,
            "uptime_seconds": round(uptime, 2),
            "websocket": {
                "connected": self.connection_status["connected"],
                "healthy": ws_healthy,
                "last_message_age_seconds": round(last_message_age, 2) if last_message_age else None,
                "message_count": self.connection_status["message_count"],
                "error_count": self.connection_status["error_count"],
                "last_error": self.connection_status["last_error"]
            },
            "system": {
                "healthy": system_healthy,
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2) if memory else None,
                    "available_gb": round(memory.available / (1024**3), 2) if memory else None,
                    "percent": memory.percent if memory else None
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2) if disk else None,
                    "free_gb": round(disk.free / (1024**3), 2) if disk else None,
                    "percent": disk.percent if disk else None
                }
            },
            "configuration": self.get_default_config()
        }

        status_code = 200 if overall_healthy else 503
        return web.json_response(health_data, status=status_code)

    async def handle_market_data(self, request: web.Request) -> web.Response:
        """Get the latest market data from the WebSocket stream."""
        if self.latest_market_data is None:
            return web.json_response(
                {"error": "No market data available yet"},
                status=503
            )

        # Check if data is recent (within last 60 seconds)
        data_age = time.time() - self.latest_market_data["received_at"]
        if data_age > 60:
            return web.json_response(
                {
                    "error": "Market data is stale",
                    "data_age_seconds": round(data_age, 2),
                    "last_data": self.latest_market_data
                },
                status=503
            )

        return web.json_response(self.latest_market_data)

    def create_app(self) -> web.Application:
        """Create aiohttp application with routes."""
        app = web.Application()
        app.router.add_get("/health", self.handle_health)
        app.router.add_get("/market", self.handle_market_data)
        return app

    async def run_server_and_ws(self) -> None:
        """Run HTTP server and WebSocket connection."""
        config = self.get_default_config()
        
        app = self.create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        
        # Get server configuration from the listener's config
        server_config = config.get("server", {})
        host = server_config.get("host", "0.0.0.0")
        port = server_config.get("port", 8000)
        site = web.TCPSite(runner, host=host, port=port)
        await site.start()
        
        if self.logger:
            self.logger.info(f"HTTP server started on http://{host}:{port}")
            self.logger.info(f"Exchange: {self.get_exchange_name()}")
        else:
            print(f"HTTP server started on http://{host}:{port}")
            print(f"Exchange: {self.get_exchange_name()}")

        ws_task = asyncio.create_task(self.connect_and_subscribe())
        try:
            await ws_task
        except asyncio.CancelledError:
            if self.logger:
                self.logger.info("WebSocket task cancelled")
        finally:
            await runner.cleanup()

    def _install_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        """Install signal handlers for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, loop.stop)
            except NotImplementedError:
                pass

    def main(self) -> None:
        """Main entry point for the listener application."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._install_signal_handlers(loop)
        try:
            loop.run_until_complete(self.run_server_and_ws())
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("Interrupted, shutting down...")
            else:
                print("Interrupted, shutting down...")
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            if self.logger:
                self.logger.info("Shutdown complete")
        sys.exit(0)

