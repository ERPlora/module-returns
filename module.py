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
MODULE_CATEGORY = "operations"

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
DEPENDENCIES = ["sales>=1.0.0"]

# Default Settings
SETTINGS = {
    "allow_no_receipt_returns": False,
    "default_return_window_days": 30,
    "store_credit_expiry_days": 365,
}

# Permissions
PERMISSIONS = [
    "returns.view_return",
    "returns.add_return",
    "returns.change_return",
    "returns.delete_return",
    "returns.view_returnreason",
    "returns.add_returnreason",
    "returns.change_returnreason",
    "returns.delete_returnreason",
    "returns.view_storecredit",
    "returns.add_storecredit",
    "returns.change_storecredit",
]
