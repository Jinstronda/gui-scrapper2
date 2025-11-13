import logging
import os
from datetime import datetime


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scraper.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def take_screenshot(device, prefix="error"):
    from config import SCREENSHOT_DIR
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOT_DIR}/{prefix}_{timestamp}.png"
    device.screenshot(filename)
    return filename


def format_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
