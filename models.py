"""
Tables Module Models

Provides table and floor management for hospitality businesses.
Integrates with the sales module to link sales to specific tables.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal


class TablesConfig(models.Model):
    """
    Singleton configuration for the tables module.

    Stores global settings for table management.
    """
    # Display settings
    show_table_timer = models.BooleanField(
        default=True,
        verbose_name=_("Show Table Timer"),
        help_text=_("Show elapsed time since table was occupied")
    )
    show_table_total = models.BooleanField(
        default=True,
        verbose_name=_("Show Table Total"),
        help_text=_("Show current sale total on table card")
    )

    # Default values
    default_table_capacity = models.PositiveIntegerField(
        default=4,
        verbose_name=_("Default Table Capacity"),
        help_text=_("Default number of seats when creating a new table")
    )

    # Behavior
    auto_close_on_payment = models.BooleanField(
        default=True,
        verbose_name=_("Auto Close on Payment"),
        help_text=_("Automatically close table when sale is completed")
    )
    require_table_for_order = models.BooleanField(
        default=False,
        verbose_name=_("Require Table for Orders"),
        help_text=_("Require a table to be selected before creating a sale")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'tables'
        db_table = 'tables_config'
        verbose_name = _("Tables Configuration")
        verbose_name_plural = _("Tables Configuration")

    def __str__(self):
        return "Tables Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton config instance."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class Area(models.Model):
    """
    Represents a section or zone in the establishment.

    Examples: Main Floor, Terrace, VIP Room, Bar Counter
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
        help_text=_("Area name (e.g., 'Main Floor', 'Terrace')")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    color = models.CharField(
        max_length=7,
        default="#3B82F6",
        verbose_name=_("Color"),
        help_text=_("Color code for visual identification (hex)")
    )
    icon = models.CharField(
        max_length=50,
        default="grid-outline",
        verbose_name=_("Icon"),
        help_text=_("Ionicon name for the area")
    )

    # Ordering and status
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Display Order")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Inactive areas are hidden from the floor view")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'tables'
        db_table = 'tables_area'
        verbose_name = _("Area")
        verbose_name_plural = _("Areas")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @property
    def table_count(self):
        """Number of tables in this area."""
        return self.tables.count()

    @property
    def occupied_count(self):
        """Number of occupied tables in this area."""
        return self.tables.filter(status=Table.STATUS_OCCUPIED).count()

    @property
    def available_count(self):
        """Number of available tables in this area."""
        return self.tables.filter(status=Table.STATUS_AVAILABLE).count()


class Table(models.Model):
    """
    Represents a physical table in the establishment.

    Each table can be linked to an active sale from the sales module.
    """
    # Status choices
    STATUS_AVAILABLE = 'available'
    STATUS_OCCUPIED = 'occupied'
    STATUS_RESERVED = 'reserved'
    STATUS_BLOCKED = 'blocked'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, _('Available')),
        (STATUS_OCCUPIED, _('Occupied')),
        (STATUS_RESERVED, _('Reserved')),
        (STATUS_BLOCKED, _('Blocked')),
    ]

    # Basic info
    number = models.CharField(
        max_length=20,
        verbose_name=_("Table Number"),
        help_text=_("Table identifier (e.g., '1', 'A1', 'VIP-1')")
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Name"),
        help_text=_("Optional descriptive name (e.g., 'Window Table')")
    )

    # Location
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tables',
        verbose_name=_("Area")
    )

    # Capacity
    capacity = models.PositiveIntegerField(
        default=4,
        verbose_name=_("Capacity"),
        help_text=_("Maximum number of guests")
    )
    min_capacity = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Minimum Capacity"),
        help_text=_("Minimum number of guests for this table")
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_AVAILABLE,
        verbose_name=_("Status")
    )

    # Current sale (FK to sales module)
    # Using integer ID to avoid circular import issues
    current_sale_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Current Sale ID"),
        help_text=_("ID of the active sale at this table")
    )

    # Session tracking
    opened_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Opened At"),
        help_text=_("When the table was opened/occupied")
    )
    guests = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Current Guests"),
        help_text=_("Number of guests currently seated")
    )
    waiter = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Waiter/Server"),
        help_text=_("Name of the assigned waiter")
    )

    # Visual settings
    position_x = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Position X"),
        help_text=_("X coordinate for floor plan positioning")
    )
    position_y = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Position Y"),
        help_text=_("Y coordinate for floor plan positioning")
    )
    shape = models.CharField(
        max_length=20,
        default='square',
        verbose_name=_("Shape"),
        help_text=_("Table shape for visual display")
    )

    # Flags
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'tables'
        db_table = 'tables_table'
        verbose_name = _("Table")
        verbose_name_plural = _("Tables")
        ordering = ['area__order', 'number']
        unique_together = [['area', 'number']]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['area', 'status']),
            models.Index(fields=['current_sale_id']),
        ]

    def __str__(self):
        if self.area:
            return f"{self.area.name} - {_('Table')} {self.number}"
        return f"{_('Table')} {self.number}"

    @property
    def is_available(self):
        """Check if table is available."""
        return self.status == self.STATUS_AVAILABLE

    @property
    def is_occupied(self):
        """Check if table is occupied."""
        return self.status == self.STATUS_OCCUPIED

    @property
    def elapsed_time(self):
        """Get elapsed time since table was opened."""
        if not self.opened_at:
            return None
        delta = timezone.now() - self.opened_at
        return delta

    @property
    def elapsed_minutes(self):
        """Get elapsed time in minutes."""
        elapsed = self.elapsed_time
        if elapsed:
            return int(elapsed.total_seconds() / 60)
        return 0

    @property
    def elapsed_display(self):
        """Get formatted elapsed time (HH:MM)."""
        minutes = self.elapsed_minutes
        if minutes == 0:
            return "-"
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    @property
    def current_sale(self):
        """Get the current sale object from sales module."""
        if not self.current_sale_id:
            return None
        try:
            from sales.models import Sale
            return Sale.objects.get(pk=self.current_sale_id)
        except Exception:
            return None

    @property
    def current_total(self):
        """Get the current sale total."""
        sale = self.current_sale
        if sale:
            return sale.total
        return Decimal('0.00')

    def open_table(self, guests=None, waiter='', sale_id=None):
        """
        Open the table and optionally link to a sale.

        Args:
            guests: Number of guests
            waiter: Name of the waiter/server
            sale_id: ID of the sale to link (optional, can be set later)
        """
        self.status = self.STATUS_OCCUPIED
        self.opened_at = timezone.now()
        self.guests = guests or self.capacity
        self.waiter = waiter
        if sale_id:
            self.current_sale_id = sale_id
        self.save()
        return self

    def close_table(self):
        """Close the table and clear session data."""
        self.status = self.STATUS_AVAILABLE
        self.current_sale_id = None
        self.opened_at = None
        self.guests = 0
        self.waiter = ''
        self.save()
        return self

    def link_sale(self, sale_id):
        """Link a sale to this table."""
        self.current_sale_id = sale_id
        if self.status == self.STATUS_AVAILABLE:
            self.status = self.STATUS_OCCUPIED
            self.opened_at = timezone.now()
        self.save()
        return self

    def transfer_to(self, target_table):
        """
        Transfer the current sale to another table.

        Args:
            target_table: Table instance to transfer to
        """
        if not self.current_sale_id:
            raise ValueError(_("No active sale to transfer"))

        if target_table.status == self.STATUS_OCCUPIED:
            raise ValueError(_("Target table is already occupied"))

        # Transfer sale to target
        target_table.open_table(
            guests=self.guests,
            waiter=self.waiter,
            sale_id=self.current_sale_id
        )

        # Close this table
        self.close_table()

        return target_table

    def block(self, reason=''):
        """Block the table (e.g., for maintenance)."""
        self.status = self.STATUS_BLOCKED
        self.save()

    def unblock(self):
        """Unblock the table."""
        self.status = self.STATUS_AVAILABLE
        self.save()

    def reserve(self):
        """Mark the table as reserved."""
        if self.status != self.STATUS_AVAILABLE:
            raise ValueError(_("Table is not available"))
        self.status = self.STATUS_RESERVED
        self.save()

    def cancel_reservation(self):
        """Cancel the reservation."""
        if self.status == self.STATUS_RESERVED:
            self.status = self.STATUS_AVAILABLE
            self.save()
