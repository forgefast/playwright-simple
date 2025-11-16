#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form interaction methods.

Handles select, form filling.
"""

import asyncio
import logging
from typing import Optional

from .base import BaseInteractionMixin
from ..constants import ACTION_DELAY
from ..logger import get_logger

logger = logging.getLogger(__name__)
structured_logger = get_logger()


class FormInteractionMixin(BaseInteractionMixin):
    """Mixin providing form-related interaction methods."""
    
    async def select(self, selector: str, option: str, description: str = "") -> 'FormInteractionMixin':
        """
        Select an option from a dropdown.
        
        Args:
            selector: Selector for the select element
            option: Option value or label to select
            description: Optional description
        """
        if self._helpers is None:
            raise RuntimeError("_helpers not initialized")
        
        element, x, y = await self._helpers.prepare_element_interaction(selector, description)
        await element.select_option(option)
        await asyncio.sleep(ACTION_DELAY * 2)
        structured_logger.action(
            f"Opção selecionada: '{option}' em '{selector}'",
            action="select", selector=selector, option=option
        )
        return self

