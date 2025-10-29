"""
Content Summarization Module
Uses Google Gemini API to extract key points and create slide content from PDF text
"""

from google import genai
from google.genai import types
from typing import List, Dict, Optional
import json
from tqdm import tqdm


# Multiple API keys for fallback
API_KEYS = [
    "AIzaSyBN1AzldxCLFOJVJKAh-jqnTq8FeOgC1fk",
    "AIzaSyC40W_Joan3PQN1_jmcskHS2OOnSnBWqwQ",
    "AIzaSyAQ10Q9N5XFS5TyQj4YlOEXWwQN31f-aRM",
    "AIzaSyAwOhd3Ve0gglbFMjuyttuwvPF3KuV5Zss",
    "AIzaSyCqz5vIB3gc3PXgk_12Cou6KSHT4jDkam4"
]


class ContentSummarizer:
    """Summarize PDF content and extract key points for slides using Google Gemini"""
    
    def __init__(self, api_keys: List[str] = API_KEYS, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize the summarizer with Google Gemini API (supports multiple keys for fallback)
        
        Args:
            api_keys: List of Google AI API keys (will try each one if previous fails)
            model: Gemini model to use (gemini-2.0-flash-exp, gemini-1.5-flash, etc.)
        """
        self.api_keys = api_keys if isinstance(api_keys, list) else [api_keys]
        self.model_name = model
        self.current_key_index = 0
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize client with first available API key"""
        if self.current_key_index < len(self.api_keys):
            self.client = genai.Client(api_key=self.api_keys[self.current_key_index])
    
    def _try_next_key(self):
        """Switch to next API key if available"""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            print(f"Switching to backup API key #{self.current_key_index + 1}...")
            self._init_client()
            return True
        return False
    
    def _call_gemini(self, prompt: str, temperature: float = 0.3, max_tokens: int = 4000) -> str:
        """
        Call Gemini API with automatic key fallback
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature
            max_tokens: Maximum output tokens
            
        Returns:
            Response text from Gemini
        """
        last_error = None
        
        # Try each API key
        for attempt in range(len(self.api_keys)):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    )
                )
                return response.text
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if it's a rate limit or quota error
                if any(term in error_msg for term in ['rate', 'quota', 'limit', 'resource_exhausted']):
                    print(f"API key #{self.current_key_index + 1} hit rate limit")
                    if not self._try_next_key():
                        break
                else:
                    # Other error, raise it
                    raise e
        
        # All keys failed
        raise Exception(f"All API keys failed. Last error: {last_error}")
        
    def extract_key_points(self, text: str, num_points: int = 8, max_slides: int = 12) -> List[Dict[str, str]]:
        """
        Extract key points from text and structure them for slides
        
        Args:
            text: Input text from PDF
            num_points: Target number of key points (6-12 for slides)
            max_slides: Maximum number of slides to generate
            
        Returns:
            List of dictionaries with slide content:
            [
                {
                    'title': 'Slide Title',
                    'bullets': ['Bullet 1', 'Bullet 2'],
                    'speaker_notes': 'Notes for narration'
                },
                ...
            ]
        """
        # Adjust num_points to be within max_slides
        num_points = min(num_points, max_slides)
        
        prompt = f"""You are an expert at creating educational slide presentations from technical documents.

Analyze the following text and extract the {num_points} most important key points or topics.

For each key point, create a slide with:
1. A concise title (6-15 words)
2. 2-3 bullet points that explain the concept (each bullet 8-20 words)
3. Speaker notes (1-2 sentences for narration)

IMPORTANT RULES:
- ALWAYS use full forms instead of abbreviations (e.g., "Machine Learning" not "ML", "Data Science" not "DS", "Artificial Intelligence" not "AI")
- Expand ALL acronyms and abbreviations in titles, bullets, and speaker notes
- Make content accessible to general audience by avoiding jargon

Format your response as a JSON array of objects with this structure:
[
    {{
        "title": "Slide title here",
        "bullets": ["First bullet point", "Second bullet point", "Third bullet point"],
        "speaker_notes": "One or two sentences explaining this concept for voice narration."
    }},
    ...
]

Focus on:
- Main concepts and ideas
- Important insights or lessons
- Key takeaways
- Actionable information

Make slides educational, clear, and engaging.

TEXT TO ANALYZE:
{text}

Respond ONLY with the JSON array, no additional text."""

        try:
            # Call Gemini with fallback support
            result_text = self._call_gemini(prompt, temperature=0.3, max_tokens=4000).strip()
            
            # Remove markdown code blocks if present
            if result_text.startswith("```"):
                # Remove ```json or ``` at start and ``` at end
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            
            # Parse JSON
            slides = json.loads(result_text)
            
            # Validate structure
            validated_slides = []
            for slide in slides:
                if 'title' in slide and 'bullets' in slide and 'speaker_notes' in slide:
                    validated_slides.append({
                        'title': slide['title'],
                        'bullets': slide['bullets'][:3],  # Max 3 bullets
                        'speaker_notes': slide['speaker_notes']
                    })
            
            return validated_slides[:max_slides]
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response was: {result_text[:500]}") 
            return self._fallback_extraction(text, num_points)
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._fallback_extraction(text, num_points)
    
    def _fallback_extraction(self, text: str, num_points: int) -> List[Dict[str, str]]:
        """
        Fallback method if API fails - simple text splitting
        
        Args:
            text: Input text
            num_points: Number of sections to create
            
        Returns:
            Basic slide structure
        """
        # Split text into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        slides = []
        paragraphs_per_slide = max(1, len(paragraphs) // num_points)
        
        for i in range(0, len(paragraphs), paragraphs_per_slide):
            chunk = paragraphs[i:i+paragraphs_per_slide]
            if not chunk:
                continue
                
            # Create basic slide
            slides.append({
                'title': f"Key Point {len(slides) + 1}",
                'bullets': chunk[:3],
                'speaker_notes': ' '.join(chunk)[:200]
            })
            
            if len(slides) >= num_points:
                break
        
        return slides
    
    def generate_title_slide(self, text: str, filename: str = "") -> Dict[str, str]:
        """
        Generate a title slide from the document
        
        Args:
            text: Document text
            filename: Original filename
            
        Returns:
            Title slide content
        """
        prompt = f"""Based on the following document text, create a compelling title slide.

Provide:
1. A main title (5-12 words)
2. A subtitle or tagline (8-15 words)

IMPORTANT: Use full forms instead of abbreviations (e.g., "Machine Learning" not "ML", "Data Science" not "DS").

Format as JSON:
{{
    "title": "Main Title Here",
    "subtitle": "Subtitle or tagline here"
}}

Document text (first 1000 chars):
{text[:1000]}

Respond ONLY with the JSON object."""

        try:
            # Call Gemini with fallback support
            result_text = self._call_gemini(prompt, temperature=0.4, max_tokens=200).strip()
            if result_text.startswith("```"):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            
            title_data = json.loads(result_text)
            return title_data
            
        except Exception as e:
            print(f"Error generating title: {e}")
            return {
                "title": filename.replace('_', ' ').replace('.pdf', ''),
                "subtitle": "Key Insights and Learnings"
            }
    
    def summarize_for_video(self, slides: List[Dict[str, str]]) -> str:
        """
        Create a cohesive narration script for the entire video
        
        Args:
            slides: List of slide content
            
        Returns:
            Complete narration script
        """
        script_parts = []
        
        for i, slide in enumerate(slides, 1):
            # Use speaker notes if available, otherwise synthesize from title and bullets
            if slide.get('speaker_notes'):
                script_parts.append(slide['speaker_notes'])
            else:
                text = f"{slide['title']}. {' '.join(slide.get('bullets', []))}"
                script_parts.append(text)
        
        return ' '.join(script_parts)


def extract_slides_from_pdf_text(pdf_text: str, num_slides: int = 8, api_keys: List[str] = API_KEYS) -> Dict:
    """
    Convenience function to extract slides from PDF text
    
    Args:
        pdf_text: Extracted text from PDF
        num_slides: Target number of slides
        api_keys: List of Google AI API keys (will try each one if previous fails)
        
    Returns:
        Dictionary with title slide and content slides
    """
    summarizer = ContentSummarizer(api_keys=api_keys)
    
    print(f"\nGenerating slide content with Google Gemini...")
    
    # Generate title slide
    title_slide = summarizer.generate_title_slide(pdf_text)
    
    # Extract key points as slides
    content_slides = summarizer.extract_key_points(pdf_text, num_points=num_slides)
    
    return {
        'title_slide': title_slide,
        'content_slides': content_slides,
        'total_slides': len(content_slides) + 1,
        'narration_script': summarizer.summarize_for_video(content_slides)
    }


if __name__ == "__main__":
    # Example usage
    import sys
    from pathlib import Path
    
    # Read fixed filename from intermediate folder
    intermediate_dir = Path("output/intermediate")
    text_file = intermediate_dir / "extracted_text.txt"
    
    if not text_file.exists():
        print(f"Error: {text_file} not found")
        print(f"Please run pdf_parser.py first to extract text from a PDF")
        sys.exit(1)
    
    print(f"Processing: {text_file}")
    
    # Use built-in API keys
    print(f"Using {len(API_KEYS)} API keys with automatic fallback")
    
    # Read text file
    with open(text_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    print(f"Processing: {text_file}")
    print(f"Text length: {len(text)} characters\n")
    
    # Extract slides
    result = extract_slides_from_pdf_text(text, num_slides=8)
    
    print(f"\nGenerated {result['total_slides']} slides")
    print(f"\nTitle Slide:")
    print(f"   Title: {result['title_slide']['title']}")
    print(f"   Subtitle: {result['title_slide']['subtitle']}")
    
    print(f"\nContent Slides:")
    for i, slide in enumerate(result['content_slides'], 1):
        print(f"\n   Slide {i}: {slide['title']}")
        for bullet in slide['bullets']:
            print(f"      - {bullet}")
    
    # Save results to intermediate folder with fixed name
    intermediate_dir = Path("output/intermediate")
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = intermediate_dir / "slides.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved slide content to: {output_file}")