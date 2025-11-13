import logging
import time
import config
from database import attendee_exists, save_attendee
from extractor import extract_from_detail_page, extract_name_from_list
from utils import take_screenshot

logger = logging.getLogger(__name__)


def get_attendee_buttons(device):
    """Get only attendee buttons, filtering out navigation/UI buttons"""
    all_buttons = device(className="android.widget.Button", clickable=True)
    attendee_buttons = []
    
    for i in range(all_buttons.count):
        try:
            button = all_buttons[i]
            info = button.info
            content_desc = info.get('contentDescription', '')
            text = info.get('text', '')
            
            # Attendee buttons have specific format: "INITIALS, TITLE, NAME, ROLE\nCOMPANY"
            # Must have: no text + 4+ comma-separated parts
            if not text and ',' in content_desc:
                parts = content_desc.split(',')
                if len(parts) >= 4:
                    attendee_buttons.append(button)
                    logger.debug(f"Found attendee button: {content_desc[:80]}...")
        except Exception as e:
            logger.debug(f"Error checking button {i}: {e}")
            continue
    
    logger.info(f"Found {len(attendee_buttons)} attendee buttons")
    return attendee_buttons


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
            
            # Get attendee buttons (filtered)
            items = get_attendee_buttons(device)
            
            if len(items) == 0:
                logger.warning("No attendee items found, stopping")
                break
            
            if index >= len(items):
                logger.info("Reached end of current view")
                break
            
            # Get the button at current index
            button = items[index]
            
            # Extract name from button content-desc
            info = button.info
            content_desc = info.get('contentDescription', '')
            
            # Parse name from content-desc: "INITIALS, TITLE, NAME, ROLE\nCOMPANY"
            # Format example: "HH, FOUNDER / CEO (VISIONARY FOUNDERS), Haaris Hasnain, Founder\nDigivenX"
            name = None
            if content_desc and ',' in content_desc:
                parts = content_desc.split(',')
                if len(parts) >= 3:
                    # Name is in parts[2]
                    name = parts[2].strip().split('\n')[0].strip()
            
            if not name:
                logger.warning(f"Could not parse name at index {index}, content-desc: {content_desc[:100]}")
                index += 1
                continue
            
            # Check if already scraped (BEFORE clicking)
            if attendee_exists(name):
                logger.info(f"✓ Skipping duplicate: {name}")
                index += 1
                continue
            
            # Click item to open detail page
            logger.info(f"Processing: {name} (index {index})")
            try:
                button.click()
                time.sleep(config.CLICK_TIMEOUT)
                logger.debug(f"Clicked item {index}, waiting for page load...")
            except Exception as e:
                logger.error(f"Failed to click item {index}: {e}")
                index += 1
                continue
            
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
            
            # Scroll when we reach the last visible item
            if index >= len(items):
                logger.info("Scrolling to see more attendees...")
                
                # Save last attendee name before scroll (to detect duplicates)
                last_name = name
                
                try:
                    # Small scroll
                    list_container = device(**config.LIST_CONTAINER_SELECTOR)
                    if list_container.exists:
                        list_container.scroll.forward(steps=1)
                        time.sleep(0.5)
                        
                        # Check if we see new items
                        new_items = get_attendee_buttons(device)
                        
                        if len(new_items) == 0:
                            logger.info("No more attendees found after scroll, stopping")
                            break
                        
                        # Reset index to continue
                        index = 0
                        continue
                    else:
                        logger.info("Cannot scroll, stopping")
                        break
                except Exception as e:
                    logger.warning(f"Scroll error: {e}, stopping")
                    break
        
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
