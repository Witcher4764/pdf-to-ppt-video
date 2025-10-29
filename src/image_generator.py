"""
Image/Icon Generation Module
Uses Gemini AI to extract icon search queries and The Noun Project API to download icons
"""

import requests
from requests_oauthlib import OAuth1
from pathlib import Path
import json
from typing import Dict, List
from google import genai
from google.genai import types

# The Noun Project API credentials
NOUN_API_KEY = "5c46ebc492f74cbe9b010314237aa601"
NOUN_API_SECRET = "f3b343ac20bd403a88f1ed75c816a5d4"

# Multiple API keys for fallback
API_KEYS = [
    "AIzaSyBN1AzldxCLFOJVJKAh-jqnTq8FeOgC1fk",
    "AIzaSyC40W_Joan3PQN1_jmcskHS2OOnSnBWqwQ",
    "AIzaSyAQ10Q9N5XFS5TyQj4YlOEXWwQN31f-aRM",
    "AIzaSyAwOhd3Ve0gglbFMjuyttuwvPF3KuV5Zss",
    "AIzaSyCqz5vIB3gc3PXgk_12Cou6KSHT4jDkam4"
]


class IconSearchQueryGenerator:
    """Use Gemini AI to generate optimal icon search queries"""
    
    def __init__(self, api_keys: List[str] = API_KEYS, model: str = "gemini-2.0-flash-exp"):
        self.api_keys = api_keys
        self.model_name = model
        self.current_key_index = 0
        self.client = None
        self._init_client()
    
    def generate_alternative_query(self, slide_title: str, bullets: List[str],
                                   failed_queries: List[str]) -> str:
        """
        Generate alternative icon search query when previous attempts failed
        
        Args:
            slide_title: The slide title
            bullets: List of bullet points
            failed_queries: List of queries that already failed
            
        Returns:
            Alternative icon search query (1-3 words)
        """
        bullets_text = "\n".join([f"- {b}" for b in bullets])
        failed_text = ", ".join([f"'{q}'" for q in failed_queries])
        
        prompt = f"""You are an expert at choosing icons for presentations.

Given this slide content, provide EXACTLY ONE ALTERNATIVE icon search query (1-3 words maximum).

IMPORTANT: Do NOT use any of these queries that already failed: {failed_text}

The query should be:
- Simple and concrete (e.g., "document", "chart", "lightbulb", "network")
- DIFFERENT from the failed queries
- More generic/broader than previous attempts
- Suitable for finding a professional icon

Slide Title: {slide_title}

Bullet Points:
{bullets_text}

Respond with ONLY the search query, nothing else. No quotes, no explanation, just the query."""

        try:
            query = self._call_gemini(prompt, temperature=0.5, max_tokens=20)
            # Clean the response
            query = query.strip().strip('"').strip("'").lower()
            # Take only first 3 words if multiple
            words = query.split()[:3]
            query = " ".join(words)
            
            # Ensure it's not a duplicate
            if query in failed_queries:
                # Extract a different word from title
                return self._extract_alternative_from_title(slide_title, failed_queries)
            
            return query
        except Exception as e:
            print(f"Error generating alternative query: {e}")
            return self._extract_alternative_from_title(slide_title, failed_queries)
    
    def _extract_alternative_from_title(self, title: str, avoid_queries: List[str]) -> str:
        """Extract alternative query from title, avoiding previous attempts"""
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'}
        
        words = title.lower().split()
        candidates = []
        
        for word in words:
            clean_word = word.strip(',:;.!?')
            if clean_word not in stop_words and len(clean_word) > 3:
                candidates.append(clean_word)
        
        # Find first candidate not in failed queries
        for candidate in candidates:
            if candidate not in avoid_queries:
                return candidate
        
        # If all candidates tried, return generic terms
        generic_fallbacks = ["icon", "symbol", "graphic", "element", "concept"]
        for fallback in generic_fallbacks:
            if fallback not in avoid_queries:
                return fallback
        
        return "circle"  # Ultimate fallback
    
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
    
    def _call_gemini(self, prompt: str, temperature: float = 0.3, max_tokens: int = 100) -> str:
        """Call Gemini API with automatic key fallback"""
        last_error = None
        
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
                
                if any(term in error_msg for term in ['rate', 'quota', 'limit', 'resource_exhausted']):
                    print(f"API key #{self.current_key_index + 1} hit rate limit")
                    if not self._try_next_key():
                        break
                else:
                    raise e
        
        raise Exception(f"All API keys failed. Last error: {last_error}")
    
    def generate_icon_query(self, slide_title: str, bullets: List[str]) -> str:
        """
        Generate optimal icon search query from slide content
        
        Args:
            slide_title: The slide title
            bullets: List of bullet points
            
        Returns:
            Single icon search query (1-3 words)
        """
        bullets_text = "\n".join([f"- {b}" for b in bullets])
        
        prompt = f"""You are an expert at choosing icons for presentations.

Given this slide content, provide EXACTLY ONE icon search query (1-3 words maximum) that best represents the main concept.

The query should be:
- Simple and concrete (e.g., "document", "chart", "lightbulb", "network")
- Suitable for finding a professional icon
- Representative of the main concept

Slide Title: {slide_title}

Bullet Points:
{bullets_text}

Respond with ONLY the search query, nothing else. No quotes, no explanation, just the query."""

        try:
            query = self._call_gemini(prompt, temperature=0.2, max_tokens=20)
            # Clean the response
            query = query.strip().strip('"').strip("'").lower()
            # Take only first 3 words if multiple
            words = query.split()[:3]
            query = " ".join(words)
            return query
        except Exception as e:
            print(f"Error generating query for '{slide_title}': {e}")
            # Fallback: extract first important word from title
            return self._fallback_query(slide_title)
    
    def _fallback_query(self, title: str) -> str:
        """Generate fallback query from title"""
        # Common stop words to skip
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'}
        
        words = title.lower().split()
        for word in words:
            clean_word = word.strip(',:;.!?')
            if clean_word not in stop_words and len(clean_word) > 3:
                return clean_word
        
        return "document"  # Ultimate fallback


class NounProjectIconFetcher:
    """Fetch icons from The Noun Project API"""
    
    def __init__(self, api_key: str = NOUN_API_KEY, api_secret: str = NOUN_API_SECRET):
        self.api_key = api_key
        self.api_secret = api_secret
        self.auth = OAuth1(api_key, api_secret)
    
    def search_and_download(self, query: str, save_path: str, limit: int = 1,
                           query_generator=None, slide_title: str = None,
                           bullets: List[str] = None) -> bool:
        """
        Search for icon and download it with intelligent fallback using Gemini
        
        Args:
            query: Initial search query
            save_path: Path to save the icon
            limit: Number of results to fetch
            query_generator: IconSearchQueryGenerator instance for re-querying
            slide_title: Slide title (needed for re-querying)
            bullets: Slide bullets (needed for re-querying)
            
        Returns:
            True if successful, False otherwise
        """
        failed_queries = []
        max_attempts = 4  # Original + 2 Gemini retries + generic fallback
        
        # Attempt 1: Try original query
        if self._try_search_download(query, save_path, limit):
            return True
        failed_queries.append(query)
        
        # Attempt 2: If multi-word query, try first word only
        words = query.split()
        if len(words) > 1:
            fallback_query = words[0]
            print(f"   Retry 1/3: '{fallback_query}'")
            if self._try_search_download(fallback_query, save_path, limit):
                return True
            failed_queries.append(fallback_query)
        
        # Attempt 3-4: Re-query Gemini for alternatives (if available)
        if query_generator and slide_title and bullets:
            for retry_num in range(2):
                print(f"   Asking Gemini for alternative query (retry {retry_num + 2}/3)...")
                alt_query = query_generator.generate_alternative_query(
                    slide_title, bullets, failed_queries
                )
                print(f"   Gemini suggests: '{alt_query}'")
                
                if self._try_search_download(alt_query, save_path, limit):
                    return True
                failed_queries.append(alt_query)
        
        # Final fallback: generic icon
        print(f"   Final fallback: 'circle'")
        return self._try_search_download("circle", save_path, limit)
    
    def _try_search_download(self, query: str, save_path: str, limit: int = 1) -> bool:
        """Internal method to try a single search and download"""
        endpoint = f"https://api.thenounproject.com/v2/icon?query={query}&limit={limit}"
        
        try:
            resp = requests.get(endpoint, auth=self.auth, timeout=15)
            
            if resp.status_code != 200:
                return False
            
            data = resp.json()
            icons = data.get("icons", [])
            
            if not icons:
                return False
            
            # Get first icon
            icon = icons[0]
            thumbnail_url = icon.get("thumbnail_url") or icon.get("icon_url")
            
            if not thumbnail_url:
                print(f"No download URL for icon")
                return False
            
            # Download icon
            img_resp = requests.get(thumbnail_url, timeout=10)
            if img_resp.status_code == 200:
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, "wb") as f:
                    f.write(img_resp.content)
                return True
            else:
                print(f"Failed to download image, status: {img_resp.status_code}")
                return False
                
        except Exception as e:
            print(f"Error fetching icon for '{query}': {e}")
            return False


def generate_icons_for_slides(slides_json_path: str = "output/intermediate/slides.json",
                              output_dir: str = "output/intermediate/images") -> Dict[str, str]:
    """
    Generate icons for all slides using Gemini + The Noun Project
    
    Args:
        slides_json_path: Path to slides JSON file
        output_dir: Directory to save icons
        
    Returns:
        Dictionary mapping slide keys to icon paths
    """
    slides_path = Path(slides_json_path)
    if not slides_path.exists():
        raise FileNotFoundError(f"Slides JSON not found: {slides_json_path}")
    
    # Load slides
    with open(slides_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize generators
    query_gen = IconSearchQueryGenerator()
    icon_fetcher = NounProjectIconFetcher()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    icon_paths = {}
    
    print(f"\nGenerating icons for {data['total_slides']} slides...")
    print(f"Output directory: {output_dir}\n")
    
    # Title slide
    print("Title Slide:")
    title_query = query_gen.generate_icon_query(
        data['title_slide']['title'],
        [data['title_slide']['subtitle']]
    )
    print(f"   Query: '{title_query}'")
    
    title_icon_path = output_dir / "title.png"
    success = icon_fetcher.search_and_download(
        title_query,
        str(title_icon_path),
        query_generator=query_gen,
        slide_title=data['title_slide']['title'],
        bullets=[data['title_slide']['subtitle']]
    )
    
    if success:
        icon_paths['title'] = str(title_icon_path)
        print(f"   Saved: {title_icon_path.name}\n")
    else:
        print(f"   Failed to get icon\n")
    
    # Content slides
    for i, slide in enumerate(data['content_slides'], 1):
        print(f"Slide {i}: {slide['title'][:50]}...")
        
        # Generate search query using Gemini
        query = query_gen.generate_icon_query(slide['title'], slide['bullets'])
        print(f"   Query: '{query}'")
        
        # Download icon with intelligent fallback
        icon_path = output_dir / f"slide_{i:02d}.png"
        success = icon_fetcher.search_and_download(
            query,
            str(icon_path),
            query_generator=query_gen,
            slide_title=slide['title'],
            bullets=slide['bullets']
        )
        
        if success:
            icon_paths[f'slide_{i}'] = str(icon_path)
            print(f"   Saved: {icon_path.name}\n")
        else:
            print(f"   Failed to get icon\n")
    
    print(f"Generated {len(icon_paths)} icons")
    return icon_paths


if __name__ == "__main__":
    import sys
    
    try:
        # Check if API keys are configured
        if NOUN_API_KEY == "YOUR_API_KEY":
            print("Error: Please configure The Noun Project API credentials")
            print("\nGet your API key from: https://thenounproject.com/developers/")
            print("Then update NOUN_API_KEY and NOUN_API_SECRET in this file")
            sys.exit(1)
        
        # Generate icons
        icon_paths = generate_icons_for_slides()
        
        print(f"\nAll icons saved to: output/intermediate/images/")
        print(f"\nIcon paths:")
        for key, path in icon_paths.items():
            print(f"   {key}: {path}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)