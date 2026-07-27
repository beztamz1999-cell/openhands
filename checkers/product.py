"""
Product Availability Checker
Checks product availability on REI.com with size/color options
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from loguru import logger

from config import config
from browser import GoLoginBrowser


@dataclass
class SizeInfo:
    """Size availability info"""
    size: str
    available: bool
    disabled: bool = False


@dataclass
class ColorInfo:
    """Color option info"""
    color: str
    selected: bool = False


@dataclass
class ProductResult:
    """Product check result"""
    available: bool = False
    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    on_sale: bool = False
    discount_percent: Optional[int] = None
    sizes: List[SizeInfo] = field(default_factory=list)
    colors: List[ColorInfo] = field(default_factory=list)
    selected_size: Optional[str] = None
    selected_color: Optional[str] = None
    size_available: Optional[bool] = None
    images: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    reviews: Optional[int] = None
    url: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "available": self.available,
            "sku": self.sku,
            "name": self.name,
            "price": self.price,
            "original_price": self.original_price,
            "on_sale": self.on_sale,
            "discount_percent": self.discount_percent,
            "sizes": [{"size": s.size, "available": s.available} for s in self.sizes],
            "colors": [{"color": c.color, "selected": c.selected} for c in self.colors],
            "selected_size": self.selected_size,
            "selected_color": self.selected_color,
            "size_available": self.size_available,
            "images": self.images,
            "rating": self.rating,
            "reviews": self.reviews,
            "url": self.url,
            "error": self.error
        }


class ProductChecker:
    """
    Product Availability Checker
    Checks if products are available on REI.com with specific options
    """
    
    def __init__(self):
        self.browser = GoLoginBrowser()
    
    def _parse_availability(self, html: str, url: str = "") -> ProductResult:
        """Parse product availability from HTML"""
        result = ProductResult()
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
            
            # Extract price
            price_elem = soup.select_one('[data-testid="product-price"], .product-price, .price-current')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'\$?(\d+\.?\d*)', price_text)
                if price_match:
                    result.price = float(price_match.group(1))
            
            # Check if on sale
            result.on_sale = bool(soup.select_one('[data-testid="price-save"], .sale-price'))
            if result.on_sale:
                # Try to find original price
                original_elem = soup.select_one('.was-price, .original-price, [data-testid="was-price"]')
                if original_elem:
                    orig_text = original_elem.get_text(strip=True)
                    orig_match = re.search(r'\$?(\d+\.?\d*)', orig_text)
                    if orig_match:
                        result.original_price = float(orig_match.group(1))
                        if result.price and result.original_price:
                            result.discount_percent = int(
                                ((result.original_price - result.price) / result.original_price) * 100
                            )
            
            # Extract sizes
            size_selectors = '[data-testid="size-option"], .size-option, button[data-size], .size-swatch'
            for size_elem in soup.select(size_selectors):
                size_text = size_elem.get_text(strip=True)
                if size_text:
                    is_disabled = (
                        "disabled" in size_elem.get("class", []) or
                        size_elem.get("aria-disabled") == "true" or
                        "unavailable" in size_elem.get("class", []) or
                        "sold-out" in size_elem.get("class", [])
                    )
                    result.sizes.append(SizeInfo(
                        size=size_text,
                        available=not is_disabled,
                        disabled=is_disabled
                    ))
            
            # Extract colors
            color_selectors = '[data-testid="color-option"], .color-option, button[data-color]'
            for color_elem in soup.select(color_selectors):
                color_text = color_elem.get("aria-label") or color_elem.get_text(strip=True)
                if color_text:
                    is_selected = (
                        "selected" in color_elem.get("class", []) or
                        color_elem.get("aria-pressed") == "true"
                    )
                    result.colors.append(ColorInfo(color=color_text, selected=is_selected))
                    if is_selected:
                        result.selected_color = color_text
            
            # Check overall availability
            add_to_cart = soup.select_one('[data-testid="add-to-cart"], .add-to-cart, button:contains("Add to Cart")')
            any_size_available = any(s.available for s in result.sizes)
            result.available = bool(any_size_available and add_to_cart)
            
            # Extract images
            for img in soup.select('img[data-testid="product-image"], .product-image img, #pdp-gallery img'):
                src = img.get("src") or img.get("data-src")
                if src and src.startswith("http"):
                    result.images.append(src)
            
            # Extract rating
            rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of|of)\s*\d+\s*stars', html, re.I)
            if rating_match:
                result.rating = float(rating_match.group(1))
            
            # Extract reviews count
            reviews_match = re.search(r'(\d+(?:,\d*)*)\s*reviews', html, re.I)
            if reviews_match:
                result.reviews = int(reviews_match.group(1).replace(",", ""))
            
        except Exception as e:
            result.error = f"Parse error: {str(e)}"
            logger.error(f"Product parse error: {e}")
        
        return result
    
    async def check_product(self, sku_or_url: str, 
                           size: Optional[str] = None,
                           color: Optional[str] = None,
                           zip_code: Optional[str] = None,
                           timeout: int = 30000) -> ProductResult:
        """
        Check product availability
        
        Args:
            sku_or_url: Product SKU or full URL
            size: Filter by specific size
            color: Filter by specific color
            zip_code: Check store availability near zip
            timeout: Request timeout in milliseconds
            
        Returns:
            ProductResult with availability info
        """
        logger.info(f"Checking product: {sku_or_url}")
        
        # Build product URL
        if sku_or_url.startswith("http"):
            product_url = sku_or_url
        else:
            product_url = config.rei.product_url_template.format(sku=sku_or_url)
        
        try:
            # Launch browser
            await self.browser.initialize()
            await self.browser.launch(profile_name=f"REI-Product-{sku_or_url}")
            
            # Navigate to product page
            await self.browser.navigate(product_url)
            
            # Get page content
            html = await self.browser.get_content()
            result = self._parse_availability(html, product_url)
            
            # Check specific size if requested
            if size and result.sizes:
                size_info = next((s for s in result.sizes if s.size.lower() == size.lower()), None)
                result.selected_size = size
                result.size_available = size_info.available if size_info else False
            
            # Check specific color if requested
            if color and result.colors:
                color_info = next(
                    (c for c in result.colors if color.lower() in c.color.lower()),
                    None
                )
                result.selected_color = color
                # Color availability would need to click through
            
            await self.browser.close()
            
            logger.info(f"Product check complete: {result.name} - {'Available' if result.available else 'Not Available'}")
            return result
            
        except Exception as e:
            logger.error(f"Product check failed: {e}")
            try:
                await self.browser.close()
            except:
                pass
            return ProductResult(error=str(e))
    
    async def batch_check(self, products: List[Dict[str, Any]], 
                         delay: int = 2000) -> List[ProductResult]:
        """
        Batch check multiple products
        
        Args:
            products: List of product dicts with 'sku' key
            delay: Delay between requests in milliseconds
            
        Returns:
            List of ProductResult
        """
        results = []
        
        for product in products:
            result = await self.check_product(
                sku_or_url=product.get("sku"),
                size=product.get("size"),
                color=product.get("color")
            )
            results.append(result)
            
            # Delay between requests
            if delay > 0:
                await asyncio.sleep(delay / 1000)
        
        return results


# Synchronous wrapper for GUI
class ProductCheckerSync:
    """Synchronous wrapper for ProductChecker"""
    
    def __init__(self):
        self.checker = ProductChecker()
    
    def check(self, sku_or_url: str, size: Optional[str] = None,
              color: Optional[str] = None) -> ProductResult:
        """Check product synchronously"""
        import asyncio
        return asyncio.run(
            self.checker.check_product(sku_or_url, size, color)
        )
