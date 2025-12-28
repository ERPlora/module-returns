"""
Returns & Refunds Module Admin Configuration
"""

from django.contrib import admin
from .models import ReturnsConfig, ReturnReason, Return, ReturnLine, StoreCredit


@admin.register(ReturnsConfig)
class ReturnsConfigAdmin(admin.ModelAdmin):
    """Admin for ReturnsConfig singleton."""
    list_display = ['__str__', 'allow_returns', 'return_window_days', 'allow_store_credit', 'updated_at']

    def has_add_permission(self, request):
        # Only allow one instance
        return not ReturnsConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReturnReason)
class ReturnReasonAdmin(admin.ModelAdmin):
    """Admin for ReturnReason model."""
    list_display = ['name', 'restocks_inventory', 'requires_note', 'order', 'is_active']
    list_filter = ['is_active', 'restocks_inventory', 'requires_note']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


class ReturnLineInline(admin.TabularInline):
    """Inline for ReturnLine in Return admin."""
    model = ReturnLine
    extra = 0
    readonly_fields = ['line_subtotal', 'line_tax', 'line_total']
    fields = ['product_name', 'product_sku', 'quantity', 'unit_price', 'condition', 'line_total']


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    """Admin for Return model."""
    list_display = ['return_number', 'status', 'reason', 'total_amount', 'refund_method', 'created_at']
    list_filter = ['status', 'refund_method', 'reason']
    search_fields = ['return_number', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['return_number', 'subtotal', 'tax_amount', 'total_amount', 'processed_at', 'created_at', 'updated_at']
    inlines = [ReturnLineInline]

    fieldsets = (
        (None, {
            'fields': ('return_number', 'sale_id', 'status')
        }),
        ('Return Details', {
            'fields': ('reason', 'notes')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax_amount', 'total_amount', 'refund_method')
        }),
        ('Processing', {
            'fields': ('processed_by', 'processed_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StoreCredit)
class StoreCreditAdmin(admin.ModelAdmin):
    """Admin for StoreCredit model."""
    list_display = ['code', 'customer_name', 'original_amount', 'current_amount', 'is_active', 'expires_at']
    list_filter = ['is_active']
    search_fields = ['code', 'customer_name', 'customer_email', 'customer_phone']
    ordering = ['-created_at']
    readonly_fields = ['code', 'original_amount', 'return_order', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('code', 'return_order')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Balance', {
            'fields': ('original_amount', 'current_amount')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
