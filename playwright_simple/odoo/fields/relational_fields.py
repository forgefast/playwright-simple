#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Relational field types for Odoo (many2one, many2many, one2many).
"""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import Page, Locator


class RelationalFieldsHandler:
    """Handler for relational Odoo field types."""
    
    def __init__(self, page: Page):
        """Initialize relational fields handler."""
        self.page = page
    
    async def fill_many2one(
        self,
        field_locator: Locator,
        search_text: str,
        position: Optional[str] = None
    ) -> bool:
        """Fill Many2one field using locator."""
        try:
            await field_locator.fill(search_text)
            await asyncio.sleep(0.05)
            
            # Determine position index
            position_index = 0
            if position:
                position_lower = position.lower()
                if position_lower in ['primeiro', 'first', '1']:
                    position_index = 0
                elif position_lower in ['segundo', 'second', '2']:
                    position_index = 1
                elif position_lower in ['último', 'last']:
                    # Will handle separately
                    position_index = -1
                else:
                    try:
                        position_index = int(position) - 1
                    except ValueError:
                        position_index = 0
            
            # Click autocomplete option
            autocomplete_selectors = [
                '.ui-autocomplete li',
                '.o_m2o_dropdown_option',
                '.ui-menu-item',
            ]
            
            for autocomplete_sel in autocomplete_selectors:
                try:
                    options = self.page.locator(autocomplete_sel)
                    count = await options.count()
                    
                    if count > 0:
                        if position_index == -1:
                            # Last option
                            option = options.nth(count - 1)
                        else:
                            # Specific position
                            option = options.nth(position_index)
                        
                        if await option.count() > 0:
                            await option.click()
                            await asyncio.sleep(0.02)
                            return True
                except Exception:
                    continue
            
            return False
        except Exception:
            return False
    
    async def fill_many2many(self, field_name: str, values: List[str]) -> bool:
        """Fill a Many2many field (tags)."""
        # Many2many fields use tags
        for value in values:
            try:
                # Click to add tag
                add_sel = f'.o_field_many2many_tags[name="{field_name}"] .o_field_many2many_tags_input'
                add_input = self.page.locator(add_sel).first
                if await add_input.count() > 0:
                    await add_input.fill(value)
                    await asyncio.sleep(0.05)
                    # Press Enter or click suggestion
                    await self.page.keyboard.press("Enter")
                    await asyncio.sleep(0.02)
            except Exception:
                continue
        
        return True
    
    async def fill_one2many(self, field_name: str, records: List[Dict[str, Any]], field_helper) -> bool:
        """Fill a One2many field (add multiple records)."""
        for record in records:
            # Click add button
            add_selectors = [
                f'.o_field_one2many[name="{field_name}"] .o_field_x2many_list_row_add a',
                f'.o_field_one2many[name="{field_name}"] a:has-text("Adicionar")',
            ]
            
            for selector in add_selectors:
                try:
                    add_btn = self.page.locator(selector).first
                    if await add_btn.count() > 0:
                        await add_btn.click()
                        await asyncio.sleep(0.05)
                        break
                except Exception:
                    continue
            
            # Fill fields in the new record
            for field_name_inner, field_value in record.items():
                if isinstance(field_value, dict) and 'type' in field_value:
                    # Handle special field types
                    field_type = field_value['type']
                    value = field_value['value']
                    
                    if field_type == 'many2one':
                        await field_helper.fill_many2one(field_name_inner, value)
                    elif field_type == 'char':
                        await field_helper.fill_char(field_name_inner, value)
                    elif field_type == 'integer':
                        await field_helper.fill_integer(field_name_inner, value)
                    elif field_type == 'float':
                        await field_helper.fill_float(field_name_inner, value)
                    elif field_type == 'boolean':
                        await field_helper.toggle_boolean(field_name_inner)
                else:
                    # Default to char
                    await field_helper.fill_char(field_name_inner, str(field_value))
            
            await asyncio.sleep(0.02)
        
        return True

