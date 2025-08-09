# PDF Processor

A comprehensive PDF processing application that combines OCR (Optical Character Recognition) and PDF unlocking capabilities. Available as both a GUI application and a Discord bot!

## Features

- **OCR Processing**: Extract text from PDF files and save it to a text file
- **PDF Unlocking**: Remove password protection from PDF files
  - Manual password entry
  - Brute force password cracking (for simple passwords)
- **Discord Bot Integration**: Process PDFs directly through Discord commands

## Prerequisites

- Python 3.7 or higher
- Tesseract OCR engine
- Poppler (for PDF to image conversion)
- Required Python packages:
  - `pikepdf`
  - `pdf2image`
  - `pytesseract`
  - `discord.py`
  - `python-dotenv`
  - `customtkinter`

### Installing Prerequisites

#### Windows:
1. Install Tesseract OCR:
   - Download the installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your system PATH

2. Install Poppler:
   - Download from [poppler releases](http://blog.alivate.com.au/poppler-windows/)
   - Extract to a folder (e.g., C:\poppler-xx.xx.x)
   - Add the bin folder to your system PATH

#### Linux:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install poppler-utils
```

#### macOS:
```bash
brew install tesseract
brew install poppler
```

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/pdf-processor.git
cd pdf-processor
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```



## Usage

### GUI Application
1. Run the application:
```bash
python app.py
```

2. The application has two main tabs:

#### OCR Tab
- Click "Browse" to select a PDF file
- Choose an export directory
- Click "Start OCR" to begin text extraction
- The extracted text will be saved to a text file in the chosen directory

#### Unlock PDF Tab
- Click "Browse" to select a password-protected PDF
- Choose an export directory
- Either:
  - Enter the known password and click "Unlock with Password"
  - Click "Brute Force Unlock" to attempt to crack the password

### Discord Bot
1. Create a new Discord application and bot at [Discord Developer Portal](https://discord.com/developers/applications)
2. Get your bot token
3. Create a `.env` file in the project root and add your token:
```
DISCORD_TOKEN=<your-bot-token-here>
```
4. Run the bot:
```bash
python bot.py
```

#### Bot Commands
- `pdf help` - Show help message
- `pdf ocr` - Extract text from a PDF file (attach the PDF to your message)
- `pdf unlock <password>` - Unlock a PDF with a password (attach the PDF)
- `pdf bruteforce` - Attempt to crack the PDF password (attach the PDF)

## Notes

- The brute force feature is limited to simple passwords (length 1-4 characters) by default

- OCR accuracy depends on the quality of the PDF and the Tesseract installation
- The Discord bot creates a temporary directory for processing files, which are automatically cleaned up

## License

This project is licensed under the MIT License - see the LICENSE file for details.