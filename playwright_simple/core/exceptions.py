#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom exceptions for playwright-simple.

Provides specific exceptions for better error handling and debugging.
All exceptions inherit from PlaywrightSimpleError for easy catching.
"""


class PlaywrightSimpleError(Exception):
    """
    Base exception for playwright-simple.
    
    All custom exceptions in playwright-simple inherit from this class,
    allowing easy catching of all playwright-simple errors.
    """
    pass


class ElementNotFoundError(PlaywrightSimpleError):
    """
    Raised when an element cannot be found.
    
    This exception is raised when a selector does not match any element
    on the page, or when an element is expected but not present.
    
    Example:
        ```python
        try:
            await test.click('.non-existent-element')
        except ElementNotFoundError as e:
            print(f"Element not found: {e}")
        ```
    """
    pass


class NavigationError(PlaywrightSimpleError):
    """
    Raised when navigation fails.
    
    This exception is raised when navigation to a URL fails, or when
    navigation validation fails (e.g., URL doesn't change as expected).
    
    Example:
        ```python
        try:
            await test.go_to("/invalid-url")
        except NavigationError as e:
            print(f"Navigation failed: {e}")
        ```
    """
    pass


class VideoProcessingError(PlaywrightSimpleError):
    """
    Raised when video processing fails.
    
    This exception is raised when video recording, processing, or conversion
    fails (e.g., FFmpeg errors, file system errors).
    
    Example:
        ```python
        try:
            await runner.run_test(test_func)
        except VideoProcessingError as e:
            print(f"Video processing failed: {e}")
        ```
    """
    pass


class ConfigurationError(PlaywrightSimpleError):
    """
    Raised when configuration is invalid.
    
    This exception is raised when test configuration contains invalid values
    or missing required parameters.
    
    Example:
        ```python
        try:
            config = TestConfig(base_url="")  # Invalid empty URL
        except ConfigurationError as e:
            print(f"Invalid configuration: {e}")
        ```
    """
    pass


class TTSGenerationError(PlaywrightSimpleError):
    """
    Raised when TTS (Text-to-Speech) generation fails.
    
    This exception is raised when TTS audio generation fails (e.g., API errors,
    file system errors, unsupported languages).
    
    Example:
        ```python
        try:
            await tts_manager.generate("Hello world")
        except TTSGenerationError as e:
            print(f"TTS generation failed: {e}")
        ```
    """
    pass


class ActionValidationError(PlaywrightSimpleError):
    """
    Raised when action validation fails.
    
    This exception is raised when an action (click, type, etc.) is performed
    but validation indicates it didn't have the expected effect (e.g., URL
    didn't change after navigation, element state didn't change).
    
    Example:
        ```python
        try:
            await test.click('.button')
            # Validation checks if click had effect
        except ActionValidationError as e:
            print(f"Action validation failed: {e}")
        ```
    """
    pass

