#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base handler for Playwright commands.

Provides common functionality for all handlers.
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class BaseHandler:
    """Base class for Playwright command handlers."""
    
    def __init__(
        self,
        yaml_writer,
        page_getter: Optional[Callable] = None,
        cursor_controller_getter: Optional[Callable] = None,
        recorder=None,
        recorder_logger=None
    ):
        """Initialize base handler."""
        self.yaml_writer = yaml_writer
        self._get_page = page_getter
        self._get_cursor_controller = cursor_controller_getter
        self._recorder = recorder
        self.recorder_logger = recorder_logger
    
    def _get_delay_from_speed_level(self, normal_delay: float, fast_delay: float = None) -> float:
        """Get delay based on speed_level from recorder."""
        if not self._recorder:
            return normal_delay
        
        speed_level = getattr(self._recorder, 'speed_level', None)
        if speed_level:
            try:
                from ..config import SpeedLevel
                if speed_level == SpeedLevel.ULTRA_FAST:
                    return 0.0
                elif speed_level == SpeedLevel.FAST:
                    return fast_delay if fast_delay is not None else normal_delay * 0.1
                return normal_delay
            except ImportError:
                pass
        
        fast_mode = getattr(self._recorder, 'fast_mode', False)
        if fast_mode:
            return fast_delay if fast_delay is not None else normal_delay * 0.1
        
        return normal_delay
    
    async def _wait_for_page_stable(self, timeout: float = 10.0):
        """Wait for page to stabilize."""
        page = self._get_page()
        if not page:
            return
        
        try:
            if self._recorder and hasattr(self._recorder, '_wait_for_page_stable'):
                await self._recorder._wait_for_page_stable(timeout=timeout)
            else:
                await page.wait_for_load_state('domcontentloaded', timeout=5000)
                delay = self._get_delay_from_speed_level(0.5, 0.01)
                await asyncio.sleep(delay)
                try:
                    await page.wait_for_load_state('networkidle', timeout=3000)
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error waiting for page stable: {e}")

