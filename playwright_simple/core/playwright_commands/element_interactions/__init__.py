#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element Interactions Package.

Refactored from element_interactions.py to improve maintainability.
"""

from .element_interactions import ElementInteractions
from .click_handler import ClickHandler
from .type_handler import TypeHandler
from .focus_helper import FocusHelper

__all__ = [
    'ElementInteractions',
    'ClickHandler',
    'TypeHandler',
    'FocusHelper',
]

