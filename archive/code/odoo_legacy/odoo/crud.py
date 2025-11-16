#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRUD methods for OdooTestBase.

Contains methods for creating, reading, updating, and deleting records.
"""

from typing import Optional, Dict, Any


class OdooCRUDMixin:
    """Mixin providing CRUD methods for OdooTestBase.
    
    Assumes base class has: page, view, field, go_to_model
    """
    
    async def create_record(self, model_name: Optional[str] = None, fields: Optional[Dict[str, Any]] = None) -> 'OdooCRUDMixin':
        """
        Create a new record.
        
        Args:
            model_name: Model name (optional, if already on the model page)
            fields: Dictionary of field names and values
            
        Returns:
            Self for method chaining
        """
        # Navigate to model if specified
        if model_name:
            await self.go_to_model(model_name, "list")
        
        # Click create button
        await self.view.create_record()
        
        # Fill fields if provided
        if fields:
            for field_name, value in fields.items():
                if isinstance(value, dict) and 'type' in value:
                    field_type = value['type']
                    field_value = value['value']
                    
                    if field_type == 'many2one':
                        await self.field.fill_many2one(field_name, field_value)
                    elif field_type == 'one2many':
                        await self.field.fill_one2many(field_name, field_value)
                    elif field_type == 'char':
                        await self.field.fill_char(field_name, field_value)
                    elif field_type == 'integer':
                        await self.field.fill_integer(field_name, field_value)
                    elif field_type == 'float':
                        await self.field.fill_float(field_name, field_value)
                    elif field_type == 'boolean':
                        await self.field.toggle_boolean(field_name)
                    elif field_type == 'date':
                        await self.field.fill_date(field_name, field_value)
                    elif field_type == 'datetime':
                        await self.field.fill_datetime(field_name, field_value)
                else:
                    # Default to char
                    await self.field.fill_char(field_name, str(value))
        
        return self
    
    async def search_and_open(self, model_name: str, search_text: str) -> 'OdooCRUDMixin':
        """
        Search for a record and open it.
        
        Args:
            model_name: Model name
            search_text: Text to search for
            
        Returns:
            Self for method chaining
        """
        await self.go_to_model(model_name, "list")
        await self.view.search_records(search_text)
        await self.view.open_record(0)
        return self
    
    async def assert_record_exists(self, model_name: str, search_text: str) -> 'OdooCRUDMixin':
        """
        Assert that a record exists.
        
        Args:
            model_name: Model name
            search_text: Text to search for
            
        Returns:
            Self for method chaining
        """
        await self.go_to_model(model_name, "list")
        await self.view.search_records(search_text)
        
        # Check if any results found
        results = self.page.locator('tr.o_data_row, .o_kanban_record')
        count = await results.count()
        assert count > 0, f"Record with '{search_text}' not found in {model_name}"
        
        return self
    
    async def open_record(
        self,
        search_text: str,
        position: Optional[str] = None
    ) -> 'OdooCRUDMixin':
        """
        Search for a record by text and open it.
        
        Args:
            search_text: Text to search for (visible in the record)
            position: Position to select if multiple results ('primeiro', 'segundo', 'último', '1', '2', 'last')
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If no records found or position invalid
            
        Example:
            ```python
            await test.open_record("João Silva")
            await test.open_record("João Silva", position="primeiro")
            await test.open_record("João", position="segundo")
            ```
        """
        await self.view.find_and_open_record(search_text, position)
        return self
    
    async def add_line(self, button_text: Optional[str] = None) -> 'OdooCRUDMixin':
        """
        Add a line to a One2many table (e.g., add product to sale order).
        
        Args:
            button_text: Optional button text (e.g., "Adicionar linha", "Add a line").
                        If not provided, auto-detects the button.
            
        Returns:
            Self for method chaining
            
        Example:
            ```python
            await test.add_line()
            await test.add_line("Adicionar linha")
            ```
        """
        await self.view.add_line(button_text)
        return self

