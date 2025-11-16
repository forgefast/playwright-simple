#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interaction mixins for SimpleTestBase.

Divided into modules by interaction type for better maintainability.
"""

from .base import BaseInteractionMixin
from .click_interactions import ClickInteractionMixin
from .keyboard_interactions import KeyboardInteractionMixin
from .mouse_interactions import MouseInteractionMixin
from .form_interactions import FormInteractionMixin

__all__ = [
    'InteractionMixin',
    'BaseInteractionMixin',
    'ClickInteractionMixin',
    'KeyboardInteractionMixin',
    'MouseInteractionMixin',
    'FormInteractionMixin',
]


class InteractionMixin(
    ClickInteractionMixin,
    KeyboardInteractionMixin,
    MouseInteractionMixin,
    FormInteractionMixin
):
    """
    Main interaction mixin combining all interaction types.
    
    This class combines all interaction mixins for backward compatibility.
    Individual mixins can be used separately if needed.
    """
    pass

