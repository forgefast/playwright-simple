#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser utilities.

Shared browser management code.
"""

from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    """Manages browser lifecycle."""
    
    def __init__(self, headless: bool = False, viewport: Optional[Dict[str, int]] = None, 
                 record_video: bool = False, video_dir: Optional[str] = None):
        """
        Initialize browser manager.
        
        Args:
            headless: Run in headless mode
            viewport: Viewport size (default: 1280x720)
            record_video: Enable video recording
            video_dir: Directory to save videos (default: 'videos')
        """
        self.headless = headless
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.record_video = record_video
        self.video_dir = video_dir or 'videos'
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def start(self):
        """Start browser."""
        from pathlib import Path
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=100
        )
        
        # Prepare context options
        context_options = {
            'viewport': self.viewport,
        }
        
        # Add video recording if enabled
        if self.record_video:
            video_path = Path(self.video_dir)
            video_path.mkdir(parents=True, exist_ok=True)
            context_options['record_video_dir'] = str(video_path)
            context_options['record_video_size'] = self.viewport
        
        self.context = await self.browser.new_context(**context_options)
        self.page = await self.context.new_page()
        return self.page
    
    async def stop(self):
        """Stop browser."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

