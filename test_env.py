"""
Test script to verify .env loading
Run this to check if token is loaded correctly
"""

from pathlib import Path
import os

# Test 1: Check current directory
print("=" * 50)
print("TEST 1: Current Directory")
print("=" * 50)
print(f"Current dir: {os.getcwd()}")
print(f"Files here: {list(Path('.').glob('*'))}")

# Test 2: Check .env file
print("\n" + "=" * 50)
print("TEST 2: Check .env File")
print("=" * 50)

env_path = Path(".env")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    print(f".env content (first 100 chars): {env_path.read_text()[:100]}...")
else:
    print("❌ .env file NOT FOUND!")

# Test 3: Load dotenv and check
print("\n" + "=" * 50)
print("TEST 3: Load dotenv")
print("=" * 50)

from dotenv import load_dotenv

# Load from script directory
script_dir = Path(__file__).parent
load_dotenv(script_dir / ".env")

print(f"Loaded from: {script_dir / '.env'}")
print(f"GOLOGIN_TOKEN after load: {os.getenv('GOLOGIN_TOKEN', 'NOT SET')[:20] if os.getenv('GOLOGIN_TOKEN') else 'NOT SET'}...")

# Test 4: Load config
print("\n" + "=" * 50)
print("TEST 4: Load Config")
print("=" * 50)

from config import config
print(f"config.gologin.token: {config.gologin.token[:20] if config.gologin.token else 'EMPTY'}...")

# Final result
print("\n" + "=" * 50)
print("RESULT")
print("=" * 50)
if config.gologin.token:
    print("✅ TOKEN LOADED SUCCESSFULLY!")
else:
    print("❌ TOKEN NOT LOADED - Check .env file location and format")
    print("\nMake sure:")
    print("1. .env file is in the same folder as main.py")
    print("2. Format: GOLOGIN_TOKEN=your_token_here (no quotes, no spaces)")
