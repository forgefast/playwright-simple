#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form methods for SimpleTestBase.

Contains methods for filling forms, finding fields by labels, and form interactions.
"""

import asyncio
import logging
from typing import Dict, Optional
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from .cursor import CursorManager
from .screenshot import ScreenshotManager
from .selectors import SelectorManager
from .config import TestConfig
from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class FormsMixin:
    """
    Mixin providing form methods for test base classes.
    
    This mixin provides methods for filling forms, finding fields by labels,
    and form interactions. It assumes the base class has:
    - page: Playwright Page instance
    - cursor_manager: CursorManager instance
    - screenshot_manager: ScreenshotManager instance
    - selector_manager: SelectorManager instance
    - config: TestConfig instance
    - _ensure_cursor: Method to ensure cursor is injected
    - type: Method to type text into a field
    """
    
    async def _ensure_cursor(self) -> None:
        """
        Ensure cursor is injected.
        
        Must be implemented by base class.
        
        Raises:
            NotImplementedError: If not implemented by base class
        """
        raise NotImplementedError("_ensure_cursor must be implemented by base class")
    
    async def type(
        self,
        selector: str,
        text: str,
        description: str = ""
    ) -> 'FormsMixin':
        """
        Type text into a field.
        
        Must be implemented by base class (usually InteractionMixin).
        
        Raises:
            NotImplementedError: If not implemented by base class
        """
        raise NotImplementedError("type must be implemented by base class")
    
    async def fill_form(self, fields: Dict[str, str]) -> 'FormsMixin':
        """
        Fill a form with multiple fields.
        
        Fills multiple form fields in sequence. Each field is filled using
        the type() method with a small delay between fields.
        
        Args:
            fields: Dictionary mapping CSS selectors to values
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If fields dictionary is empty
            ElementNotFoundError: If any field is not found
            
        Example:
            ```python
            await test.fill_form({
                'input[name="name"]': "John",
                'input[name="email"]': "john@example.com",
            })
            ```
        """
        if not fields:
            raise ValueError("fields dictionary cannot be empty")
        
        try:
            for selector, value in fields.items():
                if not selector:
                    logger.warning("Skipping empty selector in fill_form")
                    continue
                
                await self.type(selector, str(value), f"Form field: {selector}")
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to fill form with {len(fields)} fields: {e}")
            raise
        
        return self
    
    async def fill_by_label(
        self,
        label: str,
        value: str,
        context: Optional[str] = None
    ) -> 'FormsMixin':
        """
        Fill a field by its visible label (generic web application support).
        
        Args:
            label: Visible label text (e.g., "Email", "Name", "Password")
            value: Value to fill
            context: Optional context to narrow search (e.g., "Section Name")
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If field not found or multiple fields found without context
            
        Example:
            ```python
            await test.fill_by_label("Email", "user@example.com")
            await test.fill_by_label("Name", "John", context="Personal Info")
            ```
        """
        await self._ensure_cursor()
        
        label_normalized = label.strip()
        
        # Build selectors to find label
        label_selectors = [
            f'label:has-text("{label_normalized}")',
            f'label:has-text("{label_normalized}"):visible',
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
                        parent_text = await label_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('fieldset, section, .form-group, .field-group');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find associated field
                    field_name = await label_elem.get_attribute("for")
                    
                    if field_name:
                        # Find input/field by name
                        field_selectors = [
                            f'input[name="{field_name}"]',
                            f'textarea[name="{field_name}"]',
                            f'select[name="{field_name}"]',
                            f'[name="{field_name}"]',
                        ]
                    else:
                        # Try to find field near the label
                        field_selectors = [
                            'input',
                            'textarea',
                            'select',
                        ]
                    
                    # Find field
                    for field_sel in field_selectors:
                        try:
                            if field_name:
                                field = self.page.locator(field_sel).first
                            else:
                                # Find field near label (next sibling or in same container)
                                field = label_elem.locator('xpath=following::*[self::input or self::textarea or self::select][1]')
                            
                            if await field.count() > 0 and await field.is_visible():
                                found_fields.append(field)
                                break
                        except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                            logger.debug(f"Field selector '{field_sel}' failed: {e}")
                            continue
                        except Exception as e:
                            logger.warning(f"Unexpected error with field selector '{field_sel}': {e}")
                            continue
            except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                logger.debug(f"Label selector '{label_sel}' failed: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error with label selector '{label_sel}': {e}")
                continue
        
        if not found_fields:
            raise ValueError(
                f"Campo com label '{label}' não encontrado. "
                f"Verifique se o label está correto e visível na tela."
            )
        
        if len(found_fields) > 1 and not context:
            raise ValueError(
                f"Múltiplos campos '{label}' encontrados. "
                f"Use context para especificar (ex: context='Seção Nome'). "
                f"Campos encontrados: {len(found_fields)}"
            )
        
        try:
            # Fill the first matching field
            field = found_fields[0]
            
            # Check if it's a select dropdown
            tag_name = await field.evaluate("(el) => el.tagName.toLowerCase()")
            if tag_name == "select":
                await field.select_option(label=value)
            else:
                await field.fill(str(value))
            
            await asyncio.sleep(0.2)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("fill_by_label", label)
        except Exception as e:
            logger.error(f"Failed to fill field with label '{label}': {e}")
            raise ValueError(f"Failed to fill field '{label}': {e}") from e
        
        return self
    
    async def select_by_label(
        self,
        label: str,
        option: str,
        context: Optional[str] = None
    ) -> 'FormsMixin':
        """
        Select an option in a dropdown by its visible label.
        
        Args:
            label: Visible label text
            option: Option text or value to select
            context: Optional context to narrow search
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.select_by_label("Country", "Brazil")
            ```
        """
        await self._ensure_cursor()
        
        label_normalized = label.strip()
        
        # Find label
        label_selectors = [
            f'label:has-text("{label_normalized}")',
            f'label:has-text("{label_normalized}"):visible',
            f'[for*="{label_normalized.lower()}"]',
        ]
        
        field = None
        for label_sel in label_selectors:
            try:
                label_elem = self.page.locator(label_sel).first
                if await label_elem.count() > 0 and await label_elem.is_visible():
                    # Check context if provided
                    if context:
                        parent_text = await label_elem.evaluate("""
                            (el) => {
                                let parent = el.closest('fieldset, section, .form-group');
                                return parent ? parent.textContent : '';
                            }
                        """)
                        if context.lower() not in parent_text.lower():
                            continue
                    
                    # Find associated select
                    field_name = await label_elem.get_attribute("for")
                    if field_name:
                        field = self.page.locator(f'select[name="{field_name}"]').first
                    else:
                        field = label_elem.locator('xpath=following::select[1]')
                    
                    if await field.count() > 0:
                        break
            except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                logger.debug(f"Field selector failed: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error with field selector: {e}")
                continue
        
        if not field or await field.count() == 0:
            raise ValueError(f"Dropdown com label '{label}' não encontrado.")
        
        try:
            await field.select_option(label=option)
            await asyncio.sleep(0.2)
            
            if self.config.screenshots.auto:
                await self.screenshot_manager.capture_on_action("select_by_label", label)
        except Exception as e:
            logger.error(f"Failed to select option '{option}' in dropdown '{label}': {e}")
            raise ValueError(
                f"Failed to select option '{option}' in dropdown '{label}': {e}"
            ) from e
        
        return self

