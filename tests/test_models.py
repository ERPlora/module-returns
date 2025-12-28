"""
Tests for tables module models.
"""

import pytest
from django.utils import timezone
from tables.models import TablesConfig, Area, Table


class TestTablesConfig:
    """Tests for TablesConfig model."""

    def test_get_config_creates_singleton(self, db):
        """Test that get_config creates a singleton instance."""
        config1 = TablesConfig.get_config()
        config2 = TablesConfig.get_config()

        assert config1.pk == 1
        assert config2.pk == 1
        assert TablesConfig.objects.count() == 1

    def test_config_default_values(self, tables_config):
        """Test default configuration values."""
        assert tables_config.show_table_timer is True
        assert tables_config.show_table_total is True
        assert tables_config.default_table_capacity == 4
        assert tables_config.auto_close_on_payment is True
        assert tables_config.require_table_for_order is False

    def test_config_str(self, tables_config):
        """Test string representation."""
        assert str(tables_config) == "Tables Configuration"


class TestArea:
    """Tests for Area model."""

    def test_area_creation(self, area):
        """Test area creation with all fields."""
        assert area.name == "Main Floor"
        assert area.description == "Main dining area"
        assert area.color == "#3B82F6"
        assert area.icon == "grid-outline"
        assert area.order == 1
        assert area.is_active is True

    def test_area_str(self, area):
        """Test string representation."""
        assert str(area) == "Main Floor"

    def test_area_table_count(self, area, table):
        """Test table_count property."""
        assert area.table_count == 1

    def test_area_occupied_count(self, area, table, occupied_table):
        """Test occupied_count property."""
        assert area.occupied_count == 1

    def test_area_available_count(self, area, table, occupied_table):
        """Test available_count property."""
        assert area.available_count == 1

    def test_area_ordering(self, area, area_terrace):
        """Test areas are ordered by order field."""
        areas = list(Area.objects.all())
        assert areas[0] == area
        assert areas[1] == area_terrace


class TestTable:
    """Tests for Table model."""

    def test_table_creation(self, table):
        """Test table creation with all fields."""
        assert table.number == "1"
        assert table.name == "Window Table"
        assert table.capacity == 4
        assert table.min_capacity == 2
        assert table.status == Table.STATUS_AVAILABLE
        assert table.is_active is True

    def test_table_str_with_area(self, table):
        """Test string representation with area."""
        assert "Main Floor" in str(table)
        assert "1" in str(table)

    def test_table_str_without_area(self, db):
        """Test string representation without area."""
        table = Table.objects.create(number="X1", capacity=2)
        assert "X1" in str(table)

    def test_is_available_property(self, table):
        """Test is_available property."""
        assert table.is_available is True
        table.status = Table.STATUS_OCCUPIED
        assert table.is_available is False

    def test_is_occupied_property(self, table, occupied_table):
        """Test is_occupied property."""
        assert table.is_occupied is False
        assert occupied_table.is_occupied is True

    def test_open_table(self, table):
        """Test opening a table."""
        table.open_table(guests=3, waiter="Alice")

        assert table.status == Table.STATUS_OCCUPIED
        assert table.guests == 3
        assert table.waiter == "Alice"
        assert table.opened_at is not None

    def test_open_table_with_sale(self, table):
        """Test opening a table with a sale ID."""
        table.open_table(guests=2, sale_id=123)

        assert table.current_sale_id == 123
        assert table.status == Table.STATUS_OCCUPIED

    def test_close_table(self, occupied_table):
        """Test closing a table."""
        occupied_table.close_table()

        assert occupied_table.status == Table.STATUS_AVAILABLE
        assert occupied_table.current_sale_id is None
        assert occupied_table.opened_at is None
        assert occupied_table.guests == 0
        assert occupied_table.waiter == ''

    def test_link_sale(self, table):
        """Test linking a sale to a table."""
        table.link_sale(456)

        assert table.current_sale_id == 456
        assert table.status == Table.STATUS_OCCUPIED

    def test_transfer_to(self, occupied_table, table):
        """Test transferring a sale to another table."""
        occupied_table.current_sale_id = 789
        occupied_table.save()

        target = occupied_table.transfer_to(table)

        assert target == table
        assert table.current_sale_id == 789
        assert table.status == Table.STATUS_OCCUPIED
        assert occupied_table.status == Table.STATUS_AVAILABLE
        assert occupied_table.current_sale_id is None

    def test_transfer_to_occupied_fails(self, occupied_table, db, area):
        """Test transfer to occupied table fails."""
        target = Table.objects.create(
            number="99",
            area=area,
            status=Table.STATUS_OCCUPIED
        )
        occupied_table.current_sale_id = 123
        occupied_table.save()

        with pytest.raises(ValueError):
            occupied_table.transfer_to(target)

    def test_transfer_without_sale_fails(self, table, db, area):
        """Test transfer without active sale fails."""
        target = Table.objects.create(number="99", area=area)

        with pytest.raises(ValueError):
            table.transfer_to(target)

    def test_block_table(self, table):
        """Test blocking a table."""
        table.block()

        assert table.status == Table.STATUS_BLOCKED

    def test_unblock_table(self, table):
        """Test unblocking a table."""
        table.block()
        table.unblock()

        assert table.status == Table.STATUS_AVAILABLE

    def test_reserve_table(self, table):
        """Test reserving a table."""
        table.reserve()

        assert table.status == Table.STATUS_RESERVED

    def test_reserve_occupied_fails(self, occupied_table):
        """Test reserving an occupied table fails."""
        with pytest.raises(ValueError):
            occupied_table.reserve()

    def test_cancel_reservation(self, table):
        """Test canceling a reservation."""
        table.reserve()
        table.cancel_reservation()

        assert table.status == Table.STATUS_AVAILABLE

    def test_elapsed_time(self, occupied_table):
        """Test elapsed time calculation."""
        assert occupied_table.elapsed_time is not None
        assert occupied_table.elapsed_minutes >= 0

    def test_elapsed_display(self, occupied_table):
        """Test elapsed time display format."""
        display = occupied_table.elapsed_display
        assert display is not None
        # Should be something like "0m" for newly opened table

    def test_elapsed_display_not_opened(self, table):
        """Test elapsed display for unopened table."""
        assert table.elapsed_display == "-"

    def test_unique_together_constraint(self, table, area):
        """Test that table number is unique within an area."""
        with pytest.raises(Exception):
            Table.objects.create(
                number="1",  # Same number as existing table
                area=area,
                capacity=2
            )

    def test_tables_in_different_areas_same_number(self, area, area_terrace):
        """Test same table number can exist in different areas."""
        table1 = Table.objects.create(number="1", area=area)
        table2 = Table.objects.create(number="1", area=area_terrace)

        assert table1.number == table2.number
        assert table1.area != table2.area
