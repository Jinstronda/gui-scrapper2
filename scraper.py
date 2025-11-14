import logging
import time
import config
from database import attendee_exists, save_attendee
from extractor import extract_from_detail_page

logger = logging.getLogger(__name__)


def check_and_recover_from_main_page(device):
    """
    Detect if we're on the main page and navigate back to attendee list.
    Returns True if we recovered, False if already on correct page.
    """
    # Check if "People" button exists (unique to main page)
    if device(content_desc="People").exists:
        logger.warning("Detected main page! Navigating back to attendees...")

        # Click on "People" tab
        device(content_desc="People").click()
        time.sleep(1.0)

        # Click on "Attendees" tab at the top (after People page loads)
        # Attendees tab should appear after clicking People
        if device(text="Attendees").exists:
            device(text="Attendees").click()
            time.sleep(1.0)
            logger.info("Successfully navigated back to attendee list")
            return True
        else:
            logger.warning("Could not find Attendees tab after clicking People")
            return False

    return False


def run_scraper(device):
    scraped_count = 0
    clicked_buttons = set()  # Track content-desc of buttons we've clicked

    while True:
        try:
            if scraped_count > 0 and scraped_count % 10 == 0:
                logger.info(f"[Progress] Saved: {scraped_count}")

            if config.MAX_ATTENDEES and scraped_count >= config.MAX_ATTENDEES:
                logger.info(f"Reached limit: {config.MAX_ATTENDEES}")
                break

            # Get RecyclerView
            recyclerview = device(className="androidx.recyclerview.widget.RecyclerView")
            if not recyclerview.exists:
                logger.warning("RecyclerView not found, scrolling...")
                # Check if we accidentally navigated to main page and recover
                if check_and_recover_from_main_page(device):
                    continue  # Recovery successful, restart loop
                device.swipe(500, 1500, 500, 700, duration=0.3)
                time.sleep(1.0)
                continue

            # Get ALL buttons inside RecyclerView (NO FILTERING)
            all_buttons = recyclerview.child(className="android.widget.Button")
            if not all_buttons.exists or all_buttons.count == 0:
                logger.info("No buttons found, scrolling...")
                device.swipe(500, 1500, 500, 700, duration=0.3)
                time.sleep(1.0)
                continue

            logger.info(f">> Found {all_buttons.count} buttons")

            # Click each button we haven't clicked yet
            for i in range(all_buttons.count):
                try:
                    button = all_buttons[i]
                    content_desc = button.info.get('contentDescription', '')

                    # Skip if we've already clicked this exact button
                    if content_desc in clicked_buttons:
                        continue

                    # CLICK IT
                    logger.info(f"CLICK button {i+1}/{all_buttons.count}")
                    button.click()
                    time.sleep(config.PAGE_LOAD_TIMEOUT)

                    # Extract ALL data from detail page
                    data = extract_from_detail_page(device)

                    # Mark as clicked (so we never click again)
                    clicked_buttons.add(content_desc)

                    # Go back
                    device.press("back")
                    time.sleep(config.CLICK_TIMEOUT)

                    # Check if we got valid data
                    if not data['name']:
                        logger.warning("No name found")
                        continue

                    # Check if already in DB
                    if attendee_exists(data['name']):
                        logger.info(f"SKIP: {data['name']} (in DB)")
                        continue

                    # Save new attendee
                    saved = save_attendee(
                        data['name'],
                        data['job_title'],
                        data['company'],
                        data['industry'],
                        data['job_function'],
                        data['operates_in']
                    )

                    if saved:
                        scraped_count += 1
                        fields = []
                        if data['job_title']: fields.append(f"title={data['job_title']}")
                        if data['company']: fields.append(f"company={data['company']}")
                        if data['industry']: fields.append(f"industry={data['industry']}")
                        if data['job_function']: fields.append(f"job={data['job_function']}")
                        if data['operates_in']: fields.append(f"location={data['operates_in']}")
                        logger.info(f"SAVED #{scraped_count}: {data['name']} | {', '.join(fields)}")

                except Exception as e:
                    logger.error(f"Error with button {i}: {e}")
                    device.press("back")
                    time.sleep(config.CLICK_TIMEOUT)
                    continue

            # Scroll to reveal more
            logger.info(f"[SCROLL] Total unique buttons clicked: {len(clicked_buttons)}")
            device.swipe(500, 1500, 500, 700, duration=0.3)
            time.sleep(1.0)

        except Exception as e:
            logger.error(f"Error: {e}")
            device.press("back")
            time.sleep(config.CLICK_TIMEOUT)

    return scraped_count
