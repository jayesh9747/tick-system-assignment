from django.apps import AppConfig


class TickConsumerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tick_consumer'
    verbose_name = 'Tick Consumer'
