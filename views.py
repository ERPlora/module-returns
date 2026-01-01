"""
Returns & Refunds Module Views

Provides return processing, store credit management, and refund handling.
"""

import json

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Q
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.urls import reverse
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal

from apps.core.htmx import htmx_view
from .models import ReturnsConfig, ReturnReason, Return, ReturnLine, StoreCredit


# =============================================================================
# DASHBOARD
# =============================================================================

@htmx_view(
    'returns/pages/index.html',
    'returns/partials/dashboard_content.html'
)
def dashboard(request):
    """
    Returns module dashboard with statistics.
    """
    from apps.core.services.currency_service import format_currency

    config = ReturnsConfig.get_config()

    # Get filter parameters
    status_filter = request.GET.get('status')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    # Build queryset
    returns = Return.objects.all().select_related('reason')

    if status_filter:
        returns = returns.filter(status=status_filter)
    if date_from:
        returns = returns.filter(created_at__date__gte=date_from)
    if date_to:
        returns = returns.filter(created_at__date__lte=date_to)

    # Statistics
    total_returns = Return.objects.count()
    pending_returns = Return.objects.filter(status=Return.STATUS_PENDING).count()
    processed_returns = Return.objects.filter(status=Return.STATUS_PROCESSED).count()
    total_refunded = Return.objects.filter(
        status=Return.STATUS_PROCESSED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Recent returns with formatted amounts
    recent_returns_qs = returns.order_by('-created_at')[:10]
    recent_returns = []
    for ret in recent_returns_qs:
        ret.total_amount_formatted = format_currency(ret.total_amount)
        recent_returns.append(ret)

    context = {
        'config': config,
        'recent_returns': recent_returns,
        'status_filter': status_filter,
        'stats': {
            'total': total_returns,
            'pending': pending_returns,
            'processed': processed_returns,
            'total_refunded_formatted': format_currency(total_refunded),
        }
    }

    return context


# =============================================================================
# RETURN CRUD
# =============================================================================

@htmx_view(
    'returns/pages/return_list.html',
    'returns/partials/return_list.html'
)
def return_list(request):
    """List all returns with filtering and pagination."""
    returns = Return.objects.all().select_related('reason').order_by('-created_at')

    # Filters
    status = request.GET.get('status')
    if status:
        returns = returns.filter(status=status)

    # Pagination
    paginator = Paginator(returns, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return {
        'returns': page_obj,
        'status_filter': status,
    }


@htmx_view(
    'returns/pages/return_form.html',
    'returns/partials/return_form.html'
)
def return_create(request):
    """Create a new return."""
    config = ReturnsConfig.get_config()
    reasons = ReturnReason.objects.filter(is_active=True).order_by('order', 'name')

    if request.method == 'POST':
        sale_id = request.POST.get('sale_id', '').strip()
        reason_id = request.POST.get('reason')
        notes = request.POST.get('notes', '').strip()
        refund_method = request.POST.get('refund_method', Return.REFUND_CASH)

        # Validate
        if config.require_receipt and not sale_id:
            messages.error(request, _("Sale ID / Receipt is required"))
            return {
                'form_data': request.POST,
                'reasons': reasons,
                'config': config,
                'is_edit': False,
            }

        reason = None
        if reason_id:
            reason = get_object_or_404(ReturnReason, pk=reason_id)
            if reason.requires_note and not notes:
                messages.error(request, _("Notes are required for this return reason"))
                return {
                    'form_data': request.POST,
                    'reasons': reasons,
                    'config': config,
                    'is_edit': False,
                }

        # Create return
        return_order = Return.objects.create(
            sale_id=sale_id if sale_id else None,
            reason=reason,
            notes=notes,
            refund_method=refund_method,
        )

        messages.success(request, _("Return created. Add items to continue."))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': return_order.pk})
        return response

    return {
        'reasons': reasons,
        'config': config,
        'is_edit': False,
    }


@htmx_view(
    'returns/pages/return_detail.html',
    'returns/partials/return_detail.html'
)
def return_detail(request, pk):
    """View return details."""
    return_order = get_object_or_404(Return, pk=pk)
    lines = return_order.lines.all()

    return {
        'return_order': return_order,
        'lines': lines,
    }


@htmx_view(
    'returns/pages/return_form.html',
    'returns/partials/return_form.html'
)
def return_edit(request, pk):
    """Edit a return."""
    return_order = get_object_or_404(Return, pk=pk)
    reasons = ReturnReason.objects.filter(is_active=True).order_by('order', 'name')
    config = ReturnsConfig.get_config()

    if return_order.status == Return.STATUS_PROCESSED:
        messages.error(request, _("Cannot edit a processed return"))
        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
        return response

    if request.method == 'POST':
        reason_id = request.POST.get('reason')
        notes = request.POST.get('notes', '').strip()
        refund_method = request.POST.get('refund_method', Return.REFUND_CASH)

        if reason_id:
            return_order.reason = get_object_or_404(ReturnReason, pk=reason_id)
        return_order.notes = notes
        return_order.refund_method = refund_method
        return_order.save()

        messages.success(request, _("Return updated successfully"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
        return response

    return {
        'return_order': return_order,
        'reasons': reasons,
        'config': config,
        'is_edit': True,
    }


@require_POST
def return_approve(request, pk):
    """Approve a pending return."""
    return_order = get_object_or_404(Return, pk=pk)

    if return_order.status != Return.STATUS_PENDING:
        messages.error(request, _("Only pending returns can be approved"))
    else:
        return_order.approve()
        messages.success(request, _("Return approved"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
    return response


@require_POST
def return_process(request, pk):
    """Process an approved return and issue refund."""
    return_order = get_object_or_404(Return, pk=pk)

    if return_order.status not in [Return.STATUS_PENDING, Return.STATUS_APPROVED]:
        messages.error(request, _("This return cannot be processed"))
    elif not return_order.lines.exists():
        messages.error(request, _("Cannot process return without items"))
    else:
        # Get username if available
        processed_by = getattr(request.user, 'username', '') if hasattr(request, 'user') else ''
        return_order.process(processed_by=processed_by)

        # Create store credit if refund method is store credit
        if return_order.refund_method == Return.REFUND_STORE_CREDIT:
            _create_store_credit_from_return(return_order)

        messages.success(request, _("Return processed successfully"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
    return response


@require_POST
def return_cancel(request, pk):
    """Cancel a return."""
    return_order = get_object_or_404(Return, pk=pk)

    if return_order.status == Return.STATUS_PROCESSED:
        messages.error(request, _("Cannot cancel a processed return"))
    else:
        return_order.cancel()
        messages.success(request, _("Return cancelled"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:return_list')
    return response


# =============================================================================
# RETURN LINES
# =============================================================================

@require_POST
def line_add(request, pk):
    """Add a line item to a return."""
    return_order = get_object_or_404(Return, pk=pk)

    if return_order.status != Return.STATUS_PENDING:
        messages.error(request, _("Cannot add items to a non-pending return"))
        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
        return response

    product_name = request.POST.get('product_name', '').strip()
    product_sku = request.POST.get('product_sku', '').strip()
    quantity = int(request.POST.get('quantity', 1))
    unit_price = Decimal(request.POST.get('unit_price', '0.00'))
    tax_rate = Decimal(request.POST.get('tax_rate', '21.00'))
    condition = request.POST.get('condition', 'good')

    if not product_name:
        messages.error(request, _("Product name is required"))
    else:
        line = ReturnLine.objects.create(
            return_order=return_order,
            product_name=product_name,
            product_sku=product_sku,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=tax_rate,
            condition=condition,
        )

        # Update return totals
        _update_return_totals(return_order)

        messages.success(request, _("Item added to return"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
    return response


@require_POST
def line_remove(request, pk, line_pk):
    """Remove a line item from a return."""
    return_order = get_object_or_404(Return, pk=pk)
    line = get_object_or_404(ReturnLine, pk=line_pk, return_order=return_order)

    if return_order.status != Return.STATUS_PENDING:
        messages.error(request, _("Cannot remove items from a non-pending return"))
    else:
        line.delete()
        _update_return_totals(return_order)
        messages.success(request, _("Item removed from return"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:return_detail', kwargs={'pk': pk})
    return response


# =============================================================================
# RETURN REASONS
# =============================================================================

@htmx_view(
    'returns/pages/reasons.html',
    'returns/partials/reason_list.html'
)
def reason_list(request):
    """List all return reasons."""
    reasons = ReturnReason.objects.all().order_by('order', 'name')
    return {'reasons': reasons}


@htmx_view(
    'returns/pages/reason_form.html',
    'returns/partials/reason_form.html'
)
def reason_create(request):
    """Create a new return reason."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        restocks_inventory = request.POST.get('restocks_inventory') == 'on'
        requires_note = request.POST.get('requires_note') == 'on'
        order = int(request.POST.get('order', 0))

        if not name:
            messages.error(request, _("Name is required"))
            return {'form_data': request.POST, 'is_edit': False}

        ReturnReason.objects.create(
            name=name,
            description=description,
            restocks_inventory=restocks_inventory,
            requires_note=requires_note,
            order=order,
        )

        messages.success(request, _("Return reason created"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:reason_list')
        return response

    return {'is_edit': False}


@htmx_view(
    'returns/pages/reason_form.html',
    'returns/partials/reason_form.html'
)
def reason_edit(request, pk):
    """Edit a return reason."""
    reason = get_object_or_404(ReturnReason, pk=pk)

    if request.method == 'POST':
        reason.name = request.POST.get('name', '').strip()
        reason.description = request.POST.get('description', '').strip()
        reason.restocks_inventory = request.POST.get('restocks_inventory') == 'on'
        reason.requires_note = request.POST.get('requires_note') == 'on'
        reason.order = int(request.POST.get('order', 0))
        reason.is_active = request.POST.get('is_active') == 'on'

        if not reason.name:
            messages.error(request, _("Name is required"))
            return {'reason': reason, 'form_data': request.POST, 'is_edit': True}

        reason.save()
        messages.success(request, _("Return reason updated"))

        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:reason_list')
        return response

    return {'reason': reason, 'is_edit': True}


@require_POST
def reason_delete(request, pk):
    """Delete a return reason."""
    reason = get_object_or_404(ReturnReason, pk=pk)

    if Return.objects.filter(reason=reason).exists():
        messages.error(request, _("Cannot delete reason in use by returns"))
    else:
        reason.delete()
        messages.success(request, _("Return reason deleted"))

    response = HttpResponse()
    response['HX-Redirect'] = reverse('returns:reason_list')
    return response


# =============================================================================
# STORE CREDIT
# =============================================================================

@htmx_view(
    'returns/pages/credits.html',
    'returns/partials/credit_list.html'
)
def credit_list(request):
    """List all store credits."""
    credits = StoreCredit.objects.all().order_by('-created_at')

    # Filters
    active_only = request.GET.get('active')
    if active_only == '1':
        credits = credits.filter(is_active=True, current_amount__gt=0)

    search = request.GET.get('search', '').strip()
    if search:
        credits = credits.filter(
            Q(code__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(customer_phone__icontains=search)
        )

    # Pagination
    paginator = Paginator(credits, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return {
        'credits': page_obj,
        'search': search,
        'active_only': active_only,
    }


@htmx_view(
    'returns/pages/credit_detail.html',
    'returns/partials/credit_detail.html'
)
def credit_detail(request, pk):
    """View store credit details."""
    credit = get_object_or_404(StoreCredit, pk=pk)
    return {'credit': credit}


@htmx_view(
    'returns/pages/credit_form.html',
    'returns/partials/credit_form.html'
)
def credit_create(request):
    """Create a new store credit manually."""
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        amount = Decimal(request.POST.get('amount', '0.00'))
        notes = request.POST.get('notes', '').strip()

        if amount <= 0:
            messages.error(request, _("Amount must be greater than zero"))
            return {'form_data': request.POST}

        # Generate code
        import secrets
        code = f"SC-{secrets.token_hex(4).upper()}"

        StoreCredit.objects.create(
            code=code,
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            original_amount=amount,
            current_amount=amount,
            notes=notes,
        )

        messages.success(request, _("Store credit created with code: ") + code)

        response = HttpResponse()
        response['HX-Redirect'] = reverse('returns:credit_list')
        return response

    return {}


@require_GET
def credit_lookup(request):
    """API: Lookup store credit by code."""
    code = request.GET.get('code', '').strip()

    if not code:
        return JsonResponse({'error': 'Code is required'}, status=400)

    try:
        credit = StoreCredit.objects.get(code=code)
        return JsonResponse({
            'code': credit.code,
            'customer_name': credit.customer_name,
            'original_amount': str(credit.original_amount),
            'current_amount': str(credit.current_amount),
            'is_valid': credit.is_valid,
            'is_expired': credit.is_expired(),
            'expires_at': credit.expires_at.isoformat() if credit.expires_at else None,
        })
    except StoreCredit.DoesNotExist:
        return JsonResponse({'error': 'Store credit not found'}, status=404)


# =============================================================================
# SETTINGS
# =============================================================================

@htmx_view(
    'returns/pages/settings.html',
    'returns/partials/settings.html'
)
def settings_view(request):
    """Returns module settings."""
    config = ReturnsConfig.get_config()
    return {
        'config': config,
        'returns_toggle_url': reverse('returns:settings_toggle'),
        'returns_input_url': reverse('returns:settings_input'),
    }


@require_POST
def settings_save(request):
    """Save returns settings via JSON."""
    try:
        data = json.loads(request.body)
        config = ReturnsConfig.get_config()

        config.allow_returns = data.get('allow_returns', True)
        config.require_receipt = data.get('require_receipt', True)
        config.allow_store_credit = data.get('allow_store_credit', True)
        config.return_window_days = int(data.get('return_window_days', 30))
        config.auto_restore_stock = data.get('auto_restore_stock', True)
        config.save()

        return JsonResponse({'success': True, 'message': 'Settings saved'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
def settings_toggle(request):
    """Toggle a single setting via HTMX."""
    # Support both 'name'/'value' (new components) and 'setting_name'/'setting_value' (legacy)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value', request.POST.get('setting_value', 'false'))
    setting_value = value == 'true' or value is True

    config = ReturnsConfig.get_config()

    boolean_settings = ['allow_returns', 'require_receipt', 'allow_store_credit',
                       'auto_restore_stock']

    if name in boolean_settings:
        setattr(config, name, setting_value)
        config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@require_http_methods(["POST"])
def settings_input(request):
    """Update a numeric setting via HTMX."""
    # Support both 'name'/'value' (new components) and 'setting_name'/'setting_value' (legacy)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value') or request.POST.get('setting_value')

    config = ReturnsConfig.get_config()

    if name == 'return_window_days':
        try:
            config.return_window_days = int(value)
            config.save()
        except (ValueError, TypeError):
            pass

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@require_http_methods(["POST"])
def settings_reset(request):
    """Reset all settings to defaults via HTMX."""
    config = ReturnsConfig.get_config()

    config.allow_returns = True
    config.require_receipt = True
    config.allow_store_credit = True
    config.return_window_days = 30
    config.auto_restore_stock = True
    config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Settings reset to defaults')), 'color': 'warning'},
        'refreshPage': True
    })
    return response


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _update_return_totals(return_order):
    """Recalculate and update return totals from lines."""
    lines = return_order.lines.all()

    subtotal = sum(line.line_subtotal for line in lines)
    tax_amount = sum(line.line_tax for line in lines)
    total_amount = sum(line.line_total for line in lines)

    return_order.subtotal = subtotal
    return_order.tax_amount = tax_amount
    return_order.total_amount = total_amount
    return_order.save()


def _create_store_credit_from_return(return_order):
    """Create a store credit from a processed return."""
    import secrets
    code = f"SC-{secrets.token_hex(4).upper()}"

    StoreCredit.objects.create(
        code=code,
        original_amount=return_order.total_amount,
        current_amount=return_order.total_amount,
        return_order=return_order,
        notes=f"Created from return {return_order.return_number}",
    )
