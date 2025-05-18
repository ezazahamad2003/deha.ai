import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def extract_calendar_events(text):
    """
    Extract calendar events from medical record text.
    
    Args:
        text (str): The medical record text to process
        
    Returns:
        list: List of calendar events with dates and descriptions
    """
    try:
        events = []
        
        # Common date patterns in medical records
        date_patterns = [
            # MM/DD/YYYY or MM-DD-YYYY
            r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
            # Month DD, YYYY
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
            # YYYY-MM-DD
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        # Combine all patterns
        combined_pattern = '|'.join(date_patterns)
        
        # Find all dates and surrounding context
        lines = text.split('\n')
        for line in lines:
            matches = re.finditer(combined_pattern, line, re.IGNORECASE)
            for match in matches:
                date_str = match.group(0)
                try:
                    # Parse the date string into a datetime object
                    if '/' in date_str or '-' in date_str:
                        if len(date_str.split('/')[-1]) == 4 or len(date_str.split('-')[-1]) == 4:
                            date = datetime.strptime(date_str, '%m/%d/%Y' if '/' in date_str else '%m-%d-%Y')
                        else:
                            date = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date = datetime.strptime(date_str, '%B %d, %Y')
                    
                    # Get context around the date (the full line)
                    context = line.strip()
                    
                    # Categorize the event based on keywords
                    category = categorize_event(context)
                    
                    events.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'description': context,
                        'category': category
                    })
                    
                except ValueError as e:
                    logger.warning(f"Could not parse date '{date_str}': {str(e)}")
                    continue
        
        # Sort events by date
        events.sort(key=lambda x: x['date'])
        return events
        
    except Exception as e:
        logger.error(f"Error extracting calendar events: {str(e)}")
        return []

def categorize_event(context):
    """
    Categorize medical events based on context keywords.
    """
    context = context.lower()
    
    categories = {
        'appointment': ['appointment', 'visit', 'consultation', 'follow-up', 'follow up', 'scheduled'],
        'procedure': ['surgery', 'procedure', 'operation', 'scan', 'mri', 'ct', 'x-ray', 'test'],
        'medication': ['prescription', 'refill', 'medication', 'drug', 'dose'],
        'lab': ['lab', 'blood', 'test', 'sample', 'results'],
        'general': ['exam', 'check', 'review']
    }
    
    for category, keywords in categories.items():
        if any(keyword in context for keyword in keywords):
            return category
    
    return 'other'