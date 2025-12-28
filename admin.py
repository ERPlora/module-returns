"""
Tables Module Admin Configuration
"""

from django.contrib import admin
from .models import TablesConfig, Area, Table


@admin.register(TablesConfig)
class TablesConfigAdmin(admin.ModelAdmin):
    """Admin for TablesConfig singleton."""
    list_display = ['__str__', 'default_table_capacity', 'show_table_timer', 'updated_at']

    def has_add_permission(self, request):
        # Only allow one instance
        return not TablesConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    """Admin for Area model."""
    list_display = ['name', 'color', 'order', 'is_active', 'table_count', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']

    def table_count(self, obj):
        return obj.tables.count()
    table_count.short_description = 'Tables'


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """Admin for Table model."""
    list_display = ['number', 'name', 'area', 'capacity', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'area', 'is_active']
    search_fields = ['number', 'name', 'waiter']
    ordering = ['area__order', 'number']
    raw_id_fields = []

    fieldsets = (
        (None, {
            'fields': ('number', 'name', 'area')
        }),
        ('Capacity', {
            'fields': ('capacity', 'min_capacity')
        }),
        ('Status', {
            'fields': ('status', 'is_active')
        }),
        ('Current Session', {
            'fields': ('current_sale_id', 'opened_at', 'guests', 'waiter'),
            'classes': ('collapse',)
        }),
        ('Visual Settings', {
            'fields': ('position_x', 'position_y', 'shape'),
            'classes': ('collapse',)
        }),
    )
