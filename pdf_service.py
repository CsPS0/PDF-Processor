import os
import itertools
import string
import pytesseract
from pdf2image import convert_from_path
import pikepdf

def process_ocr(pdf_path: str, export_dir: str, max_pages: int = None) -> str:
    """
    Extracts text from a PDF using OCR and saves it to a text file.
    Raises ValueError if the PDF exceeds max_pages (if provided).
    Returns the path to the saved text file.
    """
    images = convert_from_path(pdf_path)
    
    if max_pages and len(images) > max_pages:
        raise ValueError(f"PDF too long ({len(images)} pages). Max allowed: {max_pages}")

    extracted_text = ""
    for i, img in enumerate(images):
        extracted_text += f"Page {i+1}:\n{pytesseract.image_to_string(img)}\n"
        extracted_text += "=" * 50 + "\n"

    output_file = os.path.join(export_dir, "extracted_text.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(extracted_text)
        
    return output_file

def unlock_pdf(pdf_path: str, password: str, export_dir: str) -> str:
    """
    Unlocks a PDF with the given password and saves it to export_dir.
    Returns the path to the unlocked PDF.
    Raises pikepdf.PasswordError if incorrect.
    """
    pdf = pikepdf.open(pdf_path, password=password)
    unlocked_pdf_path = os.path.join(export_dir, "unlocked.pdf")
    pdf.save(unlocked_pdf_path)
    return unlocked_pdf_path

def brute_force_pdf(pdf_path: str, export_dir: str, max_length: int = 4, charset: str = None, progress_callback=None) -> tuple[str, str]:
    """
    Attempts to brute force a PDF password.
    Returns a tuple of (found_password, unlocked_pdf_path) or (None, None) if not found.
    progress_callback is a function that takes (current_attempt, total_attempts)
    """
    if not charset:
        charset = string.ascii_letters + string.digits
        
    total_attempts = sum(len(charset)**l for l in range(1, max_length + 1))
    attempt_count = 0
    
    for length in range(1, max_length + 1):
        for password_tuple in itertools.product(charset, repeat=length):
            password = ''.join(password_tuple)
            attempt_count += 1
            
            # Call progress callback periodically (e.g. every 500 attempts)
            if progress_callback and attempt_count % 500 == 0:
                progress_callback(attempt_count, total_attempts)
                
            try:
                pdf = pikepdf.open(pdf_path, password=password)
                unlocked_pdf_path = os.path.join(export_dir, "unlocked.pdf")
                pdf.save(unlocked_pdf_path)
                return password, unlocked_pdf_path
            except pikepdf.PasswordError:
                continue
                
    return None, None
