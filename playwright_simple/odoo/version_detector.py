#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo version detection module.

Detects Odoo version automatically from the web interface.
Supports Odoo versions 14, 15, 16, 17, and 18.
"""

import re
from typing import Optional, Dict, Any
from playwright.async_api import Page


async def detect_version(page: Page) -> Optional[str]:
    """
    Detect Odoo version automatically.
    
    Tries multiple strategies:
    1. JavaScript window.odoo.version_info
    2. DOM attributes (data-version, version-info)
    3. URL patterns (/web/webclient/version_info)
    4. CSS classes specific to versions
    5. HTML meta tags
    
    Args:
        page: Playwright page instance
        
    Returns:
        Version string (e.g., "14.0", "15.0", "16.0", "17.0", "18.0") or None if not detected
    """
    try:
        # Strategy 1: JavaScript window.odoo.version_info
        version = await page.evaluate("""
            () => {
                if (window.odoo && window.odoo.version_info) {
                    return window.odoo.version_info[0] + '.' + window.odoo.version_info[1];
                }
                return null;
            }
        """)
        if version:
            return normalize_version(version)
    except Exception:
        pass
    
    try:
        # Strategy 2: Check for version in DOM attributes
        version_attr = await page.get_attribute('html', 'data-version')
        if version_attr:
            return normalize_version(version_attr)
    except Exception:
        pass
    
    try:
        # Strategy 3: Check meta tags
        meta_version = await page.get_attribute('meta[name="version"]', 'content')
        if meta_version:
            return normalize_version(meta_version)
    except Exception:
        pass
    
    try:
        # Strategy 4: Check CSS classes on body/html
        body_classes = await page.get_attribute('body', 'class')
        if body_classes:
            version = extract_version_from_classes(body_classes)
            if version:
                return normalize_version(version)
    except Exception:
        pass
    
    try:
        # Strategy 5: Try to fetch version info endpoint
        response = await page.request.get(f"{page.url.split('/web')[0]}/web/webclient/version_info")
        if response.ok:
            data = await response.json()
            if isinstance(data, dict) and 'server_version' in data:
                return normalize_version(data['server_version'])
    except Exception:
        pass
    
    try:
        # Strategy 6: Check for version in JavaScript variables
        version = await page.evaluate("""
            () => {
                // Try odoo.session_info
                if (window.odoo && window.odoo.session_info && window.odoo.session_info.server_version) {
                    return window.odoo.session_info.server_version;
                }
                // Try odoo._version
                if (window.odoo && window.odoo._version) {
                    return window.odoo._version;
                }
                return null;
            }
        """)
        if version:
            return normalize_version(version)
    except Exception:
        pass
    
    return None


def normalize_version(version: str) -> str:
    """
    Normalize version string to major.minor format.
    
    Args:
        version: Version string (e.g., "14.0", "14.0.1", "14", "v14.0")
        
    Returns:
        Normalized version (e.g., "14.0", "15.0")
    """
    if not version:
        return None
    
    # Remove 'v' prefix and extract numbers
    version = str(version).strip().lower().lstrip('v')
    
    # Extract major and minor version numbers
    match = re.match(r'(\d+)\.?(\d+)?', version)
    if match:
        major = match.group(1)
        minor = match.group(2) or '0'
        return f"{major}.{minor}"
    
    # If only major version is found
    match = re.match(r'(\d+)', version)
    if match:
        return f"{match.group(1)}.0"
    
    return None


def extract_version_from_classes(classes: str) -> Optional[str]:
    """
    Extract version from CSS classes.
    
    Args:
        classes: Space-separated CSS classes
        
    Returns:
        Version string or None
    """
    if not classes:
        return None
    
    # Look for patterns like o_odoo_14, odoo-14, version-14, etc.
    patterns = [
        r'o_odoo_(\d+)',
        r'odoo-(\d+)',
        r'version-(\d+)',
        r'v(\d+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, classes, re.IGNORECASE)
        if match:
            return f"{match.group(1)}.0"
    
    return None


def is_community(version: Optional[str] = None) -> bool:
    """
    Check if version is Community Edition.
    
    Note: This is a heuristic. Enterprise edition detection
    is usually done by checking for enterprise-specific features.
    
    Args:
        version: Version string (optional, for future use)
        
    Returns:
        True if Community, False otherwise
    """
    # By default, assume Community unless Enterprise features are detected
    # This can be enhanced by checking for enterprise modules/features
    return True


def is_enterprise(version: Optional[str] = None) -> bool:
    """
    Check if version is Enterprise Edition.
    
    Args:
        version: Version string (optional, for future use)
        
    Returns:
        True if Enterprise, False otherwise
    """
    return not is_community(version)


def get_version_info(version: str) -> Dict[str, Any]:
    """
    Get information about a specific Odoo version.
    
    Args:
        version: Version string (e.g., "14.0", "15.0")
        
    Returns:
        Dictionary with version information
    """
    major = int(version.split('.')[0]) if version else 0
    
    return {
        "version": version,
        "major": major,
        "minor": int(version.split('.')[1]) if '.' in version else 0,
        "is_community": is_community(version),
        "is_enterprise": is_enterprise(version),
        "supports_web_responsive": major >= 14,
        "supports_new_ui": major >= 16,
    }


async def detect_edition(page: Page) -> str:
    """
    Detect if Odoo is Community or Enterprise edition.
    
    Args:
        page: Playwright page instance
        
    Returns:
        "community" or "enterprise"
    """
    try:
        # Check for enterprise-specific elements/classes
        enterprise_indicators = [
            'body.o_enterprise',
            '.o_enterprise',
            '[data-enterprise="true"]',
        ]
        
        for indicator in enterprise_indicators:
            element = page.locator(indicator).first
            if await element.count() > 0:
                return "enterprise"
        
        # Check JavaScript
        is_enterprise = await page.evaluate("""
            () => {
                if (window.odoo && window.odoo.session_info) {
                    return window.odoo.session_info.is_enterprise || false;
                }
                return false;
            }
        """)
        
        if is_enterprise:
            return "enterprise"
    except Exception:
        pass
    
    return "community"

