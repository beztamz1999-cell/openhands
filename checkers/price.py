"""
Price Tracker
Tracks product prices over time on REI.com
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from loguru import logger

from config import config
from browser import GoLoginBrowser


@dataclass
class PriceEntry:
    """Single price observation"""
    price: Optional[float]
    original_price: Optional[float]
    on_sale: bool
    discount_percent: Optional[int]
    timestamp: str


@dataclass
class PriceHistory:
    """Price history for a product"""
    sku: str
    name: Optional[str] = None
    url: Optional[str] = None
    prices: List[PriceEntry] = field(default_factory=list)
    lowest_price: Optional[float] = None
    lowest_price_date: Optional[str] = None
    highest_price: Optional[float] = None
    highest_price_date: Optional[str] = None
    price_changes: int = 0
    last_checked: Optional[str] = None
    last_price: Optional[float] = None


@dataclass
class PriceResult:
    """Price track result"""
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    on_sale: bool = False
    discount: Optional[float] = None
    discount_percent: Optional[int] = None
    member_price: Optional[float] = None
    timestamp: Optional[str] = None
    url: Optional[str] = None
    history: Optional[Dict] = None
    alert: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "on_sale": self.on_sale,
            "discount": self.discount,
            "discount_percent": self.discount_percent,
            "member_price": self.member_price,
            "timestamp": self.timestamp,
            "url": self.url,
            "history": self.history,
            "alert": self.alert,
            "error": self.error
        }


class PriceTracker:
    """
    Price Tracker
    Tracks product prices over time
    """
    
    def __init__(self):
        self.browser = GoLoginBrowser()
        self._ensure_data_file()
    
    def _ensure_data_file(self) -> None:
        """Ensure data file exists"""
        config.prices_file.parent.mkdir(parents=True, exist_ok=True)
        if not config.prices_file.exists():
            config.prices_file.write_text("{}")
    
    def _load_history(self) -> Dict[str, Any]:
        """Load price history from file"""
        try:
            return json.loads(config.prices_file.read_text())
        except Exception:
            return {}
    
    def _save_history(self, history: Dict[str, Any]) -> None:
        """Save price history to file"""
        config.prices_file.write_text(json.dumps(history, indent=2, ensure_ascii=False))
    
    def _parse_price(self, html: str, url: str = "") -> PriceResult:
        """Parse price from HTML"""
        result = PriceResult()
        result.url = url
        result.timestamp = datetime.now().isoformat()
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
            
            # Extract current price
            price_elem = soup.select_one('[data-testid="product-price"], .product-price, .price-current, .price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                if price_match:
                    result.price = float(price_match.group(1))
            
            # Check if on sale
            sale_elem = soup.select_one('[data-testid="sale-price"], .sale-price, .was-price, .original-price')
            if sale_elem:
                result.on_sale = True
                orig_text = sale_elem.get_text(strip=True)
                orig_match = re.search(r'\$?(\d+\.?\d*)', orig_text)
                if orig_match:
                    result.original_price = float(orig_match.group(1))
            
            # Calculate discount
            if result.on_sale and result.price and result.original_price:
                result.discount = result.original_price - result.price
                result.discount_percent = int((result.discount / result.original_price) * 100)
            
            # Check for "save $X" text
            save_match = re.search(r'save\s*\$?(\d+\.?\d*)', html, re.I)
            if save_match:
                result.discount = float(save_match.group(1))
            
            # Check for member price
            member_match = re.search(r'rei\s+(?:co-op\s+)?member\s+(?:price|price):?\s*\$?(\d+\.?\d*)', html, re.I)
            if member_match:
                result.member_price = float(member_match.group(1))
            
        except Exception as e:
            result.error = f"Parse error: {str(e)}"
            logger.error(f"Price parse error: {e}")
        
        return result
    
    async def track_price(self, sku_or_url: str,
                          save_history: bool = True,
                          alert_on_drop: bool = False) -> PriceResult:
        """
        Track price for a product
        
        Args:
            sku_or_url: Product SKU or URL
            save_history: Save to price history
            alert_on_drop: Alert if price is at lowest
            
        Returns:
            PriceResult with current price and history
        """
        logger.info(f"Tracking price for: {sku_or_url}")
        
        # Build product URL
        if sku_or_url.startswith("http"):
            product_url = sku_or_url
        else:
            product_url = config.rei.product_url_template.format(sku=sku_or_url)
        
        try:
            await self.browser.initialize()
            await self.browser.launch(profile_name=f"REI-Price-{sku_or_url}")
            
            await self.browser.navigate(product_url)
            
            html = await self.browser.get_content()
            result = self._parse_price(html, product_url)
            
            # Load and update history
            if save_history:
                history = self._load_history()
                sku = result.sku or sku_or_url
                
                if sku not in history:
                    history[sku] = {
                        "sku": sku,
                        "name": result.name,
                        "url": product_url,
                        "prices": [],
                        "lowest_price": None,
                        "highest_price": None,
                        "price_changes": 0
                    }
                
                product_history = history[sku]
                product_history["prices"].append({
                    "price": result.price,
                    "original_price": result.original_price,
                    "on_sale": result.on_sale,
                    "discount": result.discount,
                    "discount_percent": result.discount_percent,
                    "timestamp": result.timestamp
                })
                
                # Update stats
                if result.price:
                    lowest = product_history.get("lowest_price")
                    highest = product_history.get("highest_price")
                    
                    if not lowest or result.price < lowest["price"]:
                        product_history["lowest_price"] = {
                            "price": result.price,
                            "timestamp": result.timestamp
                        }
                    
                    if not highest or result.price > highest["price"]:
                        product_history["highest_price"] = {
                            "price": result.price,
                            "timestamp": result.timestamp
                        }
                    
                    # Count price changes
                    if len(product_history["prices"]) >= 2:
                        last_price = product_history["prices"][-2]["price"]
                        if result.price != last_price:
                            product_history["price_changes"] += 1
                
                product_history["last_checked"] = result.timestamp
                product_history["last_price"] = result.price
                
                self._save_history(history)
                result.history = product_history
                
                # Alert on price drop
                if alert_on_drop and product_history["lowest_price"]:
                    if result.price == product_history["lowest_price"]["price"]:
                        if len(product_history["prices"]) > 1:
                            result.alert = f"🎉 Price dropped to lowest: ${result.price}!"
            
            await self.browser.close()
            logger.info(f"Price tracking complete: {sku_or_url} - ${result.price}")
            return result
            
        except Exception as e:
            logger.error(f"Price tracking failed: {e}")
            try:
                await self.browser.close()
            except:
                pass
            return PriceResult(error=str(e))
    
    def get_history(self, sku: str) -> Optional[Dict]:
        """Get price history for a product"""
        history = self._load_history()
        return history.get(sku)
    
    def get_all_tracked(self) -> List[Dict]:
        """Get all tracked products"""
        history = self._load_history()
        return list(history.values())
    
    async def batch_track(self, products: List[Dict[str, Any]],
                          delay: int = 2000,
                          save_history: bool = True) -> List[PriceResult]:
        """Batch track multiple products"""
        results = []
        
        for product in products:
            result = await self.track_price(
                sku_or_url=product.get("sku"),
                save_history=save_history
            )
            results.append(result)
            
            if delay > 0:
                await asyncio.sleep(delay / 1000)
        
        return results


# Synchronous wrapper
class PriceTrackerSync:
    """Synchronous wrapper for PriceTracker"""
    
    def __init__(self):
        self.tracker = PriceTracker()
    
    def track(self, sku_or_url: str, save_history: bool = True) -> PriceResult:
        """Track price synchronously"""
        return asyncio.run(self.tracker.track_price(sku_or_url, save_history))
    
    def get_history(self, sku: str) -> Optional[Dict]:
        """Get price history"""
        return self.tracker.get_history(sku)
    
    def get_all(self) -> List[Dict]:
        """Get all tracked products"""
        return self.tracker.get_all_tracked()
