"""
Returns Module Configuration

This file defines the module metadata and navigation for the Returns module.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "returns"
MODULE_NAME = _("Returns")
MODULE_ICON = "arrow-undo-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "sales"  # Changed from "operations" to valid category

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "retail",    # Retail stores
    "wholesale", # Wholesale distributors
    "ecommerce", # E-commerce
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Returns"),
    "icon": "arrow-undo-outline",
    "order": 25,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Dashboard"),
        "icon": "home-outline",
        "view": "",
    },
    {
        "id": "returns",
        "label": _("Returns"),
        "icon": "return-down-back-outline",
        "view": "returns",
    },
    {
        "id": "credits",
        "label": _("Credits"),
        "icon": "card-outline",
        "view": "credits",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = ['sales', 'customers', 'inventory']

# Default Settings
SETTINGS = {
    "allow_no_receipt_returns": False,
    "default_return_window_days": 30,
    "store_credit_expiry_days": 365,
}

# Permissions
# Format: (action_suffix, display_name) -> becomes "returns.action_suffix"
PERMISSIONS = [
    ("view_return", _("Can view returns")),
    ("add_return", _("Can create returns")),
    ("change_return", _("Can edit returns")),
    ("delete_return", _("Can delete returns")),
    ("approve_return", _("Can approve returns")),
    ("view_reason", _("Can view return reasons")),
    ("add_reason", _("Can add return reasons")),
    ("change_reason", _("Can edit return reasons")),
    ("delete_reason", _("Can delete return reasons")),
    ("view_credit", _("Can view store credits")),
    ("add_credit", _("Can add store credits")),
    ("change_credit", _("Can edit store credits")),
    ("use_credit", _("Can use store credits")),
    ("manage_settings", _("Can manage returns settings")),
]

# Role Permissions - Default permissions for each system role in this module
# Keys are role names, values are lists of permission suffixes (without module prefix)
# Use ["*"] to grant all permissions in this module
ROLE_PERMISSIONS = {
    "admin": ["*"],  # Full access to all returns permissions
    "manager": [
        "view_return",
        "add_return",
        "change_return",
        "approve_return",
        "view_reason",
        "add_reason",
        "change_reason",
        "view_credit",
        "add_credit",
        "change_credit",
        "use_credit",
    ],
    "employee": [
        "view_return",
        "add_return",
        "view_reason",
        "view_credit",
        "use_credit",
    ],
}
