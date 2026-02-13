from django.core.management.base import BaseCommand, CommandError
from tick_consumer.tasks import get_broker, consume_tick
from tick_producer.websocket_client import BinanceWebSocketClient
from django.conf import settings
import logging
import signal
import sys
from datetime import datetime

logger = logging.getLogger('tick_producer')


class Command(BaseCommand):
    help = 'Run tick producer for specified broker - connects to WebSocket and forwards ticks to Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--broker_id',
            type=int,
            required=True,
            help='Broker ID to fetch configuration from'
        )

    def handle(self, *args, **options):
        broker_id = options['broker_id']

        self.stdout.write(f"Starting tick producer for broker ID: {broker_id}")

        try:
            # Fetch broker configuration synchronously
            self.stdout.write("Fetching broker configuration...")
            broker_data = get_broker(broker_id)

            if not broker_data:
                raise CommandError(f"Broker {broker_id} not found")

            self.stdout.write(self.style.SUCCESS(
                f"Loaded broker: {broker_data['name']} ({broker_data['type']})"
            ))

            # Validate broker type
            if broker_data['type'] != 'BINANCE':
                raise CommandError(f"Unsupported broker type: {broker_data['type']}")

            # Extract scripts
            scripts = broker_data.get('scripts', [])
            if not scripts:
                raise CommandError(f"No scripts configured for broker {broker_id}")

            # Create symbol -> script_id mapping
            symbol_map = {
                script['trading_symbol']: script['id']
                for script in scripts
            }

            symbols = list(symbol_map.keys())
            self.stdout.write(f"Monitoring {len(symbols)} symbols: {', '.join(symbols)}")

            # Tick callback handler
            def on_tick(tick_data):
                """Process incoming tick and send to Celery"""
                try:
                    symbol = tick_data['symbol']
                    script_id = symbol_map.get(symbol)

                    if not script_id:
                        logger.warning(f"Received tick for unmapped symbol: {symbol}")
                        return

                    tick_payload = {
                        'script_id': script_id,
                        'tick_value': str(tick_data['price']),
                        'volume': str(tick_data['volume']) if tick_data.get('volume') else None,
                        'received_at_producer': tick_data['timestamp'].isoformat()
                    }

                    # Send to Celery asynchronously
                    consume_tick.delay(tick_payload)

                    logger.info(f"Forwarded tick: {symbol} @ {tick_data['price']}")

                except Exception as e:
                    logger.error(f"Error handling tick: {e}", exc_info=True)

            # Get WebSocket URL from settings
            ws_url = getattr(settings, 'BINANCE_WS_URL',
                           'wss://stream.binance.com:9443/ws')

            # Initialize WebSocket client
            ws_client = BinanceWebSocketClient(
                symbols=symbols,
                on_tick_callback=on_tick,
                ws_url=ws_url
            )

            # Graceful shutdown handler
            def signal_handler(sig, frame):
                self.stdout.write("\nShutting down tick producer...")
                ws_client.disconnect()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            # Start WebSocket connection (blocking)
            self.stdout.write(self.style.SUCCESS("WebSocket client starting..."))
            ws_client.connect()

        except Exception as e:
            raise CommandError(f"Failed to start tick producer: {e}")
