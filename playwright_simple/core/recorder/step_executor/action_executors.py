#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Action executors module.

Provides executors for different step actions (go_to, click, type, submit, wait).
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)


class ActionExecutors:
    """Executors for different step actions."""
    
    def __init__(
        self,
        page,
        command_handlers,
        recorder_logger=None,
        speed_level=None,
        wait_for_page_stable: Optional[Callable] = None
    ):
        """
        Initialize action executors.
        
        Args:
            page: Playwright page object
            command_handlers: Command handlers instance
            recorder_logger: Optional recorder logger
            speed_level: Optional speed level configuration
            wait_for_page_stable: Function to wait for page to stabilize
        """
        self.page = page
        self.command_handlers = command_handlers
        self.recorder_logger = recorder_logger
        self.speed_level = speed_level
        self._wait_for_page_stable = wait_for_page_stable
    
    async def execute_go_to(self, step: Dict[str, Any], step_num: int):
        """Execute go_to action."""
        url = step.get('url')
        if not url:
            return
        
        if self.recorder_logger:
            self.recorder_logger.log_screen_event(
                event_type='navigation',
                page_state={'url': url, 'previous_url': self.page.url if hasattr(self.page, 'url') else ''}
            )
        
        await self.page.goto(url, wait_until='domcontentloaded')
        
        if self._wait_for_page_stable:
            await self._wait_for_page_stable(timeout=10.0)
        
        if self.recorder_logger:
            try:
                page_title = await self.page.title()
            except:
                page_title = 'N/A'
            self.recorder_logger.log_screen_event(
                event_type='page_loaded',
                page_state={'url': self.page.url, 'title': page_title}
            )
    
    async def execute_click(self, step: Dict[str, Any], step_num: int):
        """Execute click action."""
        text = step.get('text')
        selector = step.get('selector')
        
        try:
            await self.page.wait_for_load_state('domcontentloaded', timeout=5000)
        except:
            pass
        
        if text:
            result = await self.command_handlers.handle_pw_click(f'"{text}"')
        elif selector:
            result = await self.command_handlers.handle_pw_click(f'selector "{selector}"')
        else:
            logger.warning(f"Click step has no text or selector: {step}")
            result = {'success': False, 'error': 'No text or selector'}
        
        if self.recorder_logger:
            duration_ms = self.recorder_logger.end_action_timer(f"step_{step_num}_click")
            element_info = {'text': text, 'selector': selector} if text or selector else None
            try:
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            page_state = {
                'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                'title': page_title
            }
            self.recorder_logger.log_step_execution(
                step_number=step_num,
                action='click',
                success=result.get('success', False) if result else False,
                duration_ms=duration_ms,
                error=result.get('error') if result else None,
                element_info=element_info,
                page_state=page_state
            )
        
        if self._wait_for_page_stable:
            await self._wait_for_page_stable(timeout=10.0)
    
    async def execute_type(self, step: Dict[str, Any], step_num: int):
        """Execute type action."""
        text = step.get('text', '')
        selector = step.get('selector')
        field_text = step.get('field_text')
        
        if selector:
            result = await self.command_handlers.handle_pw_type(f'"{text}" selector "{selector}"')
        elif field_text:
            result = await self.command_handlers.handle_pw_type(f'"{text}" into "{field_text}"')
        else:
            result = await self.command_handlers.handle_pw_type(f'"{text}"')
        
        if self.recorder_logger:
            duration_ms = self.recorder_logger.end_action_timer(f"step_{step_num}_type")
            element_info = {'field': field_text or selector, 'text': text}
            try:
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            page_state = {
                'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                'title': page_title
            }
            self.recorder_logger.log_step_execution(
                step_number=step_num,
                action='type',
                success=result.get('success', False) if result else False,
                duration_ms=duration_ms,
                error=result.get('error') if result else None,
                element_info=element_info,
                page_state=page_state
            )
        
        if self._wait_for_page_stable:
            await self._wait_for_page_stable(timeout=5.0)
    
    async def execute_submit(self, step: Dict[str, Any], step_num: int):
        """Execute submit action."""
        button_text = step.get('button_text') or step.get('text')
        
        if button_text:
            result = await self.command_handlers.handle_pw_submit(f'"{button_text}"')
        else:
            result = await self.command_handlers.handle_pw_submit('')
        
        if self.recorder_logger:
            duration_ms = self.recorder_logger.end_action_timer(f"step_{step_num}_submit")
            element_info = {'button_text': button_text}
            try:
                if hasattr(self.page, 'title'):
                    page_title = await self.page.title()
                else:
                    page_title = 'N/A'
            except:
                page_title = 'N/A'
            page_state = {
                'url': self.page.url if hasattr(self.page, 'url') else 'N/A',
                'title': page_title
            }
            self.recorder_logger.log_step_execution(
                step_number=step_num,
                action='submit',
                success=result.get('success', False) if result else False,
                duration_ms=duration_ms,
                error=result.get('error') if result else None,
                element_info=element_info,
                page_state=page_state
            )
        
        if self._wait_for_page_stable:
            await self._wait_for_page_stable(timeout=10.0)
    
    async def execute_wait(self, step: Dict[str, Any], step_num: int):
        """Execute wait action."""
        seconds = step.get('seconds', 1.0)
        
        if self.speed_level:
            multiplier = self.speed_level.get_multiplier()
            min_delay = self.speed_level.get_min_delay()
            seconds = max(seconds * multiplier, min_delay)
        
        await asyncio.sleep(seconds)
        
        if self.recorder_logger:
            duration_ms = self.recorder_logger.end_action_timer(f"step_{step_num}_wait")
            self.recorder_logger.log_step_execution(
                step_number=step_num,
                action='wait',
                success=True,
                duration_ms=duration_ms,
                details={'wait_seconds': seconds}
            )

