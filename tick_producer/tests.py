from django.test import TestCase
from tick_producer.websocket_client import BinanceWebSocketClient
from unittest.mock import Mock, patch


class BinanceWebSocketClientTest(TestCase):
    def test_initialization(self):
        callback = Mock()
        client = BinanceWebSocketClient(
            symbols=['BTCUSDT', 'ETHUSDT'],
            on_tick_callback=callback,
            ws_url='wss://test.binance.com:9443/ws'
        )
        self.assertEqual(client.symbols, ['btcusdt', 'ethusdt'])
        self.assertEqual(client.on_tick_callback, callback)

    def test_get_stream_url(self):
        callback = Mock()
        client = BinanceWebSocketClient(
            symbols=['BTCUSDT'],
            on_tick_callback=callback,
            ws_url='wss://test.binance.com:9443/ws'
        )
        url = client._get_stream_url()
        self.assertEqual(url, 'wss://test.binance.com:9443/ws/btcusdt@ticker')
