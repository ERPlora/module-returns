"""
Returns & Refunds Module Models

Merges old (ReturnReason, StoreCredit, config policies) with new
(HubBaseModel, real FKs, approve/reject/complete workflow, ReturnItem).
"""

import secrets
from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from apps.core.models import HubBaseModel


# =============================================================================
# Settings (per-hub, replaces old singleton)
# =============================================================================

class ReturnsSettings(HubBaseModel):
    """Per-hub settings for the returns module."""

    allow_returns = models.BooleanField(
        _('Allow Returns'),
        default=True,
    )
    return_window_days = models.PositiveIntegerField(
        _('Return Window (Days)'),
        default=30,
        help_text=_('Number of days after sale to allow returns'),
    )
    allow_store_credit = models.BooleanField(
        _('Allow Store Credit'),
        default=True,
    )
    require_receipt = models.BooleanField(
        _('Require Receipt'),
        default=True,
    )
    auto_restore_stock = models.BooleanField(
        _('Auto Restore Stock'),
        default=True,
        help_text=_('Automatically restore inventory when return is processed'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'returns_settings'
        verbose_name = _('Returns Settings')
        verbose_name_plural = _('Returns Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f'Returns Settings (Hub {self.hub_id})'

    @classmethod
    def get_settings(cls, hub_id):
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


# =============================================================================
# Return Reason (from old — predefined reasons)
# =============================================================================

class ReturnReason(HubBaseModel):
    """Predefined reasons for product returns."""

    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True, default='')
    restocks_inventory = models.BooleanField(
        _('Restocks Inventory'),
        default=True,
        help_text=_('Whether returning with this reason restores stock'),
    )
    requires_note = models.BooleanField(
        _('Requires Note'),
        default=False,
    )
    sort_order = models.PositiveIntegerField(_('Sort Order'), default=0)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'returns_reason'
        verbose_name = _('Return Reason')
        verbose_name_plural = _('Return Reasons')
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


# =============================================================================
# Return (merged old+new)
# =============================================================================

class Return(HubBaseModel):
    """A product return linked to an original sale."""

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    REFUND_METHOD_CHOICES = [
        ('original', _('Original Payment Method')),
        ('cash', _('Cash')),
        ('store_credit', _('Store Credit')),
    ]

    number = models.CharField(
        _('Return Number'),
        max_length=50,
        blank=True,
        default='',
    )

    # Real FKs (from new)
    original_sale = models.ForeignKey(
        'sales.Sale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name=_('Original Sale'),
    )
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name=_('Customer'),
    )
    employee = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_returns',
        verbose_name=_('Processed By'),
    )

    # Return reason (from old — FK to ReturnReason model)
    reason = models.ForeignKey(
        ReturnReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name=_('Return Reason'),
    )
    reason_notes = models.TextField(_('Reason Notes'), blank=True, default='')

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    # Financial
    subtotal = models.DecimalField(
        _('Subtotal'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    tax_amount = models.DecimalField(
        _('Tax Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    total_refund = models.DecimalField(
        _('Total Refund'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    refund_method = models.CharField(
        _('Refund Method'),
        max_length=20,
        choices=REFUND_METHOD_CHOICES,
        default='original',
    )

    notes = models.TextField(_('Notes'), blank=True, default='')

    # Workflow timestamps (from new)
    approved_by = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_returns',
        verbose_name=_('Approved By'),
    )
    approved_at = models.DateTimeField(_('Approved At'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Completed At'), null=True, blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'returns_return'
        verbose_name = _('Return')
        verbose_name_plural = _('Returns')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return self.number or f'RET-{str(self.id)[:8]}'

    def save(self, *args, **kwargs):
        if not self.number:
            self.number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        today = timezone.now()
        prefix = f'RET-{today.strftime("%Y%m%d")}'
        last = Return.all_objects.filter(
            hub_id=self.hub_id,
            number__startswith=prefix,
        ).order_by('-number').first()

        if last and last.number:
            try:
                seq = int(last.number.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f'{prefix}-{seq:04d}'

    @property
    def item_count(self):
        return self.items.filter(is_deleted=False).count()

    @property
    def total_quantity(self):
        return self.items.filter(is_deleted=False).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    def recalculate_total(self):
        """Recalculate totals from items."""
        items = self.items.filter(is_deleted=False)
        self.subtotal = items.aggregate(
            total=models.Sum('refund_amount')
        )['total'] or Decimal('0.00')
        self.total_refund = self.subtotal
        self.save(update_fields=['subtotal', 'total_refund', 'updated_at'])

    # Workflow methods (from new)
    def approve(self, approved_by):
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

    def reject(self):
        self.status = 'rejected'
        self.save(update_fields=['status', 'updated_at'])

    def complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at', 'updated_at'])

    def cancel(self):
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])


# =============================================================================
# ReturnItem (from new, replaces old ReturnLine)
# =============================================================================

class ReturnItem(HubBaseModel):
    """Individual item within a return."""

    CONDITION_CHOICES = [
        ('new', _('New / Unopened')),
        ('good', _('Good Condition')),
        ('damaged', _('Damaged')),
        ('defective', _('Defective')),
    ]

    return_obj = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Return'),
    )
    sale_item = models.ForeignKey(
        'sales.SaleItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_items',
        verbose_name=_('Original Sale Item'),
    )
    product = models.ForeignKey(
        'inventory.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_items',
        verbose_name=_('Product'),
    )

    # Snapshot fields
    product_name = models.CharField(
        _('Product Name'),
        max_length=255,
        blank=True,
        default='',
        help_text=_('Snapshot of product name at time of return'),
    )
    product_sku = models.CharField(
        _('Product SKU'),
        max_length=100,
        blank=True,
        default='',
    )

    quantity = models.PositiveIntegerField(
        _('Quantity'),
        default=1,
        validators=[MinValueValidator(1)],
    )
    unit_price = models.DecimalField(
        _('Unit Price'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    tax_rate = models.DecimalField(
        _('Tax Rate %'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
    )
    refund_amount = models.DecimalField(
        _('Refund Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    condition = models.CharField(
        _('Condition'),
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good',
    )
    restock = models.BooleanField(
        _('Restock Item'),
        default=True,
        help_text=_('Return item to inventory stock'),
    )
    notes = models.TextField(_('Notes'), blank=True, default='')

    class Meta(HubBaseModel.Meta):
        db_table = 'returns_return_item'
        verbose_name = _('Return Item')
        verbose_name_plural = _('Return Items')
        ordering = ['created_at']

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'

    def save(self, *args, **kwargs):
        if not self.product_name and self.product:
            self.product_name = self.product.name
        if self.refund_amount == Decimal('0.00') and self.unit_price > 0:
            self.refund_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)


# =============================================================================
# StoreCredit (from old — kept, with real FK to Customer)
# =============================================================================

class StoreCredit(HubBaseModel):
    """Store credit issued via returns or manually."""

    code = models.CharField(
        _('Credit Code'),
        max_length=20,
        unique=True,
    )

    # Real FK to Customer (replacing old string fields)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='store_credits',
        verbose_name=_('Customer'),
    )

    # Fallback customer info (from old, for when customer module not available)
    customer_name = models.CharField(
        _('Customer Name'),
        max_length=200,
        blank=True,
        default='',
    )
    customer_email = models.EmailField(
        _('Customer Email'),
        blank=True,
        default='',
    )
    customer_phone = models.CharField(
        _('Customer Phone'),
        max_length=20,
        blank=True,
        default='',
    )

    # Balance
    original_amount = models.DecimalField(
        _('Original Amount'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )
    current_amount = models.DecimalField(
        _('Current Balance'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
    )

    # Related return
    return_obj = models.OneToOneField(
        Return,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='store_credit',
        verbose_name=_('Related Return'),
    )

    expires_at = models.DateTimeField(_('Expires At'), null=True, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)
    notes = models.TextField(_('Notes'), blank=True, default='')

    class Meta(HubBaseModel.Meta):
        db_table = 'returns_store_credit'
        verbose_name = _('Store Credit')
        verbose_name_plural = _('Store Credits')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'Credit {self.code} - {self.current_amount}'

    @classmethod
    def generate_code(cls):
        return f'SC-{secrets.token_hex(4).upper()}'

    def add_credit(self, amount):
        self.current_amount += amount
        self.save(update_fields=['current_amount', 'updated_at'])

    def deduct_credit(self, amount):
        if amount > self.current_amount:
            raise ValueError(_('Insufficient store credit'))
        self.current_amount -= amount
        self.save(update_fields=['current_amount', 'updated_at'])

    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired() and self.current_amount > 0
