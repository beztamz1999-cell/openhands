"""
GoLogin Browser Manager
Handles browser automation using GoLogin anti-detect browser with Playwright
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import httpx
from loguru import logger

from config import config


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
        
    async def initialize(self) -> None:
        """Initialize Playwright"""
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            logger.info("Playwright initialized")
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
            raise
    
    async def init_api(self) -> httpx.AsyncClient:
        """Initialize GoLogin API client"""
        if not config.gologin.token:
            raise ValueError("GoLogin API token is required. Get it from https://app.gologin.com/")
        
        client = httpx.AsyncClient(
            base_url=config.gologin.browser_url,
            headers={
                "Authorization": f"Bearer {config.gologin.token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
        return client
    
    async def create_profile(self, name: str = "REI Checker Profile") -> Dict[str, Any]:
        """Create a new browser profile"""
        api = await self.init_api()
        
        profile_data = {
            "name": name,
            "os": "win",
            "browserType": "chromium",
            "maskType": "stable",
            "viewport": {
                "width": config.browser.viewport_width,
                "height": config.browser.viewport_height
            },
            "webgl": {"mode": "noise"},
            "timezone": {"mode": "auto"},
            "geo": {"mode": "auto"},
            "dns": {"mode": "auto"},
            "permissions": ["microphone", "camera"],
            "storage": {"isLocal": True}
        }
        
        # Add proxy if enabled
        if config.proxy.enabled:
            proxy_mode = "http"
            profile_data["proxy"] = {
                "mode": proxy_mode,
                "host": config.proxy.host,
                "port": config.proxy.port,
                "username": config.proxy.user,
                "password": config.proxy.password
            }
        else:
            profile_data["proxy"] = {"mode": "none"}
        
        try:
            response = await api.post("/browser/profiles", json=profile_data)
            response.raise_for_status()
            profile = response.json()
            logger.info(f"Created GoLogin profile: {profile['id']}")
            await api.aclose()
            return profile
        except httpx.HTTPError as e:
            logger.error(f"Failed to create profile: {e}")
            await api.aclose()
            raise
    
    async def list_profiles(self) -> List[Dict[str, Any]]:
        """List all browser profiles"""
        api = await self.init_api()
        
        try:
            response = await api.get("/browser/profiles")
            response.raise_for_status()
            profiles = response.json()
            await api.aclose()
            return profiles
        except httpx.HTTPError as e:
            logger.error(f"Failed to list profiles: {e}")
            await api.aclose()
            return []
    
    async def delete_profile(self, profile_id: str) -> None:
        """Delete a browser profile"""
        api = await self.init_api()
        
        try:
            response = await api.delete(f"/browser/profiles/{profile_id}")
            response.raise_for_status()
            logger.info(f"Deleted profile: {profile_id}")
            await api.aclose()
        except httpx.HTTPError as e:
            logger.error(f"Failed to delete profile: {e}")
            await api.aclose()
    
    async def start_browser(self, profile_id: str) -> str:
        """Start browser with GoLogin profile, return WebSocket URL"""
        api = await self.init_api()
        
        try:
            response = await api.post(
                f"/browser/profiles/{profile_id}/start",
                json={"headless": config.browser.headless}
            )
            response.raise_for_status()
            data = response.json()
            
            ws_url = data.get("wsUrl")
            status = data.get("status", "")
            
            if status != "Success" and not ws_url:
                raise RuntimeError(f"Failed to start browser: {status}")
            
            logger.info(f"Browser started with profile: {profile_id}")
            self.ws_url = ws_url
            self.profile_id = profile_id
            await api.aclose()
            return ws_url
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to start browser: {e}")
            await api.aclose()
            raise
    
    async def stop_browser(self, profile_id: str) -> None:
        """Stop browser"""
        api = await self.init_api()
        
        try:
            response = await api.post(f"/browser/profiles/{profile_id}/stop")
            response.raise_for_status()
            logger.info(f"Browser stopped for profile: {profile_id}")
            await api.aclose()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to stop browser: {e}")
            await api.aclose()
    
    async def connect(self, ws_url: str) -> None:
        """Connect to GoLogin browser using Playwright CDP"""
        if not self._playwright:
            await self.initialize()
        
        try:
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
        target_profile_id = profile_id or config.gologin.profile_id
        
        # If no profile specified, create new or use existing
        if not target_profile_id:
            if use_existing:
                profiles = await self.list_profiles()
                if profiles:
                    target_profile_id = profiles[0]["id"]
                    logger.info(f"Using existing profile: {target_profile_id}")
                else:
                    new_profile = await self.create_profile(profile_name)
                    target_profile_id = new_profile["id"]
            else:
                new_profile = await self.create_profile(profile_name)
                target_profile_id = new_profile["id"]
        
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
