from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Broker(models.Model):
    """Broker configuration model"""
    BROKER_TYPES = [
        ('BINANCE', 'Binance'),
        ('COINBASE', 'Coinbase'),
        ('KRAKEN', 'Kraken'),
    ]

    type = models.CharField(max_length=50, choices=BROKER_TYPES)
    name = models.CharField(max_length=255)
    api_config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'brokers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.type})"


class Script(models.Model):
    """Trading symbol/script model"""
    broker = models.ForeignKey(
        Broker,
        on_delete=models.CASCADE,
        related_name='scripts'
    )
    name = models.CharField(max_length=255)  # e.g., "Bitcoin", "Ethereum"
    trading_symbol = models.CharField(max_length=50)  # e.g., "BTCUSDT"
    additional_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scripts'
        ordering = ['name']
        unique_together = [['broker', 'trading_symbol']]

    def __str__(self):
        return f"{self.name} - {self.trading_symbol}"


class Ticks(models.Model):
    """Market tick data model"""
    script = models.ForeignKey(
        Script,
        on_delete=models.CASCADE,
        related_name='ticks'
    )
    tick_value = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))]
    )
    volume = models.DecimalField(
        max_digits=30,
        decimal_places=8,
        null=True,
        blank=True
    )
    received_at_producer = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ticks'
        ordering = ['-received_at_producer']
        indexes = [
            models.Index(fields=['script', '-received_at_producer']),
            models.Index(fields=['-received_at_producer']),
        ]

    def __str__(self):
        return f"{self.script.trading_symbol} @ {self.tick_value}"
