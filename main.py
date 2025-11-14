import os
import sys
import logging
from utils import setup_logging
from device import connect_device
from database import init_db, get_attendee_count
from scraper import run_scraper
import config

logger = None


def main():
    global logger
    
    # Setup logging with minimal output
    logger = setup_logging()
    logger.info("Scraper started")
    
    try:
        # Create screenshot directory
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
        
        # Initialize database
        init_db()
        
        # Connect to device and init
        device = connect_device(config.DEVICE_SERIAL)
        initial_count = get_attendee_count()
        
        # Run scraper
        scraped_count = run_scraper(device)
        
        # Final summary
        final_count = get_attendee_count()
        logger.info(f"DONE: {scraped_count} new | Total: {final_count}")
        
    except KeyboardInterrupt:
        final_count = get_attendee_count()
        logger.info(f"\nSTOPPED by user | Total: {final_count}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
