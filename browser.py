"""
GoLogin Browser Manager
Handles browser automation using GoLogin anti-detect browser with Playwright
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from loguru import logger

from config import config
from gologin_client import GoLoginClient, GoLoginAPIError


class GoLoginBrowser:
    """
    GoLogin Browser Manager using Playwright
    Handles browser automation with anti-detect features
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.profile_id = None
        self._playwright = None
        self.ws_url = None
        self.client = None
        
    def _get_client(self) -> GoLoginClient:
        """Get or create GoLogin client"""
        if not config.gologin.token:
            raise ValueError("GoLogin API token is required. Get it from https://app.gologin.com/")
        
        if not self.client:
            self.client = GoLoginClient(token=config.gologin.token)
        return self.client
    
    async def initialize(self) -> None:
        """Initialize Playwright"""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            logger.info("Playwright initialized")
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            raise
    
    async def create_profile(self, name: str = "REI Checker Profile") -> Dict[str, Any]:
        """Create a new browser profile using quick profile"""
        client = self._get_client()
        
        try:
            # Use quick profile creation (simplest method)
            profile = client.create_quick_profile(name=name, os_type="win")
            logger.info(f"Created GoLogin profile: {profile.get('id', 'unknown')}")
            return profile
        except GoLoginAPIError as e:
            logger.error(f"Failed to create profile: {e}")
            raise
    
    async def list_profiles(self) -> List[Dict[str, Any]]:
        """List all browser profiles"""
        client = self._get_client()
        
        try:
            profiles = client.list_profiles()
            logger.info(f"Found {len(profiles)} profiles")
            return profiles
        except GoLoginAPIError as e:
            logger.error(f"Failed to list profiles: {e}")
            return []
    
    async def delete_profile(self, profile_id: str) -> None:
        """Delete a browser profile"""
        client = self._get_client()
        
        try:
            client.delete_profiles([profile_id])
            logger.info(f"Deleted profile: {profile_id}")
        except GoLoginAPIError as e:
            logger.error(f"Failed to delete profile: {e}")
    
    async def start_browser(self, profile_id: str) -> str:
        """Start browser with GoLogin profile, return WebSocket URL"""
        client = self._get_client()
        
        try:
            # Run profile on cloud browser
            result = client.run_profile_cloud(profile_id)
            
            # The result should contain WebSocket URL or connection info
            ws_url = result.get("wsUrl") or result.get("data", {}).get("wsUrl")
            
            if not ws_url:
                # Try alternative: use get_cloud_connect_url
                ws_url = client.get_cloud_connect_url(profile_id)
            
            logger.info(f"Browser started with profile: {profile_id}")
            self.ws_url = ws_url
            self.profile_id = profile_id
            return ws_url
            
        except GoLoginAPIError as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def stop_browser(self, profile_id: str) -> None:
        """Stop browser"""
        client = self._get_client()
        
        try:
            client.stop_profile_cloud(profile_id)
            logger.info(f"Browser stopped for profile: {profile_id}")
        except GoLoginAPIError as e:
            logger.warning(f"Failed to stop browser: {e}")
    
    async def connect(self, ws_url: str) -> None:
        """Connect to GoLogin browser using Playwright CDP"""
        if not self._playwright:
            await self.initialize()
        
        try:
            # Connect to Cloud Browser via WebSocket
            self.browser = await self._playwright.chromium.connect_over_cdp(ws_url)
            
            # Get context or create new one
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = await self.browser.new_context(
                    viewport={
                        "width": config.browser.viewport_width,
                        "height": config.browser.viewport_height
                    }
                )
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(config.browser.page_load_timeout)
            
            logger.info("Connected to GoLogin browser via Playwright CDP")
            
        except Exception as e:
            logger.error(f"Failed to connect to browser: {e}")
            raise
    
    async def launch(self, profile_name: str = "REI Checker", 
                     use_existing: bool = True, 
                     profile_id: Optional[str] = None) -> None:
        """
        Launch browser with GoLogin profile
        
        Args:
            profile_name: Name for new profile if created
            use_existing: Use existing profile if available
            profile_id: Use specific profile ID
        """
        # Check token first
        if not config.gologin.token:
            raise ValueError("GoLogin API token is required. Get it from https://app.gologin.com/")
        
        target_profile_id = profile_id or config.gologin.profile_id
        
        # If no profile specified, create new or use existing
        if not target_profile_id:
            if use_existing:
                profiles = await self.list_profiles()
                if profiles and len(profiles) > 0:
                    target_profile_id = profiles[0].get("id")
                    logger.info(f"Using existing profile: {target_profile_id}")
                else:
                    new_profile = await self.create_profile(profile_name)
                    target_profile_id = new_profile.get("id")
            else:
                new_profile = await self.create_profile(profile_name)
                target_profile_id = new_profile.get("id")
        
        if not target_profile_id:
            raise ValueError("Could not get or create a profile")
        
        # Start browser and connect
        ws_url = await self.start_browser(target_profile_id)
        await self.connect(ws_url)
        
        self.profile_id = target_profile_id
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> None:
        """Navigate to URL"""
        if not self.page:
            raise RuntimeError("Browser not initialized. Call launch() first.")
        
        logger.info(f"Navigating to: {url}")
        await self.page.goto(url, wait_until=wait_until)
    
    async def screenshot(self, path: str = "screenshot.png", full_page: bool = True) -> str:
        """Take screenshot"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.screenshot(path=path, full_page=full_page)
        logger.info(f"Screenshot saved: {path}")
        return path
    
    async def get_content(self) -> str:
        """Get page HTML content"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        return await self.page.content()
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in page context"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        return await self.page.evaluate(script)
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None,
                                 state: str = "visible") -> None:
        """Wait for selector"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.wait_for_selector(
            selector, 
            timeout=timeout or config.browser.timeout,
            state=state
        )
    
    async def click(self, selector: str) -> None:
        """Click element"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.click(selector)
    
    async def fill(self, selector: str, text: str) -> None:
        """Fill input field"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.fill(selector, text)
    
    async def select_option(self, selector: str, value: str) -> None:
        """Select option in dropdown"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.select_option(selector, value)
    
    async def close(self) -> None:
        """Close browser and cleanup"""
        if self.page:
            await self.page.close()
            self.page = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self.profile_id:
            try:
                await self.stop_browser(self.profile_id)
            except:
                pass
            self.profile_id = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Browser session closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


# Synchronous wrapper for GUI use
class BrowserController:
    """
    Synchronous wrapper for async browser operations
    Used by GUI to run browser tasks in thread pool
    """
    
    def __init__(self):
        self.browser = GoLoginBrowser()
        self.loop = None
        self.thread = None
    
    def _run_async(self, coro):
        """Run async coroutine in event loop"""
        import threading
        
        if self.loop is None or not self.loop.is_running():
            self.loop = asyncio.new_event_loop()
            return self.loop.run_until_complete(coro)
        else:
            # If already in a running loop (nested), create task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
    
    def launch_browser(self, profile_name: str = "REI Checker", 
                       use_existing: bool = True,
                       profile_id: Optional[str] = None) -> dict:
        """Launch browser synchronously"""
        async def _launch():
            await self.browser.initialize()
            await self.browser.launch(profile_name, use_existing, profile_id)
            return {"success": True, "profile_id": self.browser.profile_id}
        
        return self._run_async(_launch())
    
    def navigate(self, url: str) -> dict:
        """Navigate to URL synchronously"""
        async def _navigate():
            await self.browser.navigate(url)
            return {"success": True, "url": url}
        
        return self._run_async(_navigate())
    
    def get_page_content(self) -> str:
        """Get page content synchronously"""
        return self._run_async(self.browser.get_content())
    
    def take_screenshot(self, path: str = "screenshot.png") -> str:
        """Take screenshot synchronously"""
        return self._run_async(self.browser.screenshot(path))
    
    def close(self) -> None:
        """Close browser synchronously"""
        self._run_async(self.browser.close())
    
    def click_element(self, selector: str) -> None:
        """Click element synchronously"""
        self._run_async(self.browser.click(selector))
    
    def fill_input(self, selector: str, text: str) -> None:
        """Fill input synchronously"""
        self._run_async(self.browser.fill(selector, text))
    
    def wait_for_element(self, selector: str, timeout: int = 30000) -> None:
        """Wait for element synchronously"""
        self._run_async(self.browser.wait_for_selector(selector, timeout=timeout))
