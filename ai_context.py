"""
AI context for the Returns module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Returns

### Models

**ReturnsSettings** — Per-hub configuration (singleton per hub).
- `allow_returns`, `return_window_days` (default 30)
- `allow_store_credit`, `require_receipt`, `auto_restore_stock`
- Use `ReturnsSettings.get_settings(hub_id)`

**ReturnReason** — Predefined return reasons.
- `name`, `description`
- `restocks_inventory` (bool): Whether this reason puts items back in stock
- `requires_note` (bool): Forces staff to enter a note
- `sort_order`, `is_active`

**Return** — A product return transaction (number format: RET-YYYYMMDD-NNNN).
- `number` (auto-generated)
- `original_sale` FK → sales.Sale
- `customer` FK → customers.Customer
- `employee` FK → accounts.LocalUser (who processed it)
- `reason` FK → ReturnReason
- `reason_notes`
- `status`: 'pending' | 'approved' | 'rejected' | 'completed' | 'cancelled'
- `subtotal`, `tax_amount`, `total_refund`
- `refund_method`: 'original' | 'cash' | 'store_credit'
- `notes`
- `approved_by` FK → accounts.LocalUser, `approved_at`
- `completed_at`
- Methods: `approve(approved_by)`, `reject()`, `complete()`, `cancel()`, `recalculate_total()`

**ReturnItem** — Individual item within a return.
- `return_obj` FK → Return (related_name='items')
- `sale_item` FK → sales.SaleItem (original line item)
- `product` FK → inventory.Product
- `product_name`, `product_sku`: Snapshot fields
- `quantity` (min 1), `unit_price`, `tax_rate` (default 21%), `refund_amount`
- `condition`: 'new' | 'good' | 'damaged' | 'defective'
- `restock` (bool): Whether to return to inventory
- `notes`

**StoreCredit** — Store credit issued via returns or manually.
- `code` (unique, format: SC-{8 hex chars})
- `customer` FK → customers.Customer
- `customer_name`, `customer_email`, `customer_phone`: Fallback snapshots
- `original_amount`, `current_amount`
- `return_obj` OneToOne → Return (optional)
- `expires_at`, `is_active`
- Methods: `add_credit(amount)`, `deduct_credit(amount)`, `is_expired()`, property `is_valid`

### Key Flows

1. **Create return**: Create Return (status='pending') → add ReturnItems (refund_amount auto-calculated) → `return_obj.recalculate_total()`
2. **Approve**: `return_obj.approve(user)` → status='approved'
3. **Complete**: `return_obj.complete()` → status='completed'; if `auto_restore_stock` and item's `restock=True`, inventory is restored externally
4. **Issue store credit**: When `refund_method='store_credit'`, create StoreCredit linked to the return with `original_amount = total_refund`
5. **Apply store credit**: Look up by code, verify `is_valid`, call `deduct_credit(amount)`

### Relationships
- `Return.original_sale` → sales.Sale
- `Return.customer` → customers.Customer
- `ReturnItem.product` → inventory.Product
- `ReturnItem.sale_item` → sales.SaleItem
- `StoreCredit.customer` → customers.Customer
"""
