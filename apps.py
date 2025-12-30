from django.apps import AppConfig


class ReturnsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'returns'
    verbose_name = 'Returns & Refunds'

    def ready(self):
        """
        Register extension points for the Returns module.

        This module EMITS signals:
        - sale_refunded: When a sale is refunded (partial or full)
        - stock_changed: When returned items are restocked

        This module provides HOOKS:
        - returns.before_refund: Validate before processing refund
        - returns.after_refund: Actions after refund completes
        """
        pass  # Signals are emitted when refunds are processed
