#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo view interaction module.

Handles interaction with different Odoo views (List, Kanban, Form, etc.).
"""

import asyncio
from typing import Optional, List
from playwright.async_api import Page

from .selectors import get_view_selectors, get_button_selectors


class ViewHelper:
    """Helper class for interacting with Odoo views."""
    
    def __init__(self, page: Page):
        """Initialize view helper."""
        self.page = page
    
    async def switch_to_list_view(self) -> bool:
        """Switch to List view."""
        return await self._switch_view("list")
    
    async def switch_to_kanban_view(self) -> bool:
        """Switch to Kanban view."""
        return await self._switch_view("kanban")
    
    async def switch_to_form_view(self) -> bool:
        """Switch to Form view."""
        return await self._switch_view("form")
    
    async def switch_to_graph_view(self) -> bool:
        """Switch to Graph view."""
        return await self._switch_view("graph")
    
    async def switch_to_pivot_view(self) -> bool:
        """Switch to Pivot view."""
        return await self._switch_view("pivot")
    
    async def _switch_view(self, view_type: str) -> bool:
        """Switch to a specific view type."""
        selectors = [
            f'button[data-view-type="{view_type}"]',
            f'a[data-view-type="{view_type}"]',
            f'.o_view_controller button:has-text("{view_type.title()}")',
        ]
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(0.8)
                    return True
            except Exception:
                continue
        
        return False
    
    async def create_record(self) -> bool:
        """Click the Create button to create a new record."""
        button_sel = get_button_selectors().get("create", "")
        selectors = button_sel.split(", ") if button_sel else []
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0 and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def open_record(self, index: int = 0) -> bool:
        """Open a record from list/kanban view."""
        selectors = [
            f'tr.o_data_row:nth-child({index + 1})',
            f'.o_kanban_record:nth-child({index + 1})',
            f'tbody tr:nth-child({index + 1})',
        ]
        
        for selector in selectors:
            try:
                row = self.page.locator(selector).first
                if await row.count() > 0:
                    await row.click()
                    await asyncio.sleep(1)
                    return True
            except Exception:
                continue
        
        return False
    
    async def delete_record(self, index: int = 0) -> bool:
        """Delete a record."""
        # First open the record
        if not await self.open_record(index):
            return False
        
        # Click delete button
        button_sel = get_button_selectors().get("delete", "")
        selectors = button_sel.split(", ") if button_sel else []
        
        for selector in selectors:
            try:
                btn = self.page.locator(selector).first
                if await btn.count() > 0:
                    await btn.click()
                    await asyncio.sleep(0.5)
                    # Confirm deletion if dialog appears
                    await self.page.get_by_role("button", name="Ok").click()
                    await asyncio.sleep(0.5)
                    return True
            except Exception:
                continue
        
        return False
    
    async def search_records(self, search_text: str) -> List:
        """
        Search for records and return list of found records.
        
        Args:
            search_text: Text to search for
            
        Returns:
            List of record locators found
        """
        search_sel = 'input[placeholder*="Buscar"], .o_searchview_input, input[placeholder*="Search"]'
        try:
            search_input = self.page.locator(search_sel).first
            if await search_input.count() > 0:
                await search_input.fill(search_text)
                await asyncio.sleep(1)
                
                # Wait for results to appear
                await asyncio.sleep(0.5)
                
                # Find all result records
                record_selectors = [
                    'tr.o_data_row',
                    '.o_kanban_record',
                    'tbody tr',
                ]
                
                found_records = []
                for record_sel in record_selectors:
                    records = self.page.locator(record_sel)
                    count = await records.count()
                    if count > 0:
                        for i in range(count):
                            record = records.nth(i)
                            if await record.is_visible():
                                found_records.append(record)
                        break
                
                return found_records
        except Exception:
            pass
        
        return []
    
    async def find_and_open_record(
        self,
        search_text: str,
        position: Optional[str] = None
    ) -> bool:
        """
        Search for records by text and open one based on position.
        
        Args:
            search_text: Text to search for
            position: Position to select ('primeiro', 'segundo', 'último', '1', '2', 'last').
                     If None and multiple results, uses first. If single result, opens automatically.
            
        Returns:
            True if record was found and opened
            
        Raises:
            ValueError: If no records found or position invalid
        """
        # Search for records
        records = await self.search_records(search_text)
        
        if not records:
            raise ValueError(
                f"Nenhum registro encontrado com '{search_text}'. "
                f"Verifique se o texto está correto e se há registros na lista."
            )
        
        # Determine which record to open
        if len(records) == 1:
            # Only one result, open it
            record_index = 0
        elif position:
            # Parse position
            position_lower = position.lower()
            if position_lower in ['primeiro', 'first', '1']:
                record_index = 0
            elif position_lower in ['segundo', 'second', '2']:
                record_index = 1
            elif position_lower in ['último', 'last']:
                record_index = len(records) - 1
            else:
                try:
                    record_index = int(position) - 1
                    if record_index < 0 or record_index >= len(records):
                        raise ValueError(f"Posição '{position}' inválida. Encontrados {len(records)} registros.")
                except ValueError as e:
                    raise ValueError(
                        f"Posição '{position}' inválida. "
                        f"Use 'primeiro', 'segundo', 'último' ou um número (1, 2, etc.). "
                        f"Encontrados {len(records)} registros."
                    ) from e
        else:
            # Multiple results, no position specified, use first
            record_index = 0
        
        # Open the selected record
        try:
            record = records[record_index]
            await record.click()
            await asyncio.sleep(1)
            return True
        except Exception as e:
            raise ValueError(
                f"Erro ao abrir registro na posição {record_index + 1}. "
                f"Total de registros encontrados: {len(records)}"
            ) from e
    
    async def add_line(self, button_text: Optional[str] = None) -> bool:
        """
        Add a line to a One2many table.
        
        Args:
            button_text: Optional button text to search for (e.g., "Adicionar linha", "Add a line").
                        If not provided, auto-detects the add button.
            
        Returns:
            True if line was added successfully
            
        Raises:
            ValueError: If add button not found
        """
        # Common button texts for adding lines
        if button_text:
            button_texts = [button_text]
        else:
            # Try common texts in Portuguese and English
            button_texts = [
                "Adicionar linha",
                "Add a line",
                "Adicionar",
                "Add",
                "Adicionar uma linha",
                "Add a new line",
            ]
        
        # Selectors for add buttons in One2many fields
        add_button_selectors = [
            '.o_field_x2many_list_row_add a',
            '.o_field_one2many .o_list_button_add',
            'a:has-text("{}")',
            'button:has-text("{}")',
            '.o_field_one2many a[title*="Adicionar"]',
            '.o_field_one2many a[title*="Add"]',
        ]
        
        for btn_text in button_texts:
            for selector_template in add_button_selectors:
                try:
                    if '{}' in selector_template:
                        selector = selector_template.format(btn_text)
                    else:
                        selector = selector_template
                    
                    button = self.page.locator(selector).first
                    if await button.count() > 0 and await button.is_visible():
                        await button.click()
                        await asyncio.sleep(0.6)
                        return True
                except Exception:
                    continue
        
        # If not found with specific text, try generic selectors
        generic_selectors = [
            '.o_field_x2many_list_row_add a',
            '.o_field_one2many .o_list_button_add',
            '.o_field_one2many a[title*="Adicionar"]',
            '.o_field_one2many a[title*="Add"]',
        ]
        
        for selector in generic_selectors:
            try:
                button = self.page.locator(selector).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    await asyncio.sleep(0.6)
                    return True
            except Exception:
                continue
        
        raise ValueError(
            f"Botão para adicionar linha não encontrado. "
            f"Verifique se está em uma tabela One2many e se o botão está visível."
        )
    
    async def filter_records(self, filter_name: str, value: Optional[str] = None) -> bool:
        """Apply a filter."""
        # Click filter menu
        filter_btn = self.page.locator('button[title*="Filtros"], .o_filters_menu').first
        if await filter_btn.count() > 0:
            await filter_btn.click()
            await asyncio.sleep(0.5)
            
            # Click filter option
            filter_option = self.page.locator(f'text={filter_name}').first
            if await filter_option.count() > 0:
                await filter_option.click()
                await asyncio.sleep(1)
                return True
        
        return False

