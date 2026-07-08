from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# =====================================================
# Project Information
# =====================================================

PROJECT_NAME = os.getenv("PROJECT_NAME", "PixelAura AI Engine")
VERSION = os.getenv("VERSION", "0.5")

# =====================================================
# Wallpaper Settings
# =====================================================

DAILY_WALLPAPERS = int(os.getenv("DAILY_WALLPAPERS", "10"))
DEFAULT_CATEGORY = os.getenv("DEFAULT_CATEGORY", "AMOLED")

IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1080"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "2400"))

# =====================================================
# Image Provider
# =====================================================

IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "pollinations")

# =====================================================
# Paths
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

HISTORY_DIR = BASE_DIR / "history"
LOG_DIR = BASE_DIR / "logs"

WEBSITE_DIR = BASE_DIR.parent / "website"

IMAGE_OUTPUT_DIR = WEBSITE_DIR / "assets" / "images" / "generated"

DATA_DIR = WEBSITE_DIR / "data"

# =====================================================
# Auto Create Directories
# =====================================================

HISTORY_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)