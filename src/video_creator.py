"""
Video Creator Module
Complete standalone module for creating animated explainer videos
Includes: PDF to images conversion, TTS generation, and video assembly
"""

from moviepy import (
    ImageClip, AudioFileClip,
    concatenate_videoclips, CompositeAudioClip,
    vfx
)
from pdf2image import convert_from_path
from gtts import gTTS
from pathlib import Path
from typing import List, Tuple, Dict
import json
import os


def convert_pdf_to_images(pdf_path: str = "output/slides.pdf",
                          output_dir: str = "output/intermediate/slide_images",
                          dpi: int = 100) -> List[str]:
    """
    Convert PDF slides to individual PNG images
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images
        dpi: Image resolution (100 for faster processing)
        
    Returns:
        List of paths to generated images
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nConverting PDF to images...")
    print(f"Input: {pdf_path}")
    print(f"Output: {output_dir}")
    print(f"Resolution: {dpi} DPI\n")
    
    # Convert PDF pages to images
    pages = convert_from_path(str(pdf_path), dpi=dpi)
    
    image_paths = []
    for i, page_img in enumerate(pages):
        # Save with zero-padded numbering (slide_00.png, slide_01.png, etc.)
        img_path = output_dir / f"slide_{i:02d}.png"
        page_img.save(str(img_path), "PNG")
        image_paths.append(str(img_path))
        print(f"   Slide {i + 1}/{len(pages)}: {img_path.name}")
    
    print(f"\nConverted {len(image_paths)} slides to images")
    return image_paths


def generate_tts_audio(slides_json_path: str = "output/intermediate/slides.json",
                       output_dir: str = "output/intermediate/audio",
                       title_duration: float = 3.0) -> List[Tuple[str, float]]:
    """
    Generate TTS audio files from slide speaker notes
    
    Args:
        slides_json_path: Path to slides JSON file
        output_dir: Directory to save audio files
        title_duration: Duration for title slide (no audio, just display time)
        
    Returns:
        List of (audio_path, duration) tuples
    """
    slides_path = Path(slides_json_path)
    if not slides_path.exists():
        raise FileNotFoundError(f"Slides JSON not found: {slides_json_path}")
    
    # Load slides
    with open(slides_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating TTS audio narration...")
    print(f"Output: {output_dir}\n")
    
    audio_clips = []
    
    # Title slide - no audio, just duration (silent)
    print("Title slide (silent)...")
    audio_clips.append((None, title_duration))  # No audio file, fixed duration
    print(f"   Silent display: {title_duration}s")
    
    # Content slides
    for i, slide in enumerate(data['content_slides'], 1):
        print(f"Slide {i}: {slide['title'][:50]}...")
        
        # Use speaker notes if available, otherwise synthesize from title and bullets
        if slide.get('speaker_notes'):
            text = slide['speaker_notes']
        else:
            text = f"{slide['title']}. {' '.join(slide.get('bullets', []))}"
        
        audio_path = output_dir / f"audio_{i:02d}.mp3"
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(audio_path))
        
        # Get duration
        audio = AudioFileClip(str(audio_path))
        duration = audio.duration
        audio.close()
        
        audio_clips.append((str(audio_path), duration))
        print(f"   Generated: {audio_path.name} ({duration:.1f}s)")
    
    # Calculate total duration (excluding None audio paths)
    audio_count = sum(1 for path, _ in audio_clips if path is not None)
    total_duration = sum(dur for _, dur in audio_clips)
    print(f"\nGenerated {audio_count} audio files + 1 silent title")
    print(f"Total duration: {total_duration:.1f} seconds")
    
    return audio_clips


class VideoCreator:
    """Create animated videos from slide images and audio"""
    
    def __init__(self):
        """Initialize video creator"""
        # Video settings (optimized for speed)
        self.fps = 10  # Lower FPS for faster rendering
        self.resolution = (1280, 720)  # 720p HD
        self.transition_duration = 0.5
    
    def create_video(self, slide_images: List[str], audio_clips: List[Tuple[str, float]],
                    output_path: str = "output/video.mp4",
                    background_music_path: str = None) -> str:
        """
        Create complete video from slide images and audio
        
        Args:
            slide_images: List of slide image paths
            audio_clips: List of (audio_path, duration) tuples
            output_path: Path to save the video
            background_music_path: Optional path to background music file
            
        Returns:
            Path to created video
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\nAssembling video...")
        print(f"Output: {output_path}\n")
        
        # Create video clips
        print("Creating video clips...")
        video_clips = []
        
        for i, (img_path, (audio_path, duration)) in enumerate(zip(slide_images, audio_clips)):
            print(f"   Processing slide {i + 1}/{len(slide_images)}...")
            
            # Create image clip
            img_clip = ImageClip(img_path).with_duration(duration)
            img_clip = img_clip.with_fps(self.fps)
            
            # Add audio if available (skip if None for silent slides)
            if audio_path and os.path.exists(audio_path):
                audio = AudioFileClip(audio_path)
                img_clip = img_clip.with_audio(audio)
            # If audio_path is None, the slide will be silent
            
            # Add fade transitions
            img_clip = vfx.FadeIn(self.transition_duration).apply(img_clip)
            img_clip = vfx.FadeOut(self.transition_duration).apply(img_clip)
            
            video_clips.append(img_clip)
        
        # Concatenate clips
        print("\nAssembling final video...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Add background music (if provided)
        if background_music_path and Path(background_music_path).exists():
            print("   Adding background music...")
            bg_music = AudioFileClip(background_music_path)
            bg_music = bg_music.volumex(0.2)  # 20% volume
            
            # Loop music if needed
            if bg_music.duration < final_video.duration:
                bg_music = bg_music.fx(lambda clip: clip.loop(duration=final_video.duration))
            else:
                bg_music = bg_music.subclip(0, final_video.duration)
            
            # Mix with narration
            if final_video.audio:
                final_audio = CompositeAudioClip([final_video.audio, bg_music])
                final_video = final_video.with_audio(final_audio)
            else:
                final_video = final_video.with_audio(bg_music)
        
        # Write video file
        print(f"\nRendering video to {output_path}...")
        temp_dir = output_path.parent / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=str(temp_dir / 'temp_audio.m4a'),
            remove_temp=True,
            threads=4,
            preset='fast'  # Faster encoding preset
        )
        
        # Cleanup
        for clip in video_clips:
            clip.close()
        final_video.close()
        
        print(f"\nVideo created: {output_path}")
        print(f"Duration: {final_video.duration:.1f} seconds")
        
        return str(output_path)


def create_video_complete(pdf_path: str = "output/slides.pdf",
                         slides_json_path: str = "output/intermediate/slides.json",
                         images_dir: str = "output/intermediate/slide_images",
                         audio_dir: str = "output/intermediate/audio",
                         output_path: str = "output/video.mp4",
                         background_music_path: str = None) -> str:
    """
    Complete video creation pipeline: PDF → Images → TTS → Video
    
    Args:
        pdf_path: Path to PDF slides file
        slides_json_path: Path to slides JSON (for speaker notes)
        images_dir: Directory to save/load slide images
        audio_dir: Directory to save/load audio files
        output_path: Path to save the video
        background_music_path: Optional background music file
        
    Returns:
        Path to created video
    """
    images_dir = Path(images_dir)
    audio_dir = Path(audio_dir)
    
    # Step 1: Convert PDF to images (if not already done)
    if not images_dir.exists() or not list(images_dir.glob("slide_*.png")):
        print("Converting PDF to images...")
        slide_images = convert_pdf_to_images(pdf_path, str(images_dir))
    else:
        print("Using existing slide images...")
        slide_images = sorted([str(p) for p in images_dir.glob("slide_*.png")])
        print(f"   Found {len(slide_images)} images")
    
    # Step 2: Generate TTS audio (if not already done)
    if not audio_dir.exists() or not list(audio_dir.glob("audio_*.mp3")):
        print("\nGenerating TTS audio...")
        audio_clips = generate_tts_audio(slides_json_path, str(audio_dir))
    else:
        print("\nUsing existing audio files...")
        # Load existing audio files with durations
        audio_files = sorted(audio_dir.glob("audio_*.mp3"))
        audio_clips = []
        for audio_file in audio_files:
            audio = AudioFileClip(str(audio_file))
            duration = audio.duration
            audio.close()
            audio_clips.append((str(audio_file), duration))
        print(f"   Found {len(audio_clips)} audio files")
    
    # Step 3: Create video
    creator = VideoCreator()
    return creator.create_video(slide_images, audio_clips, output_path, background_music_path)


if __name__ == "__main__":
    import sys
    
    try:
        # Create complete video
        video_path = create_video_complete()
        
        print(f"\nSuccess! Video created:")
        print(f"   {video_path}")
        print(f"\nYou can play it with:")
        print(f"   mpv {video_path}")
        print(f"   vlc {video_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
