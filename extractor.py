import xml.etree.ElementTree as ET
import logging
import time
import config

logger = logging.getLogger(__name__)


def extract_from_detail_page(device):
    time.sleep(config.PAGE_LOAD_TIMEOUT)

    # Extract texts from top first (to get name, job title, company)
    xml = device.dump_hierarchy()
    root = ET.fromstring(xml)

    all_texts = []
    for elem in root.iter():
        if elem.get('class') == 'android.widget.TextView':
            text = elem.get('text', '').strip()
            if text:
                all_texts.append(text)

    logger.debug(f"Texts before scroll (first 15): {all_texts[:15]}")

    # Gentle scroll to see Industry/Job Function/Operates in (don't scroll too much!)
    device.swipe(500, 1400, 500, 1000, duration=0.3)  # Small scroll (400px)
    time.sleep(0.3)

    # Extract after scroll
    xml = device.dump_hierarchy()
    root = ET.fromstring(xml)

    for elem in root.iter():
        if elem.get('class') == 'android.widget.TextView':
            text = elem.get('text', '').strip()
            if text and text not in all_texts:
                all_texts.append(text)

    # Second small scroll
    device.swipe(500, 1400, 500, 1000, duration=0.3)  # Small scroll (400px)
    time.sleep(0.3)

    # Extract again after second scroll
    xml = device.dump_hierarchy()
    root = ET.fromstring(xml)

    for elem in root.iter():
        if elem.get('class') == 'android.widget.TextView':
            text = elem.get('text', '').strip()
            if text and text not in all_texts:
                all_texts.append(text)

    logger.debug(f"Total texts collected: {len(all_texts)}")
    
    # Initialize data
    data = {
        'name': None,
        'job_title': None,
        'company': None,
        'industry': None,
        'job_function': None,
        'operates_in': None
    }

    # Find name - look for proper name (2-4 words, letters and spaces)
    skip_texts = ['Introduction', 'Interests', 'Chat', 'Suggest meeting',
                  'Navigate up', 'Operates in', 'Industry', 'Job Function']

    name_index = None
    for i, text in enumerate(all_texts):
        if (text not in skip_texts and
            len(text) > 5 and
            2 <= len(text.split()) <= 4 and
            all(c.isalpha() or c.isspace() for c in text) and
            data['name'] is None):
            data['name'] = text
            name_index = i
            break

    # Job title and Company come AFTER the name as separate TextViews
    if name_index is not None:
        # Job title is the next TextView after name
        if name_index + 1 < len(all_texts):
            job_title_candidate = all_texts[name_index + 1].strip()
            # Make sure it's not a label or skip text
            if job_title_candidate not in skip_texts and len(job_title_candidate) > 0:
                data['job_title'] = job_title_candidate

        # Company is the TextView after job title
        if name_index + 2 < len(all_texts):
            company_candidate = all_texts[name_index + 2].strip()
            # Make sure it's not a label or skip text
            if company_candidate not in skip_texts and len(company_candidate) > 0:
                data['company'] = company_candidate


    # Parse labeled fields
    for i, text in enumerate(all_texts):
        if text == config.FIELD_LABEL_INDUSTRY and i + 1 < len(all_texts):
            next_text = all_texts[i + 1]
            if next_text not in skip_texts:
                data['industry'] = next_text

        elif text == config.FIELD_LABEL_JOB_FUNCTION and i + 1 < len(all_texts):
            next_text = all_texts[i + 1]
            if next_text not in skip_texts:
                data['job_function'] = next_text

        elif text == config.FIELD_LABEL_OPERATES_IN and i + 1 < len(all_texts):
            countries = []
            j = i + 1
            while j < len(all_texts):
                next_text = all_texts[j]
                if next_text in [config.FIELD_LABEL_INDUSTRY, config.FIELD_LABEL_JOB_FUNCTION]:
                    break
                if (next_text not in skip_texts and
                    len(next_text) > 2 and
                    all(c.isalpha() or c.isspace() for c in next_text)):
                    countries.append(next_text)
                j += 1
                if len(countries) >= 5:
                    break

            if countries:
                data['operates_in'] = ', '.join(countries)

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
