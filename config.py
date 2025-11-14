# Device Configuration
DEVICE_SERIAL = None  # None for auto-detect, or specify serial number

# Timeouts (in seconds)
CLICK_TIMEOUT = 0.3
PAGE_LOAD_TIMEOUT = 1.0
SCROLL_WAIT = 0.01

# Scraping Behavior
MAX_ATTENDEES = None  # No limit - scrape all attendees
SAVE_SCREENSHOTS_ON_ERROR = True

# Database
DB_PATH = "attendees_v2.db"  # New database with job_title and company columns

# Screenshots
SCREENSHOT_DIR = "screenshots"

# ============================================
# UI SELECTORS - DISCOVERED FROM hierarchy.xml
# ============================================

APP_PACKAGE = "com.brella"

# List view selectors
LIST_ITEM_SELECTOR = {
    "className": "android.widget.Button",
    "clickable": True
}

LIST_CONTAINER_SELECTOR = {
    "className": "androidx.recyclerview.widget.RecyclerView"
}

# Alternative scroll container (if RecyclerView doesn't work)
SCROLL_VIEW_SELECTOR = {
    "className": "android.widget.ScrollView"
}

# Detail Page Field Labels (discovered from detail page hierarchy)
FIELD_LABEL_INDUSTRY = "Industry"
FIELD_LABEL_JOB_FUNCTION = "Job Function"
FIELD_LABEL_OPERATES_IN = "Operates in"
