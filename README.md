# Infooware Edu Prototype

**PDF to Slides & Animated Video Pipeline**

Automatically convert educational PDF documents into professional slide decks and animated explainer videos with AI-powered content summarization and text-to-speech narration.

---

## Overview

This project transforms PDF documents into:
1. **PowerPoint Presentation** (`.pptx`) - Vibrant slides with professional icons
2. **PDF Slides** (`.pdf`) - Beautiful PDF version for universal compatibility
3. **Animated Video** (`.mp4`) - Engaging explainer video with TTS narration

### Key Features

- AI-Powered Summarization - Google Gemini extracts key points automatically
- Professional Icons - Auto-generated from The Noun Project API
- Text-to-Speech - Natural narration using Google TTS
- Automated Video - Smooth transitions and animations
- One Command - Complete pipeline from PDF to video
- Smart Detection - Auto-processes PDFs from input folder

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Tesseract OCR (for scanned PDFs)
- Poppler (for PDF to image conversion)
- FFmpeg (for video generation)

### System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils ffmpeg
```

**macOS:**
```bash
brew install tesseract poppler ffmpeg
```

**Windows:**
- Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases/
- Download FFmpeg: https://ffmpeg.org/download.html

### Python Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd infow

# Install Python packages
pip install -r requirements.txt
```

---

## Quick Start

### Simple Usage

Just place your PDF in the `input/` folder and run:

```bash
python run_pipeline.py
```

The pipeline will automatically:
1. Detect the PDF in `input/` folder
2. Extract and summarize content
3. Generate slides and video
4. Save everything to `output/` folder

### Custom Usage

```bash
# Specify input PDF and output directory
python run_pipeline.py --input path/to/document.pdf --outdir results/

# Process specific PDF from input folder
python run_pipeline.py --input input/my-document.pdf
```

---

## Project Structure

```
infow/
├── run_pipeline.py          # Main CLI script
├── requirements.txt         # Python dependencies
├── README.md               # This file
│
├── input/                  # Place your PDF files here
│   └── *.pdf
│
├── output/                 # Generated outputs
│   ├── slides.pptx        # PowerPoint presentation
│   ├── slides.pdf         # PDF slides
│   ├── video.mp4          # Animated video
│   └── intermediate/      # Intermediate files
│       ├── extracted_text.txt
│       ├── slides.json
│       ├── images/        # Downloaded icons
│       ├── slide_images/  # Slide PNG images
│       └── audio/         # TTS audio files
│
├── sample pdfs/            # Example PDFs for testing
│   └── *.pdf
│
└── src/                    # Source code modules
    ├── pdf_parser.py      # PDF text extraction
    ├── summarizer.py      # AI content summarization
    ├── image_generator.py # Icon generation
    ├── slide_creator.py   # PowerPoint generation
    ├── pdf_slide_creator.py # PDF slides generation
    └── video_creator.py   # Video assembly
```

---

## API Configuration

### Required API Keys

1. **Google Gemini API** (for AI summarization)
   - Get your key: https://makersuite.google.com/app/apikey
   - Already configured in `src/summarizer.py` with fallback keys

2. **The Noun Project API** (for professional icons)
   - Get your key: https://thenounproject.com/developers/
   - Already configured in `src/image_generator.py`

> **Note:** The project includes fallback API keys for testing. For production use, replace with your own keys.

---

## Pipeline Steps

The complete pipeline consists of 6 automated steps:

### 1. PDF Text Extraction
- Intelligently detects digital vs scanned content
- Auto-applies OCR when needed
- Preserves document structure

### 2. AI Content Summarization
- Uses Google Gemini to extract key points
- Generates 6-12 slides automatically
- Creates slide titles, bullets, and speaker notes
- **Expands all abbreviations** (ML → Machine Learning)

### 3. Icon Generation
- Generates search queries using AI
- Downloads professional icons from The Noun Project
- Smart fallback for failed searches
- Creates consistent visual style

### 4. PowerPoint Generation
- Creates vibrant, professional PPTX
- Modern color scheme with gradients
- Properly formatted text and bullets
- Embedded speaker notes

### 5. PDF Slides Generation
- Generates identical PDF version
- Cross-platform compatible
- Optimized for video conversion

### 6. Video Generation
- Converts slides to images (100 DPI)
- Generates TTS narration for content slides only (title slide is silent)
- Assembles video with fade transitions
- **Silent title slide** (3 seconds display time)
- **10 FPS, fast encoding** for quick generation
- Outputs MP4 video (~2 minutes typical)

---

## Customization

### Video Settings

Edit `src/video_creator.py`:

```python
# Video quality
self.fps = 10              # Frames per second (10 = fast, 15 = smooth)
self.resolution = (1280, 720)  # 720p HD

# Image quality
dpi = 100                  # DPI for slide images (100 = fast, 150 = high quality)

# Encoding
preset = 'fast'            # 'ultrafast', 'fast', 'medium', 'slow'

# Title slide duration
title_duration = 3.0       # Seconds
```

### Slide Count

Edit `run_pipeline.py`:

```python
# Generate 6-12 slides
slides_data = extract_slides_from_pdf_text(text, num_slides=8)
```

---

## Output Examples

### Generated Files

After running the pipeline, you'll get:

- `output/slides.pptx` - Full PowerPoint presentation
- `output/slides.pdf` - PDF version with all design elements
- `output/video.mp4` - Animated video with narration

### Video Specifications

- **Resolution:** 1280×720 (720p HD)
- **Frame Rate:** 10 FPS
- **Codec:** H.264 (MP4)
- **Audio:** AAC, TTS narration
- **Duration:** Typically 1.5-2.5 minutes per 8-slide deck

---

## Troubleshooting

### Common Issues

**1. "No PDF files found in input/"**
- Make sure you have a `.pdf` file in the `input/` directory
- Check file extension is lowercase `.pdf`

**2. "Tesseract not found"**
```bash
# Install Tesseract
sudo apt install tesseract-ocr  # Ubuntu/Debian
brew install tesseract          # macOS
```

**3. "Poppler not found"**
```bash
# Install Poppler
sudo apt install poppler-utils  # Ubuntu/Debian
brew install poppler            # macOS
```

**4. API Rate Limits**
- The project includes 5 fallback Gemini API keys
- If all keys are exhausted, wait 1 minute and retry
- For heavy use, add your own API keys

**5. Video Generation Fails**
```bash
# Make sure FFmpeg is installed
ffmpeg -version

# Install if missing
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg      # macOS
```

---

## Advanced Usage

### Individual Module Testing

```bash
# Test PDF parsing
python src/pdf_parser.py

# Test summarization
python src/summarizer.py

# Test icon generation
python src/image_generator.py

# Test slide generation
python src/pdf_slide_creator.py

# Test video creation
python src/video_creator.py
```

### Using Existing Intermediate Files

The pipeline smartly reuses existing files:
- If `output/intermediate/extracted_text.txt` exists, skips PDF parsing
- If `output/intermediate/slides.json` exists, skips AI summarization
- If `output/intermediate/images/` exists, skips icon downloads
- If `output/intermediate/audio/` exists, skips TTS generation

This makes iterative development much faster!

---

## Performance

### Typical Execution Times

- **PDF Parsing:** 5-10 seconds (10-page document)
- **AI Summarization:** 10-15 seconds
- **Icon Generation:** 15-20 seconds (9 icons)
- **Slide Creation:** 5 seconds (PPTX + PDF)
- **Video Generation:** 30-60 seconds

**Total:** ~1.5-2 minutes for complete pipeline

### Optimization Tips

For faster generation:
- Reduce FPS to 10 (already set)
- Lower DPI to 100 (already set)
- Use 'fast' or 'ultrafast' preset (already 'fast')
- Cache intermediate files (automatic)

---
