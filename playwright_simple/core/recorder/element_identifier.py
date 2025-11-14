#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Element identifier module.

Identifies elements in a generic way (not CSS-specific).
Uses multiple strategies to find the best identifier.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ElementIdentifier:
    """Identifies elements using generic strategies."""
    
    @staticmethod
    def identify(element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify element using multiple strategies.
        
        Args:
            element_info: Element information from browser
            
        Returns:
            Dictionary with identification strategy and values:
            {
                'text': str or None,
                'description': str,
                'selector': str or None (fallback)
            }
        """
        # Strategy 1: Visible text (best for buttons, links)
        text = ElementIdentifier._get_visible_text(element_info)
        
        # Strategy 2: Label (for inputs)
        label = ElementIdentifier._get_label(element_info)
        
        # Strategy 3: Placeholder (for inputs)
        placeholder = ElementIdentifier._get_placeholder(element_info)
        
        # Strategy 4: ARIA label or accessible name
        aria_label = ElementIdentifier._get_aria_label(element_info)
        
        # Strategy 5: Type + context description
        type_description = ElementIdentifier._get_type_description(element_info)
        
        # Strategy 6: Position-based (last resort)
        position_description = ElementIdentifier._get_position_description(element_info)
        
        # Build result
        result = {
            'text': None,
            'description': '',
            'selector': None
        }
        
        # Prefer text if available
        if text and len(text.strip()) > 0:
            result['text'] = text.strip()
            result['description'] = f"Clicar em '{text.strip()}'"
        # For inputs, prefer label or placeholder
        elif label:
            result['description'] = f"Campo '{label}'"
        elif placeholder:
            result['description'] = f"Campo com placeholder '{placeholder}'"
        elif aria_label:
            result['text'] = aria_label
            result['description'] = f"Clicar em '{aria_label}'"
        elif type_description:
            result['description'] = type_description
        else:
            result['description'] = position_description or "Elemento"
        
        # Add fallback selector if needed (for debugging)
        if element_info.get('id'):
            result['selector'] = f"#{element_info['id']}"
        elif element_info.get('name'):
            result['selector'] = f"[name='{element_info['name']}']"
        
        return result
    
    @staticmethod
    def _get_visible_text(element_info: Dict[str, Any]) -> Optional[str]:
        """Get visible text from element."""
        text = element_info.get('text', '').strip()
        
        # For buttons, get the text content or value
        tag_name = element_info.get('tagName', '').upper()
        if tag_name == 'BUTTON' or tag_name == 'INPUT':
            # Try value attribute for input buttons
            value = element_info.get('value', '').strip()
            if value and len(value) < 100:
                return value
        
        # Filter out very long texts (probably not button text)
        if text and len(text) < 100:
            return text
        
        return None
    
    @staticmethod
    def _get_label(element_info: Dict[str, Any]) -> Optional[str]:
        """Get label for input element."""
        label = element_info.get('label', '').strip()
        if label:
            return label
        return None
    
    @staticmethod
    def _get_placeholder(element_info: Dict[str, Any]) -> Optional[str]:
        """Get placeholder text."""
        placeholder = element_info.get('placeholder', '').strip()
        if placeholder:
            return placeholder
        return None
    
    @staticmethod
    def _get_aria_label(element_info: Dict[str, Any]) -> Optional[str]:
        """Get ARIA label."""
        aria_label = element_info.get('ariaLabel', '').strip()
        if aria_label:
            return aria_label
        
        # Check role
        role = element_info.get('role', '').strip()
        if role:
            return f"{role} element"
        
        return None
    
    @staticmethod
    def _get_type_description(element_info: Dict[str, Any]) -> Optional[str]:
        """Get description based on element type."""
        tag_name = element_info.get('tagName', '').upper()
        element_type = element_info.get('type', '').lower()
        name = element_info.get('name', '')
        
        if tag_name == 'INPUT':
            if element_type == 'submit':
                return "Botão de submit"
            elif element_type == 'button':
                return "Botão"
            elif element_type in ['text', 'email', 'password']:
                field_name = name or element_info.get('placeholder', 'campo')
                return f"Campo de texto '{field_name}'"
            elif element_type == 'checkbox':
                return "Checkbox"
            elif element_type == 'radio':
                return "Radio button"
            else:
                return f"Campo {element_type}"
        elif tag_name == 'BUTTON':
            return "Botão"
        elif tag_name == 'A':
            href = element_info.get('href', '')
            if href:
                return f"Link para {href}"
            return "Link"
        elif tag_name == 'SELECT':
            return "Dropdown/Select"
        elif tag_name == 'TEXTAREA':
            return "Área de texto"
        
        return None
    
    @staticmethod
    def _get_position_description(element_info: Dict[str, Any]) -> Optional[str]:
        """Get position-based description (last resort)."""
        tag_name = element_info.get('tagName', '').upper()
        element_type = element_info.get('type', '').lower()
        
        if tag_name == 'INPUT':
            if element_type in ['text', 'email', 'password']:
                return "Campo de entrada"
            elif element_type == 'submit':
                return "Botão de envio"
            elif element_type == 'button':
                return "Botão"
        elif tag_name == 'BUTTON':
            return "Botão"
        elif tag_name == 'A':
            return "Link"
        
        return f"Elemento {tag_name}"
    
    @staticmethod
    def identify_for_input(element_info: Dict[str, Any], value: str = '') -> Dict[str, Any]:
        """
        Identify input element specifically for typing actions.
        
        Args:
            element_info: Element information
            value: Value that was typed
            
        Returns:
            Dictionary with identification for type action
        """
        result = {
            'text': value,
            'description': '',
            'selector': None
        }
        
        # Prefer label
        label = ElementIdentifier._get_label(element_info)
        if label:
            result['description'] = f"Campo '{label}'"
        # Then placeholder
        elif element_info.get('placeholder'):
            result['description'] = f"Campo com placeholder '{element_info['placeholder']}'"
        # Then name
        elif element_info.get('name'):
            result['description'] = f"Campo '{element_info['name']}'"
        # Then type
        else:
            element_type = element_info.get('type', 'text')
            result['description'] = f"Campo de {element_type}"
        
        return result

