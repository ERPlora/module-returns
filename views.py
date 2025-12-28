"""
Tables Module Views

Provides floor view, table management, and integration with sales module.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.urls import reverse

from apps.modules_runtime.decorators import htmx_view
from .models import TablesConfig, Area, Table


# =============================================================================
# FLOOR VIEW (Main Dashboard)
# =============================================================================

@htmx_view(
    page_template='tables/pages/floor.html',
    partial_template='tables/partials/floor_content.html'
)
def floor_view(request):
    """
    Main floor view showing all tables organized by area.

    Query params:
        - area: Filter by area ID
        - status: Filter by status (available, occupied, reserved, blocked)
    """
    config = TablesConfig.get_config()

    # Get filter parameters
    area_filter = request.GET.get('area')
    status_filter = request.GET.get('status')

    # Build queryset
    tables = Table.objects.filter(is_active=True).select_related('area')

    if area_filter:
        tables = tables.filter(area_id=area_filter)
    if status_filter:
        tables = tables.filter(status=status_filter)

    # Get areas for filter
    areas = Area.objects.filter(is_active=True).order_by('order', 'name')

    # Calculate stats
    total_tables = Table.objects.filter(is_active=True).count()
    occupied_tables = Table.objects.filter(is_active=True, status=Table.STATUS_OCCUPIED).count()
    available_tables = Table.objects.filter(is_active=True, status=Table.STATUS_AVAILABLE).count()
    reserved_tables = Table.objects.filter(is_active=True, status=Table.STATUS_RESERVED).count()

    context = {
        'config': config,
        'tables': tables,
        'areas': areas,
        'area_filter': area_filter,
        'status_filter': status_filter,
        'stats': {
            'total': total_tables,
            'occupied': occupied_tables,
            'available': available_tables,
            'reserved': reserved_tables,
        }
    }

    return context


# =============================================================================
# AREA CRUD
# =============================================================================

@htmx_view(
    page_template='tables/pages/areas.html',
    partial_template='tables/partials/area_list.html'
)
def area_list(request):
    """List all areas."""
    areas = Area.objects.annotate(
        table_count=Count('tables'),
        occupied_count=Count('tables', filter=Q(tables__status=Table.STATUS_OCCUPIED))
    ).order_by('order', 'name')

    return {'areas': areas}


@htmx_view(
    page_template='tables/pages/area_form.html',
    partial_template='tables/partials/area_form.html'
)
def area_create(request):
    """Create a new area."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        color = request.POST.get('color', '#3B82F6')
        icon = request.POST.get('icon', 'grid-outline')
        order = int(request.POST.get('order', 0))

        if not name:
            messages.error(request, _("Name is required"))
            return {
                'form_data': request.POST,
                'is_edit': False,
            }

        area = Area.objects.create(
            name=name,
            description=description,
            color=color,
            icon=icon,
            order=order
        )

        messages.success(request, _("Area created successfully"))

        # Redirect to area list
        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:area_list')
        return response

    return {'is_edit': False}


@htmx_view(
    page_template='tables/pages/area_detail.html',
    partial_template='tables/partials/area_detail.html'
)
def area_detail(request, pk):
    """View area details with its tables."""
    area = get_object_or_404(Area, pk=pk)
    tables = area.tables.filter(is_active=True).order_by('number')

    return {
        'area': area,
        'tables': tables,
    }


@htmx_view(
    page_template='tables/pages/area_form.html',
    partial_template='tables/partials/area_form.html'
)
def area_edit(request, pk):
    """Edit an area."""
    area = get_object_or_404(Area, pk=pk)

    if request.method == 'POST':
        area.name = request.POST.get('name', '').strip()
        area.description = request.POST.get('description', '').strip()
        area.color = request.POST.get('color', '#3B82F6')
        area.icon = request.POST.get('icon', 'grid-outline')
        area.order = int(request.POST.get('order', 0))
        area.is_active = request.POST.get('is_active') == 'on'

        if not area.name:
            messages.error(request, _("Name is required"))
            return {
                'area': area,
                'form_data': request.POST,
                'is_edit': True,
            }

        area.save()
        messages.success(request, _("Area updated successfully"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:area_list')
        return response

    return {
        'area': area,
        'is_edit': True,
    }


@require_POST
def area_delete(request, pk):
    """Delete an area."""
    area = get_object_or_404(Area, pk=pk)

    # Check if area has tables
    if area.tables.exists():
        messages.error(request, _("Cannot delete area with tables. Move or delete tables first."))
        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:area_list')
        return response

    area.delete()
    messages.success(request, _("Area deleted successfully"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('tables:area_list')
    return response


# =============================================================================
# TABLE CRUD
# =============================================================================

@htmx_view(
    page_template='tables/pages/tables.html',
    partial_template='tables/partials/table_list.html'
)
def table_list(request):
    """List all tables."""
    tables = Table.objects.filter(is_active=True).select_related('area').order_by('area__order', 'number')
    areas = Area.objects.filter(is_active=True).order_by('order', 'name')

    return {
        'tables': tables,
        'areas': areas,
    }


@htmx_view(
    page_template='tables/pages/table_form.html',
    partial_template='tables/partials/table_form.html'
)
def table_create(request):
    """Create a new table."""
    config = TablesConfig.get_config()
    areas = Area.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        number = request.POST.get('number', '').strip()
        name = request.POST.get('name', '').strip()
        area_id = request.POST.get('area')
        capacity = int(request.POST.get('capacity', config.default_table_capacity))
        min_capacity = int(request.POST.get('min_capacity', 1))

        if not number:
            messages.error(request, _("Table number is required"))
            return {
                'form_data': request.POST,
                'areas': areas,
                'config': config,
                'is_edit': False,
            }

        area = None
        if area_id:
            area = get_object_or_404(Area, pk=area_id)

        # Check for duplicate
        if Table.objects.filter(area=area, number=number).exists():
            messages.error(request, _("A table with this number already exists in this area"))
            return {
                'form_data': request.POST,
                'areas': areas,
                'config': config,
                'is_edit': False,
            }

        table = Table.objects.create(
            number=number,
            name=name,
            area=area,
            capacity=capacity,
            min_capacity=min_capacity
        )

        messages.success(request, _("Table created successfully"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:floor_view')
        return response

    return {
        'areas': areas,
        'config': config,
        'is_edit': False,
    }


@htmx_view(
    page_template='tables/pages/table_detail.html',
    partial_template='tables/partials/table_detail.html'
)
def table_detail(request, pk):
    """View table details."""
    table = get_object_or_404(Table, pk=pk)

    return {'table': table}


@htmx_view(
    page_template='tables/pages/table_form.html',
    partial_template='tables/partials/table_form.html'
)
def table_edit(request, pk):
    """Edit a table."""
    table = get_object_or_404(Table, pk=pk)
    areas = Area.objects.filter(is_active=True).order_by('order', 'name')
    config = TablesConfig.get_config()

    if request.method == 'POST':
        table.number = request.POST.get('number', '').strip()
        table.name = request.POST.get('name', '').strip()
        area_id = request.POST.get('area')
        table.capacity = int(request.POST.get('capacity', 4))
        table.min_capacity = int(request.POST.get('min_capacity', 1))
        table.is_active = request.POST.get('is_active') == 'on'

        if not table.number:
            messages.error(request, _("Table number is required"))
            return {
                'table': table,
                'form_data': request.POST,
                'areas': areas,
                'config': config,
                'is_edit': True,
            }

        if area_id:
            table.area = get_object_or_404(Area, pk=area_id)
        else:
            table.area = None

        # Check for duplicate (excluding current table)
        if Table.objects.filter(area=table.area, number=table.number).exclude(pk=pk).exists():
            messages.error(request, _("A table with this number already exists in this area"))
            return {
                'table': table,
                'form_data': request.POST,
                'areas': areas,
                'config': config,
                'is_edit': True,
            }

        table.save()
        messages.success(request, _("Table updated successfully"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:floor_view')
        return response

    return {
        'table': table,
        'areas': areas,
        'config': config,
        'is_edit': True,
    }


@require_POST
def table_delete(request, pk):
    """Delete a table."""
    table = get_object_or_404(Table, pk=pk)

    if table.status == Table.STATUS_OCCUPIED:
        messages.error(request, _("Cannot delete an occupied table"))
        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:floor_view')
        return response

    table.delete()
    messages.success(request, _("Table deleted successfully"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('tables:floor_view')
    return response


# =============================================================================
# TABLE ACTIONS
# =============================================================================

@htmx_view(
    page_template='tables/pages/table_open.html',
    partial_template='tables/partials/table_open.html'
)
def table_open(request, pk):
    """
    Open a table and start a new sale.

    This redirects to the sales module to create a new sale linked to this table.
    """
    table = get_object_or_404(Table, pk=pk)

    if table.status == Table.STATUS_OCCUPIED:
        messages.warning(request, _("Table is already occupied"))
        # Redirect to the existing sale
        if table.current_sale_id:
            response = HttpResponse()
            response['HX-Redirect'] = f"/modules/sales/?table={table.pk}"
            return response

    if request.method == 'POST':
        guests = int(request.POST.get('guests', table.capacity))
        waiter = request.POST.get('waiter', '').strip()

        # Open the table
        table.open_table(guests=guests, waiter=waiter)

        messages.success(request, _("Table opened. Creating new sale..."))

        # Redirect to sales module with table context
        response = HttpResponse()
        response['HX-Redirect'] = f"/modules/sales/?table={table.pk}&new=1"
        return response

    return {
        'table': table,
    }


@require_POST
def table_close(request, pk):
    """Close a table."""
    table = get_object_or_404(Table, pk=pk)

    if table.current_sale_id:
        # Check if sale is completed
        sale = table.current_sale
        if sale and sale.status != 'completed':
            messages.error(request, _("Cannot close table with unpaid sale"))
            response = HttpResponse()
            response['HX-Redirect'] = reverse('tables:floor_view')
            return response

    table.close_table()
    messages.success(request, _("Table closed successfully"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('tables:floor_view')
    return response


@htmx_view(
    page_template='tables/pages/table_transfer.html',
    partial_template='tables/partials/table_transfer.html'
)
def table_transfer(request, pk):
    """Transfer a table's sale to another table."""
    table = get_object_or_404(Table, pk=pk)

    if not table.current_sale_id:
        messages.error(request, _("No active sale to transfer"))
        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:floor_view')
        return response

    available_tables = Table.objects.filter(
        is_active=True,
        status=Table.STATUS_AVAILABLE
    ).exclude(pk=pk).select_related('area').order_by('area__order', 'number')

    if request.method == 'POST':
        target_id = request.POST.get('target_table')
        if not target_id:
            messages.error(request, _("Please select a target table"))
            return {
                'table': table,
                'available_tables': available_tables,
            }

        target_table = get_object_or_404(Table, pk=target_id)

        try:
            table.transfer_to(target_table)
            messages.success(request, _("Sale transferred successfully"))
        except ValueError as e:
            messages.error(request, str(e))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:floor_view')
        return response

    return {
        'table': table,
        'available_tables': available_tables,
    }


@require_POST
def table_block(request, pk):
    """Block a table."""
    table = get_object_or_404(Table, pk=pk)

    if table.status == Table.STATUS_OCCUPIED:
        messages.error(request, _("Cannot block an occupied table"))
    else:
        table.block()
        messages.success(request, _("Table blocked"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('tables:floor_view')
    return response


@require_POST
def table_unblock(request, pk):
    """Unblock a table."""
    table = get_object_or_404(Table, pk=pk)
    table.unblock()
    messages.success(request, _("Table unblocked"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('tables:floor_view')
    return response


# =============================================================================
# SETTINGS
# =============================================================================

@htmx_view(
    page_template='tables/pages/settings.html',
    partial_template='tables/partials/settings.html'
)
def settings_view(request):
    """Tables module settings."""
    config = TablesConfig.get_config()

    if request.method == 'POST':
        config.show_table_timer = request.POST.get('show_table_timer') == 'on'
        config.show_table_total = request.POST.get('show_table_total') == 'on'
        config.default_table_capacity = int(request.POST.get('default_table_capacity', 4))
        config.auto_close_on_payment = request.POST.get('auto_close_on_payment') == 'on'
        config.require_table_for_order = request.POST.get('require_table_for_order') == 'on'
        config.save()

        messages.success(request, _("Settings saved successfully"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('tables:settings')
        return response

    return {'config': config}


# =============================================================================
# API ENDPOINTS
# =============================================================================

@require_GET
def api_tables_status(request):
    """
    API: Get current status of all tables.

    Returns JSON with table statuses for real-time updates.
    """
    tables = Table.objects.filter(is_active=True).select_related('area')

    data = []
    for table in tables:
        data.append({
            'id': table.pk,
            'number': table.number,
            'area': table.area.name if table.area else None,
            'status': table.status,
            'guests': table.guests,
            'waiter': table.waiter,
            'elapsed_minutes': table.elapsed_minutes,
            'elapsed_display': table.elapsed_display,
            'current_total': str(table.current_total),
            'current_sale_id': table.current_sale_id,
        })

    return JsonResponse({'tables': data})


@require_GET
def api_areas(request):
    """API: Get list of areas."""
    areas = Area.objects.filter(is_active=True).order_by('order', 'name')

    data = []
    for area in areas:
        data.append({
            'id': area.pk,
            'name': area.name,
            'color': area.color,
            'icon': area.icon,
            'table_count': area.table_count,
            'occupied_count': area.occupied_count,
            'available_count': area.available_count,
        })

    return JsonResponse({'areas': data})
