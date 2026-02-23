import os
from dotenv import load_dotenv

# Load local config file (Stealth renamed .env)
load_dotenv("config.dat")

# Get keys from config.dat or default to an empty list
raw_keys = os.getenv("GEMINI_KEYS", "")
API_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]

# UI Settings
OVERLAY_OPACITY = 255