"""
REI Checker Configuration
Configuration management using environment variables and YAML
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).parent


@dataclass
class GoLoginConfig:
    """GoLogin browser configuration"""
    token: str = field(default_factory=lambda: os.getenv("GOLOGIN_TOKEN", ""))
    profile_id: Optional[str] = field(default_factory=lambda: os.getenv("GOLOGIN_PROFILE_ID", ""))
    base_url: str = "https://api.gologin.com"
    browser_url: str = "https://gologin.com"  # Updated URL


@dataclass
class ProxyConfig:
    """Proxy configuration"""
    enabled: bool = os.getenv("PROXY_ENABLED", "false").lower() == "true"
    host: str = field(default_factory=lambda: os.getenv("PROXY_HOST", ""))
    port: int = field(default_factory=lambda: int(os.getenv("PROXY_PORT", "8080")))
    user: str = field(default_factory=lambda: os.getenv("PROXY_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("PROXY_PASS", ""))

    @property
    def proxy_url(self) -> Optional[str]:
        if self.enabled and self.host:
            if self.user and self.password:
                return f"http://{self.user}:{self.password}@{self.host}:{self.port}"
            return f"http://{self.host}:{self.port}"
        return None


@dataclass
class BrowserConfig:
    """Browser settings"""
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"
    timeout: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    page_load_timeout: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "60000"))
    viewport_width: int = 1920
    viewport_height: int = 1080


@dataclass
class APIConfig:
    """API server configuration"""
    host: str = os.getenv("API_HOST", "localhost")
    port: int = int(os.getenv("API_PORT", "3000"))


@dataclass
class REIConfig:
    """REI website configuration"""
    base_url: str = "https://www.rei.com"
    product_url_template: str = "https://www.rei.com/product/{sku}"
    search_url_template: str = "https://www.rei.com/search?q={query}"
    account_url: str = "https://www.rei.com/account/signin"
    stores_url: str = "https://www.rei.com/stores"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv("LOG_LEVEL", "INFO")
    file_path: Path = BASE_DIR / "logs" / "rei_checker.log"


@dataclass
class AppConfig:
    """Main application configuration"""
    gologin: GoLoginConfig = field(default_factory=GoLoginConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    api: APIConfig = field(default_factory=APIConfig)
    rei: REIConfig = field(default_factory=REIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Paths
    data_dir: Path = BASE_DIR / "data"
    screenshots_dir: Path = BASE_DIR / "screenshots"
    prices_file: Path = data_dir / "prices.json"

    def __post_init__(self):
        """Create directories if they don't exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.logging.file_path.parent.mkdir(exist_ok=True, parents=True)


# Global config instance
config = AppConfig()
