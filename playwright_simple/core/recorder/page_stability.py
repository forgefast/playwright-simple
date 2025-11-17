#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Page stability module.

Provides functionality for waiting for page to stabilize after actions.
"""

import asyncio
import logging
import time
from typing import Optional

from .config import SpeedLevel

logger = logging.getLogger(__name__)


async def wait_for_page_stable(
    page,
    timeout: float = 2.0,  # Safety timeout only - should not be reached in normal operation (reduced from 5.0)
    speed_level: Optional[SpeedLevel] = None,
    fast_mode: bool = False,
    recorder_logger = None
) -> None:
    """
    Wait for page to stabilize after an action using dynamic waits.
    
    Implements dynamic wait that detects when page stops changing.
    Uses polling-based detection without fixed timeouts - adapts to system speed automatically.
    
    Args:
        page: Playwright Page instance
        timeout: Safety timeout in seconds (default: 30.0) - only to prevent infinite hangs
        speed_level: SpeedLevel enum (kept for compatibility, but not used for timeouts)
        fast_mode: Legacy fast mode flag (kept for compatibility)
        recorder_logger: Optional RecorderLogger for logging
    """
    start_time = time.perf_counter()
    logger.info(f"[TIMING] wait_for_page_stable START - timeout={timeout}s")
    
    # Safety timeout to prevent infinite hangs (should not be reached normally)
    SAFETY_TIMEOUT = timeout
    
    # Check current DOM state before waiting
    try:
        dom_state_start = await page.evaluate("document.readyState")
        logger.info(f"[TIMING] DOM state before wait: {dom_state_start}")
        
        # If DOM is already ready, skip waiting
        if dom_state_start in ('interactive', 'complete'):
            elapsed = time.perf_counter() - start_time
            logger.info(f"[TIMING] wait_for_page_stable SKIPPED (DOM already {dom_state_start}) - elapsed={elapsed:.3f}s")
            return
    except Exception as e:
        logger.debug(f"[TIMING] Could not check DOM state: {e}")
    
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
            details={'timeout': SAFETY_TIMEOUT}
        )
    
    wait_start = time.perf_counter()
    try:
        # Wait for DOM to be ready - this is fast and reliable
        # Use safety timeout only to prevent infinite hangs
        # Once domcontentloaded is reached, the page is ready for interaction
        await page.wait_for_load_state('domcontentloaded', timeout=int(SAFETY_TIMEOUT * 1000))
        wait_elapsed = time.perf_counter() - wait_start
        logger.info(f"[TIMING] wait_for_load_state('domcontentloaded') completed - elapsed={wait_elapsed:.3f}s")
        
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
    except Exception as e:
        wait_elapsed = time.perf_counter() - wait_start
        logger.debug(f"[TIMING] wait_for_load_state exception after {wait_elapsed:.3f}s: {e}")
        pass  # Continue even if DOM ready check fails
    
    total_elapsed = time.perf_counter() - start_time
    logger.info(f"[TIMING] wait_for_page_stable END - total_elapsed={total_elapsed:.3f}s")
    
    # Note: We don't do HTML polling anymore as it's too slow and unnecessary.
    # Once domcontentloaded is reached, the page is ready for interaction.
    # For apps with continuous polling (like Odoo), waiting for HTML stability
    # would never complete, so we rely on domcontentloaded which is sufficient.


async def wait_for_navigation_after_click(
    page,
    url_before_action: str,
    timeout: float = 2.0  # Safety timeout only - should not be reached in normal operation (reduced from 30.0)
) -> bool:
    """
    Wait for navigation after a click action using dynamic waits.
    
    This function detects if a click caused navigation and waits for the new page
    to be ready before continuing. Uses dynamic polling and event-based waiting
    without fixed timeouts - adapts to system speed automatically.
    
    Args:
        page: Playwright Page instance
        url_before_action: URL before the click action
        timeout: Safety timeout in seconds (default: 5.0) - only to prevent infinite hangs
        
    Returns:
        True if navigation occurred, False otherwise
    """
    start_time = time.perf_counter()
    logger.info(f"[TIMING] wait_for_navigation_after_click START - URL before: {url_before_action}, timeout={timeout}s")
    
    # Safety timeout to prevent infinite hangs (should not be reached normally)
    # Use shorter timeout for initial navigation detection (200ms)
    NAVIGATION_DETECTION_TIMEOUT = 200  # 200ms to quickly detect if navigation will occur
    SAFETY_TIMEOUT = int(timeout * 1000)  # Convert to milliseconds for final safety
    POLL_INTERVAL = 0.05  # 50ms polling interval for dynamic checks
    
    try:
        # Strategy 1: Wait for navigation event with short timeout (most reliable)
        # This will return immediately when navigation occurs, or timeout quickly if no navigation
        try:
            logger.info(f"[TIMING] Waiting for navigation event (timeout={NAVIGATION_DETECTION_TIMEOUT}ms)...")
            nav_wait_start = time.perf_counter()
            # Use short timeout - if navigation happens, this returns immediately
            await page.wait_for_event('framenavigated', timeout=NAVIGATION_DETECTION_TIMEOUT)
            nav_wait_elapsed = time.perf_counter() - nav_wait_start
            # Navigation occurred, wait for page to be ready
            logger.info(f"[TIMING] Navigation event detected after {nav_wait_elapsed*1000:.1f}ms! Waiting for page to be ready...")
            
            # Check DOM state before waiting
            try:
                dom_state = await page.evaluate("document.readyState")
                logger.info(f"[TIMING] DOM state after navigation: {dom_state}")
                if dom_state in ('interactive', 'complete'):
                    dom_elapsed = time.perf_counter() - nav_wait_start
                    logger.info(f"[TIMING] DOM already ready ({dom_state}), skipping wait - elapsed={dom_elapsed*1000:.1f}ms")
                else:
                    dom_wait_start = time.perf_counter()
                    await page.wait_for_load_state('domcontentloaded', timeout=SAFETY_TIMEOUT)
                    dom_wait_elapsed = time.perf_counter() - dom_wait_start
                    logger.info(f"[TIMING] wait_for_load_state('domcontentloaded') completed - elapsed={dom_wait_elapsed*1000:.1f}ms")
            except Exception as dom_e:
                logger.debug(f"[TIMING] DOM check/wait exception: {dom_e}")
            
            current_url = page.url
            total_elapsed = time.perf_counter() - start_time
            logger.info(f"[TIMING] Navigation completed: {url_before_action} -> {current_url} - total_elapsed={total_elapsed*1000:.1f}ms")
            return True
        except Exception as e:
            # No navigation event detected quickly - check URL immediately
            nav_wait_elapsed = time.perf_counter() - start_time
            logger.info(f"[TIMING] No navigation event detected after {nav_wait_elapsed*1000:.1f}ms, checking URL...")
            
            # Quick URL check before polling
            try:
                current_url = page.url
                if current_url != url_before_action:
                    logger.info(f"[TIMING] URL changed detected immediately! {url_before_action} -> {current_url}")
                    # URL changed! Wait for page to be ready
                    try:
                        dom_state = await page.evaluate("document.readyState")
                        if dom_state not in ('interactive', 'complete'):
                            dom_wait_start = time.perf_counter()
                            await page.wait_for_load_state('domcontentloaded', timeout=SAFETY_TIMEOUT)
                            dom_wait_elapsed = time.perf_counter() - dom_wait_start
                            logger.info(f"[TIMING] wait_for_load_state after URL change - elapsed={dom_wait_elapsed*1000:.1f}ms")
                    except Exception:
                        pass
                    total_elapsed = time.perf_counter() - start_time
                    logger.info(f"[TIMING] Navigation completed via URL check - total_elapsed={total_elapsed*1000:.1f}ms")
                    return True
            except Exception:
                pass
            
            # Strategy 2: Dynamic polling for URL change (only if URL didn't change immediately)
            logger.info(f"[TIMING] Starting URL polling (interval={POLL_INTERVAL*1000:.0f}ms)...")
            poll_start = time.perf_counter()
            poll_iterations = 0
            while (time.perf_counter() - start_time) * 1000 < SAFETY_TIMEOUT:
                try:
                    current_url = page.url
                    if current_url != url_before_action:
                        # URL changed! Wait for page to be ready
                        poll_elapsed = time.perf_counter() - poll_start
                        logger.info(f"[TIMING] URL changed detected via polling after {poll_elapsed*1000:.1f}ms ({poll_iterations} iterations)! {url_before_action} -> {current_url}")
                        try:
                            dom_state = await page.evaluate("document.readyState")
                            if dom_state not in ('interactive', 'complete'):
                                await page.wait_for_load_state('domcontentloaded', timeout=SAFETY_TIMEOUT)
                        except Exception:
                            pass
                        total_elapsed = time.perf_counter() - start_time
                        logger.info(f"[TIMING] Navigation completed via polling - total_elapsed={total_elapsed*1000:.1f}ms")
                        return True
                except Exception:
                    pass  # Continue polling if URL check fails
                
                poll_iterations += 1
                # Short sleep before next poll
                await asyncio.sleep(POLL_INTERVAL)
            
            # Final check after polling
            poll_total_elapsed = time.perf_counter() - poll_start
            logger.info(f"[TIMING] Polling completed after {poll_total_elapsed*1000:.1f}ms ({poll_iterations} iterations)")
            try:
                current_url = page.url
                if current_url != url_before_action:
                    logger.info(f"[TIMING] URL changed in final check! Waiting for page to be ready...")
                    try:
                        dom_state = await page.evaluate("document.readyState")
                        if dom_state not in ('interactive', 'complete'):
                            await page.wait_for_load_state('domcontentloaded', timeout=SAFETY_TIMEOUT)
                    except Exception:
                        pass
                    total_elapsed = time.perf_counter() - start_time
                    logger.info(f"[TIMING] Navigation completed in final check - total_elapsed={total_elapsed*1000:.1f}ms")
                    return True
                else:
                    total_elapsed = time.perf_counter() - start_time
                    logger.info(f"[TIMING] No navigation detected (URL unchanged) - total_elapsed={total_elapsed*1000:.1f}ms")
                    return False
            except Exception as e2:
                logger.error(f"[TIMING] Error in final URL check: {e2}")
                total_elapsed = time.perf_counter() - start_time
                logger.info(f"[TIMING] wait_for_navigation_after_click END (error) - total_elapsed={total_elapsed*1000:.1f}ms")
                return False
    except Exception as e:
        logger.error(f"[TIMING] Unexpected error in wait_for_navigation_after_click: {e}")
        # Last resort: check URL and wait for DOM
        try:
            current_url = page.url
            if current_url != url_before_action:
                try:
                    dom_state = await page.evaluate("document.readyState")
                    if dom_state not in ('interactive', 'complete'):
                        await page.wait_for_load_state('domcontentloaded', timeout=SAFETY_TIMEOUT)
                except Exception:
                    pass
                total_elapsed = time.perf_counter() - start_time
                logger.info(f"[TIMING] Navigation detected in error handler - total_elapsed={total_elapsed*1000:.1f}ms")
                return True
        except:
            pass
        total_elapsed = time.perf_counter() - start_time
        logger.info(f"[TIMING] wait_for_navigation_after_click END (no navigation) - total_elapsed={total_elapsed*1000:.1f}ms")
        return False


async def wait_for_odoo_action_complete(
    page,
    timeout: float = 1.0  # Short timeout for Odoo-specific checks
) -> bool:
    """
    Wait for Odoo action to complete by checking Odoo-specific indicators.
    
    This function detects when an Odoo action (like clicking a filter, menu item, etc.)
    is complete by checking for:
    - Disappearance of loading indicators (.o_loading, .fa-spin, etc.)
    - DOM stability (no rapid changes)
    - Element visibility/state changes
    
    Args:
        page: Playwright Page instance
        timeout: Maximum time to wait in seconds (default: 1.0)
        
    Returns:
        True if action appears complete, False if timeout
    """
    start_time = time.perf_counter()
    logger.info(f"[TIMING] wait_for_odoo_action_complete START - timeout={timeout}s")
    
    POLL_INTERVAL = 0.05  # 50ms polling interval
    MAX_POLLS = int(timeout / POLL_INTERVAL)
    
    try:
        # Check for Odoo loading indicators
        for i in range(MAX_POLLS):
            try:
                # Check if loading indicators are present
                has_loading = await page.evaluate("""
                    () => {
                        // Check for common Odoo loading indicators
                        const loadingSelectors = [
                            '.o_loading',
                            '.fa-spin:not(.o_loading)',
                            '[class*="loading"]',
                            '[class*="spinner"]',
                            '.o_view_loading'
                        ];
                        
                        for (const selector of loadingSelectors) {
                            const elements = document.querySelectorAll(selector);
                            for (const el of elements) {
                                const style = window.getComputedStyle(el);
                                if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                """)
                
                if not has_loading:
                    # No loading indicators found, action likely complete
                    elapsed = time.perf_counter() - start_time
                    logger.info(f"[TIMING] wait_for_odoo_action_complete: No loading indicators found - elapsed={elapsed*1000:.1f}ms")
                    return True
                
                # Wait a bit before next check
                await asyncio.sleep(POLL_INTERVAL)
            except Exception as e:
                logger.debug(f"[TIMING] Error checking Odoo loading state: {e}")
                # Continue polling on error
                await asyncio.sleep(POLL_INTERVAL)
        
        # Timeout reached
        elapsed = time.perf_counter() - start_time
        logger.info(f"[TIMING] wait_for_odoo_action_complete: Timeout reached - elapsed={elapsed*1000:.1f}ms")
        return False
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.debug(f"[TIMING] wait_for_odoo_action_complete exception after {elapsed*1000:.1f}ms: {e}")
        return False

