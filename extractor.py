import xml.etree.ElementTree as ET
import logging
import time
import config

logger = logging.getLogger(__name__)


def extract_from_detail_page(device):
    time.sleep(config.PAGE_LOAD_TIMEOUT)
    
    xml = device.dump_hierarchy()
    root = ET.fromstring(xml)
    
    # Extract all TextViews
    all_texts = []
    for elem in root.iter():
        if elem.get('class') == 'android.widget.TextView':
            text = elem.get('text', '').strip()
            if text:
                all_texts.append(text)
    
    logger.debug(f"All texts found: {all_texts}")
    
    # Initialize data
    data = {
        'name': None,
        'industry': None,
        'job_function': None,
        'operates_in': None
    }
    
    # Find name - look for large name TextView (usually between index 2-6)
    # Skip common UI labels
    skip_texts = ['Introduction', 'Interests', 'Chat', 'Suggest meeting', 
                  'Navigate up', 'Operates in', 'Industry', 'Job Function']
    
    for i, text in enumerate(all_texts):
        # Name is usually a proper name (2-4 words, letters and spaces)
        if (text not in skip_texts and 
            len(text) > 5 and 
            2 <= len(text.split()) <= 4 and
            all(c.isalpha() or c.isspace() for c in text) and
            data['name'] is None):
            data['name'] = text
            logger.debug(f"Found name: {text}")
            break
    
    # Parse labeled fields
    for i, text in enumerate(all_texts):
        if text == config.FIELD_LABEL_INDUSTRY and i + 1 < len(all_texts):
            next_text = all_texts[i + 1]
            if next_text not in skip_texts:
                data['industry'] = next_text
                logger.debug(f"Found industry: {next_text}")
        
        elif text == config.FIELD_LABEL_JOB_FUNCTION and i + 1 < len(all_texts):
            next_text = all_texts[i + 1]
            if next_text not in skip_texts:
                data['job_function'] = next_text
                logger.debug(f"Found job function: {next_text}")
        
        elif text == config.FIELD_LABEL_OPERATES_IN and i + 1 < len(all_texts):
            # Collect countries (skip labels and UI elements)
            countries = []
            j = i + 1
            while j < len(all_texts):
                next_text = all_texts[j]
                # Stop if we hit another label
                if next_text in [config.FIELD_LABEL_INDUSTRY, config.FIELD_LABEL_JOB_FUNCTION]:
                    break
                # Add if it looks like a country name (not a label)
                if (next_text not in skip_texts and 
                    len(next_text) > 2 and 
                    all(c.isalpha() or c.isspace() for c in next_text)):
                    countries.append(next_text)
                j += 1
                if len(countries) >= 5:  # Max 5 countries
                    break
            
            if countries:
                data['operates_in'] = ', '.join(countries)
                logger.debug(f"Found operates in: {data['operates_in']}")
    
    logger.info(f"Extracted from detail page: {data}")
    return data


def extract_name_from_list(device, index):
    try:
        items = device(**config.LIST_ITEM_SELECTOR)
        
        if index >= items.count:
            logger.warning(f"Index {index} >= item count {items.count}")
            return None
            
        item = items[index]
        
        # Get content-desc which has format: "TITLE, NAME, ROLE\nCOMPANY"
        info = item.info
        content_desc = info.get('contentDescription', '')
        
        logger.debug(f"Button {index} content-desc: {content_desc}")
        
        if content_desc:
            # Split by comma to get parts
            parts = content_desc.split(',')
            if len(parts) >= 2:
                # Second part is the name (before any newline)
                name = parts[1].strip().split('\n')[0].strip()
                logger.debug(f"Parsed name from content-desc: {name}")
                return name
        
        # Fallback: try TextViews
        try:
            text_views = item.child(className="android.widget.TextView")
            if text_views.exists and text_views.count > 1:
                # Usually name is the second TextView
                name = text_views[1].get_text().strip()
                logger.debug(f"Fallback: got name from TextView: {name}")
                return name
        except Exception as e:
            logger.debug(f"Fallback TextView extraction failed: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract name at index {index}: {e}")
        return None
