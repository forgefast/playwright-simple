#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Odoo version detector.
"""

import pytest
from playwright_simple.odoo.version_detector import (
    normalize_version,
    extract_version_from_classes,
    get_version_info,
    is_community,
    is_enterprise,
)


def test_normalize_version():
    """Test version normalization."""
    assert normalize_version("14.0") == "14.0"
    assert normalize_version("14.0.1") == "14.0"
    assert normalize_version("14") == "14.0"
    assert normalize_version("v14.0") == "14.0"
    assert normalize_version("18.0.1") == "18.0"


def test_extract_version_from_classes():
    """Test version extraction from CSS classes."""
    assert extract_version_from_classes("o_odoo_14") == "14.0"
    assert extract_version_from_classes("odoo-15") == "15.0"
    assert extract_version_from_classes("version-16") == "16.0"
    assert extract_version_from_classes("") is None


def test_get_version_info():
    """Test version info retrieval."""
    info = get_version_info("14.0")
    assert info["version"] == "14.0"
    assert info["major"] == 14
    assert info["minor"] == 0
    
    info = get_version_info("18.0")
    assert info["major"] == 18


def test_is_community():
    """Test community detection."""
    # By default, assumes community
    assert is_community() is True
    assert is_community("14.0") is True


def test_is_enterprise():
    """Test enterprise detection."""
    # By default, assumes not enterprise
    assert is_enterprise() is False

