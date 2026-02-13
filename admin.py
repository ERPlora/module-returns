from django.contrib import admin
from .models import ReturnsSettings, ReturnReason, Return, ReturnItem, StoreCredit


@admin.register(ReturnsSettings)
class ReturnsSettingsAdmin(admin.ModelAdmin):
    list_display = ['allow_returns', 'return_window_days', 'allow_store_credit']


@admin.register(ReturnReason)
class ReturnReasonAdmin(admin.ModelAdmin):
    list_display = ['name', 'restocks_inventory', 'requires_note', 'is_active']
    list_filter = ['is_active']


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['status', 'refund_method', 'created_at']
    list_filter = ['status', 'refund_method']
    inlines = [ReturnItemInline]


@admin.register(ReturnItem)
class ReturnItemAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'quantity', 'unit_price']


@admin.register(StoreCredit)
class StoreCreditAdmin(admin.ModelAdmin):
    list_display = ['code', 'customer_name', 'original_amount', 'current_amount', 'is_active']
    list_filter = ['is_active']
    search_fields = ['code', 'customer_name']
