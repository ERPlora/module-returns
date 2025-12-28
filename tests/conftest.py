"""
Pytest fixtures for tables module tests.
"""

import pytest
from tables.models import TablesConfig, Area, Table


@pytest.fixture
def tables_config(db):
    """Create a TablesConfig instance."""
    return TablesConfig.get_config()


@pytest.fixture
def area(db):
    """Create an Area instance."""
    return Area.objects.create(
        name="Main Floor",
        description="Main dining area",
        color="#3B82F6",
        icon="grid-outline",
        order=1,
        is_active=True
    )


@pytest.fixture
def area_terrace(db):
    """Create a terrace Area instance."""
    return Area.objects.create(
        name="Terrace",
        description="Outdoor seating",
        color="#10B981",
        icon="sunny-outline",
        order=2,
        is_active=True
    )


@pytest.fixture
def table(db, area):
    """Create a Table instance."""
    return Table.objects.create(
        number="1",
        name="Window Table",
        area=area,
        capacity=4,
        min_capacity=2,
        status=Table.STATUS_AVAILABLE,
        is_active=True
    )


@pytest.fixture
def occupied_table(db, area):
    """Create an occupied Table instance."""
    table = Table.objects.create(
        number="2",
        area=area,
        capacity=6,
        is_active=True
    )
    table.open_table(guests=4, waiter="John")
    return table


@pytest.fixture
def multiple_tables(db, area, area_terrace):
    """Create multiple tables across areas."""
    tables = []

    # Main floor tables
    for i in range(1, 6):
        tables.append(Table.objects.create(
            number=str(i),
            area=area,
            capacity=4,
            is_active=True
        ))

    # Terrace tables
    for i in range(1, 4):
        tables.append(Table.objects.create(
            number=f"T{i}",
            area=area_terrace,
            capacity=2,
            is_active=True
        ))

    return tables
