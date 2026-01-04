# Returns Module

Return and refund management for POS including exchanges, credits, and partial returns.

## Features

- Return processing
- Full and partial refunds
- Exchange handling
- Store credit issuance
- Return reason tracking
- Integration with Sales and Inventory modules

## Installation

This module is installed automatically when activated in ERPlora Hub.

### Dependencies

- ERPlora Hub >= 1.0.0
- Required: `sales` >= 1.0.0
- Required: `inventory` >= 1.0.0

## Configuration

Access module settings at `/m/returns/settings/`.

### Available Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `return_window_days` | integer | `30` | Days allowed for returns |
| `require_receipt` | boolean | `true` | Require original receipt |
| `allow_no_receipt` | boolean | `false` | Allow returns without receipt |
| `restock_automatically` | boolean | `true` | Auto-restock returned items |

## Usage

### Views

| View | URL | Description |
|------|-----|-------------|
| Returns | `/m/returns/` | Return list |
| Process | `/m/returns/process/` | Process new return |
| Credits | `/m/returns/credits/` | Store credits |
| Settings | `/m/returns/settings/` | Module configuration |

### Return Types

- **Full Refund**: Complete order refund
- **Partial Refund**: Specific items only
- **Exchange**: Swap for different product
- **Store Credit**: Issue credit for future use

## Permissions

| Permission | Description |
|------------|-------------|
| `returns.view_return` | View returns |
| `returns.process_return` | Process returns |
| `returns.approve_return` | Approve returns |
| `returns.issue_credit` | Issue store credits |
| `returns.void_return` | Void returns |

## Module Icon

Location: `static/icons/icon.svg`

Icon source: [React Icons - Ionicons 5](https://react-icons.github.io/react-icons/icons/io5/)

---

**Version:** 1.0.0
**Category:** pos
**Author:** ERPlora Team
