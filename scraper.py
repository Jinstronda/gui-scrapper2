import logging
import time
import config
from database import attendee_exists, save_attendee
from extractor import extract_from_detail_page, extract_name_from_list
from utils import take_screenshot

logger = logging.getLogger(__name__)


def run_scraper(device):
    index = 0
    scraped_count = 0
    
    logger.info("Starting scraper...")
    
    while True:
        try:
            # Check if we've reached the limit
            if config.MAX_ATTENDEES and scraped_count >= config.MAX_ATTENDEES:
                logger.info(f"Reached limit: {config.MAX_ATTENDEES}")
                break
            
            # Get list items
            items = device(**config.LIST_ITEM_SELECTOR)
            
            if items.count == 0:
                logger.warning("No items found, stopping")
                break
            
            if index >= items.count:
                logger.info("Reached end of current view")
                break
            
            # Extract name from list first for duplicate check
            name = extract_name_from_list(device, index)
            
            if not name:
                logger.warning(f"Could not extract name at index {index}")
                index += 1
                continue
            
            # Check if already scraped
            if attendee_exists(name):
                logger.info(f"Skipping duplicate: {name}")
                index += 1
                continue
            
            # Click item to open detail page
            logger.info(f"Processing: {name} (index {index})")
            items[index].click()
            time.sleep(config.CLICK_TIMEOUT)
            
            # Extract data from detail page
            data = extract_from_detail_page(device)
            
            # Press back to return to list
            device.press("back")
            time.sleep(config.CLICK_TIMEOUT)
            
            # Save to database
            if data['name']:
                save_attendee(
                    data['name'],
                    data['industry'],
                    data['job_function'],
                    data['operates_in']
                )
                scraped_count += 1
                logger.info(f"Saved {scraped_count}: {data['name']}")
            
            # Move to next item
            index += 1
            
            # Scroll if we've processed 11 items
            if index >= 11:
                logger.info("Scrolling to next batch")
                try:
                    # Try RecyclerView first
                    list_container = device(**config.LIST_CONTAINER_SELECTOR)
                    if list_container.exists:
                        list_container.scroll.forward(steps=5)
                    else:
                        # Fallback to ScrollView
                        scroll_view = device(**config.SCROLL_VIEW_SELECTOR)
                        scroll_view.scroll.forward(steps=5)
                    time.sleep(config.SCROLL_WAIT)
                except Exception as e:
                    logger.warning(f"Scroll failed: {e}")
                index = 0
        
        except Exception as e:
            logger.error(f"Error at index {index}: {e}")
            
            if config.SAVE_SCREENSHOTS_ON_ERROR:
                take_screenshot(device, f"error_idx{index}")
            
            # Try to recover by pressing back
            device.press("back")
            time.sleep(config.CLICK_TIMEOUT)
            
            # Skip this item
            index += 1
    
    logger.info(f"Scraping completed. Total scraped: {scraped_count}")
    return scraped_count
