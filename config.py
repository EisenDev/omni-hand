import os
import sys
from dotenv import load_dotenv

# Get the directory of the executable or script
if getattr(sys, 'frozen', False):
    # Running in a bundle (EXE)
    base_dir = os.path.dirname(sys.executable)
else:
    # Running in normal Python environment
    base_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(base_dir, "config.dat")

# Force load from config.dat, overriding any existing environment variables
if os.path.exists(config_path):
    load_dotenv(config_path, override=True)
    print(f"[Config] Loading keys from: {config_path}")
else:
    # Fallback to .env if config.dat doesn't exist
    load_dotenv(os.path.join(base_dir, ".env"), override=True)
    print(f"[Config] config.dat not found. Checking .env...")

# Get keys from environment or default to an empty list
raw_keys = os.getenv("GEMINI_KEYS", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

print(f"[Config] Found {len(API_KEYS)} API keys.")

# UI Settings
OVERLAY_OPACITY = 255