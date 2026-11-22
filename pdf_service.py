import os
import time
import string
import shutil
import itertools
import pikepdf
from pdf2image import convert_from_path
import pytesseract
from exceptions import OperationCancelledError, InvalidPDFError


CHARSETS = {
    "Alphanumeric": string.ascii_letters + string.digits,
    "Numbers Only": string.digits,
    "Lowercase Letters": string.ascii_lowercase,
    "Uppercase Letters": string.ascii_uppercase,
    "Letters Only": string.ascii_letters,
    "All ASCII": string.printable.strip(),
}


def check_dependencies():
    issues = []
    if not shutil.which("tesseract"):
        issues.append(
            ("Tesseract OCR", "https://github.com/tesseract-ocr/tesseract")
        )
    if not shutil.which("pdftoppm") and not shutil.which("pdftocairo"):
        issues.append(
            ("Poppler", "https://github.com/oschwartz10612/poppler-windows/releases")
        )
    return issues


def get_pdf_info(pdf_path):
    if not os.path.isfile(pdf_path):
        raise InvalidPDFError(f"File not found: {pdf_path}")

    file_size = os.path.getsize(pdf_path)
    size_mb = file_size / (1024 * 1024)

    try:
        pdf = pikepdf.open(pdf_path)
        pages = len(pdf.pages)
        encrypted = False
        title = ""
        author = ""
        if pdf.docinfo:
            title = str(pdf.docinfo.get("/Title", ""))
            author = str(pdf.docinfo.get("/Author", ""))
        pdf.close()
    except pikepdf.PasswordError:
        pages = "N/A"
        encrypted = True
        title = ""
        author = ""
    except Exception as e:
        raise InvalidPDFError(f"Cannot read PDF: {e}")

    return {
        "filename": os.path.basename(pdf_path),
        "pages": pages,
        "size_mb": size_mb,
        "encrypted": encrypted,
        "title": title,
        "author": author,
    }


def _safe_output_path(directory, filename):
    path = os.path.join(directory, filename)
    if not os.path.exists(path):
        return path
    name, ext = os.path.splitext(filename)
    counter = 1
    while os.path.exists(os.path.join(directory, f"{name}_{counter}{ext}")):
        counter += 1
    return os.path.join(directory, f"{name}_{counter}{ext}")


def process_ocr(pdf_path, export_dir, lang="eng", max_pages=None,
                progress_callback=None, cancel_event=None):
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be at least 1")

    images = convert_from_path(pdf_path)

    if max_pages:
        images = images[:max_pages]

    total_pages = len(images)
    extracted_text = []

    for i, image in enumerate(images):
        if cancel_event and cancel_event.is_set():
            raise OperationCancelledError("OCR cancelled")

        text = pytesseract.image_to_string(image, lang=lang)
        extracted_text.append(f"--- Page {i + 1} ---\n{'=' * 50}\n{text}\n")

        if progress_callback:
            progress_callback(i + 1, total_pages)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = _safe_output_path(export_dir, f"{pdf_name}_extracted.txt")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(extracted_text))

    return output_path


def unlock_pdf(pdf_path, password, export_dir):
    pdf = pikepdf.open(pdf_path, password=password)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    output_path = _safe_output_path(export_dir, f"{pdf_name}_unlocked.pdf")
    pdf.save(output_path)
    pdf.close()
    return output_path


def brute_force_pdf(pdf_path, export_dir, max_length=4, charset=None,
                    progress_callback=None, cancel_event=None):
    if charset is None:
        charset = CHARSETS["Alphanumeric"]

    total = sum(len(charset) ** length for length in range(1, max_length + 1))
    current = 0
    start_time = time.time()

    for length in range(1, max_length + 1):
        for attempt in itertools.product(charset, repeat=length):
            if cancel_event and cancel_event.is_set():
                raise OperationCancelledError("Brute force cancelled")

            password = "".join(attempt)
            current += 1

            try:
                pdf = pikepdf.open(pdf_path, password=password)
                pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
                output_path = _safe_output_path(
                    export_dir, f"{pdf_name}_cracked.pdf"
                )
                pdf.save(output_path)
                pdf.close()
                return password, output_path
            except pikepdf.PasswordError:
                pass

            if progress_callback and current % 500 == 0:
                elapsed = time.time() - start_time
                speed = current / elapsed if elapsed > 0 else 0
                remaining = total - current
                eta = remaining / speed if speed > 0 else 0
                progress_callback(current, total, speed, eta)

    return None, None
