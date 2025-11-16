#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page stability module.

Provides functionality for waiting for page to stabilize after actions.
"""

import asyncio
import logging
from typing import Optional

from .config import SpeedLevel

logger = logging.getLogger(__name__)


async def wait_for_page_stable(
    page,
    timeout: float = 10.0,
    speed_level: Optional[SpeedLevel] = None,
    fast_mode: bool = False,
    recorder_logger = None
) -> None:
    """
    Wait for page to stabilize after an action.
    
    Implements dynamic wait that detects when page stops changing.
    Timeouts are adjusted based on speed_level for better performance.
    
    Args:
        page: Playwright Page instance
        timeout: Maximum time to wait in seconds (adjusted by speed_level)
        speed_level: SpeedLevel enum (ULTRA_FAST, FAST, NORMAL, SLOW)
        fast_mode: Legacy fast mode flag (for backward compatibility)
        recorder_logger: Optional RecorderLogger for logging
    """
    # Adjust timeout and delays based on speed_level
    if speed_level:
        if speed_level == SpeedLevel.ULTRA_FAST:
            timeout = min(timeout, 1.5)  # Ultra fast: max 1.5s
            check_interval = 0.05  # Check every 50ms
            min_stable_time = 0.1  # Need 100ms stable
        elif speed_level == SpeedLevel.FAST:
            timeout = min(timeout, 3.0)  # Fast: max 3s
            check_interval = 0.1  # Check every 100ms
            min_stable_time = 0.2  # Need 200ms stable
        else:  # NORMAL or SLOW
            check_interval = 0.2  # Check every 200ms
            min_stable_time = 0.5  # Need 500ms stable
    elif fast_mode:
        timeout = min(timeout, 3.0)
        check_interval = 0.1
        min_stable_time = 0.2
    else:
        check_interval = 0.2
        min_stable_time = 0.5
    
    # Log screen event: waiting for page stability
    if recorder_logger and recorder_logger.is_debug:
        try:
            page_title = await page.title()
        except:
            page_title = 'N/A'
        page_state = {
            'url': page.url if hasattr(page, 'url') else 'N/A',
            'title': page_title
        }
        recorder_logger.log_screen_event(
            event_type='waiting_for_stability',
            page_state=page_state,
            details={'timeout': timeout}
        )
    
    try:
        # First, wait for DOM to be ready
        await page.wait_for_load_state('domcontentloaded', timeout=int(timeout * 1000))
        
        # Log screen event: DOM ready
        if recorder_logger and recorder_logger.is_debug:
            try:
                page_title = await page.title()
            except:
                page_title = 'N/A'
            page_state = {
                'url': page.url if hasattr(page, 'url') else 'N/A',
                'title': page_title
            }
            recorder_logger.log_screen_event(
                event_type='dom_ready',
                page_state=page_state
            )
    except Exception:
        pass
    
    try:
        # Wait for network to be idle - use optimized timeout
        networkidle_timeout = timeout
        if speed_level == SpeedLevel.ULTRA_FAST:
            networkidle_timeout = min(timeout, 1.0)  # Max 1s for ultra fast
        elif speed_level == SpeedLevel.FAST:
            networkidle_timeout = min(timeout, 2.0)  # Max 2s for fast
        await page.wait_for_load_state('networkidle', timeout=int(networkidle_timeout * 1000))
        
        # Log screen event: network idle
        if recorder_logger and recorder_logger.is_debug:
            try:
                page_title = await page.title()
            except:
                page_title = 'N/A'
            page_state = {
                'url': page.url if hasattr(page, 'url') else 'N/A',
                'title': page_title,
                'network_idle': True
            }
            recorder_logger.log_screen_event(
                event_type='network_idle',
                page_state=page_state
            )
    except Exception:
        # Fallback: wait for load state
        try:
            await page.wait_for_load_state('load', timeout=int(timeout * 1000))
            
            # Log screen event: page loaded
            if recorder_logger and recorder_logger.is_debug:
                try:
                    page_title = await page.title()
                except:
                    page_title = 'N/A'
                page_state = {
                    'url': page.url if hasattr(page, 'url') else 'N/A',
                    'title': page_title
                }
                recorder_logger.log_screen_event(
                    event_type='page_loaded',
                    page_state=page_state
                )
        except Exception:
            pass
    
    # Additional wait for dynamic content - optimized check
    try:
        initial_html = await page.content()
        await asyncio.sleep(check_interval)
        final_html = await page.content()
        
        # If HTML changed, wait until stable
        if initial_html != final_html:
            stable_count = 0
            last_html = final_html
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                await asyncio.sleep(check_interval)
                current_html = await page.content()
                
                if current_html == last_html:
                    stable_count += 1
                    if stable_count * check_interval >= min_stable_time:
                        break
                else:
                    stable_count = 0
                    last_html = current_html
    except Exception:
        pass

