# Book to Markdown Converter

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

A document converter that transforms books and documents into clean, well-formatted Markdown. Built with PyMuPDF (Fitz) for reliable text extraction and structure analysis.

## ✨ Features

- **Multiple Format Support**: Convert PDF, EPUB, MOBI, FB2, and XPS files to Markdown
- **Intelligent Structure Detection**: Automatically identifies headers, paragraphs, and code blocks based on font analysis
- **Clean Output**: Generates readable Markdown with proper formatting
- **Header/Footer Filtering**: Intelligently removes page numbers and repetitive headers from PDFs
- **Code Block Detection**: Recognizes monospace fonts and converts them to proper Markdown code blocks
- **Type-Safe**: Fully typed with comprehensive type hints for better IDE support

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/soficis/book-to-markdown.git
   cd book-to-markdown
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   Or manually:
   ```bash
   pip install PyMuPDF
   ```

### Programmatic Usage

You can also use the converter in your Python code:

```python
from book_to_md import convert_document_to_markdown

# Convert a document
convert_document_to_markdown("input.pdf", "output.md")
```

See `example.py` for a complete example script.

**Basic conversion:**
```bash
python book_to_md.py your-book.pdf
```

**Specify output file:**
```bash
python book_to_md.py your-book.epub output.md
```

**Supported formats:**
- PDF (`.pdf`)
- EPUB (`.epub`)
- MOBI (`.mobi`)
- FB2 (`.fb2`)
- XPS (`.xps`)

## 📁 Project Structure

```
book-to-markdown/
├── book_to_md.py          # Main converter module
├── example.py             # Example usage script
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── LICENSE                # MIT License
├── .gitignore            # Git ignore rules
└── REFACTORING_SUMMARY.md # Clean Code refactoring details
```

The converter uses advanced font analysis to understand document structure:

1. **Font Analysis**: Scans the entire document to identify font sizes and styles
2. **Structure Detection**: Determines which fonts represent headers, paragraphs, and code blocks
3. **Content Extraction**: Extracts text while preserving logical structure
4. **Markdown Generation**: Converts the structured content to clean Markdown

### Font Detection Logic

- **Headers**: Larger fonts than the most common paragraph font
- **Paragraphs**: Most frequently used font size in the document
- **Code Blocks**: Monospace fonts (Courier, Consolas, Monaco, etc.)
- **Small Text**: Smaller fonts, formatted as italicized text

## 🛠️ Architecture

The codebase follows Clean Code principles with well-structured components:

### Core Classes

- **`FontMetrics`**: Represents font styling information
- **`DocumentFontAnalysis`**: Results of font analysis across the document
- **`FontSizeTagMapping`**: Maps font sizes to Markdown tags
- **`PageMargins`**: Configuration for header/footer filtering
- **`TextSpan`**: Extracted text with formatting information
- **`DocumentProcessor`**: Main processing logic with static methods

### Key Functions

- `analyze_document_fonts()`: Extracts and analyzes fonts
- `extract_text_with_tags()`: Extracts text with structural tags
- `format_markdown()`: Converts tagged content to Markdown
- `convert_document_to_markdown()`: Main conversion function

## 📋 System Requirements

- **Python**: 3.8 or higher

### Dependencies

- **PyMuPDF (Fitz)**: `>= 1.23.0` - PDF processing and text extraction
- **Standard Library**: `os`, `sys`, `re`, `dataclasses`, `typing`, `operator`

### Supported Platforms

- **Windows**: ✅ Fully supported
- **macOS**: ✅ Should work (not tested)
- **Linux**: ✅ Should work (not tested)

## 🔧 Development

### Setting up Development Environment

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install PyMuPDF
   ```

3. **Run tests:**
   ```bash
   python -m pytest  # If you add tests
   ```

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

The GPLv3 ensures that this software remains free and open source, requiring that any modifications or derivative works also be released under the same license.

## 🙏 Acknowledgments

- Built with [PyMuPDF](https://pymupdf.readthedocs.io/) (Fitz) for PDF processing
- Font detection logic adapted from various document processing projects