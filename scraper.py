import logging
import time
import config
from database import attendee_exists, save_attendee
from extractor import extract_from_detail_page

logger = logging.getLogger(__name__)


def check_and_recover_from_main_page(device):
    """
    Detect if we're on the main page and navigate to attendee list.
    Navigation flow: Event Home → Menu → Attendees
    Returns True if we recovered, False if already on correct page.
    """
    # Check if we're already on attendees page (RecyclerView exists)
    if device(className="androidx.recyclerview.widget.RecyclerView").exists:
        logger.debug("Already on attendees page")
        return False

    logger.warning("Not on attendees page! Attempting to navigate...")

    # Check if we're on the menu/people page (attendees tab visible)
    if device(text="attendees").exists:
        logger.info("On menu page, clicking 'attendees' tab...")
        device(text="attendees").click()
        time.sleep(2.0)

        # Verify we made it to attendees list
        if device(className="androidx.recyclerview.widget.RecyclerView").exists:
            logger.info("Successfully navigated to attendee list")
            return True
        else:
            logger.warning("Clicked attendees but RecyclerView not found")
            return False

    # Check if we're on event home page (Menu button visible)
    if device(text="Menu").exists:
        logger.info("On event home page, clicking 'Menu' button...")
        device(text="Menu").click()
        time.sleep(2.0)

        # Now click attendees tab
        if device(text="attendees").exists:
            logger.info("Menu opened, clicking 'attendees' tab...")
            device(text="attendees").click()
            time.sleep(2.0)

            # Verify we made it to attendees list
            if device(className="androidx.recyclerview.widget.RecyclerView").exists:
                logger.info("Successfully navigated to attendee list")
                return True
            else:
                logger.warning("Clicked attendees but RecyclerView not found")
                return False
        else:
            logger.error("Menu opened but 'attendees' tab not found!")
            return False

    # If we can't find Menu or attendees, we're in an unknown state
    logger.error("Unknown page state - cannot find Menu or attendees elements")
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
                    # Check if it's a stale button reference error
                    if "UiObjectNotFoundException" in str(e):
                        logger.warning("Stale button reference, restarting iteration...")
                        break  # Break out of button loop, restart from top

                    # Only press back if we're NOT on the list page (i.e., we're on a detail page)
                    # This prevents accidentally exiting the app if we're on the home page
                    if not device(className="androidx.recyclerview.widget.RecyclerView").exists:
                        logger.info("Not on list page, pressing back to recover...")
                        device.press("back")
                        time.sleep(config.CLICK_TIMEOUT)
                    else:
                        logger.info("Already on list page, no need to press back")
                    continue

            # Scroll to reveal more
            logger.info(f"[SCROLL] Total unique buttons clicked: {len(clicked_buttons)}")
            device.swipe(500, 1500, 500, 700, duration=0.3)
            time.sleep(1.0)

        except Exception as e:
            logger.error(f"Error: {e}")
            # Do NOT press back here - let the recovery function handle navigation
            # Pressing back blindly could exit the app if we're on the home page
            time.sleep(config.CLICK_TIMEOUT)

    return scraped_count
