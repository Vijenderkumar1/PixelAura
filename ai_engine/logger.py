import logging
from pathlib import Path

from config import LOG_DIR

LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / "engine.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("PixelAura")