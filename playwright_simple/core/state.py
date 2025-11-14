#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State machine for test steps.

Each step knows:
- From where it came (previous state: cursor position, HTML, URL, etc.)
- What it does (the action)
- Where it goes (resulting state: new cursor position, new HTML, etc.)
"""

import logging
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WebState:
    """
    Represents the state of a web application at a point in time.
    
    This state is captured before and after each step, allowing steps to:
    - Know where they came from (previous state)
    - Know where they're going (resulting state)
    - Make decisions based on state changes
    """
    
    # URL and navigation
    url: str = ""
    title: str = ""
    
    # Cursor position
    cursor_x: Optional[float] = None
    cursor_y: Optional[float] = None
    
    # Page state
    scroll_x: float = 0.0
    scroll_y: float = 0.0
    viewport_width: int = 1920
    viewport_height: int = 1080
    
    # DOM state
    html_hash: Optional[str] = None  # Hash of HTML for quick comparison
    html_snapshot: Optional[str] = None  # Full HTML (optional, can be large)
    dom_ready: bool = False
    
    # Interactive elements
    visible_elements: List[Dict[str, Any]] = field(default_factory=list)
    focused_element: Optional[str] = None  # Selector of focused element
    
    # Page load state
    load_state: str = "none"  # none, load, domcontentloaded, networkidle
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Step information
    step_number: Optional[int] = None
    action_type: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    async def capture(cls, page, step_number: Optional[int] = None, action_type: Optional[str] = None) -> 'WebState':
        """
        Capture current state from a Playwright page.
        
        Args:
            page: Playwright Page instance
            step_number: Optional step number
            action_type: Optional action type
            
        Returns:
            WebState instance with current page state
        """
        state = cls()
        state.step_number = step_number
        state.action_type = action_type
        
        try:
            # URL and title
            state.url = page.url
            state.title = await page.title()
            
            # Cursor position (if available from cursor manager)
            cursor_manager = getattr(page, '_cursor_manager', None)
            if cursor_manager and hasattr(cursor_manager, 'get_position'):
                try:
                    pos = cursor_manager.get_position()
                    if pos:
                        state.cursor_x, state.cursor_y = pos
                except:
                    pass
            
            # Scroll position
            scroll_pos = await page.evaluate("() => ({ x: window.scrollX, y: window.scrollY })")
            if scroll_pos:
                state.scroll_x = scroll_pos.get('x', 0.0)
                state.scroll_y = scroll_pos.get('y', 0.0)
            
            # Viewport
            viewport = page.viewport_size
            if viewport:
                state.viewport_width = viewport.get('width', 1920)
                state.viewport_height = viewport.get('height', 1080)
            
            # DOM state
            try:
                html = await page.content()
                state.html_hash = hashlib.md5(html.encode()).hexdigest()
                # Only store full HTML if explicitly requested (can be large)
                # state.html_snapshot = html
            except:
                pass
            
            # Load state
            try:
                # Check if page is loaded
                state.dom_ready = await page.evaluate("() => document.readyState === 'complete'")
            except:
                pass
            
            # Focused element
            try:
                focused = await page.evaluate("""
                    () => {
                        const el = document.activeElement;
                        if (el && el !== document.body) {
                            // Try to get a meaningful selector
                            if (el.id) return '#' + el.id;
                            if (el.className) return '.' + el.className.split(' ')[0];
                            return el.tagName.toLowerCase();
                        }
                        return null;
                    }
                """)
                state.focused_element = focused
            except:
                pass
            
            # Visible interactive elements (simplified - can be expanded)
            try:
                visible_count = await page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
                        return Array.from(elements).filter(el => {
                            const rect = el.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0 && 
                                   window.getComputedStyle(el).visibility !== 'hidden' &&
                                   window.getComputedStyle(el).display !== 'none';
                        }).length;
                    }
                """)
                state.metadata['visible_interactive_elements'] = visible_count
            except:
                pass
            
        except Exception as e:
            logger.warning(f"Error capturing state: {e}")
        
        return state
    
    def changed_from(self, previous: 'WebState') -> Dict[str, Any]:
        """
        Compare this state with a previous state and return what changed.
        
        Args:
            previous: Previous WebState to compare with
            
        Returns:
            Dictionary with changed fields and their values
        """
        changes = {}
        
        if self.url != previous.url:
            changes['url'] = {'from': previous.url, 'to': self.url}
        
        if self.title != previous.title:
            changes['title'] = {'from': previous.title, 'to': self.title}
        
        if self.cursor_x != previous.cursor_x or self.cursor_y != previous.cursor_y:
            changes['cursor'] = {
                'from': (previous.cursor_x, previous.cursor_y),
                'to': (self.cursor_x, self.cursor_y)
            }
        
        if self.scroll_x != previous.scroll_x or self.scroll_y != previous.scroll_y:
            changes['scroll'] = {
                'from': (previous.scroll_x, previous.scroll_y),
                'to': (self.scroll_x, self.scroll_y)
            }
        
        if self.html_hash != previous.html_hash:
            changes['html'] = {'from': previous.html_hash, 'to': self.html_hash}
        
        if self.focused_element != previous.focused_element:
            changes['focus'] = {'from': previous.focused_element, 'to': self.focused_element}
        
        if self.load_state != previous.load_state:
            changes['load_state'] = {'from': previous.load_state, 'to': self.load_state}
        
        return changes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            'url': self.url,
            'title': self.title,
            'cursor': {'x': self.cursor_x, 'y': self.cursor_y},
            'scroll': {'x': self.scroll_x, 'y': self.scroll_y},
            'viewport': {'width': self.viewport_width, 'height': self.viewport_height},
            'html_hash': self.html_hash,
            'dom_ready': self.dom_ready,
            'focused_element': self.focused_element,
            'load_state': self.load_state,
            'step_number': self.step_number,
            'action_type': self.action_type,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebState':
        """Create state from dictionary."""
        state = cls()
        state.url = data.get('url', '')
        state.title = data.get('title', '')
        
        cursor = data.get('cursor', {})
        state.cursor_x = cursor.get('x')
        state.cursor_y = cursor.get('y')
        
        scroll = data.get('scroll', {})
        state.scroll_x = scroll.get('x', 0.0)
        state.scroll_y = scroll.get('y', 0.0)
        
        viewport = data.get('viewport', {})
        state.viewport_width = viewport.get('width', 1920)
        state.viewport_height = viewport.get('height', 1080)
        
        state.html_hash = data.get('html_hash')
        state.dom_ready = data.get('dom_ready', False)
        state.focused_element = data.get('focused_element')
        state.load_state = data.get('load_state', 'none')
        state.step_number = data.get('step_number')
        state.action_type = data.get('action_type')
        state.metadata = data.get('metadata', {})
        
        if 'timestamp' in data:
            state.timestamp = datetime.fromisoformat(data['timestamp'])
        
        return state
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WebState(step={self.step_number}, action={self.action_type}, "
            f"url={self.url[:50]}, cursor=({self.cursor_x}, {self.cursor_y}))"
        )

