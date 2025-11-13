#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session management for playwright-simple.

Handles saving and loading browser session state (cookies, localStorage, sessionStorage)
to enable test continuity.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from playwright.async_api import BrowserContext, Page


class SessionManager:
    """
    Manages browser session state persistence.
    
    Saves and loads cookies, localStorage, and sessionStorage to enable
    test continuity across multiple test executions.
    """
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            sessions_dir: Directory to store session files (defaults to .sessions/)
        """
        if sessions_dir is None:
            sessions_dir = Path.cwd() / ".sessions"
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_name: str) -> Path:
        """
        Get path to session file.
        
        Args:
            session_name: Name of the session
            
        Returns:
            Path to session JSON file
        """
        # Sanitize session name for filename
        safe_name = "".join(c for c in session_name if c.isalnum() or c in ('-', '_'))
        return self.sessions_dir / f"{safe_name}.json"
    
    async def save_session(
        self,
        context: BrowserContext,
        session_name: str,
        include_storage: bool = True
    ) -> Path:
        """
        Save browser session state.
        
        Args:
            context: Browser context to save state from
            session_name: Name to save session as
            include_storage: Whether to include localStorage/sessionStorage
            
        Returns:
            Path to saved session file
        """
        session_data: Dict[str, Any] = {}
        
        # Save cookies
        cookies = await context.cookies()
        session_data["cookies"] = cookies
        
        # Save storage if requested
        if include_storage:
            # Get storage from first page or create a temporary one
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
                try:
                    # Navigate to a page to access storage
                    await page.goto("about:blank")
                except Exception:
                    pass
            
            try:
                # Get localStorage
                localStorage_data = await page.evaluate("""
                    () => {
                        const data = {};
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            data[key] = localStorage.getItem(key);
                        }
                        return data;
                    }
                """)
                session_data["localStorage"] = localStorage_data
                
                # Get sessionStorage
                session_storage_data = await page.evaluate("""
                    () => {
                        const data = {};
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            data[key] = sessionStorage.getItem(key);
                        }
                        return data;
                    }
                """)
                session_data["sessionStorage"] = session_storage_data
            except Exception as e:
                # If storage access fails, continue without it
                print(f"  ⚠️  Warning: Could not save storage: {e}")
                session_data["localStorage"] = {}
                session_data["sessionStorage"] = {}
            
            # Close temporary page if we created it
            if not pages:
                try:
                    await page.close()
                except Exception:
                    pass
        
        # Save to file
        session_path = self._get_session_path(session_name)
        with open(session_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"  💾 Session saved: {session_name} -> {session_path}")
        return session_path
    
    async def load_session(
        self,
        context: BrowserContext,
        session_name: str,
        apply_storage: bool = True
    ) -> bool:
        """
        Load browser session state.
        
        Args:
            context: Browser context to load state into
            session_name: Name of session to load
            apply_storage: Whether to apply localStorage/sessionStorage
            
        Returns:
            True if session was loaded, False if not found
        """
        session_path = self._get_session_path(session_name)
        
        if not session_path.exists():
            print(f"  ⚠️  Session not found: {session_name} ({session_path})")
            return False
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        except Exception as e:
            print(f"  ❌ Error loading session {session_name}: {e}")
            return False
        
        # Load cookies
        if "cookies" in session_data:
            await context.add_cookies(session_data["cookies"])
        
        # Load storage if requested
        if apply_storage:
            # Get or create a page to set storage
            pages = context.pages
            if pages:
                page = pages[0]
            else:
                page = await context.new_page()
                try:
                    await page.goto("about:blank")
                except Exception:
                    pass
            
            try:
                # Set localStorage
                if "localStorage" in session_data:
                    localStorage_data = session_data["localStorage"]
                    await page.evaluate("""
                        (data) => {
                            for (const [key, value] of Object.entries(data)) {
                                localStorage.setItem(key, value);
                            }
                        }
                    """, localStorage_data)
                
                # Set sessionStorage
                if "sessionStorage" in session_data:
                    session_storage_data = session_data["sessionStorage"]
                    await page.evaluate("""
                        (data) => {
                            for (const [key, value] of Object.entries(data)) {
                                sessionStorage.setItem(key, value);
                            }
                        }
                    """, session_storage_data)
            except Exception as e:
                print(f"  ⚠️  Warning: Could not load storage: {e}")
            
            # Close temporary page if we created it
            if not pages:
                try:
                    await page.close()
                except Exception:
                    pass
        
        print(f"  📂 Session loaded: {session_name}")
        return True
    
    def delete_session(self, session_name: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_name: Name of session to delete
            
        Returns:
            True if deleted, False if not found
        """
        session_path = self._get_session_path(session_name)
        
        if not session_path.exists():
            return False
        
        try:
            session_path.unlink()
            print(f"  🗑️  Session deleted: {session_name}")
            return True
        except Exception as e:
            print(f"  ❌ Error deleting session {session_name}: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """
        List all saved sessions.
        
        Returns:
            List of session names
        """
        sessions = []
        for session_file in self.sessions_dir.glob("*.json"):
            # Remove .json extension to get session name
            session_name = session_file.stem
            sessions.append(session_name)
        return sorted(sessions)

