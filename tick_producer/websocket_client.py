import websocket
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Callable
import time
import threading

logger = logging.getLogger('tick_producer')


class BinanceWebSocketClient:
    """
    Binance WebSocket client with auto-reconnect and error handling.
    """

    def __init__(self, symbols: List[str], on_tick_callback: Callable, ws_url: str):
        """
        Initialize WebSocket client.

        Args:
            symbols: List of trading symbols (e.g., ['btcusdt', 'ethusdt'])
            on_tick_callback: Callback function to handle incoming ticks
            ws_url: Binance WebSocket URL
        """
        self.symbols = [s.lower() for s in symbols]
        self.on_tick_callback = on_tick_callback
        self.ws_url = ws_url
        self.ws = None
        self.is_running = False
        self.reconnect_delay = 5  # seconds
        self.max_reconnect_delay = 60  # seconds

    def _get_stream_url(self) -> str:
        """Construct stream URL for multiple symbols using combined streams endpoint"""
        streams = '/'.join([f"{symbol}@ticker" for symbol in self.symbols])
        # Single symbol: wss://.../ws/btcusdt@ticker
        # Multiple symbols: wss://.../stream?streams=btcusdt@ticker/ethusdt@ticker/...
        if len(self.symbols) == 1:
            return f"{self.ws_url}/{streams}"
        base = self.ws_url.rsplit('/ws', 1)[0]
        return f"{base}/stream?streams={streams}"

    def _on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)

            # Combined streams wrap payload: {"stream": "btcusdt@ticker", "data": {...}}
            if 'stream' in data and 'data' in data:
                data = data['data']

            # Binance ticker format
            if 'e' in data and data['e'] == '24hrTicker':
                tick_data = {
                    'symbol': data['s'],  # Trading symbol
                    'price': data['c'],    # Current price
                    'volume': data['v'],   # Volume
                    'timestamp': datetime.fromtimestamp(data['E'] / 1000, tz=timezone.utc)  # Event time
                }

                logger.debug(f"Received tick: {tick_data['symbol']} @ {tick_data['price']}")
                self.on_tick_callback(tick_data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    def _on_error(self, ws, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        logger.warning(f"WebSocket closed: {close_status_code} - {close_msg}")

        if self.is_running:
            logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            self._reconnect()

    def _on_open(self, ws):
        """Handle WebSocket open"""
        logger.info(f"WebSocket connected - Subscribed to {len(self.symbols)} symbols: {', '.join(self.symbols)}")
        self.reconnect_delay = 5  # Reset reconnect delay on successful connection

    def _reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        if self.is_running:
            try:
                self.connect()
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
                # Exponential backoff
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
                time.sleep(self.reconnect_delay)
                self._reconnect()

    def connect(self):
        """Establish WebSocket connection"""
        try:
            stream_url = self._get_stream_url()
            logger.info(f"Connecting to: {stream_url}")

            self.ws = websocket.WebSocketApp(
                stream_url,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close,
                on_open=self._on_open
            )

            self.is_running = True

            # Run forever with automatic reconnection
            self.ws.run_forever(
                ping_interval=30,
                ping_timeout=10
            )

        except Exception as e:
            logger.error(f"Connection failed: {e}", exc_info=True)
            raise

    def disconnect(self):
        """Close WebSocket connection"""
        logger.info("Disconnecting WebSocket...")
        self.is_running = False
        if self.ws:
            self.ws.close()
