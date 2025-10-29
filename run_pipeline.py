#!/usr/bin/env python3
"""
Infooware Edu Prototype - Complete Pipeline
Converts PDF to slides and animated video
"""

import argparse
import sys
from pathlib import Path

# Import pipeline modules
from src.pdf_parser import PDFParser
from src.summarizer import extract_slides_from_pdf_text
from src.image_generator import generate_icons_for_slides
from src.pdf_slide_creator import create_pdf_slides
from src.slide_creator import create_slides
from src.video_creator import create_video_complete


def run_pipeline(input_pdf: str, output_dir: str = "output"):
    """
    Run complete PDF to slides and video pipeline
    
    Args:
        input_pdf: Path to input PDF file
        output_dir: Output directory for all generated files
    """
    input_path = Path(input_pdf)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        print(f"Error: Input PDF not found: {input_pdf}")
        return False
    
    # Create output structure
    intermediate_dir = output_path / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"INFOOWARE EDU PROTOTYPE - PDF TO VIDEO PIPELINE")
    print(f"{'='*60}\n")
    print(f"Input PDF: {input_path}")
    print(f"Output Directory: {output_path}\n")
    
    try:
        # Step 1: Extract text from PDF
        print(f"\n{'─'*60}")
        print("STEP 1: PDF Text Extraction")
        print(f"{'─'*60}")
        
        with PDFParser(str(input_path)) as parser:
            content = parser.extract_structured_content()
            text = content['full_text']
            
            # Save extracted text
            text_file = intermediate_dir / "extracted_text.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"Extracted {len(text)} characters from {content['num_pages']} pages")
        
        # Step 2: Generate slide content with AI
        print(f"\n{'─'*60}")
        print("STEP 2: AI Content Summarization")
        print(f"{'─'*60}")
        
        slides_data = extract_slides_from_pdf_text(text, num_slides=8)
        
        # Save slides JSON
        import json
        slides_file = intermediate_dir / "slides.json"
        with open(slides_file, 'w', encoding='utf-8') as f:
            json.dump(slides_data, f, indent=2, ensure_ascii=False)
        
        print(f"Generated {slides_data['total_slides']} slides")
        
        # Step 3: Generate icons
        print(f"\n{'─'*60}")
        print("STEP 3: Icon Generation")
        print(f"{'─'*60}")
        
        icon_paths = generate_icons_for_slides(
            str(slides_file),
            str(intermediate_dir / "images")
        )
        
        print(f"Generated {len(icon_paths)} icons")
        
        # Step 4: Create PowerPoint presentation
        print(f"\n{'─'*60}")
        print("STEP 4: PowerPoint Generation")
        print(f"{'─'*60}")
        
        pptx_path = create_slides(
            str(slides_file),
            str(intermediate_dir / "images"),
            str(output_path / "slides.pptx")
        )
        
        print(f"Created: {pptx_path}")
        
        # Step 5: Create PDF presentation
        print(f"\n{'─'*60}")
        print("STEP 5: PDF Slides Generation")
        print(f"{'─'*60}")
        
        pdf_path = create_pdf_slides(
            str(slides_file),
            str(intermediate_dir / "images"),
            str(output_path / "slides.pdf")
        )
        
        print(f"Created: {pdf_path}")
        
        # Step 6: Create animated video
        print(f"\n{'─'*60}")
        print("STEP 6: Video Generation")
        print(f"{'─'*60}")
        
        video_path = create_video_complete(
            pdf_path=str(output_path / "slides.pdf"),
            slides_json_path=str(slides_file),
            images_dir=str(intermediate_dir / "slide_images"),
            audio_dir=str(intermediate_dir / "audio"),
            output_path=str(output_path / "video.mp4")
        )
        
        print(f"Created: {video_path}")
        
        # Success summary
        print(f"\n{'='*60}")
        print("PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"{'='*60}\n")
        print("Generated Files:")
        print(f"   Slides (PPTX): {output_path / 'slides.pptx'}")
        print(f"   Slides (PDF):  {output_path / 'slides.pdf'}")
        print(f"   Video (MP4):   {output_path / 'video.mp4'}")
        print(f"\nAll outputs saved to: {output_path}/\n")
        
        return True
        
    except Exception as e:
        print(f"\nError during pipeline execution: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF to slides and animated video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --input sample.pdf
  python run_pipeline.py --input document.pdf --outdir results/
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='input',
        help='Input PDF file path or directory (default: input/)'
    )
    
    parser.add_argument(
        '--outdir',
        type=str,
        default='output',
        help='Output directory (default: output/)'
    )
    
    args = parser.parse_args()
    
    # Auto-detect PDF if input is a directory
    input_path = Path(args.input)
    
    if input_path.is_dir():
        # Find first PDF in directory
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"Error: No PDF files found in {input_path}/")
            sys.exit(1)
        
        pdf_file = pdf_files[0]
        print(f"\nAuto-detected PDF: {pdf_file.name}")
    else:
        pdf_file = input_path
    
    # Run pipeline
    success = run_pipeline(str(pdf_file), args.outdir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()