#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Authentication methods for SimpleTestBase.

Contains generic login method for web applications.
"""

import asyncio
import logging
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .exceptions import ElementNotFoundError

logger = logging.getLogger(__name__)


class AuthMixin:
    """
    Mixin providing authentication methods for test base classes.
    
    This mixin provides generic login methods that work with common web
    application login forms. It assumes the base class has:
    - page: Playwright Page instance
    - config: TestConfig instance
    - go_to: Method to navigate to URL
    - type: Method to type text into fields
    - click: Method to click elements
    - _ensure_cursor: Method to ensure cursor is injected
    """
    
    async def login(
        self,
        username: str,
        password: str,
        login_url: str = "/login",
        show_process: bool = False
    ) -> 'AuthMixin':
        """
        Login to system with common selectors.
        
        Attempts to find and fill username/password fields using common
        selectors, then submits the form. Works with most standard web
        application login forms.
        
        Args:
            username: Username to login with
            password: Password to login with
            login_url: URL of login page (default: "/login")
            show_process: Whether to show login process in logs
            
        Returns:
            Self for method chaining
            
        Raises:
            ElementNotFoundError: If login fields or submit button not found
            NavigationError: If navigation to login page fails
            
        Example:
            ```python
            await test.login("admin", "password123")
            await test.login("user", "pass", login_url="/auth/login")
            ```
        """
        if not username:
            raise ValueError("Username cannot be empty")
        if not password:
            raise ValueError("Password cannot be empty")
        
        if show_process:
            logger.info(f"Logging in as {username}...")
        
        try:
            await self.go_to(login_url)
            await asyncio.sleep(0.3)
            
            # Try common login field selectors
            login_selectors = [
                'input[name="username"]',
                'input[name="login"]',
                'input[name="email"]',
                'input[type="text"]',
                'input[type="email"]',
                '#username',
                '#login',
                '#email',
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                '#password',
            ]
            
            submit_selectors = [
                'button[type="submit"]',
                'button:has-text("Entrar")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
            ]
            
            # Fill username
            username_filled = False
            for selector in login_selectors:
                try:
                    await self.type(selector, username, "Username field")
                    username_filled = True
                    break
                except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                    logger.debug(f"Username selector '{selector}' failed: {e}")
                    continue
                except Exception as e:
                    logger.warning(
                        f"Unexpected error with username selector '{selector}': {e}"
                    )
                    continue
            
            if not username_filled:
                raise ElementNotFoundError(
                    "Username field not found. Tried common selectors: "
                    f"{', '.join(login_selectors)}"
                )
            
            await asyncio.sleep(0.2)
            
            # Fill password
            password_filled = False
            for selector in password_selectors:
                try:
                    await self.type(selector, password, "Password field")
                    password_filled = True
                    break
                except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                    logger.debug(f"Password selector '{selector}' failed: {e}")
                    continue
                except Exception as e:
                    logger.warning(
                        f"Unexpected error with password selector '{selector}': {e}"
                    )
                    continue
            
            if not password_filled:
                raise ElementNotFoundError(
                    "Password field not found. Tried common selectors: "
                    f"{', '.join(password_selectors)}"
                )
            
            await asyncio.sleep(0.2)
            
            # Submit
            submit_clicked = False
            for selector in submit_selectors:
                try:
                    await self.click(selector, "Login button")
                    submit_clicked = True
                    break
                except (ElementNotFoundError, PlaywrightTimeoutError) as e:
                    logger.debug(f"Submit selector '{selector}' failed: {e}")
                    continue
                except Exception as e:
                    logger.warning(
                        f"Unexpected error with submit selector '{selector}': {e}"
                    )
                    continue
            
            if not submit_clicked:
                raise ElementNotFoundError(
                    "Login submit button not found. Tried common selectors: "
                    f"{', '.join(submit_selectors)}"
                )
            
            await asyncio.sleep(0.3)
            await self.page.wait_for_load_state(
                "load",
                timeout=self.config.browser.timeout
            )
            await asyncio.sleep(0.1)
        except ElementNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Login failed for user '{username}': {e}")
            raise
        
        return self

