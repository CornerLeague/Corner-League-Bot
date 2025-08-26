#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from libs.common.config import DatabaseSettings

print("=== Environment Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Load .env explicitly
load_dotenv()

print("\n=== Environment Variables ===")
for key, value in os.environ.items():
    if 'DATABASE' in key or 'DEEPSEEK' in key or 'JWT' in key:
        print(f"{key}={value}")

print("\n=== Testing DatabaseSettings ===")
try:
    db_settings = DatabaseSettings()
    print(f"DatabaseSettings loaded successfully: {db_settings.url}")
except Exception as e:
    print(f"DatabaseSettings failed: {e}")
    
    # Try with explicit env file
    try:
        db_settings = DatabaseSettings(_env_file=".env")
        print(f"DatabaseSettings with _env_file loaded: {db_settings.url}")
    except Exception as e2:
        print(f"DatabaseSettings with _env_file also failed: {e2}")
        
    # Try with only DATABASE_URL
    try:
        db_settings = DatabaseSettings(url=os.getenv('DATABASE_URL'))
        print(f"DatabaseSettings with explicit url loaded: {db_settings.url}")
    except Exception as e3:
        print(f"DatabaseSettings with explicit url failed: {e3}")
        
print("\n=== Testing Settings Class ===")
try:
    from libs.common.config import Settings
    settings = Settings()
    print(f"Settings loaded successfully")
    print(f"Database URL: {settings.database.url}")
except Exception as e:
    print(f"Settings failed: {e}")
    print(f"Error type: {type(e)}")