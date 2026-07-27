"""
Inventory Checker
Checks in-store and online inventory for REI products
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

from config import config
from browser import GoLoginBrowser


@dataclass
class StoreInfo:
    """Store inventory info"""
    name: str
    stock: str = "Unknown"  # "In Stock", "Limited", "Out of Stock"
    stock_count: Optional[int] = None
    distance: Optional[str] = None
    sizes: Optional[List[str]] = None


@dataclass
class InventoryResult:
    """Inventory check result"""
    sku: Optional[str] = None
    name: Optional[str] = None
    online: Optional[bool] = None
    pickup_available: bool = False
    stores: List[StoreInfo] = field(default_factory=list)
    url: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "online": self.online,
            "pickup_available": self.pickup_available,
            "stores": [
                {
                    "name": s.name,
                    "stock": s.stock,
                    "stock_count": s.stock_count,
                    "distance": s.distance,
                    "sizes": s.sizes
                }
                for s in self.stores
            ],
            "url": self.url,
            "error": self.error
        }


class InventoryChecker:
    """
    Inventory Checker
    Checks in-store and online inventory for REI products
    """
    
    def __init__(self):
        self.browser = GoLoginBrowser()
    
    def _parse_inventory(self, html: str, url: str = "") -> InventoryResult:
        """Parse inventory from HTML"""
        result = InventoryResult()
        result.url = url
        soup = BeautifulSoup(html, "lxml")
        
        try:
            # Extract SKU
            sku_match = re.search(r'data-sku="([^"]+)"', html)
            if not sku_match:
                sku_match = re.search(r'"sku"\s*:\s*"([^"]+)"', html)
            if sku_match:
                result.sku = sku_match.group(1)
            
            # Extract product name
            name_elem = soup.select_one('h1[data-testid="product-title"], h1.product-name, h1')
            if name_elem:
                result.name = name_elem.get_text(strip=True)
            
            # Check online availability
            add_to_cart = soup.select_one('[data-testid="add-to-cart"], .add-to-cart')
            if add_to_cart:
                result.online = "disabled" not in add_to_cart.get("class", [])
            
            # Check pickup available
            result.pickup_available = any(
                kw in html.lower() 
                for kw in ["pickup", "curbside", "in-store pickup", "store pickup"]
            )
            
            # Parse store inventory
            store_selectors = [
                '[data-testid="store-inventory"]',
                '.store-item',
                '.store-result',
                '.store-stock',
                '[data-store]'
            ]
            
            for selector in store_selectors:
                for store_elem in soup.select(selector):
                    store_name = (
                        store_elem.select_one('[data-testid="store-name"], .store-name, h3, h4')
                        .get_text(strip=True)
                        if store_elem.select_one('[data-testid="store-name"], .store-name, h3, h4')
                        else ""
                    )
                    
                    stock_text = (
                        store_elem.select_one('[data-testid="stock-status"], .stock-status, .availability')
                        .get_text(strip=True)
                        if store_elem.select_one('[data-testid="stock-status"], .stock-status, .availability')
                        else ""
                    )
                    
                    distance = (
                        store_elem.select_one('.distance, [data-testid="distance"]')
                        .get_text(strip=True)
                        if store_elem.select_one('.distance, [data-testid="distance"]')
                        else None
                    )
                    
                    # Parse sizes
                    sizes = [
                        s.get_text(strip=True)
                        for s in store_elem.select('.size, [data-size], .size-option')
                        if s.get_text(strip=True)
                    ]
                    
                    # Parse stock status
                    stock = "Unknown"
                    stock_count = None
                    
                    stock_lower = stock_text.lower()
                    if "in stock" in stock_lower or "available" in stock_lower:
                        stock = "In Stock"
                        count_match = re.search(r'(\d+)\s*(?:in stock|available)', stock_lower)
                        if count_match:
                            stock_count = int(count_match.group(1))
                    elif "limited" in stock_lower:
                        stock = "Limited Stock"
                        count_match = re.search(r'(\d+)', stock_text)
                        if count_match:
                            stock_count = int(count_match.group(1))
                    elif "out of stock" in stock_lower or "unavailable" in stock_lower:
                        stock = "Out of Stock"
                    
                    if store_name:
                        result.stores.append(StoreInfo(
                            name=store_name,
                            stock=stock,
                            stock_count=stock_count,
                            distance=distance,
                            sizes=sizes if sizes else None
                        ))
            
            # Parse from store selector dropdown
            if not result.stores:
                store_select = soup.select_one('select[data-testid="store-select"], select#store-selector')
                if store_select:
                    for option in store_select.select('option'):
                        option_text = option.get_text(strip=True)
                        option_value = option.get("value", "")
                        if option_value and option_text:
                            result.stores.append(StoreInfo(name=option_text))
            
        except Exception as e:
            result.error = f"Parse error: {str(e)}"
            logger.error(f"Inventory parse error: {e}")
        
        return result
    
    async def check_inventory(self, sku_or_url: str,
                              zip_code: Optional[str] = None,
                              radius: int = 50,
                              store_id: Optional[str] = None) -> InventoryResult:
        """
        Check inventory for a product
        
        Args:
            sku_or_url: Product SKU or URL
            zip_code: Check stores near this zip code
            radius: Search radius in miles
            store_id: Check specific store ID
            
        Returns:
            InventoryResult with store inventory
        """
        logger.info(f"Checking inventory: {sku_or_url}")
        
        # Build product URL
        if sku_or_url.startswith("http"):
            product_url = sku_or_url
        else:
            product_url = config.rei.product_url_template.format(sku=sku_or_url)
        
        try:
            await self.browser.initialize()
            await self.browser.launch(profile_name=f"REI-Inventory-{sku_or_url}")
            
            # Navigate to product page
            await self.browser.navigate(product_url)
            
            # Search by zip if provided
            if zip_code:
                await self._search_by_zip(zip_code, radius)
            
            # Select specific store
            if store_id:
                await self._select_store(store_id)
            
            html = await self.browser.get_content()
            result = self._parse_inventory(html, product_url)
            
            await self.browser.close()
            logger.info(f"Inventory check complete: {sku_or_url}")
            return result
            
        except Exception as e:
            logger.error(f"Inventory check failed: {e}")
            try:
                await self.browser.close()
            except:
                pass
            return InventoryResult(error=str(e))
    
    async def _search_by_zip(self, zip_code: str, radius: int = 50) -> None:
        """Search for stores by zip code"""
        try:
            # Look for store availability section
            availability_section = await self.browser.page.query_selector(
                '[data-testid="store-availability"], #store-availability'
            )
            
            if availability_section:
                zip_input = await self.browser.page.query_selector(
                    'input[name="zipCode"], input#zip-code, input[placeholder*="zip" i]'
                )
                if zip_input:
                    await zip_input.fill(zip_code)
                    await asyncio.sleep(0.5)
                    
                    search_btn = await self.browser.page.query_selector(
                        'button[type="submit"], button:has-text("Search"), button:has-text("Check")'
                    )
                    if search_btn:
                        await search_btn.click()
                        await asyncio.sleep(2)
            
            # Alternative: use store finder
            await self.browser.navigate(
                f"{config.rei.stores_url}?zip={zip_code}&radius={radius}"
            )
            await self.browser.page.wait_for_load_state("networkidle")
            
        except Exception as e:
            logger.warning(f"Store search failed: {e}")
    
    async def _select_store(self, store_id: str) -> None:
        """Select a specific store"""
        try:
            store_option = await self.browser.page.query_selector(
                f'select option[value="{store_id}"]'
            )
            if store_option:
                await store_option.click()
                await asyncio.sleep(1.5)
        except Exception as e:
            logger.warning(f"Store selection failed: {e}")
    
    async def find_stores(self, zip_code: str,
                          radius: int = 50,
                          product_sku: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find stores near a location
        
        Args:
            zip_code: Zip code to search near
            radius: Search radius in miles
            product_sku: Filter by product availability
            
        Returns:
            List of store information
        """
        logger.info(f"Finding stores near: {zip_code}")
        
        try:
            await self.browser.initialize()
            await self.browser.launch(profile_name=f"REI-FindStores-{zip_code}")
            
            # Navigate to store finder
            url = f"{config.rei.stores_url}?zip={zip_code}&radius={radius}"
            if product_sku:
                url += f"&sku={product_sku}"
            
            await self.browser.navigate(url)
            await self.browser.page.wait_for_load_state("networkidle")
            
            html = await self.browser.get_content()
            soup = BeautifulSoup(html, "lxml")
            
            stores = []
            store_selectors = [
                '[data-testid="store-card"]',
                '.store-card',
                '.store-item',
                'article[data-store]'
            ]
            
            for selector in store_selectors:
                for store_elem in soup.select(selector):
                    name = (
                        store_elem.select_one('h2, h3, .store-name, [data-testid="store-name"]')
                        .get_text(strip=True)
                        if store_elem.select_one('h2, h3, .store-name, [data-testid="store-name"]')
                        else ""
                    )
                    
                    address = (
                        store_elem.select_one('.address, [data-testid="store-address"]')
                        .get_text(strip=True)
                        if store_elem.select_one('.address, [data-testid="store-address"]')
                        else ""
                    )
                    
                    phone = (
                        store_elem.select_one('.phone, [data-testid="store-phone"]')
                        .get_text(strip=True)
                        if store_elem.select_one('.phone, [data-testid="store-phone"]')
                        else None
                    )
                    
                    hours = (
                        store_elem.select_one('.hours, [data-testid="store-hours"]')
                        .get_text(strip=True)
                        if store_elem.select_one('.hours, [data-testid="store-hours"]')
                        else None
                    )
                    
                    distance = (
                        store_elem.select_one('.distance, [data-testid="distance"]')
                        .get_text(strip=True)
                        if store_elem.select_one('.distance, [data-testid="distance"]')
                        else None
                    )
                    
                    store_id = store_elem.get("data-store-id") or store_elem.get("data-store")
                    
                    if name:
                        stores.append({
                            "name": name,
                            "address": address,
                            "phone": phone,
                            "hours": hours,
                            "distance": distance,
                            "id": store_id
                        })
            
            await self.browser.close()
            logger.info(f"Found {len(stores)} stores")
            return stores
            
        except Exception as e:
            logger.error(f"Find stores failed: {e}")
            try:
                await self.browser.close()
            except:
                pass
            return []
    
    async def batch_check(self, products: List[Dict[str, Any]],
                         delay: int = 2000) -> List[InventoryResult]:
        """Batch check inventory"""
        results = []
        
        for product in products:
            result = await self.check_inventory(
                sku_or_url=product.get("sku"),
                zip_code=product.get("zip_code")
            )
            results.append(result)
            
            if delay > 0:
                await asyncio.sleep(delay / 1000)
        
        return results


# Synchronous wrapper
class InventoryCheckerSync:
    """Synchronous wrapper for InventoryChecker"""
    
    def __init__(self):
        self.checker = InventoryChecker()
    
    def check(self, sku_or_url: str, zip_code: Optional[str] = None) -> InventoryResult:
        """Check inventory synchronously"""
        return asyncio.run(self.checker.check_inventory(sku_or_url, zip_code))
    
    def find_stores(self, zip_code: str, radius: int = 50) -> List[Dict]:
        """Find stores synchronously"""
        return asyncio.run(self.checker.find_stores(zip_code, radius))
