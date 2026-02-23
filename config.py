# config.py
import os
from dotenv import load_dotenv

# Load local .env file
load_dotenv()

# Get keys from .env or default to an empty list
raw_keys = os.getenv("GEMINI_KEYS", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

# UI Settings
OVERLAY_OPACITY = 255