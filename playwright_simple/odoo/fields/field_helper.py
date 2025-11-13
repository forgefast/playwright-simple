#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main FieldHelper class that composes specialized field handlers.
"""

import asyncio
import re
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime, date
from playwright.async_api import Page, Locator

from ..selectors import get_field_selectors, get_selector_list
from ..version_detector import detect_version
from .basic_fields import BasicFieldsHandler
from .relational_fields import RelationalFieldsHandler
from .special_fields import SpecialFieldsHandler


class FieldHelper:
    """Helper class for interacting with Odoo fields."""
    
    def __init__(self, page: Page, version: Optional[str] = None):
        """
        Initialize field helper.
        
        Args:
            page: Playwright page instance
            version: Odoo version (auto-detected if None)
        """
        self.page = page
        self._version = version
        
        # Initialize specialized handlers
        self.basic = BasicFieldsHandler()
        self.relational = RelationalFieldsHandler(page)
        self.special = SpecialFieldsHandler(page)
    
    async def _get_version(self) -> str:
        """Get Odoo version (cached)."""
        if not self._version:
            self._version = await detect_version(self.page) or "18.0"
        return self._version
    
    async def find_field_by_label(
        self, 
        label: str, 
        context: Optional[str] = None
    ) -> Tuple[Optional[Locator], Optional[str], Optional[str]]:
        """
        Find a field by its visible label.
        
        Args:
            label: Visible label text (e.g., "Cliente", "Data", "Quantidade")
            context: Optional context to narrow search (e.g., "Seção Cliente", "Wizard")
            
        Returns:
            Tuple of (field_locator, field_name, field_type) or (None, None, None) if not found
            
        Raises:
            ValueError: If multiple fields found with same label and no context provided
        """
        # Normalize label (remove extra spaces, handle case)
        label_normalized = label.strip()
        
        # Build selectors to find label
        label_selectors = [
            f'label:has-text("{label_normalized}")',
            f'label:has-text("{label_normalized}"):visible',
            f'.o_field_label:has-text("{label_normalized}")',
            f'.o_label:has-text("{label_normalized}")',
            f'[for*="{label_normalized.lower()}"]',
            f'text="{label_normalized}"',
        ]
        
        found_fields = []
        
        for label_sel in label_selectors:
            try:
                labels = self.page.locator(label_sel)
                count = await labels.count()
                
                for i in range(count):
                    label_elem = labels.nth(i)
                    if not await label_elem.is_visible():
                        continue
                    
                    # Check context if provided
                    if context:
                        # Look for context in parent elements (sections, groups, etc.)
                        parent_text = await label_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('.o_group, .o_notebook_page, .o_fieldset, .o_sheet');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find associated field
                    # Try to get field name from 'for' attribute
                    field_name = await label_elem.get_attribute("for")
                    
                    if field_name:
                        # Find input/field by name
                        field_selectors = [
                            f'input[name="{field_name}"]',
                            f'textarea[name="{field_name}"]',
                            f'select[name="{field_name}"]',
                            f'[name="{field_name}"]',
                            f'.o_field_widget[name="{field_name}"]',
                        ]
                    else:
                        # Try to find field near the label
                        field_selectors = [
                            'input',
                            'textarea',
                            'select',
                            '.o_field_widget input',
                            '.o_field_widget textarea',
                            '.o_field_widget select',
                        ]
                    
                    # Find field in same row/group as label
                    for field_sel in field_selectors:
                        try:
                            if field_name:
                                field = self.page.locator(field_sel).first
                            else:
                                # Find field near label (next sibling or in same container)
                                field = label_elem.locator(f'xpath=following::*[self::input or self::textarea or self::select][1]')
                            
                            if await field.count() > 0 and await field.is_visible():
                                # Detect field type
                                field_type = await self._detect_field_type(field)
                                
                                # Get actual field name
                                actual_name = await field.get_attribute("name") or field_name
                                
                                found_fields.append((field, actual_name, field_type))
                                break
                        except Exception:
                            continue
            except Exception:
                continue
        
        # If no fields found, try alternative approach: search by text content
        if not found_fields:
            # Try to find fields by searching for label text in the page
            # and then finding nearby input fields
            try:
                text_matches = self.page.locator(f'text={label_normalized}').filter(has_text=re.compile(label_normalized, re.I))
                count = await text_matches.count()
                
                for i in range(count):
                    text_elem = text_matches.nth(i)
                    if not await text_elem.is_visible():
                        continue
                    
                    # Check context if provided
                    if context:
                        parent_text = await text_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('.o_group, .o_notebook_page, .o_fieldset, .o_sheet');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find nearby field
                    field = text_elem.locator('xpath=following::input[1] | following::textarea[1] | following::select[1]')
                    if await field.count() > 0:
                        field_type = await self._detect_field_type(field)
                        field_name_attr = await field.get_attribute("name")
                        found_fields.append((field, field_name_attr, field_type))
            except Exception:
                pass
        
        if not found_fields:
            return (None, None, None)
        
        if len(found_fields) > 1 and not context:
            # Multiple fields found, need context
            raise ValueError(
                f"Múltiplos campos '{label}' encontrados. "
                f"Use context para especificar (ex: context='Seção Cliente'). "
                f"Campos encontrados: {len(found_fields)}"
            )
        
        # Return first match (or the one matching context)
        return found_fields[0]
    
    async def _detect_field_type(self, field: Locator) -> str:
        """
        Detect the type of an Odoo field by analyzing its HTML structure.
        
        Args:
            field: Field locator
            
        Returns:
            Field type string ('many2one', 'char', 'integer', 'float', 'date', 'boolean', 'html', etc.)
        """
        try:
            # Check class names
            class_name = await field.evaluate("(el) => el.className || ''")
            
            # Check parent classes
            parent_class = await field.evaluate("""
                (el) => {
                    let parent = el.closest('.o_field_widget, .o_input');
                    return parent ? parent.className || '' : '';
                }
            """)
            
            all_classes = f"{class_name} {parent_class}".lower()
            
            # Detect by class patterns
            if 'many2one' in all_classes or 'o_field_many2one' in all_classes:
                return 'many2one'
            elif 'many2many' in all_classes or 'o_field_many2many' in all_classes:
                return 'many2many'
            elif 'one2many' in all_classes or 'o_field_one2many' in all_classes:
                return 'one2many'
            elif 'boolean' in all_classes or 'o_field_boolean' in all_classes:
                return 'boolean'
            elif 'html' in all_classes or 'o_field_html' in all_classes:
                return 'html'
            elif 'date' in all_classes or 'o_field_date' in all_classes:
                return 'date'
            elif 'datetime' in all_classes or 'o_field_datetime' in all_classes:
                return 'datetime'
            elif 'selection' in all_classes or 'o_field_selection' in all_classes:
                return 'selection'
            
            # Detect by input type
            input_type = await field.get_attribute("type")
            if input_type == "checkbox":
                return 'boolean'
            elif input_type == "date":
                return 'date'
            elif input_type == "number":
                # Could be integer or float - check step attribute
                step = await field.get_attribute("step")
                if step and '.' in step:
                    return 'float'
                return 'integer'
            
            # Detect by tag name
            tag_name = await field.evaluate("(el) => el.tagName.toLowerCase()")
            if tag_name == "textarea":
                return 'text'
            elif tag_name == "select":
                return 'selection'
            
            # Default to char/text
            return 'char'
        except Exception:
            return 'char'
    
    async def fill_field(
        self,
        label: str,
        value: Any,
        context: Optional[str] = None
    ) -> bool:
        """
        Fill a field by its visible label. Automatically detects field type.
        
        Args:
            label: Visible label text (e.g., "Cliente", "Data", "Quantidade")
            value: Value to fill
            context: Optional context to narrow search (e.g., "Seção Cliente")
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If field not found or multiple fields found without context
        """
        # Find field by label
        field_locator, field_name, field_type = await self.find_field_by_label(label, context)
        
        if not field_locator:
            raise ValueError(f"Campo '{label}' não encontrado. Verifique se o label está correto e visível na tela.")
        
        # Fill based on field type using appropriate handler
        if field_type == 'many2one':
            return await self.relational.fill_many2one(field_locator, str(value))
        elif field_type == 'char' or field_type == 'text':
            return await self.basic.fill_char(field_locator, str(value))
        elif field_type == 'integer':
            return await self.basic.fill_integer(field_locator, int(value) if isinstance(value, str) else value)
        elif field_type == 'float':
            return await self.basic.fill_float(field_locator, float(value) if isinstance(value, str) else value)
        elif field_type == 'date':
            return await self.basic.fill_date(field_locator, value)
        elif field_type == 'datetime':
            return await self.basic.fill_datetime(field_locator, value)
        elif field_type == 'boolean':
            return await self.basic.toggle_boolean(field_locator)
        elif field_type == 'selection':
            return await self.special.select_dropdown(field_locator, str(value))
        elif field_type == 'html':
            return await self.special.fill_html(field_locator, str(value))
        else:
            # Default to char
            return await self.basic.fill_char(field_locator, str(value))
    
    async def fill_many2one(
        self, 
        field_name_or_label: str, 
        search_text: str, 
        position: Optional[str] = None,
        context: Optional[str] = None,
        description: str = ""
    ) -> bool:
        """
        Fill a Many2one field with autocomplete.
        
        Args:
            field_name_or_label: Field name (e.g., 'partner_id') or visible label (e.g., 'Cliente')
            search_text: Text to search for
            position: Position to select if multiple results ('primeiro', 'segundo', 'último', '1', '2', 'last')
            context: Optional context to narrow search if using label
            description: Description for logging (deprecated, kept for compatibility)
            
        Returns:
            True if successful
        """
        # Check if it's a label (contains spaces or doesn't look like field name) or field name
        is_label = ' ' in field_name_or_label or not field_name_or_label.endswith('_id')
        
        if is_label:
            # Find by label
            field_locator, _, _ = await self.find_field_by_label(field_name_or_label, context)
            if not field_locator:
                raise ValueError(f"Campo Many2one '{field_name_or_label}' não encontrado.")
            return await self.relational.fill_many2one(field_locator, search_text, position)
        else:
            # Use field name (old method)
            selectors = [
                f'input[name="{field_name_or_label}"]',
                f'.o_field_many2one[name="{field_name_or_label}"] input',
                f'.o_field_many2one input',
            ]
            
            for selector in selectors:
                try:
                    field = self.page.locator(selector).first
                    if await field.count() > 0:
                        return await self.relational.fill_many2one(field, search_text, position)
                except Exception:
                    continue
            
            return False
    
    # Convenience methods that delegate to handlers
    async def fill_char(self, field_name: str, value: str) -> bool:
        """Fill a Char/Text field."""
        selectors = [
            f'input[name="{field_name}"]',
            f'textarea[name="{field_name}"]',
            f'.o_field_char[name="{field_name}"] input',
        ]
        
        for selector in selectors:
            try:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    return await self.basic.fill_char(field, value)
            except Exception:
                continue
        
        return False
    
    async def fill_integer(self, field_name: str, value: Union[int, str]) -> bool:
        """Fill an Integer field."""
        return await self.fill_char(field_name, str(value))
    
    async def fill_float(self, field_name: str, value: Union[float, str]) -> bool:
        """Fill a Float field."""
        return await self.fill_char(field_name, str(value))
    
    async def fill_date(self, field_name: str, date_value: Union[date, str]) -> bool:
        """Fill a Date field."""
        if isinstance(date_value, date):
            date_str = date_value.strftime("%Y-%m-%d")
        else:
            date_str = str(date_value)
        return await self.fill_char(field_name, date_str)
    
    async def fill_datetime(self, field_name: str, datetime_value: Union[datetime, str]) -> bool:
        """Fill a Datetime field."""
        if isinstance(datetime_value, datetime):
            dt_str = datetime_value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            dt_str = str(datetime_value)
        return await self.fill_char(field_name, dt_str)
    
    async def select_dropdown(self, field_name: str, option: str) -> bool:
        """Select an option from a Selection dropdown."""
        selectors = [
            f'select[name="{field_name}"]',
            f'.o_field_selection[name="{field_name}"] select',
        ]
        
        for selector in selectors:
            try:
                field = self.page.locator(selector).first
                if await field.count() > 0:
                    return await self.special.select_dropdown(field, option)
            except Exception:
                continue
        
        return False
    
    async def toggle_boolean(self, field_name: str) -> bool:
        """Toggle a Boolean field."""
        selectors = [
            f'input[name="{field_name}"][type="checkbox"]',
            f'.o_field_boolean[name="{field_name}"] input',
        ]
        
        for selector in selectors:
            try:
                checkbox = self.page.locator(selector).first
                if await checkbox.count() > 0:
                    return await self.basic.toggle_boolean(checkbox)
            except Exception:
                continue
        
        return False
    
    async def fill_html(self, field_name: str, html: str) -> bool:
        """Fill an HTML field (uses iframe)."""
        # HTML fields in Odoo use iframes
        try:
            # Try to find the iframe
            iframe_selector = f'iframe[name*="{field_name}"]'
            iframe = self.page.frame_locator(iframe_selector).first
            
            # Try to find body in iframe
            body = iframe.locator('body')
            if await body.count() > 0:
                await body.fill(html)
                await asyncio.sleep(0.02)
                return True
        except Exception:
            pass
        
        return False
    
    async def fill_many2many(self, field_name: str, values: List[str]) -> bool:
        """Fill a Many2many field (tags)."""
        return await self.relational.fill_many2many(field_name, values)
    
    async def fill_one2many(self, field_name: str, records: List[Dict[str, Any]]) -> bool:
        """Fill a One2many field (add multiple records)."""
        return await self.relational.fill_one2many(field_name, records, self)

