#!/usr/bin/env python3
"""
REI Checker - Main Entry Point
Browser automation tool for REI.com using GoLogin
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import logging
from loguru import logger

# Configure logging
from config import config
logger.add(
    config.logging.file_path,
    level=config.logging.level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="10 MB",
    retention="7 days"
)

logger.info("=" * 50)
logger.info("REI Checker starting...")
logger.info("=" * 50)


def main():
    """Main entry point"""
    try:
        # Check Python version
        if sys.version_info < (3, 10):
            print("⚠️  Python 3.10+ required. Current version:", sys.version_info[:2])
            print("   Some features may not work correctly.")
        
        # Try to import GUI
        try:
            import customtkinter as ctk
            logger.info("CustomTkinter loaded successfully")
        except ImportError:
            logger.error("CustomTkinter not installed")
            print("❌ CustomTkinter is required. Install with:")
            print("   pip install customtkinter")
            sys.exit(1)
        
        # Import and run GUI
        from gui.main_window import MainWindow
        
        logger.info("Starting GUI...")
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application closed by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Application error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
