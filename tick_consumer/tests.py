from django.test import TestCase
from .models import Broker, Script, Ticks
from .tasks import get_broker, consume_tick
from datetime import datetime
from decimal import Decimal


class BrokerModelTest(TestCase):
    def test_create_broker(self):
        broker = Broker.objects.create(
            type='BINANCE',
            name='Binance Test',
            api_config={'key': 'value'}
        )
        self.assertEqual(broker.type, 'BINANCE')
        self.assertEqual(broker.name, 'Binance Test')
        self.assertEqual(str(broker), 'Binance Test (BINANCE)')


class ScriptModelTest(TestCase):
    def setUp(self):
        self.broker = Broker.objects.create(
            type='BINANCE',
            name='Binance Test'
        )

    def test_create_script(self):
        script = Script.objects.create(
            broker=self.broker,
            name='Bitcoin',
            trading_symbol='BTCUSDT'
        )
        self.assertEqual(script.name, 'Bitcoin')
        self.assertEqual(script.trading_symbol, 'BTCUSDT')
        self.assertEqual(str(script), 'Bitcoin - BTCUSDT')


class TicksModelTest(TestCase):
    def setUp(self):
        self.broker = Broker.objects.create(
            type='BINANCE',
            name='Binance Test'
        )
        self.script = Script.objects.create(
            broker=self.broker,
            name='Bitcoin',
            trading_symbol='BTCUSDT'
        )

    def test_create_tick(self):
        tick = Ticks.objects.create(
            script=self.script,
            tick_value=Decimal('50000.12345678'),
            volume=Decimal('100.5'),
            received_at_producer=datetime.now()
        )
        self.assertEqual(tick.script, self.script)
        self.assertEqual(tick.tick_value, Decimal('50000.12345678'))
