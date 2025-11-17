#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main CursorController class.

Coordinates all cursor modules.
"""

from typing import Optional
from playwright.async_api import Page
import logging
import asyncio

from .visual import CursorVisual
from .movement import CursorMovement
from .interaction import CursorInteraction

logger = logging.getLogger(__name__)

# Import SpeedLevel for type hints
try:
    from ..config import SpeedLevel
except ImportError:
    # Fallback if not available
    SpeedLevel = None


class CursorController:
    """Controls a visual cursor overlay in the browser."""
    
    def __init__(self, page: Page, fast_mode: bool = False, speed_level=None, recorder_logger=None):
        """Initialize cursor controller.
        
        Args:
            page: Playwright Page instance
            fast_mode: If True, reduce delays for faster execution (deprecated, use speed_level)
            speed_level: SpeedLevel enum (preferred over fast_mode)
            recorder_logger: Optional RecorderLogger instance for logging
        """
        self.page = page
        self.is_active = False
        self.current_x = 0
        self.current_y = 0
        self.fast_mode = fast_mode  # Keep for backward compatibility
        # Determine speed_level: use provided, or map from fast_mode, or default to NORMAL
        if speed_level is None:
            if SpeedLevel is not None:
                if fast_mode:
                    self.speed_level = SpeedLevel.FAST
                else:
                    self.speed_level = SpeedLevel.NORMAL
            else:
                self.speed_level = None
        else:
            self.speed_level = speed_level
        self.recorder_logger = recorder_logger
        
        # Initialize modules
        self._visual = CursorVisual(page)
        self._movement = CursorMovement(page, self)
        self._interaction = CursorInteraction(page, self)
    
    async def start(self, force: bool = False, initial_x: int = None, initial_y: int = None):
        """
        Start cursor controller and inject cursor overlay.
        
        Automatically shows the cursor and sets up navigation listener.
        
        Args:
            force: Force reinjection even if already active
            initial_x: Initial X position (None = center or last position)
            initial_y: Initial Y position (None = center or last position)
        """
        await self._visual.start(force, initial_x, initial_y)
        self.is_active = self._visual.is_active
        
        # Always update position from page storage (for navigation persistence)
        # Try sessionStorage first, then window property
        position = await self.page.evaluate("""
            () => {
                // Try sessionStorage first (more reliable across navigations)
                try {
                    const stored = sessionStorage.getItem('__playwright_cursor_last_position');
                    if (stored) {
                        return JSON.parse(stored);
                    }
                } catch (e) {
                    // sessionStorage might not be available
                }
                // Fallback to window property
                return window.__playwright_cursor_last_position || null;
            }
        """)
        if position:
            self.current_x = position.get('x', 0)
            self.current_y = position.get('y', 0)
            self._movement.current_x = self.current_x
            self._movement.current_y = self.current_y
        elif initial_x is not None and initial_y is not None:
            # Use provided initial position
            self.current_x = initial_x
            self.current_y = initial_y
            self._movement.current_x = initial_x
            self._movement.current_y = initial_y
        
        # Automatically show cursor after initialization
        await self.show()
        
        # Automatically set up navigation listener (only if not already set up)
        if not hasattr(self, '_navigation_listener_setup'):
            self.setup_navigation_listener()
            self._navigation_listener_setup = True
    
    async def show(self):
        """Show cursor overlay."""
        await self._visual.show()
    
    async def hide(self):
        """Hide cursor overlay."""
        await self._visual.hide()
    
    async def move(self, x: int, y: int, smooth: bool = True):
        """Move cursor to position."""
        await self._movement.move(x, y, smooth)
        self.current_x = self._movement.current_x
        self.current_y = self._movement.current_y
    
    async def click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Click at cursor position or specified coordinates."""
        await self._interaction.click(x, y)
        # Update position if coordinates provided
        if x is not None and y is not None:
            self.current_x = x
            self.current_y = y
    
    async def click_by_text(self, text: str) -> bool:
        """Click on element by text."""
        return await self._interaction.click_by_text(text)
    
    async def click_by_selector(self, selector: str) -> bool:
        """Click on element by CSS selector."""
        return await self._interaction.click_by_selector(selector)
    
    async def click_by_role(self, role: str, index: int = 0) -> bool:
        """Click on element by ARIA role."""
        return await self._interaction.click_by_role(role, index)
    
    async def wait_for_navigation_after_action(self, timeout: float = 5.0) -> bool:
        """
        Wait for navigation after an action (click, submit, etc.).
        
        This method encapsulates the navigation waiting logic from EventCapture._handle_navigation.
        It waits for the framenavigated event and then waits for the page to stabilize.
        
        Args:
            timeout: Maximum time to wait for navigation event (default: 5.0 seconds)
            
        Returns:
            True if navigation occurred, False otherwise
        """
        logger.info(f"[DEBUG] [CURSOR] wait_for_navigation_after_action: INÍCIO (timeout={timeout}s)")
        try:
            logger.info(f"[DEBUG] [CURSOR] Aguardando evento 'framenavigated'...")
            # Wait for navigation event (same as EventCapture does)
            await asyncio.wait_for(
                self.page.wait_for_event('framenavigated'),
                timeout=timeout
            )
            logger.info(f"[DEBUG] [CURSOR] ✓ Evento 'framenavigated' detectado!")
            
            # Wait for page to stabilize (same logic as EventCapture._handle_navigation)
            try:
                logger.info(f"[DEBUG] [CURSOR] Aguardando domcontentloaded (timeout=10s)...")
                # Wait for DOM to be ready
                await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                logger.info(f"[DEBUG] [CURSOR] ✓ domcontentloaded OK")
            except Exception as e:
                logger.info(f"[DEBUG] [CURSOR] ⚠ DOM ready timeout: {e}")
                # Try to wait for at least document.readyState
                try:
                    logger.info(f"[DEBUG] [CURSOR] Tentando wait_for_function (document.readyState)...")
                    await self.page.wait_for_function(
                        "document.readyState === 'interactive' || document.readyState === 'complete'",
                        timeout=5000
                    )
                    logger.info(f"[DEBUG] [CURSOR] ✓ document.readyState OK")
                except Exception as e2:
                    logger.info(f"[DEBUG] [CURSOR] ⚠ wait_for_function timeout: {e2}")
            
            # Wait for body to exist (ensures DOM is usable)
            try:
                logger.info(f"[DEBUG] [CURSOR] Aguardando seletor 'body'...")
                await self.page.wait_for_selector('body', timeout=5000, state='attached')
                logger.info(f"[DEBUG] [CURSOR] ✓ Body encontrado")
            except Exception as e:
                logger.info(f"[DEBUG] [CURSOR] ⚠ Body não encontrado: {e}")
            
            # Restore cursor after navigation (same as setup_navigation_listener does)
            logger.info(f"[DEBUG] [CURSOR] Restaurando cursor após navegação...")
            await self.start(force=True)
            await self.show()
            logger.info(f"[DEBUG] [CURSOR] ✓ Cursor restaurado")
            
            logger.info(f"[DEBUG] [CURSOR] wait_for_navigation_after_action: FIM (retornando True)")
            return True
        except asyncio.TimeoutError:
            # No navigation event within timeout
            logger.info(f"[DEBUG] [CURSOR] ⚠ Timeout: Nenhum evento 'framenavigated' em {timeout}s")
            logger.info(f"[DEBUG] [CURSOR] wait_for_navigation_after_action: FIM (retornando False)")
            return False
        except Exception as e:
            logger.warning(f"[DEBUG] [CURSOR] ⚠ Erro aguardando navegação: {e}", exc_info=True)
            logger.info(f"[DEBUG] [CURSOR] wait_for_navigation_after_action: FIM (retornando False)")
            return False
    
    def setup_navigation_listener(self):
        """
        Set up navigation listener to restore cursor after navigation.
        
        This method registers a 'framenavigated' event listener that restores
        the cursor position after page navigations. Used by both recording and playback.
        
        The logic is identical to what the recorder uses, encapsulated here for reuse.
        
        Note: This method is idempotent - calling it multiple times will only register
        one listener. However, it's recommended to check _navigation_listener_setup
        before calling to avoid unnecessary work.
        """
        # Prevent multiple registrations
        if hasattr(self, '_navigation_listener_setup') and self._navigation_listener_setup:
            return
        async def on_navigation(frame):
            """Restore cursor position after navigation."""
            try:
                # Only handle main frame navigation
                if frame != self.page.main_frame:
                    return
                
                # Wait for page to be ready using dynamic waits
                # First, wait for DOM to be ready (with reasonable timeout)
                try:
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                except Exception as e:
                    logger.debug(f"DOM ready timeout, continuing: {e}")
                    # Try to wait for at least document.readyState
                    try:
                        await self.page.wait_for_function(
                            "document.readyState === 'interactive' || document.readyState === 'complete'",
                            timeout=5000
                        )
                    except:
                        pass  # Continue even if timeout
                
                # Wait for body to exist (ensures DOM is usable)
                try:
                    await self.page.wait_for_selector('body', timeout=5000, state='attached')
                except:
                    pass  # Continue even if timeout
                
                # Get last position from storage (persists across navigations)
                # Try multiple times as storage might not be immediately available after navigation
                position = None
                for attempt in range(5):  # More attempts for reliability
                    try:
                        position = await self.page.evaluate("""
                            () => {
                                // Try sessionStorage first (more reliable across navigations)
                                try {
                                    const stored = sessionStorage.getItem('__playwright_cursor_last_position');
                                    if (stored) {
                                        return JSON.parse(stored);
                                    }
                                } catch (e) {
                                    // sessionStorage might not be available
                                }
                                // Fallback to window property
                                return window.__playwright_cursor_last_position || null;
                            }
                        """)
                        if position and position.get('x') and position.get('y'):
                            break
                        # Wait for storage to be available using dynamic wait
                        try:
                            await self.page.wait_for_function(
                                "(() => { try { return sessionStorage.getItem('__playwright_cursor_last_position') !== null; } catch(e) { return window.__playwright_cursor_last_position !== undefined; } })()",
                                timeout=300
                            )
                        except:
                            pass  # Continue to next attempt
                    except:
                        pass  # Continue to next attempt
                
                if position and position.get('x') and position.get('y'):
                    x = int(position.get('x'))
                    y = int(position.get('y'))
                    # Always restore cursor (force=True to reinject even if "active")
                    await self.start(force=True, initial_x=x, initial_y=y)
                    # Also update controller's current position
                    self.current_x = x
                    self.current_y = y
                    self._movement.current_x = x
                    self._movement.current_y = y
                    # Garantir que cursor esteja visível após restauração
                    await self.show()
                    logger.info(f"Cursor restored after navigation: ({x}, {y})")
                else:
                    # No saved position, start at center
                    await self.start(force=True)
                    # Garantir que cursor esteja visível após restauração
                    await self.show()
                    logger.info("Cursor restored after navigation (center)")
            except Exception as e:
                logger.warning(f"Error restoring cursor after navigation: {e}")
                # Try to restore anyway, even if there was an error
                try:
                    await self.start(force=True)
                    await self.show()
                except:
                    pass
        
        # Register navigation listener
        self.page.on('framenavigated', on_navigation)
        
        # Mark as set up to prevent multiple registrations
        self._navigation_listener_setup = True
    
    async def type_text(self, text: str, field_selector: Optional[str] = None) -> bool:
        """Type text into a field."""
        return await self._interaction.type_text(text, field_selector)
    
    async def submit_form(self, button_text: Optional[str] = None) -> bool:
        """Submit a form by clicking the submit button."""
        return await self._interaction.submit_form(button_text)
    
    async def press_key(self, key: str):
        """Press a key."""
        await self._interaction.press_key(key)
    
    async def get_element_at(self, x: int, y: int) -> Optional[dict]:
        """Get element information at cursor position."""
        return await self._interaction.get_element_at(x, y)
    
    async def stop(self):
        """Stop cursor controller."""
        await self._visual.stop()
        self.is_active = False

