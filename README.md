> [!WARNING]
> ## ARCHIVED
> This repository is archived and no longer actively maintained. For production PDF processing, text extraction, and password recovery / security auditing, please use dedicated, industry-standard, and heavily optimized open-source tools:
> This repository is archived and no longer actively maintained. For production PDF processing, text extraction, and password recovery / security auditing, please use dedicated, industry-standard, and heavily optimized open-source tools:
>
> - **Password Recovery & Security Auditing:**
>   - [John the Ripper](https://en.wikipedia.org/wiki/John_the_Ripper) (`pdf2john.py` + `john`) — Industry-standard multi-hash password cracker with GPU, OpenCL, and SIMD acceleration.
>   - [Hashcat](https://hashcat.net/hashcat/) — Highly optimized, hardware-accelerated password recovery suite with advanced rule engines.
>   - [qpdf](https://github.com/qpdf/qpdf) — Robust CLI tool for PDF transformations, structure inspection, and password stripping.
> - **OCR & Text Extraction:**
>   - [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) — The official Google open-source OCR engine.
>   - [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) — High-quality automated tool adding searchable text layers to scanned PDFs.

# PDF Processor

A comprehensive PDF processing application that combines OCR (Optical Character Recognition) and PDF unlocking capabilities. Available as both a desktop GUI application and a Discord bot.

The project uses a clean Service Layer architecture (`pdf_service.py`), ensuring code reusability and modularity across both interfaces.

## Features

- **OCR Processing**: Extract text from PDF files with multi-language support (English, Hungarian, German, French, Spanish). Powered by Tesseract OCR.
- **PDF Unlocking**: Remove password protection from PDF files with a known password.
- **Brute Force Cracking**: Crack PDF passwords with configurable character sets and max length (1–8 characters). Real-time progress with speed and ETA display.
- **Cancel Operations**: Abort any long-running operation mid-process.
- **PDF Information**: View page count, file size, and encryption status before processing.
- **Settings Persistence**: Theme, default export directory, OCR language, and brute force settings are saved between sessions.
- **Discord Bot Integration**: Process PDFs directly through Discord commands with charset selection.
- **Light/Dark Theme**: Toggle between light and dark mode. Follows system preference by default.

## Screenshots

The GUI features a modern sidebar navigation with card-based sections, an always-visible status bar with progress tracking, and a refined Oxford Blue (`#14213d`) and Orange Web (`#fca311`) color palette.

## Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine
- Poppler (for PDF to image conversion)

### Installing Prerequisites

#### Windows
1. Install Tesseract OCR:
   - Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your system PATH

2. Install Poppler:
   - Download from [poppler releases](https://github.com/oschwartz10612/poppler-windows/releases)
   - Extract and add the `bin` folder to your system PATH

#### Linux
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
```

#### macOS
```bash
brew install tesseract poppler
```

## Installation

1. Clone this repository:
```bash
git clone https://github.com/CsPS0/PDF-Processor.git
cd PDF-Processor
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### GUI Application

```bash
python app.py
```

The application has four sections accessible via the sidebar:

#### OCR
- Select a PDF file and export directory
- Choose the OCR language (English, Hungarian, German, French, Spanish)
- Click "Start OCR" to extract text
- View progress page-by-page in the status bar
- Cancel mid-operation if needed

#### Unlock PDF
- Select a password-protected PDF
- Enter the known password
- Click "Unlock PDF" to remove protection

#### Brute Force
- Select a password-protected PDF
- Choose a character set (Alphanumeric, Numbers Only, Lowercase, Uppercase, Letters Only, All ASCII)
- Set max password length (1–8 characters)
- Click "Start Brute Force" to begin cracking
- Monitor speed (attempts/second) and ETA in the status bar
- Cancel at any time

#### Settings
- Choose theme (System, Light, Dark)
- Set default export directory
- Set default OCR language
- Set default brute force max length
- Save or reset to defaults

### Discord Bot

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a `.env` file:
```
DISCORD_TOKEN=<your-bot-token-here>
```
3. Run the bot:
```bash
python bot.py
```

#### Bot Commands
- `pdf help` — Show help message with available commands
- `pdf ocr` — Extract text from an attached PDF
- `pdf unlock <password>` — Unlock an attached PDF with a password
- `pdf bruteforce [charset]` — Crack an attached PDF password (charsets: `alphanumeric`, `numbers`, `lowercase`, `uppercase`, `letters`, `all`)

### Documentation Website

The `docs/` directory contains a static documentation website with download links and feature information. Open `docs/index.html` in a browser.

## Architecture

```
app.py          → GUI (customtkinter, sidebar layout)
bot.py          → Discord bot (discord.py)
pdf_service.py  → Shared service layer (OCR, unlock, brute force)
config.py       → Persistent settings management
exceptions.py   → Custom exception hierarchy
themes/         → CustomTkinter theme JSON
docs/           → Documentation website
```

## Notes

- Brute force max length is configurable from 1 to 8 characters. Higher values with large charsets take significantly longer.
- OCR accuracy depends on PDF quality and the Tesseract language packs installed.
- Output files use safe naming to avoid overwriting existing files.
- The application checks for Tesseract and Poppler on startup and warns if missing.

## License

This project is licensed under the MIT License — see the LICENSE file for details.