#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor transition manager for controlling step transitions.

The cursor manages the transition between steps, ensuring a minimum
wait time before allowing the next step to start.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CursorTransitionManager:
    """
    Manages transitions between test steps using cursor control.
    
    Ensures a minimum delay between steps to allow for visual transitions
    and prevent steps from executing too quickly.
    """
    
    def __init__(self, transition_delay: float = 0.3):
        """
        Initialize cursor transition manager.
        
        Args:
            transition_delay: Minimum delay in seconds between steps (default: 0.3s)
        """
        self.transition_delay = transition_delay
        self.cursor_manager = None
    
    def set_cursor_manager(self, cursor_manager):
        """
        Set the cursor manager for visual cursor movement.
        
        Args:
            cursor_manager: Cursor manager instance
        """
        self.cursor_manager = cursor_manager
    
    async def wait_for_transition(
        self,
        from_step_number: Optional[int] = None,
        to_step_number: Optional[int] = None
    ):
        """
        Wait for transition between steps.
        
        This method:
        1. Waits for the minimum transition delay
        2. Optionally moves cursor visually to indicate transition
        
        Args:
            from_step_number: Number of the step we're transitioning from
            to_step_number: Number of the step we're transitioning to
        """
        if from_step_number and to_step_number:
            logger.debug(
                f"Cursor transition: Step {from_step_number} -> Step {to_step_number} | "
                f"Delay: {self.transition_delay}s"
            )
        elif from_step_number:
            logger.debug(
                f"Cursor transition: After Step {from_step_number} | "
                f"Delay: {self.transition_delay}s"
            )
        
        # Wait for minimum transition delay
        await asyncio.sleep(self.transition_delay)
        
        # Optionally, move cursor visually if cursor_manager is available
        # This can be implemented later if needed for visual feedback
        # if self.cursor_manager:
        #     await self.cursor_manager.move_to_next_position()
    
    async def wait_before_step_start(self, step_number: int):
        """
        Wait before starting a new step.
        
        This is called before a step transitions to 'starting' state.
        
        Args:
            step_number: Number of the step about to start
        """
        logger.debug(f"Cursor: Waiting before starting Step {step_number}")
        await self.wait_for_transition(to_step_number=step_number)
    
    async def wait_after_step_complete(self, step_number: int):
        """
        Wait after completing a step.
        
        This is called after a step transitions to 'completed' state.
        
        Args:
            step_number: Number of the step that just completed
        """
        logger.debug(f"Cursor: Waiting after completing Step {step_number}")
        await self.wait_for_transition(from_step_number=step_number)

