#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ForgeERP extension for playwright-simple.

Provides specialized functionality for testing ForgeERP applications
with HTMX, Tailwind CSS, and Alpine.js.
"""

from .base import ForgeERPTestBase
from .yaml_parser import ForgeERPYAMLParser

__all__ = [
    "ForgeERPTestBase",
    "ForgeERPYAMLParser",
]

