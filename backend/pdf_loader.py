import PyPDF2
import os
from .calendar_utils import extract_calendar_events
import logging

logger = logging.getLogger(__name__)

def load_pdf_text(filepath):
    """
    Load and extract text from a PDF file.
    
    Args:
        filepath (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF, or None if there was an error
    """
    try:
        if not os.path.exists(filepath):
            print(f"PDF file not found: {filepath}")
            return None
            
        print(f"Opening PDF file: {filepath}")
        with open(filepath, 'rb') as file:
            # Create PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                print("PDF is encrypted")
                return None
                
            # Extract text from each page
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
                
            if not text.strip():
                print("No text extracted from PDF")
                return None
                
            print(f"Successfully extracted {len(text)} characters from PDF")
            
            # Extract calendar events from the text
            calendar_events = extract_calendar_events(text)
            logger.info(f"Extracted {len(calendar_events)} calendar events from PDF")
            
            return {
                'text': text,
                'calendar_events': calendar_events
            }
            
    except Exception as e:
        print(f"Error loading PDF: {str(e)}")
        return None
