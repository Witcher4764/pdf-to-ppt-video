"""
PDF Slide Creator Module
Generates PDF presentations directly with full design (colors, icons, layouts)
This bypasses PPTX and creates beautiful PDFs that can be easily converted to images
"""

from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from pathlib import Path
import json
from typing import Dict, List
from PIL import Image


class PDFSlideCreator:
    """Create professional PDF presentations with vibrant design"""
    
    def __init__(self, slides_json_path: str = "output/intermediate/slides.json",
                 icons_dir: str = "output/intermediate/images"):
        """
        Initialize PDF slide creator
        
        Args:
            slides_json_path: Path to slides JSON file
            icons_dir: Directory containing icon images
        """
        self.slides_json_path = Path(slides_json_path)
        self.icons_dir = Path(icons_dir)
        
        if not self.slides_json_path.exists():
            raise FileNotFoundError(f"Slides JSON not found: {slides_json_path}")
        
        # Load slides data
        with open(self.slides_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Slide dimensions (landscape, 10" x 7.5")
        self.width = 720  # 10 inches * 72 dpi
        self.height = 540  # 7.5 inches * 72 dpi
        
        # Color scheme (vibrant modern theme) - RGB tuples for reportlab
        self.colors = {
            'primary': (41/255, 98/255, 255/255),      # Electric blue
            'secondary': (16/255, 185/255, 129/255),   # Emerald green
            'accent': (251/255, 146/255, 60/255),      # Warm orange
            'purple': (139/255, 92/255, 246/255),      # Purple
            'pink': (236/255, 72/255, 153/255),        # Pink
            'bg_light': (248/255, 250/255, 252/255),   # Light gray bg
            'text': (15/255, 23/255, 42/255),          # Almost black
            'light_text': (100/255, 116/255, 139/255), # Slate gray
            'white': (1, 1, 1)
        }
    
    def create_presentation(self, output_path: str = "output/slides.pdf") -> str:
        """
        Create complete PDF presentation
        
        Args:
            output_path: Path to save the PDF file
            
        Returns:
            Path to created presentation
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nCreating PDF presentation...")
        print(f"Output: {output_path}\n")
        
        # Create PDF canvas
        c = canvas.Canvas(str(output_path), pagesize=(self.width, self.height))
        
        # Title slide
        print("Creating title slide...")
        self._create_title_slide(c)
        c.showPage()
        
        # Content slides
        for i, slide_data in enumerate(self.data['content_slides'], 1):
            print(f"Creating slide {i}: {slide_data['title'][:40]}...")
            self._create_content_slide(c, slide_data, i)
            c.showPage()
        
        # Save PDF
        c.save()
        print(f"\nPresentation created: {output_path}")
        print(f"Total slides: {1 + len(self.data['content_slides'])}")
        
        return str(output_path)
    
    def _create_title_slide(self, c: canvas.Canvas):
        """Create vibrant title slide with gradient effect"""
        title_data = self.data['title_slide']
        
        # Top gradient (primary color)
        c.setFillColorRGB(*self.colors['primary'])
        c.rect(0, self.height - 288, self.width, 288, fill=1, stroke=0)
        
        # Bottom gradient (secondary color)
        c.setFillColorRGB(*self.colors['secondary'])
        c.rect(0, 0, self.width, self.height - 288, fill=1, stroke=0)
        
        # Decorative accent circle (top right) - semi-transparent
        c.setFillColorRGB(*self.colors['accent'], alpha=0.3)
        c.circle(self.width - 72, self.height + 72, 144, fill=1, stroke=0)
        
        # Decorative accent circle (bottom left)
        c.setFillColorRGB(*self.colors['purple'], alpha=0.3)
        c.circle(-72, 0, 126, fill=1, stroke=0)
        
        # Icon (centered at top)
        icon_path = self.icons_dir / "title.png"
        if icon_path.exists():
            try:
                img = ImageReader(str(icon_path))
                c.drawImage(img, (self.width - 144) / 2, self.height - 230, 
                           width=144, height=144, preserveAspectRatio=True, mask='auto')
            except:
                pass
        
        # Title (reduced font size for better spacing)
        c.setFillColorRGB(*self.colors['white'])
        c.setFont("Helvetica-Bold", 38)
        
        # Wrap title text
        title = title_data['title']
        words = title.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if c.stringWidth(test_line, "Helvetica-Bold", 38) < self.width - 120:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Center and draw title lines (much better spacing between lines)
        # Start from higher position for better layout
        title_start_y = 290
        line_spacing = 48  # Increased line spacing
        
        y = title_start_y
        for line in lines:
            text_width = c.stringWidth(line, "Helvetica-Bold", 38)
            c.drawString((self.width - text_width) / 2, y, line)
            y -= line_spacing
        
        # Subtitle (smaller font with better spacing)
        c.setFont("Helvetica-Bold", 22)
        subtitle = title_data['subtitle']
        
        # Wrap subtitle
        words = subtitle.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if c.stringWidth(test_line, "Helvetica-Bold", 22) < self.width - 160:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Center and draw subtitle (big gap from title - 60px)
        # Position subtitle well below title
        subtitle_start_y = y - 60  # 60px gap from last title line
        subtitle_line_spacing = 30
        
        y = subtitle_start_y
        for line in lines:
            text_width = c.stringWidth(line, "Helvetica-Bold", 22)
            c.drawString((self.width - text_width) / 2, y, line)
            y -= subtitle_line_spacing
    
    def _create_content_slide(self, c: canvas.Canvas, slide_data: Dict, slide_num: int):
        """Create vibrant content slide with modern design"""
        # Alternate colors for variety
        color_options = [self.colors['primary'], self.colors['secondary'],
                        self.colors['purple'], self.colors['pink']]
        slide_color = color_options[slide_num % len(color_options)]
        
        # Light background
        c.setFillColorRGB(*self.colors['bg_light'])
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        
        # Decorative side bar (left accent)
        c.setFillColorRGB(*slide_color)
        c.rect(0, 0, 29, self.height, fill=1, stroke=0)
        
        # Icon with background rectangle (matching PPTX design)
        icon_path = self.icons_dir / f"slide_{slide_num:02d}.png"
        if icon_path.exists():
            # Icon background rectangle (white with colored border)
            icon_bg_x = 50
            icon_bg_y = self.height - 295
            icon_bg_size = 173  # 2.4 inches * 72 dpi
            
            c.setFillColorRGB(*self.colors['white'])
            c.setStrokeColorRGB(*slide_color)
            c.setLineWidth(3)
            c.rect(icon_bg_x, icon_bg_y, icon_bg_size, icon_bg_size, fill=1, stroke=1)
            
            # Draw icon (centered in rectangle)
            try:
                img = ImageReader(str(icon_path))
                icon_size = 130  # 1.8 inches * 72 dpi
                icon_x = icon_bg_x + (icon_bg_size - icon_size) / 2
                icon_y = icon_bg_y + (icon_bg_size - icon_size) / 2
                c.drawImage(img, icon_x, icon_y,
                           width=icon_size, height=icon_size, preserveAspectRatio=True, mask='auto')
            except:
                pass
        
        # Title with colored background (increased height for better text fit)
        title_x = 252
        title_y = self.height - 90
        title_width = 432
        title_height = 100
        
        c.setFillColorRGB(*slide_color)
        c.rect(title_x - 14, title_y - 7, title_width + 29, title_height + 14, fill=1, stroke=0)
        
        # Title text (reduced font size to prevent cutoff)
        c.setFillColorRGB(*self.colors['white'])
        c.setFont("Helvetica-Bold", 24)
        
        # Wrap title
        title = slide_data['title']
        words = title.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if c.stringWidth(test_line, "Helvetica-Bold", 24) < title_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        # Draw title lines (adjusted spacing)
        y = title_y + 60
        for line in lines[:3]:  # Allow up to 3 lines
            c.drawString(title_x, y, line)
            y -= 30
        
        # Content background (white card)
        content_x = 230
        content_y = 80
        content_width = 454
        content_height = 302
        
        c.setFillColorRGB(*self.colors['white'])
        c.setStrokeColorRGB(226/255, 232/255, 240/255)
        c.setLineWidth(2)
        c.rect(content_x, content_y, content_width, content_height, fill=1, stroke=1)
        
        # Bullets with proper text wrapping
        c.setFillColorRGB(*self.colors['text'])
        c.setFont("Helvetica", 18)
        
        bullet_symbols = ['-']
        y = content_y + content_height - 40
        x = content_x + 20
        max_text_width = content_width - 40  # Leave margins
        
        for i, bullet in enumerate(slide_data['bullets']):
            if y < content_y + 20:
                break  # Prevent overflow
            
            # Wrap bullet text
            full_text = f"- {bullet}"
            
            # Split into words and wrap
            words = full_text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                if c.stringWidth(test_line, "Helvetica", 18) < max_text_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Draw wrapped lines
            for line in lines:
                if y < content_y + 20:
                    break
                c.drawString(x, y, line)
                y -= 25
            
            y -= 15  # Extra space between bullets
        
        # Decorative corner element (bottom right) - semi-transparent
        c.setFillColorRGB(*slide_color, alpha=0.2)
        c.rect(612, 0, 144, 108, fill=1, stroke=0)
    
    def _wrap_text(self, text: str, max_width: int, font: str, size: int, c: canvas.Canvas) -> List[str]:
        """Helper to wrap text to fit within width"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if c.stringWidth(test_line, font, size) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines


def create_pdf_slides(slides_json_path: str = "output/intermediate/slides.json",
                      icons_dir: str = "output/intermediate/images",
                      output_path: str = "output/slides.pdf") -> str:
    """
    Create PDF presentation from slides JSON and icons
    
    Args:
        slides_json_path: Path to slides JSON file
        icons_dir: Directory containing icon images
        output_path: Path to save the PDF file
        
    Returns:
        Path to created presentation
    """
    creator = PDFSlideCreator(slides_json_path, icons_dir)
    return creator.create_presentation(output_path)


if __name__ == "__main__":
    import sys
    
    try:
        # Create PDF slides
        output_path = create_pdf_slides()
        
        print(f"\nSuccess! Open the presentation:")
        print(f"   {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
