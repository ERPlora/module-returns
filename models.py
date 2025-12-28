"""
Returns & Refunds Module Models

Provides handling for product returns, exchanges, and refunds/store credits.
Integrates with sales and inventory modules.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal


class ReturnsConfig(models.Model):
    """
    Singleton configuration for the returns module.

    Stores global settings for return/refund processing.
    """
    # Return policies
    allow_returns = models.BooleanField(
        default=True,
        verbose_name=_("Allow Returns"),
        help_text=_("Enable product returns processing")
    )

    return_window_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Return Window (Days)"),
        help_text=_("Number of days after sale to allow returns")
    )

    allow_store_credit = models.BooleanField(
        default=True,
        verbose_name=_("Allow Store Credit"),
        help_text=_("Allow refunds as store credit instead of cash")
    )

    require_receipt = models.BooleanField(
        default=True,
        verbose_name=_("Require Receipt"),
        help_text=_("Require original receipt for returns")
    )

    # Refund method preferences
    auto_restore_stock = models.BooleanField(
        default=True,
        verbose_name=_("Auto Restore Stock"),
        help_text=_("Automatically restore inventory when return is processed")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'returns'
        db_table = 'returns_config'
        verbose_name = _("Returns Configuration")
        verbose_name_plural = _("Returns Configuration")

    def __str__(self):
        return "Returns Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class ReturnReason(models.Model):
    """
    Predefined reasons for product returns.

    Examples: Defective, Wrong Item, Changed Mind, Size Issue, etc.
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
        help_text=_("Display name (e.g., 'Defective', 'Wrong Item')")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description of this return reason")
    )

    restocks_inventory = models.BooleanField(
        default=True,
        verbose_name=_("Restocks Inventory"),
        help_text=_("Whether returning this reason restores stock")
    )

    requires_note = models.BooleanField(
        default=False,
        verbose_name=_("Requires Note"),
        help_text=_("Whether a note is required when using this reason")
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'returns'
        db_table = 'returns_reason'
        verbose_name = _("Return Reason")
        verbose_name_plural = _("Return Reasons")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Return(models.Model):
    """
    Represents a product return/refund transaction.

    Links to an original Sale and tracks returned items, refund method, and status.
    """
    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_PROCESSED = 'processed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_PROCESSED, _('Processed')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    # Refund method choices
    REFUND_CASH = 'cash'
    REFUND_STORE_CREDIT = 'store_credit'
    REFUND_ORIGINAL_PAYMENT = 'original_payment'

    REFUND_METHODS = [
        (REFUND_CASH, _('Cash')),
        (REFUND_STORE_CREDIT, _('Store Credit')),
        (REFUND_ORIGINAL_PAYMENT, _('Original Payment Method')),
    ]

    # Reference to original sale (UUID to match sales module)
    sale_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Original Sale ID"),
        help_text=_("UUID of the original sale")
    )

    # Return identification
    return_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        verbose_name=_("Return Number"),
        help_text=_("Unique identifier for this return")
    )

    # Status and processing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name=_("Status")
    )

    # Return reason
    reason = models.ForeignKey(
        ReturnReason,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Return Reason")
    )

    # Additional notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about this return")
    )

    # Financial
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Subtotal"),
        help_text=_("Subtotal of returned items")
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Tax Amount"),
        help_text=_("Tax on returned items")
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Total Amount"),
        help_text=_("Total amount to be refunded")
    )

    # Refund method
    refund_method = models.CharField(
        max_length=20,
        choices=REFUND_METHODS,
        default=REFUND_CASH,
        verbose_name=_("Refund Method")
    )

    # Processing info
    processed_by = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Processed By"),
        help_text=_("User who processed the return")
    )

    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Processed At")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'returns'
        db_table = 'returns_return'
        verbose_name = _("Return")
        verbose_name_plural = _("Returns")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['return_number']),
            models.Index(fields=['status']),
            models.Index(fields=['sale_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Return {self.return_number}"

    def save(self, *args, **kwargs):
        if not self.return_number:
            # Generate return number
            last = Return.objects.order_by('-id').first()
            next_id = (last.id + 1) if last else 1
            self.return_number = f"RET-{next_id:06d}"
        super().save(*args, **kwargs)

    def approve(self):
        """Approve the return."""
        self.status = self.STATUS_APPROVED
        self.save()

    def process(self, processed_by=''):
        """Process the return and issue refund."""
        self.status = self.STATUS_PROCESSED
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save()

    def cancel(self):
        """Cancel the return."""
        self.status = self.STATUS_CANCELLED
        self.save()


class ReturnLine(models.Model):
    """
    Individual line item in a return transaction.

    Represents one product being returned from the original sale.
    """
    return_order = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name=_("Return")
    )

    # Product reference (UUID to match inventory module)
    product_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_("Product ID"),
        help_text=_("UUID of the returned product")
    )

    # Product details (snapshot at return time)
    product_name = models.CharField(
        max_length=255,
        verbose_name=_("Product Name"),
        help_text=_("Name at time of return")
    )

    product_sku = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Product SKU")
    )

    # Quantity and pricing
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Quantity Returned"),
        help_text=_("Number of units being returned")
    )

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Unit Price"),
        help_text=_("Price per unit at time of original sale")
    )

    line_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Line Subtotal")
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('21.00'),
        verbose_name=_("Tax Rate %")
    )

    line_tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Line Tax Amount")
    )

    line_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Line Total")
    )

    # Return details
    CONDITION_CHOICES = [
        ('new', _('New/Unused')),
        ('like_new', _('Like New')),
        ('good', _('Good')),
        ('fair', _('Fair')),
        ('damaged', _('Damaged')),
    ]

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good',
        verbose_name=_("Condition")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'returns'
        db_table = 'returns_line'
        verbose_name = _("Return Line")
        verbose_name_plural = _("Return Lines")
        ordering = ['return_order', 'id']

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def calculate_totals(self):
        """Recalculate line totals based on quantity and prices."""
        self.line_subtotal = self.unit_price * self.quantity
        self.line_tax = (self.line_subtotal * self.tax_rate) / Decimal('100')
        self.line_total = self.line_subtotal + self.line_tax

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)


class StoreCredit(models.Model):
    """
    Store credit account for customers.

    Tracks store credit issued via returns or purchased.
    """
    # Credit identification
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Credit Code")
    )

    # Customer info (for lookup without customer module)
    customer_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Customer Name")
    )

    customer_email = models.EmailField(
        blank=True,
        verbose_name=_("Customer Email")
    )

    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Customer Phone")
    )

    # Balance
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Original Amount")
    )

    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name=_("Current Balance")
    )

    # Related return (if applicable)
    return_order = models.OneToOneField(
        Return,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='store_credit',
        verbose_name=_("Related Return")
    )

    # Expiration
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At")
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    # Notes
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'returns'
        db_table = 'returns_store_credit'
        verbose_name = _("Store Credit")
        verbose_name_plural = _("Store Credits")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['customer_name']),
        ]

    def __str__(self):
        return f"Credit {self.code} - {self.current_amount}"

    def add_credit(self, amount):
        """Add credit to the account."""
        self.current_amount += amount
        self.save()

    def deduct_credit(self, amount):
        """Deduct credit from the account."""
        if amount > self.current_amount:
            raise ValueError(_("Insufficient store credit"))
        self.current_amount -= amount
        self.save()

    def is_expired(self):
        """Check if credit has expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        """Check if credit is valid (active and not expired)."""
        return self.is_active and not self.is_expired() and self.current_amount > 0
