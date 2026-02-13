from django.contrib import admin
from .models import Broker, Script, Ticks


@admin.register(Broker)
class BrokerAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'type', 'script_count', 'created_at']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'type']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('type', 'name')
        }),
        ('Configuration', {
            'fields': ('api_config',),
            'description': 'API configuration in JSON format. Leave empty {} for default settings.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def script_count(self, obj):
        return obj.scripts.count()
    script_count.short_description = 'Scripts'


@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'trading_symbol', 'broker', 'tick_count', 'created_at']
    list_filter = ['broker', 'created_at']
    search_fields = ['name', 'trading_symbol']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('broker', 'name', 'trading_symbol')
        }),
        ('Additional Data', {
            'fields': ('additional_data',),
            'description': 'Additional metadata in JSON format. Use {} for empty.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def tick_count(self, obj):
        return obj.ticks.count()
    tick_count.short_description = 'Ticks'


@admin.register(Ticks)
class TicksAdmin(admin.ModelAdmin):
    list_display = ['id', 'script', 'tick_value', 'volume', 'received_at_producer', 'created_at']
    list_filter = ['script', 'received_at_producer', 'created_at']
    search_fields = ['script__trading_symbol', 'script__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'received_at_producer'

    fieldsets = (
        ('Tick Information', {
            'fields': ('script', 'tick_value', 'volume', 'received_at_producer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Read-only for ticks (data should come from WebSocket)
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
