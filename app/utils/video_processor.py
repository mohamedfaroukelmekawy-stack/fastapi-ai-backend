"""
Video processing utilities - extract metadata and thumbnails
"""
import os
import cv2
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image


class VideoProcessor:
    """Process videos to extract metadata and thumbnails"""
    
    def __init__(self):
        pass
    
    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Extract basic video metadata using OpenCV"""
        metadata = {}
        
        try:
            metadata['file_size'] = os.path.getsize(video_path)
            cap = cv2.VideoCapture(video_path)
            
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                metadata['fps'] = int(fps) if fps > 0 else None
                metadata['resolution'] = f"{width}x{height}"
                metadata['duration'] = int(frame_count / fps) if fps > 0 else None
                
                fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
                metadata['codec'] = codec
                
                cap.release()
                
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def generate_thumbnail(
        self, 
        video_path: str, 
        output_path: Optional[str] = None,
        timestamp: float = 1.0,
        size: tuple = (640, 360)
    ) -> str:
        """Generate thumbnail from video at specified timestamp"""
        if output_path is None:
            output_dir = tempfile.gettempdir()
            filename = f"thumb_{Path(video_path).stem}_{int(timestamp)}.jpg"
            output_path = os.path.join(output_dir, filename)
        
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)
        success, frame = cap.read()
        
        if success:
            frame_resized = cv2.resize(frame, size)
            cv2.imwrite(output_path, frame_resized)
        
        cap.release()
        return output_path if success else None
    
    def generate_multiple_thumbnails(
        self,
        video_path: str,
        num_thumbnails: int = 4
    ) -> List[str]:
        """Generate multiple thumbnails at evenly spaced intervals"""
        metadata = self.extract_video_metadata(video_path)
        duration = metadata.get('duration', 0)
        
        if duration == 0:
            return []
        
        thumbnails = []
        interval = duration / (num_thumbnails + 1)
        
        for i in range(1, num_thumbnails + 1):
            timestamp = interval * i
            thumb_path = self.generate_thumbnail(video_path, timestamp=timestamp)
            if thumb_path:
                thumbnails.append(thumb_path)
        
        return thumbnails
    
    def analyze_video_complete(
        self,
        video_path: str,
        include_transcript: bool = False,
        include_thumbnails: bool = True,
        num_thumbnails: int = 4
    ) -> Dict[str, Any]:
        """Complete video analysis"""
        analysis = {}
        
        print("Extracting metadata...")
        metadata = self.extract_video_metadata(video_path)
        analysis.update(metadata)
        
        if include_thumbnails:
            print("Generating thumbnails...")
            thumbnails = self.generate_multiple_thumbnails(video_path, num_thumbnails)
            analysis['thumbnails'] = thumbnails
            analysis['thumbnail_url'] = thumbnails[0] if thumbnails else None
        
        if include_transcript:
            print("Note: Transcription not available in simplified version")
            analysis['transcript'] = None
            analysis['transcript_segments'] = []
            analysis['detected_language'] = None
        
        return analysis
