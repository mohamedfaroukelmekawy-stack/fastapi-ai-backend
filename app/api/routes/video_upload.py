"""
Video upload and RAG-based Q&A
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from typing import Optional
from pydantic import BaseModel
import os
import shutil
from pathlib import Path
import tempfile
import requests
from supabase import Client
from dotenv import load_dotenv

load_dotenv()

from app.models.video_models import VideoDatabase, VideoCreate
from app.utils.video_processor import VideoProcessor

router = APIRouter(prefix="/api/videos", tags=["videos"])

video_processor = VideoProcessor()


class QuestionRequest(BaseModel):
    question: str


def get_supabase_client() -> Client:
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    return create_client(url, key)


def get_video_db(supabase: Client = Depends(get_supabase_client)) -> VideoDatabase:
    cohere_key = os.getenv("COHERE_API_KEY")
    return VideoDatabase(supabase, cohere_key)


def get_current_user() -> str:
    return "user-id-placeholder"


def upload_to_supabase_storage(file_path: str, bucket_name: str, destination_path: str, supabase: Client) -> str:
    with open(file_path, 'rb') as f:
        file_data = f.read()
    supabase.storage.from_(bucket_name).upload(
        destination_path, file_data, 
        file_options={"content-type": "video/mp4", "upsert": "true"}
    )
    return supabase.storage.from_(bucket_name).get_public_url(destination_path)


def download_video_from_url(url: str) -> str:
    """Download video from URL"""
    temp_dir = tempfile.gettempdir()
    filename = f"video_{os.urandom(8).hex()}.mp4"
    temp_path = os.path.join(temp_dir, filename)
    
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    
    with open(temp_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return temp_path


@router.post("/upload")
async def upload_video(
    file: Optional[UploadFile] = File(None),
    video_url: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db),
    supabase: Client = Depends(get_supabase_client)
):
    """
    🎥 Upload video (file or URL) with full analysis and chunking
    """
    
    if not file and not video_url:
        raise HTTPException(status_code=400, detail="Provide file or video_url")
    
    temp_path = None
    video_filename = None
    source_url = None
    youtube_id = None
    
    try:
        # Check if it's a YouTube URL
        if video_url:
            youtube_id = video_db.extract_youtube_id(video_url)
            
            # Check if video already exists
            if youtube_id or video_url:
                existing_video = video_db.check_video_exists(youtube_id=youtube_id, source_url=video_url)
                if existing_video:
                    # Video exists, just link user
                    video_db.link_user_to_video(user_id, existing_video['id'])
                    chunks = video_db.get_video_chunks(existing_video['id'])
                    
                    return {
                        "success": True,
                        "message": "Video already exists - linked to your account",
                        "video": {
                            "id": existing_video['id'],
                            "name": existing_video['title'],
                            "title": existing_video['title'],
                            "description": existing_video['description'],
                            "file_url": existing_video.get('file_url'),
                            "source_url": existing_video.get('source_url'),
                            "chunks_count": len(chunks),
                            "duration": existing_video.get('duration'),
                            "already_existed": True
                        }
                    }
        
        # Handle file upload
        if file:
            video_filename = file.filename
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"upload_{file.filename}")
            
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        
        # Handle URL download
        elif video_url:
            print(f"Downloading video from: {video_url}")
            temp_path = download_video_from_url(video_url)
            video_filename = Path(video_url).name or "video.mp4"
            source_url = video_url
        
        # Analyze video
        print("Analyzing video...")
        analysis = video_processor.analyze_video_complete(temp_path, include_transcript=False, include_thumbnails=True)
        
        # Upload to storage
        print("Uploading to storage...")
        bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "videos")
        file_destination = f"uploads/{user_id}/{video_filename}"
        file_url = upload_to_supabase_storage(temp_path, bucket_name, file_destination, supabase)
        
        # Upload thumbnail
        thumbnail_url = None
        if analysis.get('thumbnail_url'):
            try:
                thumb_dest = f"thumbnails/{user_id}/{Path(video_filename).stem}_thumb.jpg"
                thumbnail_url = upload_to_supabase_storage(analysis['thumbnail_url'], bucket_name, thumb_dest, supabase)
            except Exception as e:
                print(f"Warning: thumbnail error: {e}")
        
        # Create description
        video_title = title or Path(video_filename).stem
        full_description = description or f"Video: {video_title}. Duration: {analysis.get('duration', 0)} seconds."
        
        # Create video record
        print("Creating video record...")
        video_data = VideoCreate(
            title=video_title,
            description=full_description,
            file_path=file_destination,
            file_url=file_url,
            source_url=source_url,
            youtube_id=youtube_id,
            file_size=analysis.get('file_size'),
            mime_type="video/mp4",
            duration=analysis.get('duration'),
            resolution=analysis.get('resolution'),
            fps=analysis.get('fps'),
            codec=analysis.get('codec'),
            thumbnail_url=thumbnail_url,
            is_public=is_public
        )
        
        video_record = video_db.create_video(video_data, user_id)
        
        # Create chunks
        print("Creating content chunks...")
        chunks_created = video_db.create_video_chunks(
            video_record['id'],
            full_description,
            duration=analysis.get('duration')
        )
        
        # Cleanup
        try:
            if temp_path:
                os.remove(temp_path)
            if analysis.get('thumbnail_url'):
                os.remove(analysis['thumbnail_url'])
        except:
            pass
        
        return {
            "success": True,
            "message": "Video uploaded and analyzed",
            "video": {
                "id": video_record['id'],
                "name": video_record['title'],
                "title": video_record['title'],
                "description": video_record['description'],
                "file_url": video_record['file_url'],
                "source_url": video_record.get('source_url'),
                "thumbnail_url": video_record.get('thumbnail_url'),
                "chunks_count": len(chunks_created),
                "metadata": {
                    "duration": video_record.get('duration'),
                    "resolution": video_record.get('resolution'),
                    "fps": video_record.get('fps'),
                    "file_size_mb": round(video_record.get('file_size', 0) / (1024 * 1024), 2)
                },
                "created_at": video_record.get('created_at')
            }
        }
        
    except Exception as e:
        if temp_path:
            try:
                os.remove(temp_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/{video_id}/ask")
async def ask_video_question(
    video_id: str,
    request: QuestionRequest,
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db)
):
    """
    💬 Ask a question about a video - RAG-based Q&A
    
    Returns answer with source chunks and timestamps
    """
    try:
        answer, chunks = video_db.answer_question(video_id, user_id, request.question)
        
        return {
            "success": True,
            "question": request.question,
            "answer": answer,
            "sources": [
                {
                    "chunk_index": c['chunk_index'],
                    "content": c['content'],
                    "start_time": c.get('start_time'),
                    "end_time": c.get('end_time'),
                    "similarity": c.get('similarity')
                }
                for c in chunks
            ]
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/list")
async def list_videos(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db)
):
    """📋 List user's videos"""
    videos = video_db.get_user_videos(user_id, limit, offset)
    return {
        "success": True,
        "count": len(videos),
        "videos": videos
    }


@router.get("/{video_id}")
async def get_video(
    video_id: str,
    include_chunks: bool = False,
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db)
):
    """🎬 Get video details"""
    video = video_db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video_db.user_has_access_to_video(user_id, video_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if include_chunks:
        video['chunks'] = video_db.get_video_chunks(video_id)
    
    return {"success": True, "video": video}


@router.get("/{video_id}/chunks")
async def get_video_chunks(
    video_id: str,
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db)
):
    """📑 Get all chunks for a video"""
    if not video_db.user_has_access_to_video(user_id, video_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    chunks = video_db.get_video_chunks(video_id)
    return {
        "success": True,
        "video_id": video_id,
        "chunks_count": len(chunks),
        "chunks": chunks
    }


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    user_id: str = Depends(get_current_user),
    video_db: VideoDatabase = Depends(get_video_db)
):
    """🗑️ Delete video"""
    success = video_db.delete_video(video_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True, "message": "Video deleted"}
