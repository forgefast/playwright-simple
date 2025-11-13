#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSS style generation for cursor elements.

Contains methods for generating CSS styles for cursor, click effect, and hover effect.
"""

from .config import CursorConfig
from .constants import CURSOR_Z_INDEX, CLICK_EFFECT_Z_INDEX, HOVER_EFFECT_Z_INDEX


class CursorStyles:
    """Helper class for generating cursor CSS styles."""
    
    @staticmethod
    def get_cursor_css(config: CursorConfig) -> str:
        """Generate CSS for cursor based on configuration."""
        size_px = CursorStyles.get_size_pixels(config)
        color = config.color
        
        if config.style == "arrow":
            return f"""
                position: fixed !important;
                width: 0 !important;
                height: 0 !important;
                border-left: {size_px * 0.4}px solid transparent !important;
                border-right: {size_px * 0.4}px solid transparent !important;
                border-top: {size_px * 0.6}px solid {color} !important;
                pointer-events: none !important;
                z-index: {CURSOR_Z_INDEX} !important;
                transform: translate(-50%, -50%) rotate(45deg) !important;
                display: block !important;
                filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.5)) !important;
            """
        elif config.style == "dot":
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                background: {color} !important;
                border-radius: 50% !important;
                pointer-events: none !important;
                z-index: {CURSOR_Z_INDEX} !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
                box-shadow: 0 0 {size_px * 0.3}px {color} !important;
            """
        elif config.style == "circle":
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                border: {size_px * 0.15}px solid {color} !important;
                border-radius: 50% !important;
                background: transparent !important;
                pointer-events: none !important;
                z-index: {CURSOR_Z_INDEX} !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
                box-shadow: 0 0 {size_px * 0.3}px {color} !important;
            """
        else:  # custom
            return f"""
                position: fixed !important;
                width: {size_px}px !important;
                height: {size_px}px !important;
                background: {color} !important;
                pointer-events: none !important;
                z-index: {CURSOR_Z_INDEX} !important;
                transform: translate(-50%, -50%) !important;
                display: block !important;
            """
    
    @staticmethod
    def get_click_effect_css(config: CursorConfig) -> str:
        """Generate CSS for click effect - more visible."""
        return f"""
            position: fixed !important;
            width: 0 !important;
            height: 0 !important;
            border: 8px solid {config.click_effect_color} !important;
            border-radius: 50% !important;
            pointer-events: none !important;
            z-index: {CLICK_EFFECT_Z_INDEX} !important;
            transform: translate(-50%, -50%) !important;
            transition: all 0.4s ease-out !important;
            box-shadow: 0 0 20px {config.click_effect_color} !important;
            opacity: 0 !important;
            display: none !important;
        """
    
    @staticmethod
    def get_hover_effect_css(config: CursorConfig) -> str:
        """Generate CSS for hover effect."""
        return f"""
            position: fixed !important;
            width: 0 !important;
            height: 0 !important;
            border: 3px solid {config.hover_effect_color} !important;
            border-radius: 50% !important;
            pointer-events: none !important;
            z-index: {HOVER_EFFECT_Z_INDEX} !important;
            transform: translate(-50%, -50%) !important;
            transition: all 0.2s ease-out !important;
            opacity: 0 !important;
            display: none !important;
        """
    
    @staticmethod
    def get_size_pixels(config: CursorConfig) -> int:
        """Convert size string to pixels."""
        if isinstance(config.size, (int, float)):
            return int(config.size)
        
        size_map = {
            "small": 12,
            "medium": 20,
            "large": 32,
        }
        return size_map.get(config.size, 20)

