from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Return, ReturnItem, ReturnReason


class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = [
            'original_sale', 'customer', 'reason',
            'reason_notes', 'refund_method', 'notes',
        ]
        widgets = {
            'original_sale': forms.Select(attrs={
                'class': 'select',
            }),
            'customer': forms.Select(attrs={
                'class': 'select',
            }),
            'reason': forms.Select(attrs={
                'class': 'select',
            }),
            'reason_notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
                'placeholder': _('Reason details'),
            }),
            'refund_method': forms.Select(attrs={
                'class': 'select',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
                'placeholder': _('Additional notes'),
            }),
        }


class ReturnItemForm(forms.ModelForm):
    class Meta:
        model = ReturnItem
        fields = [
            'product', 'quantity', 'unit_price', 'tax_rate',
            'refund_amount', 'condition', 'restock', 'notes',
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'input', 'min': '1',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0', 'max': '100',
            }),
            'refund_amount': forms.NumberInput(attrs={
                'class': 'input', 'step': '0.01', 'min': '0',
            }),
            'condition': forms.Select(attrs={
                'class': 'select',
            }),
            'restock': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
            }),
        }


class ReturnReasonForm(forms.ModelForm):
    class Meta:
        model = ReturnReason
        fields = [
            'name', 'description', 'restocks_inventory',
            'requires_note', 'sort_order', 'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': _('e.g. Defective, Wrong Item'),
            }),
            'description': forms.Textarea(attrs={
                'class': 'textarea', 'rows': 2,
            }),
            'restocks_inventory': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'requires_note': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
            'sort_order': forms.NumberInput(attrs={
                'class': 'input', 'min': '0',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'toggle',
            }),
        }


class ReturnFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': _('Search by return number, customer...'),
        }),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Status')),
            ('pending', _('Pending')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('completed', _('Completed')),
            ('cancelled', _('Cancelled')),
        ],
        widget=forms.Select(attrs={'class': 'select'}),
    )
    refund_method = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Methods')),
            ('original', _('Original Payment')),
            ('cash', _('Cash')),
            ('store_credit', _('Store Credit')),
        ],
        widget=forms.Select(attrs={'class': 'select'}),
    )
