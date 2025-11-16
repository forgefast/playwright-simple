#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo-specific actions module.

Contains very specific Odoo interactions that are too specific to be in general modules.
"""

from .logo import LogoNavigator
from .filters import FilterHelper

__all__ = ['LogoNavigator', 'FilterHelper']

