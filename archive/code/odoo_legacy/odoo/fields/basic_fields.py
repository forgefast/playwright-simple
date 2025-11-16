#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic field types for Odoo (char, integer, float, date, datetime, boolean).
"""

import asyncio
from typing import Union
from datetime import datetime, date
from playwright.async_api import Locator


class BasicFieldsHandler:
    """Handler for basic Odoo field types."""
    
    async def fill_char(self, field_locator: Locator, value: str) -> bool:
        """Fill Char field using locator."""
        try:
            await field_locator.fill(value)
            await asyncio.sleep(0.02)
            return True
        except Exception:
            return False
    
    async def fill_integer(self, field_locator: Locator, value: Union[int, str]) -> bool:
        """Fill Integer field using locator."""
        return await self.fill_char(field_locator, str(value))
    
    async def fill_float(self, field_locator: Locator, value: Union[float, str]) -> bool:
        """Fill Float field using locator."""
        return await self.fill_char(field_locator, str(value))
    
    async def fill_date(self, field_locator: Locator, date_value: Union[date, str]) -> bool:
        """Fill Date field using locator."""
        if isinstance(date_value, date):
            date_str = date_value.strftime("%Y-%m-%d")
        else:
            date_str = str(date_value)
        return await self.fill_char(field_locator, date_str)
    
    async def fill_datetime(self, field_locator: Locator, datetime_value: Union[datetime, str]) -> bool:
        """Fill Datetime field using locator."""
        if isinstance(datetime_value, datetime):
            dt_str = datetime_value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt_str = str(datetime_value)
        return await self.fill_char(field_locator, dt_str)
    
    async def toggle_boolean(self, field_locator: Locator) -> bool:
        """Toggle Boolean field using locator."""
        try:
            await field_locator.click()
            await asyncio.sleep(0.02)
            return True
        except Exception:
            return False

