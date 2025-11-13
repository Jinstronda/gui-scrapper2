# Android Attendee Scraper

Automated scraper for collecting attendee data from Android emulator.

## Features

- Extracts: Name, Industry, Job Function, Operates In
- SQLite database storage
- Duplicate detection (can restart safely)
- Error recovery with screenshots
- Comprehensive logging

## Architecture

Based on proven scraper design from `Scrapper for Gui`:
- **Modular structure**: Separate concerns (device, database, extractor, scraper)
- **Always-click approach**: Clicks into each detail page for complete data
- **Error resilient**: Screenshots on error, automatic recovery
- **Duplicate detection**: Skips already-scraped attendees

## Quick Start

### 1. Install Dependencies

```bash
conda activate turing0.1
pip install -r requirements.txt
```

### 2. Discover UI Selectors

**Important: Start emulator and open the target app first!**

```bash
python setup.py
```

This will:
- Connect to your emulator
- Dump the UI hierarchy to `hierarchy.xml`
- Display the app package name

### 3. Update Config

Open `hierarchy.xml` and find:
- List item resourceId (e.g., `com.example.app:id/item_layout`)
- List container resourceId (e.g., `android:id/list`)
- Field labels on detail page (Name, Industry, Job Function, Company)

Update `config.py` with these values:

```python
APP_PACKAGE = "com.example.app"  # From setup.py output

LIST_ITEM_SELECTOR = {
    "resourceId": "com.example.app:id/item_layout"
}

LIST_CONTAINER_SELECTOR = {
    "resourceId": "android:id/list"
}

FIELD_LABEL_NAME = "Name"
FIELD_LABEL_INDUSTRY = "Industry"
FIELD_LABEL_JOB_FUNCTION = "Job Title"
FIELD_LABEL_OPERATES_IN = "Company"
```

### 4. Run Scraper

```bash
python main.py
```

The scraper will:
- Connect to your emulator
- Loop through attendees list
- Click each item → extract data → press back
- Save to SQLite database
- Skip duplicates automatically

## Configuration Options

Edit `config.py` to customize:

```python
# Test with limited attendees
MAX_ATTENDEES = 10  # Set to None for unlimited

# Adjust timing if needed
CLICK_TIMEOUT = 0.2
PAGE_LOAD_TIMEOUT = 0.8
SCROLL_WAIT = 0.01

# Error handling
SAVE_SCREENSHOTS_ON_ERROR = True
SCREENSHOT_DIR = "screenshots"
```

## Database

SQLite database: `attendees.db`

Schema:
```sql
CREATE TABLE attendees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    industry TEXT,
    job_function TEXT,
    operates_in TEXT,
    scraped_at TIMESTAMP
)
```

View data:
```bash
sqlite3 attendees.db "SELECT * FROM attendees LIMIT 10;"
```

## Project Structure

```
main.py           # Entry point
config.py         # Configuration & selectors
device.py         # Device connection
database.py       # SQLite operations
scraper.py        # Main scraping loop
extractor.py      # Data extraction logic
utils.py          # Logging & helpers
setup.py          # UI inspector
requirements.txt  # Dependencies
attendees.db      # SQLite database (auto-created)
hierarchy.xml     # UI dump (created by setup.py)
scraper.log       # Execution log
screenshots/      # Error screenshots
```

## Performance

- ~1.5-2 seconds per attendee (click + extract + back)
- ~30-40 attendees per minute
- ~1000 attendees in 25-30 minutes

## Troubleshooting

### Can't connect to device
- Check emulator is running: `adb devices`
- Try specifying serial: `DEVICE_SERIAL = "emulator-5554"` in config.py

### Wrong data extracted
- Re-run `setup.py` and check hierarchy.xml
- Verify field labels in config.py match actual UI text
- Check screenshots/ folder for error images

### Scraper stops early
- Check logs in `scraper.log`
- Verify LIST_CONTAINER_SELECTOR for scrolling
- Try increasing timeouts in config.py

### Duplicates in database
- Database has UNIQUE constraint on name
- Safe to restart scraper - will skip existing entries
- Check logs: "Skipping duplicate: [name]"

## Logs

All activity logged to:
- Console (stdout)
- `scraper.log` file

Log levels: INFO, WARNING, ERROR

## Next Steps

1. **Run setup.py** to discover selectors
2. **Update config.py** with discovered values
3. **Test with MAX_ATTENDEES=10** first
4. **Run full scrape** with MAX_ATTENDEES=None
5. **Query database** to verify data quality
