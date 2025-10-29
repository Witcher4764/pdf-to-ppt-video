"""
PDF Text Extraction Module
Handles digital, scanned, and hybrid PDFs using PyMuPDF and OCR
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm

# Define a character threshold. If a page has less digital text
# than this, it's either scanned pdf (text on images) or has a bad OCR layer.
MIN_DIGITAL_TEXT_THRESHOLD = 100 

class PDFParser:
    """Extract text from digital, scanned, and hybrid PDFs with intelligent per-page detection"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF parser
        
        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path).resolve()
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}\nResolved to: {self.pdf_path}")
        
        self.doc = fitz.open(str(self.pdf_path))
        self.num_pages = len(self.doc)
        self.extraction_stats = {
            'digital_pages': 0,
            'ocr_pages': 0,
            'hybrid_pages': 0
        }
        
    def extract_text_from_page(self, page_num: int) -> str:
        """
        Extract text from a single page using intelligent triage strategy.
        Automatically detects if page needs OCR on a per-page basis.
        
        Args:
            page_num: Page number (0-indexed)
            
        Returns:
            Extracted text from the page
        """
        page = self.doc[page_num]
        
        # 1. Get digital text
        digital_text = page.get_text().strip()
        
        # 2. Check if digital text is "sufficient"
        if len(digital_text) > MIN_DIGITAL_TEXT_THRESHOLD:
            # This page has plenty of digital text. We trust it.
            self.extraction_stats['digital_pages'] += 1
            return digital_text
        
        # 3. Digital text is insufficient. Perform high-quality OCR.
        ocr_text = self._ocr_page(page).strip()
        
        # 4. Return the "best" text.
        #    This handles the "Garbage Text" case.
        if len(ocr_text) > len(digital_text):
            self.extraction_stats['ocr_pages'] += 1
            return ocr_text
        else:
            # Digital text exists but is short (might be page numbers, headers)
            # Keep it if OCR didn't produce more
            self.extraction_stats['hybrid_pages'] += 1
            return digital_text
    
    def _ocr_page(self, page) -> str:
        """
        Perform OCR on a page
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            OCR-extracted text
        """
        # Render page to image at higher resolution for better OCR
        mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        
        # Perform OCR
        text = pytesseract.image_to_string(image)
        return text
    
    def extract_all_text(self, show_progress: bool = True) -> str:
        """
        Extract text from all pages with intelligent per-page OCR detection
        
        Args:
            show_progress: Show progress bar
            
        Returns:
            Combined text from all pages
        """
        all_text = []
        
        iterator = range(self.num_pages)
        if show_progress:
            iterator = tqdm(iterator, desc="Extracting text from PDF")
        
        for page_num in iterator:
            text = self.extract_text_from_page(page_num)
            all_text.append(f"\n--- Page {page_num + 1} ---\n{text}")
        
        return "\n".join(all_text)
    
    def extract_structured_content(self) -> Dict[str, any]:
        """
        Extract structured content with metadata and extraction statistics
        
        Returns:
            Dictionary containing structured content and stats
        """
        # Reset stats
        self.extraction_stats = {
            'digital_pages': 0,
            'ocr_pages': 0,
            'hybrid_pages': 0
        }
        
        content = {
            'filename': self.pdf_path.name,
            'num_pages': self.num_pages,
            'pages': [],
            'full_text': '',
            'metadata': self.doc.metadata,
            'extraction_stats': None  # Will be filled after extraction
        }
        
        for page_num in tqdm(range(self.num_pages), desc="Processing pages"):
            page_text = self.extract_text_from_page(page_num)
            
            content['pages'].append({
                'page_num': page_num + 1,
                'text': page_text,
                'char_count': len(page_text),
                'word_count': len(page_text.split())
            })
        
        content['full_text'] = '\n\n'.join([p['text'] for p in content['pages']])
        content['extraction_stats'] = self.extraction_stats.copy()
        
        return content
    
    def close(self):
        """Close the PDF document"""
        self.doc.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Utility function for quick extraction
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Quick utility to extract text from a PDF with automatic OCR detection
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    with PDFParser(pdf_path) as parser:
        return parser.extract_all_text()


if __name__ == "__main__":
    # Example usage
    import sys
    import glob
    
    # Check if PDF file argument provided
    if len(sys.argv) >= 2:
        pdf_file = sys.argv[1]
    else:
        # Auto-select first PDF from input folder
        input_dir = Path("input")
        pdf_files = list(input_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("No PDF files found in input/ folder")
            print("\nUsage: python pdf_parser.py [pdf_file]")
            print("   or place PDF files in input/ folder")
            sys.exit(1)
        
        pdf_file = str(pdf_files[0])
        print(f"Auto-selected: {pdf_file}")
    
    print(f"\nProcessing: {pdf_file}\n")
    
    with PDFParser(pdf_file) as parser:
        print(f"Total pages: {parser.num_pages}")
        print(f"Using intelligent per-page extraction...\n")
        
        # Extract content (will automatically use OCR where needed)
        content = parser.extract_structured_content()
        
        print(f"\nExtraction complete!")
        print(f"\nExtraction Statistics:")
        print(f"   Digital pages: {content['extraction_stats']['digital_pages']}")
        print(f"   OCR pages: {content['extraction_stats']['ocr_pages']}")
        print(f"   Hybrid pages: {content['extraction_stats']['hybrid_pages']}")
        print(f"\nContent Statistics:")
        print(f"   Total characters: {len(content['full_text'])}")
        print(f"   Total words: {sum(p['word_count'] for p in content['pages'])}")
        
        # Save to intermediate folder with fixed name
        intermediate_dir = Path("output/intermediate")
        intermediate_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = intermediate_dir / "extracted_text.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content['full_text'])
        
        print(f"\nSaved to: {output_file}")