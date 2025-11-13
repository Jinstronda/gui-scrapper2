import xml.etree.ElementTree as ET
import logging
import time
import config

logger = logging.getLogger(__name__)


def extract_from_detail_page(device):
    time.sleep(config.PAGE_LOAD_TIMEOUT)
    
    xml = device.dump_hierarchy()
    root = ET.fromstring(xml)
    
    # Extract all TextViews with their text
    all_texts = []
    for elem in root.iter():
        if elem.get('class') == 'android.widget.TextView':
            text = elem.get('text', '').strip()
            if text and text not in ['Introduction', 'Interests', 'Chat', 'Suggest meeting']:
                all_texts.append(text)
    
    # Initialize data
    data = {
        'name': None,
        'industry': None,
        'job_function': None,
        'operates_in': None
    }
    
    # Find name (large TextView near top, usually after job title)
    for i, text in enumerate(all_texts):
        if len(text) > 3 and text.replace(' ', '').isalpha():
            if data['name'] is None and i < 10:
                data['name'] = text
                break
    
    # Parse labeled fields
    for i, text in enumerate(all_texts):
        if text == config.FIELD_LABEL_INDUSTRY and i + 1 < len(all_texts):
            data['industry'] = all_texts[i + 1]
        elif text == config.FIELD_LABEL_JOB_FUNCTION and i + 1 < len(all_texts):
            data['job_function'] = all_texts[i + 1]
        elif text == config.FIELD_LABEL_OPERATES_IN and i + 1 < len(all_texts):
            # Collect all countries (may be multiple)
            countries = []
            j = i + 1
            while j < len(all_texts) and all_texts[j] not in [config.FIELD_LABEL_INDUSTRY, config.FIELD_LABEL_JOB_FUNCTION]:
                countries.append(all_texts[j])
                j += 1
                if j >= i + 5:  # Max 4 countries
                    break
            data['operates_in'] = ', '.join(countries) if countries else None
    
    logger.debug(f"Extracted: {data}")
    return data


def extract_name_from_list(device, index):
    try:
        items = device(**config.LIST_ITEM_SELECTOR)
        if index < items.count:
            item = items[index]
            
            # Try to get content-desc (Brella app uses this)
            info = item.info
            content_desc = info.get('contentDescription', '')
            
            if content_desc:
                # Parse name from content-desc
                # Format: "TITLE, Name, Job\nCompany"
                parts = content_desc.split(',')
                if len(parts) >= 2:
                    name = parts[1].strip().split('\n')[0]
                    return name
            
            # Fallback: try TextViews
            text_views = item.child(className="android.widget.TextView")
            if text_views.count > 0:
                return text_views[0].get_text().strip()
        
        return None
    except Exception as e:
        logger.error(f"Failed to extract name at index {index}: {e}")
        return None
