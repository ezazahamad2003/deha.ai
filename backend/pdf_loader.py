import PyPDF2

def load_pdf_text(path: str) -> str:
    """
    Read the entire PDF and return its text content as a single string.
    
    Args:
        path (str): The path to the PDF file.
    
    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text
