#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Screenshot management system for playwright-simple.

Handles automatic and manual screenshots with smart organization.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from playwright.async_api import Page

from .config import ScreenshotConfig


class ScreenshotManager:
    """Manages screenshot capture and organization."""
    
    def __init__(self, page: Page, config: ScreenshotConfig, test_name: Optional[str] = None):
        """
        Initialize screenshot manager.
        
        Args:
            page: Playwright page instance
            config: Screenshot configuration
            test_name: Name of current test (for organization)
        """
        self.page = page
        self.config = config
        self.test_name = test_name or "default"
        self._screenshot_count = 0
        self._screenshot_metadata: Dict[str, Dict[str, Any]] = {}  # Store metadata for screenshots
        self._setup_directories()
    
    def _setup_directories(self):
        """Create screenshot directories if needed."""
        self.screenshot_dir = Path(self.config.dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test-specific directory if organizing by test
        if self.test_name:
            self.test_dir = self.screenshot_dir / self.test_name
            self.test_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.test_dir = self.screenshot_dir
    
    async def capture(
        self,
        name: Optional[str] = None,
        full_page: Optional[bool] = None,
        element: Optional[str] = None,
        timeout: int = 5000,
        description: Optional[str] = None
    ) -> Path:
        """
        Capture a screenshot.
        
        Args:
            name: Name for screenshot file (auto-generated if not provided)
            full_page: Whether to capture full page (overrides config)
            element: Selector for element to screenshot (screenshots only that element)
            timeout: Timeout for element wait
            
        Returns:
            Path to saved screenshot
        """
        # Determine full_page setting
        use_full_page = full_page if full_page is not None else self.config.full_page
        
        # Generate filename
        if not name:
            self._screenshot_count += 1
            name = f"screenshot_{self._screenshot_count:03d}"
        
        # Ensure name has extension
        if not name.endswith(('.png', '.jpeg', '.jpg')):
            name = f"{name}.{self.config.format}"
        
        # Determine path
        screenshot_path = self.test_dir / name
        
        # Store metadata (always store, description optional)
        screenshot_name = name
        if screenshot_name.endswith(('.png', '.jpeg', '.jpg')):
            screenshot_name = screenshot_name.rsplit('.', 1)[0]
        
        self._screenshot_metadata[screenshot_name] = {
            "name": screenshot_name,
            "description": description or screenshot_name.replace("_", " ").title(),
            "path": str(screenshot_path),
            "test_name": self.test_name
        }
        
        # Capture screenshot
        if element:
            # Screenshot specific element
            try:
                element_locator = self.page.locator(element).first
                await element_locator.wait_for(state="visible", timeout=timeout)
                await element_locator.screenshot(path=str(screenshot_path))
            except Exception as e:
                # Fallback to page screenshot if element not found
                await self.page.screenshot(
                    path=str(screenshot_path),
                    full_page=use_full_page
                )
        else:
            # Screenshot page
            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=use_full_page
            )
        
        return screenshot_path
    
    async def capture_on_action(
        self,
        action_name: str,
        selector: Optional[str] = None
    ) -> Optional[Path]:
        """
        Capture screenshot automatically after an action.
        
        Args:
            action_name: Name of the action (e.g., "click", "type")
            selector: Selector of element interacted with
            
        Returns:
            Path to screenshot if captured, None otherwise
        """
        if not self.config.auto:
            return None
        
        # Generate name from action
        name = f"{action_name}_{self._screenshot_count + 1:03d}"
        if selector:
            # Sanitize selector for filename
            selector_safe = selector.replace('/', '_').replace('\\', '_')[:50]
            name = f"{action_name}_{selector_safe}_{self._screenshot_count + 1:03d}"
        
        return await self.capture(name=name)
    
    async def capture_on_failure(self, error: Exception) -> Path:
        """
        Capture screenshot on test failure.
        
        Args:
            error: The exception that caused the failure
            
        Returns:
            Path to screenshot
        """
        error_name = type(error).__name__
        name = f"failure_{error_name}_{self._screenshot_count + 1:03d}.{self.config.format}"
        return await self.capture(name=name, full_page=True)
    
    def set_test_name(self, test_name: str):
        """
        Update test name for organization.
        
        Args:
            test_name: New test name
        """
        self.test_name = test_name
        self._setup_directories()
        self._screenshot_count = 0
    
    def get_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all screenshot metadata.
        
        Returns:
            Dictionary mapping screenshot names to metadata
        """
        return self._screenshot_metadata.copy()
    
    def clear_metadata(self):
        """Clear all screenshot metadata."""
        self._screenshot_metadata.clear()


