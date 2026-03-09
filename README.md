# Returns

## Overview

| Property | Value |
|----------|-------|
| **Module ID** | `returns` |
| **Version** | `1.0.0` |
| **Icon** | `arrow-undo-outline` |
| **Dependencies** | `sales`, `customers`, `inventory` |

## Dependencies

This module requires the following modules to be installed:

- `sales`
- `customers`
- `inventory`

## Models

### `ReturnsSettings`

Per-hub settings for the returns module.

| Field | Type | Details |
|-------|------|---------|
| `allow_returns` | BooleanField |  |
| `return_window_days` | PositiveIntegerField |  |
| `allow_store_credit` | BooleanField |  |
| `require_receipt` | BooleanField |  |
| `auto_restore_stock` | BooleanField |  |

**Methods:**

- `get_settings()`

### `ReturnReason`

Predefined reasons for product returns.

| Field | Type | Details |
|-------|------|---------|
| `name` | CharField | max_length=100 |
| `description` | TextField | optional |
| `restocks_inventory` | BooleanField |  |
| `requires_note` | BooleanField |  |
| `sort_order` | PositiveIntegerField |  |
| `is_active` | BooleanField |  |

### `Return`

A product return linked to an original sale.

| Field | Type | Details |
|-------|------|---------|
| `number` | CharField | max_length=50, optional |
| `original_sale` | ForeignKey | → `sales.Sale`, on_delete=SET_NULL, optional |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `employee` | ForeignKey | → `accounts.LocalUser`, on_delete=SET_NULL, optional |
| `reason` | ForeignKey | → `returns.ReturnReason`, on_delete=SET_NULL, optional |
| `reason_notes` | TextField | optional |
| `status` | CharField | max_length=20, choices: pending, approved, rejected, completed, cancelled |
| `subtotal` | DecimalField |  |
| `tax_amount` | DecimalField |  |
| `total_refund` | DecimalField |  |
| `refund_method` | CharField | max_length=20, choices: original, cash, store_credit |
| `notes` | TextField | optional |
| `approved_by` | ForeignKey | → `accounts.LocalUser`, on_delete=SET_NULL, optional |
| `approved_at` | DateTimeField | optional |
| `completed_at` | DateTimeField | optional |

**Methods:**

- `recalculate_total()` — Recalculate totals from items.
- `approve()`
- `reject()`
- `complete()`
- `cancel()`

**Properties:**

- `item_count`
- `total_quantity`

### `ReturnItem`

Individual item within a return.

| Field | Type | Details |
|-------|------|---------|
| `return_obj` | ForeignKey | → `returns.Return`, on_delete=CASCADE |
| `sale_item` | ForeignKey | → `sales.SaleItem`, on_delete=SET_NULL, optional |
| `product` | ForeignKey | → `inventory.Product`, on_delete=SET_NULL, optional |
| `product_name` | CharField | max_length=255, optional |
| `product_sku` | CharField | max_length=100, optional |
| `quantity` | PositiveIntegerField |  |
| `unit_price` | DecimalField |  |
| `tax_rate` | DecimalField |  |
| `refund_amount` | DecimalField |  |
| `condition` | CharField | max_length=20, choices: new, good, damaged, defective |
| `restock` | BooleanField |  |
| `notes` | TextField | optional |

### `StoreCredit`

Store credit issued via returns or manually.

| Field | Type | Details |
|-------|------|---------|
| `code` | CharField | max_length=20 |
| `customer` | ForeignKey | → `customers.Customer`, on_delete=SET_NULL, optional |
| `customer_name` | CharField | max_length=200, optional |
| `customer_email` | EmailField | max_length=254, optional |
| `customer_phone` | CharField | max_length=20, optional |
| `original_amount` | DecimalField |  |
| `current_amount` | DecimalField |  |
| `return_obj` | OneToOneField | → `returns.Return`, on_delete=SET_NULL, optional |
| `expires_at` | DateTimeField | optional |
| `is_active` | BooleanField |  |
| `notes` | TextField | optional |

**Methods:**

- `generate_code()`
- `add_credit()`
- `deduct_credit()`
- `is_expired()`

**Properties:**

- `is_valid`

## Cross-Module Relationships

| From | Field | To | on_delete | Nullable |
|------|-------|----|-----------|----------|
| `Return` | `original_sale` | `sales.Sale` | SET_NULL | Yes |
| `Return` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `Return` | `employee` | `accounts.LocalUser` | SET_NULL | Yes |
| `Return` | `reason` | `returns.ReturnReason` | SET_NULL | Yes |
| `Return` | `approved_by` | `accounts.LocalUser` | SET_NULL | Yes |
| `ReturnItem` | `return_obj` | `returns.Return` | CASCADE | No |
| `ReturnItem` | `sale_item` | `sales.SaleItem` | SET_NULL | Yes |
| `ReturnItem` | `product` | `inventory.Product` | SET_NULL | Yes |
| `StoreCredit` | `customer` | `customers.Customer` | SET_NULL | Yes |
| `StoreCredit` | `return_obj` | `returns.Return` | SET_NULL | Yes |

## URL Endpoints

Base path: `/m/returns/`

| Path | Name | Method |
|------|------|--------|
| `(root)` | `index` | GET |
| `returns/` | `returns` | GET |
| `list/` | `return_list` | GET |
| `add/` | `return_add` | GET/POST |
| `<uuid:return_id>/` | `return_detail` | GET |
| `<uuid:return_id>/edit/` | `return_edit` | GET |
| `<uuid:return_id>/delete/` | `return_delete` | GET/POST |
| `<uuid:return_id>/approve/` | `return_approve` | GET |
| `<uuid:return_id>/reject/` | `return_reject` | GET |
| `<uuid:return_id>/complete/` | `return_complete` | GET |
| `<uuid:return_id>/items/add/` | `item_add` | GET/POST |
| `<uuid:return_id>/items/<uuid:item_id>/delete/` | `item_delete` | GET/POST |
| `reasons/` | `reasons` | GET |
| `reasons/add/` | `reason_add` | GET/POST |
| `reasons/<uuid:reason_id>/edit/` | `reason_edit` | GET |
| `reasons/<uuid:reason_id>/delete/` | `reason_delete` | GET/POST |
| `credits/` | `credits` | GET |
| `credits/add/` | `credit_add` | GET/POST |
| `credits/lookup/` | `credit_lookup` | GET |
| `refunds/` | `refunds` | GET |
| `settings/` | `settings` | GET |

## Permissions

| Permission | Description |
|------------|-------------|

**Role assignments:**

- **admin**: All permissions
- **manager**: `view_return`, `add_return`, `change_return`, `approve_return`, `view_reason`, `add_reason`, `change_reason`, `view_credit` (+3 more)
- **employee**: `view_return`, `add_return`, `view_reason`, `view_credit`, `use_credit`

## Navigation

| View | Icon | ID | Fullpage |
|------|------|----|----------|
| Dashboard | `home-outline` | `dashboard` | No |
| Returns | `return-down-back-outline` | `returns` | No |
| Credits | `card-outline` | `credits` | No |
| Settings | `settings-outline` | `settings` | No |

## AI Tools

Tools available for the AI assistant:

### `list_returns`

List product returns with status filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | string | No | Filter: pending, approved, rejected, completed, cancelled |
| `limit` | integer | No |  |

### `list_return_reasons`

List configured return reasons.

### `create_return_reason`

Create a return reason (e.g., 'Defectuoso', 'Talla incorrecta').

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes |  |
| `description` | string | No |  |
| `restocks_inventory` | boolean | No | Auto-restock when returned |
| `requires_note` | boolean | No |  |

### `list_store_credits`

List store credits with optional customer filter.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customer_id` | string | No |  |
| `is_active` | boolean | No |  |

## File Structure

```
CHANGELOG.md
README.md
TODO.md
__init__.py
admin.py
ai_tools.py
apps.py
forms.py
locale/
  en/
    LC_MESSAGES/
      django.po
  es/
    LC_MESSAGES/
      django.po
migrations/
  0001_initial.py
  __init__.py
models.py
module.py
static/
  icons/
    ion/
templates/
  returns/
    pages/
      credit_detail.html
      credit_form.html
      credits.html
      index.html
      reason_form.html
      reasons.html
      return_detail.html
      return_form.html
      return_list.html
      settings.html
    partials/
      credit_detail.html
      credit_form.html
      credit_list.html
      dashboard_content.html
      reason_form.html
      reason_list.html
      return_detail.html
      return_form.html
      return_list.html
      settings.html
tests/
  __init__.py
  test_models.py
  test_views.py
urls.py
views.py
```
