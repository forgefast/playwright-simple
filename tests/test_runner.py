#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for TestRunner class.
"""

import pytest
from playwright_simple import TestRunner, TestConfig


@pytest.mark.asyncio
async def test_runner_initialization():
    """Test TestRunner initialization."""
    config = TestConfig()
    runner = TestRunner(config=config)
    
    assert runner.config == config
    assert runner.video_manager is not None


@pytest.mark.asyncio
async def test_runner_get_summary():
    """Test getting execution summary."""
    config = TestConfig()
    runner = TestRunner(config=config)
    
    # Summary should be empty before running tests
    summary = runner.get_summary()
    assert summary == {}


@pytest.mark.asyncio
async def test_runner_get_results():
    """Test getting test results."""
    config = TestConfig()
    runner = TestRunner(config=config)
    
    # Results should be empty before running tests
    results = runner.get_results()
    assert results == []


