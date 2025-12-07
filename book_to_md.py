import fitz  # PyMuPDF
import sys
import re
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from operator import itemgetter

# Constants
TEXT_BLOCK_TYPE = 0
DEFAULT_OUTPUT_FILENAME = "output.md"
PDF_HEADER_MARGIN = 50
PDF_FOOTER_MARGIN = 50
FONT_TYPES = {
    "text": 0
}

# Font detection keywords for code blocks
CODE_FONT_KEYWORDS = ("mono", "courier", "code", "consolas")
MARKDOWN_PARAGRAPH_TAG = "<p>"
MARKDOWN_CODE_TAG = "<code>"
MARKDOWN_SMALL_TAG = "<s>"
MARKDOWN_HEADER_PATTERN = "<h{0}>"


@dataclass
class FontMetrics:
    """Font style information extracted from a document."""
    size: float
    font: str
    flags: int = 0
    color: int = 0

    def create_identifier(self, include_color_and_flags: bool = False) -> str:
        """Generate unique identifier for font metrics."""
        if include_color_and_flags:
            return f"{self.size}_{self.flags}_{self.font}_{self.color}"
        return str(self.size)


@dataclass
class DocumentFontAnalysis:
    """Results of analyzing fonts in a document."""
    font_frequencies: List[Tuple[str, int]]
    font_styles: Dict[str, FontMetrics]

    def is_empty(self) -> bool:
        """Check if analysis found any fonts."""
        return len(self.font_frequencies) == 0


def extract_font_metrics_from_span(span: Dict, include_granular_details: bool = False) -> FontMetrics:
    """Extract font metrics from a PyMuPDF span object."""
    return FontMetrics(
        size=span['size'],
        font=span['font'],
        flags=span.get('flags', 0) if include_granular_details else 0,
        color=span.get('color', 0) if include_granular_details else 0
    )


def analyze_document_fonts(doc: fitz.Document, include_granular_details: bool = False) -> DocumentFontAnalysis:
    """Extract and analyze fonts used throughout a document."""
    font_styles: Dict[str, FontMetrics] = {}
    font_count_map: Dict[str, int] = {}

    for page in doc:
        try:
            blocks = page.get_text("dict")["blocks"]
        except Exception:
            continue

        for block in blocks:
            if block['type'] != TEXT_BLOCK_TYPE:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    metrics = extract_font_metrics_from_span(span, include_granular_details)
                    identifier = metrics.create_identifier(include_granular_details)

                    font_styles[identifier] = metrics
                    font_count_map[identifier] = font_count_map.get(identifier, 0) + 1

    sorted_frequencies = sorted(font_count_map.items(), key=itemgetter(1), reverse=True)

    return DocumentFontAnalysis(
        font_frequencies=sorted_frequencies,
        font_styles=font_styles
    )


@dataclass
class FontSizeTagMapping:
    """Maps font sizes to Markdown tags."""
    size_to_tag: Dict[float, str]

    @staticmethod
    def build_from_fonts(font_frequencies: List[Tuple[str, int]], 
                        font_styles: Dict[str, FontMetrics]) -> "FontSizeTagMapping":
        """Build font-to-tag mapping from font analysis."""
        if not font_frequencies:
            return FontSizeTagMapping(size_to_tag={})

        paragraph_size = _extract_paragraph_size(font_frequencies, font_styles)
        font_sizes = _extract_unique_font_sizes(font_frequencies)
        
        size_to_tag = {}
        header_level = 0
        
        for size in font_sizes:
            tag = _determine_tag_for_size(size, paragraph_size, header_level, font_styles)
            size_to_tag[size] = tag
            
            if tag.startswith('<h'):
                header_level += 1
        
        return FontSizeTagMapping(size_to_tag=size_to_tag)


def _extract_paragraph_size(font_frequencies: List[Tuple[str, int]], 
                            font_styles: Dict[str, FontMetrics]) -> float:
    """Extract the most frequently used font size (paragraph size)."""
    most_used_identifier = font_frequencies[0][0]
    return font_styles[most_used_identifier].size


def _extract_unique_font_sizes(font_frequencies: List[Tuple[str, int]]) -> List[float]:
    """Extract and sort unique font sizes in descending order."""
    font_sizes = [float(identifier) for identifier, _ in font_frequencies]
    font_sizes_unique = list(set(font_sizes))
    font_sizes_unique.sort(reverse=True)
    return font_sizes_unique


def _determine_tag_for_size(size: float, paragraph_size: float, 
                            header_level: int, font_styles: Dict[str, FontMetrics]) -> str:
    """Determine Markdown tag for a given font size."""
    identifier = str(size)
    if identifier not in font_styles:
        return MARKDOWN_PARAGRAPH_TAG
    
    font_style = font_styles[identifier]
    if font_style.size == paragraph_size:
        return MARKDOWN_PARAGRAPH_TAG
    elif font_style.size > paragraph_size:
        return f"<h{header_level + 1}>"
    else:
        return MARKDOWN_SMALL_TAG


@dataclass
class PageMargins:
    """Configuration for header/footer margins used in document processing."""
    header: int = PDF_HEADER_MARGIN
    footer: int = PDF_FOOTER_MARGIN


@dataclass
class TextSpan:
    """Represents extracted text with its formatting tag."""
    tag: str
    content: str


class DocumentProcessor:
    """Processes documents and extracts structured text content."""
    
    CODE_FONT_KEYWORDS = ("mono", "courier", "code", "consolas")
    MAX_HEADER_LEVEL = 4
    
    @staticmethod
    def should_skip_margin_filtering(document: fitz.Document) -> bool:
        """Check if margin filtering should be disabled based on file type."""
        return not document.name.lower().endswith(".pdf")
    
    @staticmethod
    def is_code_font(font_name: str) -> bool:
        """Check if font indicates code block."""
        font_lower = font_name.lower()
        return any(keyword in font_lower for keyword in DocumentProcessor.CODE_FONT_KEYWORDS)
    
    @staticmethod
    def get_margins_for_document(document: fitz.Document) -> PageMargins:
        """Get appropriate margins based on document type."""
        if DocumentProcessor.should_skip_margin_filtering(document):
            return PageMargins(header=0, footer=0)
        return PageMargins()
    
    @staticmethod
    def extract_text_with_tags(document: fitz.Document, size_tag: Dict[float, str]) -> List[TextSpan]:
        """Extract text blocks with corresponding Markdown tags."""
        text_spans = []
        margins = DocumentProcessor.get_margins_for_document(document)
        first_span = True
        previous_span = {}
        current_block_tag = ""
        current_block_content = ""
        
        for page in document:
            try:
                blocks = page.get_text("dict")["blocks"]
            except Exception:
                continue
            
            page_height = page.rect.height
            
            for block in blocks:
                if block['type'] != TEXT_BLOCK_TYPE:
                    continue
                
                # Skip headers and footers in PDFs
                if not DocumentProcessor.should_skip_margin_filtering(document):
                    bbox = block["bbox"]
                    if bbox[1] < margins.header or bbox[3] > (page_height - margins.footer):
                        continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        span_tag = DocumentProcessor._get_span_tag(span, size_tag)
                        
                        if first_span:
                            previous_span = span
                            first_span = False
                            current_block_tag = span_tag
                            current_block_content = span["text"]
                        else:
                            if span_tag == current_block_tag:
                                current_block_content = DocumentProcessor._append_to_block(
                                    current_block_content, span, previous_span
                                )
                            else:
                                if current_block_content.strip():
                                    text_spans.append(TextSpan(
                                        tag=current_block_tag,
                                        content=current_block_content
                                    ))
                                current_block_content = span["text"]
                                current_block_tag = span_tag
                        
                        previous_span = span
                
                if current_block_content.strip():
                    text_spans.append(TextSpan(
                        tag=current_block_tag,
                        content=current_block_content
                    ))
                    current_block_content = ""
        
        return text_spans
    
    @staticmethod
    def _get_span_tag(span: Dict, size_tag: Dict[float, str]) -> str:
        """Determine tag for a span based on font and size."""
        if DocumentProcessor.is_code_font(span['font']):
            return MARKDOWN_CODE_TAG
        
        return size_tag.get(span['size'], MARKDOWN_PARAGRAPH_TAG)
    
    @staticmethod
    def _append_to_block(current_content: str, current_span: Dict, previous_span: Dict) -> str:
        """Append span text to block content, handling spacing."""
        text = current_span['text']
        
        if text != " ":
            if previous_span['font'] == current_span['font']:
                return current_content + (" " + text if text else "")
            return current_content + " " + text
        
        return current_content


def format_markdown(text_spans: List[TextSpan]) -> str:
    """Convert tagged content to clean Markdown."""
    markdown_output = ""
    in_code_block = False

    for text_span in text_spans:
        content = text_span.content.strip()
        if not content:
            continue
        
        # Clean up excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        if MARKDOWN_CODE_TAG in text_span.tag:
            markdown_output = _append_code_block(markdown_output, content, in_code_block)
            in_code_block = True
        else:
            if in_code_block:
                markdown_output += "```\n\n"
                in_code_block = False

            markdown_output = _append_formatted_content(markdown_output, text_span.tag, content)
    
    if in_code_block:
        markdown_output += "```\n"

    return markdown_output


def _append_code_block(output: str, content: str, in_code_block: bool) -> str:
    """Append content to code block, opening if needed."""
    if not in_code_block:
        output += "\n```\n"
    output += f"{content}\n"
    return output


def _append_formatted_content(output: str, tag: str, content: str) -> str:
    """Append formatted content based on tag type."""
    if "<h" in tag:
        return _append_header(output, tag, content)
    elif MARKDOWN_SMALL_TAG in tag:
        return output + f"*{content}*\n\n"
    else:
        return output + f"{content}\n\n"


def _append_header(output: str, tag: str, content: str) -> str:
    """Append header content with appropriate Markdown level."""
    try:
        level = int(re.findall(r'\d+', tag)[0])
        # Cap header level at MAX_HEADER_LEVEL
        level = min(level, DocumentProcessor.MAX_HEADER_LEVEL)
        prefix = "#" * level
        output += f"\n{prefix} {content}\n\n"
    except IndexError:
        output += f"{content}\n\n"
    
    return output


def convert_document_to_markdown(file_path: str, output_path: str) -> None:
    """Convert a document to Markdown format."""
    print(f"Processing {file_path}...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    try:
        document = fitz.open(file_path)
        font_analysis = analyze_document_fonts(document, include_granular_details=False)
        
        if font_analysis.is_empty():
            raise ValueError("No text found. This document might be scanned (images only).")

        size_tag_mapping = FontSizeTagMapping.build_from_fonts(
            font_analysis.font_frequencies,
            font_analysis.font_styles
        )
        text_spans = DocumentProcessor.extract_text_with_tags(
            document,
            size_tag_mapping.size_to_tag
        )
        markdown_content = format_markdown(text_spans)
        
        _write_markdown_file(output_path, markdown_content)
        print(f"Success! Markdown saved to: {output_path}")
        
    except FileNotFoundError:
        raise
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        import traceback
        print(f"Error processing file: {e}")
        traceback.print_exc()


def _write_markdown_file(output_path: str, content: str) -> None:
    """Write Markdown content to a file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python book_to_md.py <input_file> [output.md]")
        print("Supported formats: PDF, EPUB, MOBI, FB2, XPS")
    else:
        input_file = sys.argv[1]
        output_md = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_FILENAME
        convert_document_to_markdown(input_file, output_md)