#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Event capture module.

Captures browser events using injected JavaScript.
"""

import asyncio
import logging
from typing import Dict, Any, Callable, List
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class EventCapture:
    """Captures browser events for recording."""
    
    def __init__(self, page: Page, debug: bool = False):
        """Initialize event capture."""
        self.page = page
        self.debug = debug
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.is_capturing = False
        self.last_url = None
        self.last_scroll_position = None
    
    def on_event(self, event_type: str, handler: Callable):
        """Register event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    import inspect
                    if inspect.iscoroutinefunction(handler):
                        # Schedule async handler
                        asyncio.create_task(handler(data))
                    else:
                        # Sync handler
                        handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def start(self):
        """Start capturing events."""
        if self.is_capturing:
            return
        
        self.is_capturing = True
        self.last_url = self.page.url
        
        # Inject script and wait a bit for it to initialize
        # CRITICAL: Inject script immediately to catch early clicks
        await self._inject_capture_script()
        await asyncio.sleep(0.2)  # Reduced delay - script should be ready faster now
        
        # Verify script is working
        is_working = await self.page.evaluate("""
            () => {
                const initialized = !!(window.__playwright_recording_initialized && window.__playwright_recording_events);
                const hasListeners = document.addEventListener.toString().includes('native code');
                // Check if click listener is actually attached by checking event listeners count
                const hasClickHandler = typeof window.__playwright_recording_events !== 'undefined';
                return { 
                    initialized: initialized, 
                    hasListeners: hasListeners,
                    hasClickHandler: hasClickHandler,
                    eventsArrayReady: Array.isArray(window.__playwright_recording_events)
                };
            }
        """)
        
        if not is_working.get('initialized') or not is_working.get('eventsArrayReady'):
            logger.warning("Script injection may have failed, retrying...")
            await self._inject_capture_script()
            await asyncio.sleep(0.5)  # Increased wait time
            
            # Verify again
            is_working = await self.page.evaluate("""
                () => {
                    return {
                        initialized: !!(window.__playwright_recording_initialized && window.__playwright_recording_events),
                        eventsArrayReady: Array.isArray(window.__playwright_recording_events)
                    };
                }
            """)
            
            if not is_working.get('initialized') or not is_working.get('eventsArrayReady'):
                logger.error("Script injection failed after retry - events may not be captured!")
        
        if self.debug:
            logger.info(f"🔍 DEBUG: Script verification - Initialized: {is_working.get('initialized')}, Listeners available: {is_working.get('hasListeners')}")
            
            # Test if click listener is actually attached
            test_result = await self.page.evaluate("""
                () => {
                    // Check if we can see the event listeners
                    let hasClickListener = false;
                    try {
                        // Try to trigger a test click event
                        const testEl = document.createElement('div');
                        document.body.appendChild(testEl);
                        testEl.click();
                        document.body.removeChild(testEl);
                        hasClickListener = true;
                    } catch (e) {
                        // Ignore
                    }
                    return {
                        hasClickListener: hasClickListener,
                        eventArrayExists: !!window.__playwright_recording_events,
                        eventArrayLength: (window.__playwright_recording_events || []).length
                    };
                }
            """)
            logger.info(f"🔍 DEBUG: Click listener test: {test_result}")
        
        self.page.on('framenavigated', self._handle_navigation)
        
        # Start polling tasks
        poll_task = asyncio.create_task(self._poll_events())
        scroll_task = asyncio.create_task(self._monitor_scroll())
        
        # Do MULTIPLE immediate polls to catch any events that happened during initialization
        # This is CRITICAL for capturing the first click on pages that load quickly
        for poll_attempt in range(3):  # Try 3 times with increasing delays
            await asyncio.sleep(0.05 * (poll_attempt + 1))  # 0.05s, 0.1s, 0.15s
            try:
                result = await self.page.evaluate("""
                    () => {
                        const events = window.__playwright_recording_events || [];
                        const count = events.length;
                        // Don't clear yet - let polling handle it to avoid race conditions
                        return { events: events.slice(), count: count };
                    }
                """)
                events = result.get('events', [])
                if events:
                    logger.info(f"Immediate poll #{poll_attempt + 1} caught {len(events)} event(s) from initialization")
                    # Process events but don't clear array yet (polling will handle it)
                    for event in events:
                        await self._process_event(event)
                    # Now clear the array
                    await self.page.evaluate("""
                        () => {
                            window.__playwright_recording_events = [];
                        }
                    """)
            except Exception as e:
                if "Execution context was destroyed" not in str(e):
                    logger.debug(f"Error in immediate poll #{poll_attempt + 1}: {e}")
        
        logger.info("Event capture started - polling active")
    
    async def stop(self):
        """Stop capturing events."""
        self.is_capturing = False
        logger.info("Event capture stopped")
    
    async def _inject_capture_script(self):
        """Inject JavaScript to capture events."""
        # Inject script that will run on every navigation
        async def inject_on_page():
            try:
                await self.page.evaluate("""
                    (function() {
                        // Check if already initialized to avoid duplicate listeners
                        if (window.__playwright_recording_initialized) {
                            console.log('[Playwright] Script already initialized, skipping');
                            return;
                        }
                        window.__playwright_recording_initialized = true;
                        // Initialize events array if not already done by init script
                        if (!window.__playwright_recording_events) {
                            window.__playwright_recording_events = [];
                        }
                        
                        function serializeElement(element) {
                            if (!element) return null;
                            try {
                                // Get text - prefer innerText over textContent for buttons/links
                                let text = '';
                                const tag = element.tagName?.toUpperCase();
                                
                                if (tag === 'BUTTON' || tag === 'A') {
                                    // For buttons and links, get the visible text
                                    text = (element.innerText || element.textContent || '').trim();
                                    // If no text, try value attribute (for input buttons)
                                    if (!text && element.value) {
                                        text = element.value.trim();
                                    }
                                } else if (tag === 'INPUT') {
                                    // For inputs, prefer value, then placeholder
                                    text = (element.value || element.placeholder || '').trim();
                                } else {
                                    // For other elements, get text but limit length
                                    text = (element.innerText || element.textContent || '').trim();
                                    // Limit to first 100 chars to avoid getting entire page text
                                    if (text.length > 100) {
                                        text = text.substring(0, 100);
                                    }
                                }
                                
                                // Get label for inputs
                                let label = '';
                                if (element.labels && element.labels.length > 0) {
                                    label = (element.labels[0].textContent || '').trim();
                                }
                                
                                return {
                                    tagName: element.tagName || '',
                                    text: text,
                                    id: element.id || '',
                                    className: element.className || '',
                                    href: element.href || '',
                                    type: element.type || '',
                                    name: element.name || '',
                                    value: element.value || '',
                                    role: (element.getAttribute && element.getAttribute('role')) || '',
                                    ariaLabel: (element.getAttribute && element.getAttribute('aria-label')) || '',
                                    placeholder: element.placeholder || '',
                                    label: label
                                };
                            } catch (e) {
                                return null;
                            }
                        }
                        
                        // Helper function to check if element is truly interactive
                        function isInteractiveElement(element) {
                            if (!element) return false;
                            
                            const tag = element.tagName?.toUpperCase();
                            
                            // Standard interactive elements
                            if (tag === 'BUTTON' || tag === 'A' || tag === 'INPUT' || 
                                tag === 'SELECT' || tag === 'TEXTAREA' || tag === 'LABEL') {
                                return true;
                            }
                            
                            // Elements with interactive roles
                            const role = element.getAttribute('role');
                            if (role === 'button' || role === 'link' || role === 'tab' || 
                                role === 'menuitem' || role === 'option' || role === 'checkbox' ||
                                role === 'radio' || role === 'switch') {
                                return true;
                            }
                            
                            // Elements with click handlers
                            if (element.getAttribute('onclick') || 
                                element.getAttribute('data-action') ||
                                element.getAttribute('data-toggle') ||
                                element.getAttribute('data-target')) {
                                return true;
                            }
                            
                            // Elements with tabindex (focusable)
                            const tabindex = element.getAttribute('tabindex');
                            if (tabindex !== null && tabindex !== '-1') {
                                return true;
                            }
                            
                            // Elements with cursor pointer style (often clickable)
                            const style = window.getComputedStyle(element);
                            if (style.cursor === 'pointer') {
                                // But check if it's not just a text element
                                if (tag !== 'DIV' && tag !== 'SPAN' && tag !== 'P') {
                                    return true;
                                }
                                // For DIV/SPAN with pointer, check if it has meaningful content
                                if (element.textContent.trim().length > 0 && element.textContent.trim().length < 100) {
                                    return true;
                                }
                            }
                            
                            // Check if element has event listeners (complex check)
                            // Elements that are commonly clickable
                            if (element.classList && (
                                element.classList.contains('btn') ||
                                element.classList.contains('button') ||
                                element.classList.contains('clickable') ||
                                element.classList.contains('menu-item') ||
                                element.classList.contains('dropdown') ||
                                element.classList.contains('modal-trigger')
                            )) {
                                return true;
                            }
                            
                            return false;
                        }
                        
                        // Helper function to find the actual interactive element
                        function findInteractiveElement(element) {
                            if (!element) return null;
                            
                            // If element is already interactive, return it
                            if (isInteractiveElement(element)) {
                                return element;
                            }
                            
                            // Look for interactive child element
                            const interactiveChild = element.querySelector('button, a, input, select, textarea, [role="button"], [role="link"], [role="tab"], [onclick], [tabindex]:not([tabindex="-1"])');
                            if (interactiveChild && isInteractiveElement(interactiveChild)) {
                                return interactiveChild;
                            }
                            
                            // Look for interactive parent (click might be on a child of button)
                            let parent = element.parentElement;
                            let depth = 0;
                            while (parent && parent !== document.body && depth < 5) {
                                if (isInteractiveElement(parent)) {
                                    return parent;
                                }
                                parent = parent.parentElement;
                                depth++;
                            }
                            
                            return null;
                        }
                        
                        // Click listener with capture phase (true = capture phase, catches events before they bubble)
                        // CRITICAL: This must capture ALL clicks, especially the first one on page load
                        document.addEventListener('click', function(e) {
                            try {
                                if (!e.target) {
                                    return; // Ignore clicks without target
                                }
                                
                                // Find the actual interactive element
                                const interactiveEl = findInteractiveElement(e.target);
                                
                                // Only record clicks on interactive elements
                                if (!interactiveEl) {
                                    return; // Ignore clicks on non-interactive elements
                                }
                                
                                const serialized = serializeElement(interactiveEl);
                                if (serialized) {
                                    // Only record if element has meaningful interaction
                                    const tag = serialized.tagName?.toUpperCase();
                                    const hasText = serialized.text && serialized.text.trim().length > 0;
                                    const hasId = serialized.id && serialized.id.length > 0;
                                    const hasName = serialized.name && serialized.name.length > 0;
                                    const hasHref = serialized.href && serialized.href.length > 0;
                                    
                                    // IMPORTANT: Links (A tags) should ALWAYS be captured, even without text
                                    // This is critical for capturing the first "Entrar" link on Odoo homepage
                                    if (tag === 'A' && hasHref) {
                                        // Always capture links, even if they don't have visible text
                                        // (text might be in child elements or CSS)
                                        // Also check for text in child elements if not in direct text
                                        if (!serialized.text || serialized.text.trim().length === 0) {
                                            // Try to get text from child elements
                                            const childText = interactiveEl.textContent || interactiveEl.innerText || '';
                                            if (childText.trim().length > 0) {
                                                serialized.text = childText.trim();
                                            }
                                        }
                                        const eventData = {
                                            type: 'click',
                                            timestamp: Date.now(),
                                            element: serialized
                                        };
                                        window.__playwright_recording_events.push(eventData);
                                        console.log('[Playwright] Click captured (LINK):', serialized.tagName, serialized.href, serialized.text?.substring(0, 50) || 'no text', 'Events in queue:', window.__playwright_recording_events.length);
                                        return; // Early return for links
                                    }
                                    
                                    // Skip if it's a generic container without meaningful content
                                    if ((tag === 'DIV' || tag === 'MAIN' || tag === 'SECTION' || tag === 'ARTICLE') && 
                                        !hasText && !hasId && !hasName && !hasHref) {
                                        return; // Ignore clicks on empty containers
                                    }
                                    
                                    const eventData = {
                                        type: 'click',
                                        timestamp: Date.now(),
                                        element: serialized
                                    };
                                    window.__playwright_recording_events.push(eventData);
                                    // Debug: log to console
                                    console.log('[Playwright] Click captured:', serialized.tagName, serialized.text?.substring(0, 50), serialized.id || serialized.name || '', 'Events in queue:', window.__playwright_recording_events.length);
                                }
                            } catch (err) {
                                console.error('[Playwright] Error in click listener:', err);
                            }
                        }, true);  // Use capture phase to catch all clicks
                        
                        document.addEventListener('input', function(e) {
                            const target = e.target;
                            
                            // Only capture input events on actual input/textarea elements
                            if (!target) {
                                return; // Ignore if no target
                            }
                            
                            const tag = target.tagName?.toUpperCase();
                            if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
                                return; // Ignore input events on non-input elements
                            }
                            
                            // Additional check: ensure it's a real input field
                            const inputType = target.type?.toLowerCase();
                            const isContentEditable = target.isContentEditable;
                            
                            // Skip contentEditable divs and other non-standard inputs
                            if (isContentEditable && tag !== 'INPUT' && tag !== 'TEXTAREA') {
                                return;
                            }
                            
                            // Skip hidden inputs
                            if (inputType === 'hidden') {
                                return;
                            }
                            
                            const serialized = serializeElement(target);
                            if (serialized) {
                                window.__playwright_recording_events.push({
                                    type: 'input',
                                    timestamp: Date.now(),
                                    element: serialized,
                                    value: target.value || ''
                                });
                                console.log('[Playwright] Input captured:', tag, inputType || '', serialized.name || serialized.id || '');
                            }
                        }, true);
                        
                        document.addEventListener('keydown', function(e) {
                            if (e.key === 'Enter' || e.key === 'Tab' || e.key === 'Escape') {
                                const target = e.target;
                                
                                // Only capture keydown on interactive elements or inputs
                                if (!target) {
                                    return;
                                }
                                
                                const tag = target.tagName?.toUpperCase();
                                const isInput = tag === 'INPUT' || tag === 'TEXTAREA';
                                const isInteractive = tag === 'BUTTON' || tag === 'A' || 
                                                      target.getAttribute('role') === 'button' ||
                                                      target.getAttribute('tabindex') !== null;
                                
                                // Only capture if it's an input or interactive element
                                if (!isInput && !isInteractive) {
                                    return; // Ignore keydown on non-interactive elements
                                }
                                
                                const serialized = serializeElement(target);
                                if (serialized) {
                                    window.__playwright_recording_events.push({
                                        type: 'keydown',
                                        timestamp: Date.now(),
                                        element: serialized,
                                        key: e.key
                                    });
                                    console.log('[Playwright] Keydown captured:', e.key, serialized.tagName || '');
                                } else {
                                    console.warn('[Playwright] Keydown but serialization failed:', e.key, e.target);
                                }
                            }
                        }, true);
                    })();
                """)
            except Exception as e:
                if "Execution context was destroyed" not in str(e):
                    logger.debug(f"Error injecting script: {e}")
        
        # Inject on page load (runs before page content loads)
        # This ensures the events array exists even before DOM is ready
        await self.page.add_init_script("""
            (function() {
                if (!window.__playwright_recording_events) {
                    window.__playwright_recording_events = [];
                }
                // Mark as ready for injection (but don't mark as fully initialized yet)
                window.__playwright_recording_ready_for_injection = true;
            })();
        """)
        
        # Also inject after page loads and on DOMContentLoaded
        # CRITICAL: Inject as early as possible to catch first clicks
        async def on_load():
            await asyncio.sleep(0.05)  # Reduced delay for faster injection
            await inject_on_page()
        
        async def on_dom_content_loaded():
            # Inject immediately on DOMContentLoaded - this is critical for catching first clicks
            await inject_on_page()
        
        # Register listeners BEFORE injecting to catch early events
        self.page.on('load', on_load)
        self.page.on('domcontentloaded', on_dom_content_loaded)
        
        # Inject immediately if page is already loaded
        await inject_on_page()
    
    async def _poll_events(self):
        """Poll for JavaScript events."""
        poll_count = 0
        # Start polling immediately (no initial delay) to catch early clicks
        while self.is_capturing:
            try:
                poll_count += 1
                
                # Check if script is initialized
                is_initialized = await self.page.evaluate("""
                    () => {
                        return !!(window.__playwright_recording_initialized && window.__playwright_recording_events);
                    }
                """)
                
                if not is_initialized:
                    logger.warning("⚠️  Recording script not initialized, reinjecting...")
                    if self.debug:
                        logger.info("🔍 DEBUG: Script reinjection triggered")
                    await self._inject_capture_script()
                    await asyncio.sleep(0.2)
                    continue
                
                # Get events and also check event count before clearing
                result = await self.page.evaluate("""
                    () => {
                        const events = window.__playwright_recording_events || [];
                        const count = events.length;
                        window.__playwright_recording_events = [];
                        return { events: events, count: count };
                    }
                """)
                
                events = result.get('events', [])
                event_count = result.get('count', 0)
                
                # Log polling status every 50 polls in debug mode
                if self.debug and poll_count % 50 == 0:
                    logger.debug(f"🔍 DEBUG: Poll #{poll_count} - Script initialized: {is_initialized}, Events in queue: {event_count}")
                
                if events:
                    if self.debug:
                        logger.info(f"🔍 DEBUG: Polled {len(events)} event(s) from page: {[e.get('type', 'unknown') for e in events]}")
                        for event in events:
                            logger.info(f"🔍 DEBUG: Event details: {event}")
                    else:
                        logger.info(f"Polled {len(events)} event(s) from page: {[e.get('type', 'unknown') for e in events]}")
                
                for event in events:
                    await self._process_event(event)
                
                # Use shorter delay for first few polls to catch initial clicks faster
                delay = 0.05 if poll_count <= 10 else 0.1
                await asyncio.sleep(delay)
            except Exception as e:
                # Ignore context destroyed errors (happens during navigation)
                if "Execution context was destroyed" not in str(e):
                    if self.debug:
                        logger.error(f"🔍 DEBUG: Error polling events: {e}", exc_info=True)
                    else:
                        logger.debug(f"Error polling events: {e}")
                await asyncio.sleep(0.5)
    
    async def _process_event(self, event_data: Dict[str, Any]):
        """Process a single event."""
        event_type = event_data.get('type')
        if self.debug:
            logger.info(f"🔍 DEBUG: Processing event: {event_type} - {event_data}")
        else:
            logger.debug(f"Processing event: {event_type}")
        
        if event_type == 'click':
            await self._handle_click(event_data)
        elif event_type == 'input':
            await self._handle_input(event_data)
        elif event_type == 'blur':
            await self._handle_blur(event_data)
        elif event_type == 'keydown':
            await self._handle_keydown(event_data)
        else:
            if self.debug:
                logger.warning(f"🔍 DEBUG: Unknown event type: {event_type} - {event_data}")
            else:
                logger.debug(f"Unknown event type: {event_type}")
    
    async def _handle_blur(self, event_data: Dict[str, Any]):
        """Handle blur event - finalize input."""
        try:
            element_info = event_data.get('element')
            if element_info:
                logger.debug(f"Emitting blur event to finalize input")
                self._emit_event('blur', {
                    'element': element_info,
                    'value': event_data.get('value', ''),
                    'timestamp': event_data.get('timestamp')
                })
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.debug(f"Error handling blur: {e}")
    
    async def _handle_click(self, event_data: Dict[str, Any]):
        """Handle click event."""
        try:
            # Element is already serialized in the injected script
            element_info = event_data.get('element')
            if element_info:
                tag = element_info.get('tagName', 'UNKNOWN')
                text = element_info.get('text', '')[:50]
                if self.debug:
                    logger.info(f"🔍 DEBUG: Click detected - Tag: {tag}, Text: '{text}', ID: {element_info.get('id', '')}, Name: {element_info.get('name', '')}")
                else:
                    logger.debug(f"Emitting click event for element: {tag} - {text}")
                self._emit_event('click', {
                    'element': element_info,
                    'timestamp': event_data.get('timestamp')
                })
            else:
                logger.warning("Click event without element info")
                if self.debug:
                    logger.warning(f"🔍 DEBUG: Click event data: {event_data}")
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.error(f"Error handling click: {e}", exc_info=True)
    
    async def _handle_input(self, event_data: Dict[str, Any]):
        """Handle input event."""
        try:
            # Element is already serialized in the injected script
            element_info = event_data.get('element')
            value = event_data.get('value', '')
            if element_info:
                logger.debug(f"Emitting input event for element: {element_info.get('tagName')} - value length: {len(value)}")
                self._emit_event('input', {
                    'element': element_info,
                    'value': value,
                    'timestamp': event_data.get('timestamp')
                })
            else:
                logger.warning("Input event without element info")
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.debug(f"Error handling input: {e}")
    
    async def _handle_keydown(self, event_data: Dict[str, Any]):
        """Handle keydown event."""
        try:
            # Element is already serialized in the injected script
            element_info = event_data.get('element')
            if element_info:
                self._emit_event('keydown', {
                    'element': element_info,
                    'key': event_data.get('key'),
                    'timestamp': event_data.get('timestamp')
                })
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.debug(f"Error handling keydown: {e}")
    
    async def _handle_navigation(self, frame):
        """Handle navigation event."""
        if frame != self.page.main_frame:
            return
        
        try:
            new_url = self.page.url
            if new_url != self.last_url:
                self._emit_event('navigation', {
                    'url': new_url,
                    'previous_url': self.last_url
                })
                self.last_url = new_url
                
                # Wait for page to stabilize using dynamic waits
                try:
                    # Wait for DOM to be ready
                    await self.page.wait_for_load_state('domcontentloaded', timeout=10000)
                except Exception as e:
                    logger.debug(f"DOM ready timeout during script reinjection, continuing: {e}")
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
                
                try:
                    # CRITICAL: Process any pending events BEFORE clearing the array
                    # This ensures clicks that happened just before navigation are captured
                    pending_events = await self.page.evaluate("""
                        () => {
                            const events = window.__playwright_recording_events || [];
                            return events;
                        }
                    """)
                    
                    # Process pending events before navigation clears them
                    if pending_events:
                        logger.info(f"Processing {len(pending_events)} pending event(s) before navigation")
                        for event in pending_events:
                            try:
                                await self._process_event(event)
                            except Exception as e:
                                logger.debug(f"Error processing pending event before navigation: {e}")
                    
                    # Reset flag and reinject
                    await self.page.evaluate("""
                        (function() {
                            window.__playwright_recording_initialized = false;
                            window.__playwright_recording_events = [];
                        })();
                    """)
                    # Reinject the full script
                    await self._reinject_script()
                    logger.debug(f"Script reinjected after navigation to {new_url}")
                except Exception as e:
                    if "Execution context was destroyed" not in str(e):
                        logger.debug(f"Error reinjecting script: {e}")
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.debug(f"Error handling navigation: {e}")
    
    async def _reinject_script(self):
        """Reinject the capture script (used after navigation)."""
        try:
            await self.page.evaluate("""
                (function() {
                    if (window.__playwright_recording_initialized) return;
                    window.__playwright_recording_initialized = true;
                    window.__playwright_recording_events = [];
                    
                    function serializeElement(element) {
                        if (!element) return null;
                        try {
                            return {
                                tagName: element.tagName || '',
                                text: (element.textContent || '').trim(),
                                id: element.id || '',
                                className: element.className || '',
                                href: element.href || '',
                                type: element.type || '',
                                name: element.name || '',
                                value: element.value || '',
                                role: (element.getAttribute && element.getAttribute('role')) || '',
                                ariaLabel: (element.getAttribute && element.getAttribute('aria-label')) || '',
                                placeholder: element.placeholder || '',
                                label: (element.labels && element.labels.length > 0) 
                                    ? (element.labels[0].textContent || '').trim() 
                                    : ''
                            };
                        } catch (e) {
                            return null;
                        }
                    }
                    
                    document.addEventListener('click', function(e) {
                        if (e.target) {
                            const serialized = serializeElement(e.target);
                            if (serialized) {
                                window.__playwright_recording_events.push({
                                    type: 'click',
                                    timestamp: Date.now(),
                                    element: serialized
                                });
                            }
                        }
                    }, true);
                    
                    document.addEventListener('input', function(e) {
                        const target = e.target;
                        
                        // Only capture input events on actual input/textarea elements
                        if (!target) {
                            return; // Ignore if no target
                        }
                        
                        const tag = target.tagName?.toUpperCase();
                        if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
                            return; // Ignore input events on non-input elements
                        }
                        
                        // Additional check: ensure it's a real input field
                        const inputType = target.type?.toLowerCase();
                        const isContentEditable = target.isContentEditable;
                        
                        // Skip contentEditable divs and other non-standard inputs
                        if (isContentEditable && tag !== 'INPUT' && tag !== 'TEXTAREA') {
                            return;
                        }
                        
                        // Skip hidden inputs
                        if (inputType === 'hidden') {
                            return;
                        }
                        
                        const serialized = serializeElement(target);
                        if (serialized) {
                            window.__playwright_recording_events.push({
                                type: 'input',
                                timestamp: Date.now(),
                                element: serialized,
                                value: target.value || ''
                            });
                        }
                    }, true);
                    
                    // Also capture blur to finalize input
                    document.addEventListener('blur', function(e) {
                        const target = e.target;
                        
                        // Only capture blur events on actual input/textarea elements
                        if (!target) {
                            return; // Ignore if no target
                        }
                        
                        const tag = target.tagName?.toUpperCase();
                        if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
                            return; // Ignore blur events on non-input elements
                        }
                        
                        // Skip hidden inputs
                        const inputType = target.type?.toLowerCase();
                        if (inputType === 'hidden') {
                            return;
                        }
                        
                        const serialized = serializeElement(target);
                        if (serialized) {
                            window.__playwright_recording_events.push({
                                type: 'blur',
                                timestamp: Date.now(),
                                element: serialized,
                                value: target.value || ''
                            });
                        }
                    }, true);
                    
                    document.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === 'Tab' || e.key === 'Escape') {
                            const serialized = serializeElement(e.target);
                            if (serialized) {
                                window.__playwright_recording_events.push({
                                    type: 'keydown',
                                    timestamp: Date.now(),
                                    element: serialized,
                                    key: e.key
                                });
                            }
                        }
                    }, true);
                })();
            """)
        except Exception as e:
            if "Execution context was destroyed" not in str(e):
                logger.debug(f"Error in _reinject_script: {e}")
    
    async def _monitor_scroll(self):
        """Monitor scroll events."""
        while self.is_capturing:
            try:
                scroll_info = await self.page.evaluate("""
                    () => ({
                        scrollX: window.scrollX,
                        scrollY: window.scrollY
                    })
                """)
                
                current = (scroll_info['scrollX'], scroll_info['scrollY'])
                
                if self.last_scroll_position is None:
                    self.last_scroll_position = current
                elif abs(current[0] - self.last_scroll_position[0]) > 50 or \
                     abs(current[1] - self.last_scroll_position[1]) > 50:
                    self._emit_event('scroll', scroll_info)
                    self.last_scroll_position = current
                
                await asyncio.sleep(0.5)
            except Exception as e:
                # Ignore context destroyed errors (happens during navigation)
                if "Execution context was destroyed" not in str(e):
                    logger.debug(f"Error monitoring scroll: {e}")
                await asyncio.sleep(1)
