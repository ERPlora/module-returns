"""
Returns & Refunds Module Views

Merged: old (ReturnReason CRUD, StoreCredit management, settings toggles) +
new (HubBaseModel patterns, real FKs, approve/reject/complete workflow).
"""

import json
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST, require_GET

from apps.accounts.decorators import login_required, permission_required
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .forms import ReturnForm, ReturnItemForm, ReturnReasonForm
from .models import ReturnsSettings, ReturnReason, Return, ReturnItem, StoreCredit


def _hub_id(request):
    return request.session.get('hub_id')


def _employee(request):
    user_id = request.session.get('local_user_id')
    if user_id:
        from apps.accounts.models import LocalUser
        return LocalUser.objects.filter(id=user_id).first()
    return None


# =============================================================================
# Dashboard
# =============================================================================

@login_required
@with_module_nav('returns', 'dashboard')
@htmx_view('returns/pages/index.html', 'returns/partials/dashboard_content.html')
def index(request):
    hub = _hub_id(request)
    settings = ReturnsSettings.get_settings(hub)

    returns = Return.objects.filter(hub_id=hub, is_deleted=False)

    total_returns = returns.count()
    pending_returns = returns.filter(status='pending').count()
    completed_returns = returns.filter(status='completed').count()
    total_refunded = returns.filter(status='completed').aggregate(
        total=Sum('total_refund')
    )['total'] or Decimal('0.00')

    recent = returns.select_related(
        'customer', 'employee', 'reason',
    ).order_by('-created_at')[:10]

    return {
        'page_title': _('Returns'),
        'settings': settings,
        'recent_returns': recent,
        'total_returns': total_returns,
        'pending_returns': pending_returns,
        'completed_returns': completed_returns,
        'total_refunded': total_refunded,
    }


# =============================================================================
# Return CRUD
# =============================================================================

@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_list.html', 'returns/partials/return_list.html')
def return_list(request):
    hub = _hub_id(request)
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    method_filter = request.GET.get('refund_method', '')

    returns = Return.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related(
        'customer', 'employee', 'original_sale', 'reason',
    ).order_by('-created_at')

    if search:
        returns = returns.filter(
            Q(number__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(reason_notes__icontains=search)
        )
    if status_filter:
        returns = returns.filter(status=status_filter)
    if method_filter:
        returns = returns.filter(refund_method=method_filter)

    return {
        'page_title': _('Returns'),
        'returns': returns[:100],
        'search_query': search,
        'status_filter': status_filter,
        'method_filter': method_filter,
    }


@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_detail.html', 'returns/partials/return_detail.html')
def return_detail(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, is_deleted=False,
    )
    items = return_obj.items.filter(is_deleted=False).select_related('product')

    return {
        'page_title': str(return_obj),
        'return_obj': return_obj,
        'items': items,
    }


@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_form.html', 'returns/partials/return_form.html')
def return_add(request):
    hub = _hub_id(request)
    settings = ReturnsSettings.get_settings(hub)
    reasons = ReturnReason.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')

    if request.method == 'POST':
        form = ReturnForm(request.POST)
        if form.is_valid():
            return_obj = form.save(commit=False)
            return_obj.hub_id = hub
            return_obj.employee = _employee(request)
            return_obj.save()

            return {
                'page_title': _('Returns'),
                'returns': Return.objects.filter(
                    hub_id=hub, is_deleted=False
                ).order_by('-created_at')[:100],
                'template': 'returns/partials/list.html',
                'success_message': _('Return created successfully'),
            }
    else:
        form = ReturnForm()

    return {
        'page_title': _('New Return'),
        'form': form,
        'reasons': reasons,
        'settings': settings,
        'is_new': True,
    }


@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_form.html', 'returns/partials/return_form.html')
def return_edit(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, is_deleted=False,
    )
    reasons = ReturnReason.objects.filter(
        hub_id=hub, is_deleted=False, is_active=True,
    ).order_by('sort_order', 'name')

    if request.method == 'POST':
        form = ReturnForm(request.POST, instance=return_obj)
        if form.is_valid():
            form.save()
            return {
                'page_title': _('Returns'),
                'returns': Return.objects.filter(
                    hub_id=hub, is_deleted=False
                ).order_by('-created_at')[:100],
                'template': 'returns/partials/list.html',
                'success_message': _('Return updated successfully'),
            }
    else:
        form = ReturnForm(instance=return_obj)

    return {
        'page_title': _('Edit Return'),
        'form': form,
        'return_obj': return_obj,
        'reasons': reasons,
        'is_new': False,
    }


@login_required
@require_POST
def return_delete(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, is_deleted=False,
    )
    return_obj.is_deleted = True
    return_obj.deleted_at = timezone.now()
    return_obj.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': str(_('Return deleted successfully')),
    })


# =============================================================================
# Return Workflow Actions
# =============================================================================

@login_required
@require_POST
def return_approve(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, status='pending', is_deleted=False,
    )
    user = _employee(request)
    return_obj.approve(approved_by=user)

    return JsonResponse({
        'success': True,
        'message': str(_('Return approved')),
    })


@login_required
@require_POST
def return_reject(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, status='pending', is_deleted=False,
    )
    return_obj.reject()

    return JsonResponse({
        'success': True,
        'message': str(_('Return rejected')),
    })


@login_required
@require_POST
def return_complete(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, status='approved', is_deleted=False,
    )
    return_obj.complete()

    # Create store credit if refund method is store_credit
    if return_obj.refund_method == 'store_credit':
        _create_store_credit_from_return(hub, return_obj)

    return JsonResponse({
        'success': True,
        'message': str(_('Return completed and refund processed')),
    })


# =============================================================================
# Return Items
# =============================================================================

@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_detail.html', 'returns/partials/return_detail.html')
def item_add(request, return_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, is_deleted=False,
    )

    if request.method == 'POST':
        form = ReturnItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.hub_id = hub
            item.return_obj = return_obj
            item.save()
            return_obj.recalculate_total()

            items = return_obj.items.filter(is_deleted=False).select_related('product')
            return {
                'page_title': str(return_obj),
                'return_obj': return_obj,
                'items': items,
                'template': 'returns/partials/detail.html',
                'success_message': _('Item added to return'),
            }
    else:
        form = ReturnItemForm()

    return {
        'page_title': _('Add Item'),
        'form': form,
        'return_obj': return_obj,
    }


@login_required
@require_POST
def item_delete(request, return_id, item_id):
    hub = _hub_id(request)
    return_obj = get_object_or_404(
        Return, id=return_id, hub_id=hub, is_deleted=False,
    )
    item = get_object_or_404(
        ReturnItem, id=item_id, return_obj=return_obj, is_deleted=False,
    )
    item.is_deleted = True
    item.deleted_at = timezone.now()
    item.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    return_obj.recalculate_total()

    return JsonResponse({
        'success': True,
        'message': str(_('Item removed from return')),
    })


# =============================================================================
# Return Reasons (from old)
# =============================================================================

@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/reasons.html', 'returns/partials/reason_list.html')
def reasons(request):
    hub = _hub_id(request)
    reasons_list = ReturnReason.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('sort_order', 'name')

    return {
        'page_title': _('Return Reasons'),
        'reasons': reasons_list,
    }


@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/reason_form.html', 'returns/partials/reason_form.html')
def reason_add(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        form = ReturnReasonForm(request.POST)
        if form.is_valid():
            reason = form.save(commit=False)
            reason.hub_id = hub
            reason.save()

            return {
                'page_title': _('Return Reasons'),
                'reasons': ReturnReason.objects.filter(
                    hub_id=hub, is_deleted=False
                ).order_by('sort_order', 'name'),
                'template': 'returns/partials/reasons.html',
                'success_message': _('Reason created'),
            }
    else:
        form = ReturnReasonForm()

    return {
        'page_title': _('Add Reason'),
        'form': form,
        'is_new': True,
    }


@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/reason_form.html', 'returns/partials/reason_form.html')
def reason_edit(request, reason_id):
    hub = _hub_id(request)
    reason = get_object_or_404(
        ReturnReason, id=reason_id, hub_id=hub, is_deleted=False,
    )

    if request.method == 'POST':
        form = ReturnReasonForm(request.POST, instance=reason)
        if form.is_valid():
            form.save()
            return {
                'page_title': _('Return Reasons'),
                'reasons': ReturnReason.objects.filter(
                    hub_id=hub, is_deleted=False
                ).order_by('sort_order', 'name'),
                'template': 'returns/partials/reasons.html',
                'success_message': _('Reason updated'),
            }
    else:
        form = ReturnReasonForm(instance=reason)

    return {
        'page_title': _('Edit Reason'),
        'form': form,
        'reason': reason,
        'is_new': False,
    }


@login_required
@require_POST
def reason_delete(request, reason_id):
    hub = _hub_id(request)
    reason = get_object_or_404(
        ReturnReason, id=reason_id, hub_id=hub, is_deleted=False,
    )
    reason.is_deleted = True
    reason.deleted_at = timezone.now()
    reason.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': str(_('Reason deleted')),
    })


# =============================================================================
# Store Credits (from old)
# =============================================================================

@login_required
@with_module_nav('returns', 'credits')
@htmx_view('returns/pages/credits.html', 'returns/partials/credit_list.html')
def credits(request):
    hub = _hub_id(request)
    search = request.GET.get('q', '').strip()
    active_only = request.GET.get('active', '')

    qs = StoreCredit.objects.filter(
        hub_id=hub, is_deleted=False,
    ).select_related('customer').order_by('-created_at')

    if active_only == '1':
        qs = qs.filter(is_active=True, current_amount__gt=0)
    if search:
        qs = qs.filter(
            Q(code__icontains=search) |
            Q(customer_name__icontains=search) |
            Q(customer__name__icontains=search)
        )

    return {
        'page_title': _('Store Credits'),
        'credits': qs[:100],
        'search_query': search,
        'active_only': active_only,
    }


@login_required
@with_module_nav('returns', 'credits')
@htmx_view('returns/pages/credit_form.html', 'returns/partials/credit_form.html')
def credit_add(request):
    hub = _hub_id(request)

    if request.method == 'POST':
        customer_name = request.POST.get('customer_name', '').strip()
        amount = Decimal(request.POST.get('amount', '0.00'))
        notes = request.POST.get('notes', '').strip()

        if amount <= 0:
            return {
                'page_title': _('Add Store Credit'),
                'form_data': request.POST,
                'error': _('Amount must be greater than zero'),
            }

        StoreCredit.objects.create(
            hub_id=hub,
            code=StoreCredit.generate_code(),
            customer_name=customer_name,
            original_amount=amount,
            current_amount=amount,
            notes=notes,
        )

        return {
            'page_title': _('Store Credits'),
            'credits': StoreCredit.objects.filter(
                hub_id=hub, is_deleted=False
            ).order_by('-created_at')[:100],
            'template': 'returns/partials/credits.html',
            'success_message': _('Store credit created'),
        }

    return {
        'page_title': _('Add Store Credit'),
    }


@login_required
@require_GET
def credit_lookup(request):
    """API: Lookup store credit by code."""
    hub = _hub_id(request)
    code = request.GET.get('code', '').strip()

    if not code:
        return JsonResponse({'error': 'Code is required'}, status=400)

    try:
        credit = StoreCredit.objects.get(
            hub_id=hub, code=code, is_deleted=False,
        )
        return JsonResponse({
            'code': credit.code,
            'customer_name': credit.customer_name or (
                credit.customer.name if credit.customer else ''
            ),
            'original_amount': str(credit.original_amount),
            'current_amount': str(credit.current_amount),
            'is_valid': credit.is_valid,
            'is_expired': credit.is_expired(),
            'expires_at': credit.expires_at.isoformat() if credit.expires_at else None,
        })
    except StoreCredit.DoesNotExist:
        return JsonResponse({'error': 'Store credit not found'}, status=404)


# =============================================================================
# Refunds View (from old — completed returns)
# =============================================================================

@login_required
@with_module_nav('returns', 'returns')
@htmx_view('returns/pages/return_list.html', 'returns/partials/return_list.html')
def refunds(request):
    hub = _hub_id(request)
    search = request.GET.get('q', '').strip()

    completed = Return.objects.filter(
        hub_id=hub, status='completed', is_deleted=False,
    ).select_related('customer', 'employee').order_by('-completed_at')

    if search:
        completed = completed.filter(
            Q(number__icontains=search) |
            Q(customer__name__icontains=search)
        )

    total_refunded = completed.aggregate(
        total=Sum('total_refund')
    )['total'] or Decimal('0')

    return {
        'page_title': _('Refunds'),
        'refunds': completed[:100],
        'search_query': search,
        'total_refunded': total_refunded,
        'refund_count': completed.count(),
    }


# =============================================================================
# Settings
# =============================================================================

@login_required
@permission_required('returns.manage_settings')
@with_module_nav('returns', 'settings')
@htmx_view('returns/pages/settings.html', 'returns/partials/settings.html')
def settings_view(request):
    hub = _hub_id(request)
    settings = ReturnsSettings.get_settings(hub)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        value = request.POST.get('value', 'false')

        boolean_settings = [
            'allow_returns', 'require_receipt',
            'allow_store_credit', 'auto_restore_stock',
        ]

        if name in boolean_settings:
            setattr(settings, name, value == 'true')
            settings.save(update_fields=[name, 'updated_at'])

        elif name == 'return_window_days':
            try:
                settings.return_window_days = int(value)
                settings.save(update_fields=['return_window_days', 'updated_at'])
            except (ValueError, TypeError):
                pass

        response = HttpResponse(status=204)
        response['HX-Trigger'] = json.dumps({
            'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
        })
        return response

    return {
        'page_title': _('Return Settings'),
        'settings': settings,
    }


# =============================================================================
# Helpers
# =============================================================================

def _create_store_credit_from_return(hub_id, return_obj):
    StoreCredit.objects.create(
        hub_id=hub_id,
        code=StoreCredit.generate_code(),
        customer=return_obj.customer,
        customer_name=return_obj.customer.name if return_obj.customer else '',
        original_amount=return_obj.total_refund,
        current_amount=return_obj.total_refund,
        return_obj=return_obj,
        notes=f'Created from return {return_obj.number}',
    )
