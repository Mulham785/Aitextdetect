import PyPDF2
import os
from werkzeug.utils import secure_filename


def extract_text_from_pdf(file_path):
    """Extract text content from a PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)

            for page_num in range(num_pages):
                page = reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

    return text


def save_uploaded_file(file, upload_folder):
    """Save uploaded file to the specified folder"""
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        return file_path
    return None