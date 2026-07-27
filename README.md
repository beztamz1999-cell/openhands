# REI Checker - Python 3.14+ with GUI

Tool checker tự động cho REI.com sử dụng **GoLogin anti-detect browser** với **GUI đẹp mắt** bằng Python.

![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)

## 🎯 Tính năng

| Tính năng | Mô tả |
|-----------|--------|
| 🔍 **Product Checker** | Kiểm tra sản phẩm còn hàng theo size/color |
| 🔑 **Account Checker** | Kiểm tra tài khoản REI có hợp lệ không |
| 💰 **Price Tracker** | Theo dõi giá sản phẩm theo thời gian |
| 📍 **Inventory Checker** | Kiểm tra hàng tồn kho theo zip code |
| ⚙️ **Settings** | Cấu hình GoLogin, Proxy, Browser |

## 🚀 Cài đặt

### Yêu cầu

- **Python 3.14+** (khuyến nghị)
- **GoLogin** account & API Token
- **Proxy** (khuyến nghị cho việc checker nhiều)

### Cài đặt nhanh

```bash
# Clone/Download project
cd rei-checker-python

# Tạo virtual environment (khuyến nghị)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Cài đặt Playwright browsers
playwright install chromium

# Chạy ứng dụng
python main.py
```

### Cấu hình

1. **Lấy GoLogin Token:**
   - Đăng ký tại [app.gologin.com](https://app.gologin.com/)
   - Vào Settings → API
   - Copy API Token

2. **Mở ứng dụng:**
   - Tool sẽ yêu cầu bạn nhập GoLogin Token
   - Hoặc tạo file `.env` trong thư mục project

## 📖 Hướng dẫn sử dụng

### 🖥️ GUI (Recommended)

```bash
python main.py
```

Mở ứng dụng với giao diện đồ họa gồm:

- **Product Tab** - Check sản phẩm theo SKU, size, color
- **Account Tab** - Validate tài khoản email/password
- **Price Tab** - Track và xem lịch sử giá
- **Inventory Tab** - Tìm cửa hàng và check tồn kho
- **Settings Tab** - Cấu hình GoLogin, Proxy

### 🔧 Command Line

```python
from checkers import ProductChecker, AccountChecker, PriceTracker, InventoryChecker
from browser import GoLoginBrowser
import asyncio

async def main():
    # Initialize browser
    browser = GoLoginBrowser()
    await browser.initialize()
    await browser.launch(profile_name="REI Checker")
    
    # Check product
    from checkers.product import ProductCheckerSync
    checker = ProductCheckerSync()
    result = checker.check("12345", size="M")
    print(f"Available: {result.available}")
    
    await browser.close()

asyncio.run(main())
```

## 📁 Cấu trúc Project

```
rei-checker-python/
├── main.py              # Entry point
├── config.py            # Configuration
├── browser.py           # GoLogin browser manager
├── checkers/            # Checker modules
│   ├── __init__.py
│   ├── product.py       # Product availability
│   ├── account.py        # Account validation
│   ├── price.py          # Price tracking
│   └── inventory.py      # Store inventory
├── gui/                 # GUI components
│   ├── __init__.py
│   ├── main_window.py    # Main window
│   ├── product_tab.py    # Product tab
│   ├── account_tab.py    # Account tab
│   ├── price_tab.py      # Price tab
│   ├── inventory_tab.py  # Inventory tab
│   └── settings_tab.py   # Settings tab
├── requirements.txt
├── README.md
└── .env                 # Configuration (create from .env.example)
```

## ⚙️ Cấu hình

### Environment Variables

| Variable | Mô tả | Mặc định |
|----------|-------|----------|
| `GOLOGIN_TOKEN` | GoLogin API Token | - |
| `GOLOGIN_PROFILE_ID` | Profile ID (tùy chọn) | Tự tạo mới |
| `PROXY_ENABLED` | Bật proxy | `false` |
| `PROXY_HOST` | Proxy host | - |
| `PROXY_PORT` | Proxy port | `8080` |
| `PROXY_USER` | Proxy username | - |
| `PROXY_PASS` | Proxy password | - |
| `HEADLESS` | Chạy ẩn browser | `false` |
| `BROWSER_TIMEOUT` | Timeout (ms) | `30000` |

## 🔐 Bảo mật

- **Không** lưu trữ password trong code
- Sử dụng biến môi trường cho credentials
- Proxy được khuyến nghị để tránh block
- Mỗi browser session sử dụng unique fingerprint

## ⚠️ Lưu ý

1. **GoLogin Token** là bắt buộc để sử dụng
2. **Rate Limiting**: Thêm delay giữa các requests
3. **Anti-Detection**: GoLogin giúp tránh bị phát hiện bot
4. **Terms of Service**: Sử dụng tool có trách nhiệm

## 🐛 Troubleshooting

### Lỗi "GoLogin Token is required"
- Mở Settings tab
- Nhập GoLogin API Token của bạn
- Click "Save Settings"
- Khởi động lại ứng dụng

### Lỗi "Playwright not installed"
```bash
pip install playwright
playwright install chromium
```

### Browser không khởi động được
- Kiểm tra GoLogin token có hợp lệ không
- Kiểm tra internet connection
- Thử khởi động lại ứng dụng

## 📝 License

MIT License - Sử dụng tự do cho mục đích cá nhân.
