#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test step with state machine implementation.

Each test step is a state machine that tracks its lifecycle:
pending -> starting -> executing -> waiting_for_load -> completed
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from statemachine import StateMachine, State

logger = logging.getLogger(__name__)


class TestStep(StateMachine):
    """
    Test step with state machine for tracking execution lifecycle.
    
    States:
    - pending: Step is waiting to be executed
    - starting: Step is about to start
    - executing: Step action is being executed
    - waiting_for_load: Step action completed, waiting for page to load
    - completed: Step finished successfully
    - failed: Step failed with an error
    """
    
    # Define states
    pending = State('Pending', initial=True)
    starting = State('Starting')
    executing = State('Executing')
    waiting_for_load = State('WaitingForLoad')
    completed = State('Completed', final=True)
    failed = State('Failed', final=True)
    
    # Define transitions
    start = pending.to(starting)
    execute = starting.to(executing)
    wait_load = executing.to(waiting_for_load)
    complete = waiting_for_load.to(completed)
    # Multiple states can transition to failed
    fail_from_starting = starting.to(failed)
    fail_from_executing = executing.to(failed)
    fail_from_waiting = waiting_for_load.to(failed)
    
    def __init__(
        self,
        step_number: int,
        action: Dict[str, Any],
        subtitle: Optional[str] = None,
        description: Optional[str] = None,
        video_start_time: Optional[datetime] = None,
        audio: Optional[str] = None
    ):
        """
        Initialize a test step.
        
        Args:
            step_number: Sequential number of the step
            action: Action dictionary from YAML
            subtitle: Subtitle text for this step (can be shared with following steps)
            description: Description of the step
            video_start_time: Reference time when video recording started
            audio: Audio text for this step (can be shared with following steps, similar to subtitle)
        """
        super().__init__()
        self.step_number = step_number
        self.action = action
        self.subtitle = subtitle
        self.description = description or subtitle
        self.video_start_time = video_start_time or datetime.now()
        self.audio = audio
        
        # Timing information
        self.start_time: Optional[datetime] = None
        self.execute_time: Optional[datetime] = None
        self.wait_load_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # Calculated properties
        self._start_seconds: Optional[float] = None
        self._end_seconds: Optional[float] = None
        self._duration: Optional[float] = None
        
        # Error information
        self.error: Optional[Exception] = None
        self.error_message: Optional[str] = None
        
        # Action validation information
        self.element_found: Optional[bool] = None
        self.action_succeeded: Optional[bool] = None
        self.warnings: List[str] = []
        self.action_details: Dict[str, Any] = {}
    
    def on_start(self):
        """Called when transitioning to starting state."""
        self.start_time = datetime.now()
        self._start_seconds = (self.start_time - self.video_start_time).total_seconds()
        if self._start_seconds < 0:
            self._start_seconds = 0
        
        action_type = list(self.action.keys())[0] if self.action else "unknown"
        logger.info(
            f"Step {self.step_number}: pending -> starting | "
            f"Action: {action_type} | "
            f"Time: {self.start_time.strftime('%H:%M:%S.%f')[:-3]} | "
            f"Video offset: {self._start_seconds:.3f}s"
        )
    
    def on_execute(self):
        """Called when transitioning to executing state."""
        self.execute_time = datetime.now()
        action_type = list(self.action.keys())[0] if self.action else "unknown"
        logger.info(
            f"Step {self.step_number}: starting -> executing | "
            f"Action: {action_type} | "
            f"Time: {self.execute_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
        
        # Log action details if available
        if self.action_details:
            details_str = ", ".join([f"{k}={v}" for k, v in self.action_details.items()])
            logger.info(f"Step {self.step_number}: Action details: {details_str}")
    
    def on_wait_load(self):
        """Called when transitioning to waiting_for_load state."""
        self.wait_load_time = datetime.now()
        logger.info(
            f"Step {self.step_number}: executing -> waiting_for_load | "
            f"Time: {self.wait_load_time.strftime('%H:%M:%S.%f')[:-3]}"
        )
    
    def on_complete(self):
        """Called when transitioning to completed state."""
        self.end_time = datetime.now()
        self._end_seconds = (self.end_time - self.video_start_time).total_seconds()
        self._duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        # Build status message
        status_parts = []
        if self.element_found is not None:
            status_parts.append(f"Element found: {'✅' if self.element_found else '❌'}")
        if self.action_succeeded is not None:
            status_parts.append(f"Action succeeded: {'✅' if self.action_succeeded else '❌'}")
        if self.warnings:
            status_parts.append(f"Warnings: {len(self.warnings)}")
        
        status_str = " | ".join(status_parts) if status_parts else ""
        
        logger.info(
            f"Step {self.step_number}: waiting_for_load -> completed | "
            f"Time: {self.end_time.strftime('%H:%M:%S.%f')[:-3]} | "
            f"Duration: {self._duration:.3f}s | "
            f"Video offset: {self._end_seconds:.3f}s"
            + (f" | {status_str}" if status_str else "")
        )
        
        # Log warnings if any
        if self.warnings:
            for warning in self.warnings:
                logger.warning(f"Step {self.step_number}: {warning}")
    
    def on_fail(self):
        """Called when transitioning to failed state."""
        self.end_time = datetime.now()
        self._end_seconds = (self.end_time - self.video_start_time).total_seconds()
        self._duration = (self.end_time - self.start_time).total_seconds() if self.start_time else 0
        
        error_info = f" | Error: {self.error_message}" if self.error_message else ""
        logger.error(
            f"Step {self.step_number}: -> failed | "
            f"Time: {self.end_time.strftime('%H:%M:%S.%f')[:-3]} | "
            f"Duration: {self._duration:.3f}s{error_info}"
        )
    
    @property
    def start_time_seconds(self) -> float:
        """
        Get start time in seconds relative to video start.
        
        For subtitles, we use execute_time (when action actually starts)
        instead of start_time (when step preparation begins).
        This ensures subtitles appear when the action is visible.
        
        For screenshots, we use start_time (slightly before) to give context.
        """
        # Check if this is a screenshot action (instantaneous, no visual change)
        is_screenshot = 'screenshot' in (self.action or {})
        
        if is_screenshot:
            # For screenshots, use start_time (slightly before) to give context
            # This allows subtitle to appear before the screenshot is taken
            return self._start_seconds or 0.0
        else:
            # For actions with visual effects, use execute_time (when action actually happens)
            # Fall back to start_time if execute_time not available yet
            if self.execute_time and self.video_start_time:
                execute_seconds = (self.execute_time - self.video_start_time).total_seconds()
                if execute_seconds >= 0:
                    return execute_seconds
            return self._start_seconds or 0.0
    
    @property
    def end_time_seconds(self) -> float:
        """Get end time in seconds relative to video start."""
        return self._end_seconds or (self.start_time_seconds + (self.duration or 0.0))
    
    @property
    def duration(self) -> Optional[float]:
        """Get duration in seconds."""
        return self._duration
    
    def fail_with_error(self, error: Exception):
        """
        Mark step as failed with an error.
        
        Args:
            error: Exception that caused the failure
        """
        self.error = error
        self.error_message = str(error)
        # Transition to failed state based on current state
        if self.current_state == self.starting:
            self.fail_from_starting()
        elif self.current_state == self.executing:
            self.fail_from_executing()
        elif self.current_state == self.waiting_for_load:
            self.fail_from_waiting()
        else:
            # If in pending or already final state, just set error info
            logger.warning(f"Cannot transition to failed from state: {self.current_state.id}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert step to dictionary for compatibility with existing code.
        
        Returns:
            Dictionary with step information
        """
        return {
            'text': self.subtitle or self.description or f'Passo {self.step_number}',
            'description': self.description or self.subtitle or f'Passo {self.step_number}',
            'subtitle': self.subtitle,
            'start_time': self.start_time_seconds,
            'duration': self.duration or 0.0,
            'end_time': self.end_time_seconds,
            'step_number': self.step_number,
            'state': self.current_state.id,
            'action': self.action,
            'element_found': self.element_found,
            'action_succeeded': self.action_succeeded,
            'warnings': self.warnings,
            'action_details': self.action_details
        }
    
    def __repr__(self) -> str:
        """String representation of the step."""
        state = self.current_state.id if hasattr(self, 'current_state') else 'pending'
        return (
            f"TestStep(#{self.step_number}, state={state}, "
            f"subtitle='{self.subtitle}', duration={self.duration:.3f}s)"
        )

