#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base handler for Playwright commands.

Provides common functionality for all handlers.
"""

import asyncio
import logging
import time
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
    
    async def _wait_for_page_stable(self, timeout: float = 2.0):  # Reduced from 5.0 for faster execution
        """Wait for page to stabilize using dynamic waits."""
        start_time = time.perf_counter()
        logger.info(f"[TIMING] [BASE_HANDLER] _wait_for_page_stable START - timeout={timeout}s")
        
        page = self._get_page()
        if not page:
            logger.info(f"[TIMING] [BASE_HANDLER] _wait_for_page_stable SKIPPED (no page)")
            return
        
        try:
            if self._recorder and hasattr(self._recorder, '_wait_for_page_stable'):
                await self._recorder._wait_for_page_stable(timeout=timeout)
            else:
                # Fallback: check DOM state before waiting
                try:
                    dom_state = await page.evaluate("document.readyState")
                    logger.info(f"[TIMING] [BASE_HANDLER] DOM state before wait: {dom_state}")
                    
                    # If DOM is already ready, skip waiting
                    if dom_state in ('interactive', 'complete'):
                        elapsed = time.perf_counter() - start_time
                        logger.info(f"[TIMING] [BASE_HANDLER] _wait_for_page_stable SKIPPED (DOM already {dom_state}) - elapsed={elapsed*1000:.1f}ms")
                        return
                except Exception as e:
                    logger.debug(f"[TIMING] [BASE_HANDLER] Could not check DOM state: {e}")
                
                # Fallback: use wait_for_load_state with safety timeout only
                # Don't use networkidle as it can be problematic in apps with continuous polling
                wait_start = time.perf_counter()
                try:
                    # Wait for DOM to be ready - this is fast and reliable
                    await page.wait_for_load_state('domcontentloaded', timeout=int(timeout * 1000))
                    wait_elapsed = time.perf_counter() - wait_start
                    logger.info(f"[TIMING] [BASE_HANDLER] wait_for_load_state('domcontentloaded') completed - elapsed={wait_elapsed*1000:.1f}ms")
                except Exception as e:
                    wait_elapsed = time.perf_counter() - wait_start
                    logger.debug(f"[TIMING] [BASE_HANDLER] wait_for_load_state exception after {wait_elapsed*1000:.1f}ms: {e}")
                    pass  # Continue even if timeout
                
                # Note: We don't wait for networkidle in fallback as it can cause issues
                # in apps with continuous polling. The domcontentloaded check is sufficient.
        except Exception as e:
            logger.debug(f"[TIMING] [BASE_HANDLER] Error waiting for page stable: {e}")
        
        total_elapsed = time.perf_counter() - start_time
        logger.info(f"[TIMING] [BASE_HANDLER] _wait_for_page_stable END - total_elapsed={total_elapsed*1000:.1f}ms")

