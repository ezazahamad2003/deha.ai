import PyPDF2

def load_pdf_text(file_path):
    """
    Load and extract text from a PDF file.
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
                
            return text
    except Exception as e:
        print(f"Error loading PDF: {e}")
        return None
