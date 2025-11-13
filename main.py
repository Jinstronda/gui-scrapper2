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
    
    # Setup logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Android Attendee Scraper - Starting")
    logger.info("=" * 60)
    
    try:
        # Create screenshot directory
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
        
        # Initialize database
        init_db()
        
        # Connect to device
        logger.info("Connecting to Android device...")
        device = connect_device(config.DEVICE_SERIAL)
        
        # Get initial count
        initial_count = get_attendee_count()
        logger.info(f"Attendees in database: {initial_count}")
        
        # Run scraper
        scraped_count = run_scraper(device)
        
        # Final summary
        final_count = get_attendee_count()
        logger.info("=" * 60)
        logger.info(f"Scraping completed!")
        logger.info(f"Previously in DB: {initial_count}")
        logger.info(f"Newly scraped: {scraped_count}")
        logger.info(f"Total in DB: {final_count}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\nScraping interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
