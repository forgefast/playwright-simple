#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo extra for playwright-simple.

Provides OdooTestBase and helpers for testing Odoo applications.
"""

try:
    from .base import OdooTestBase
    from .version_detector import detect_version, detect_edition, get_version_info
    from .menus import MenuNavigator
    from .fields import FieldHelper
    from .views import ViewHelper
    from .wizards import WizardHelper
    from .workflows import WorkflowHelper
    from .yaml_parser import OdooYAMLParser
    
    __all__ = [
        "OdooTestBase",
        "detect_version",
        "detect_edition",
        "get_version_info",
        "MenuNavigator",
        "FieldHelper",
        "ViewHelper",
        "WizardHelper",
        "WorkflowHelper",
        "OdooYAMLParser",
    ]
except ImportError as e:
    # If core modules are not available, provide helpful error
    import sys
    raise ImportError(
        "Odoo extra requires playwright-simple core. "
        "Install with: pip install playwright-simple[odoo]"
    ) from e

