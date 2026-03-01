"""
Video upload and RAG-based Q&A
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from supabase import Client
import cohere
import re


class VideoCreate(BaseModel):
    """Schema for creating a new video"""
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    source_url: Optional[str] = None
    youtube_id: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    resolution: Optional[str] = None
    fps: Optional[int] = None
    codec: Optional[str] = None
    transcript: Optional[str] = None
    topics: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_public: bool = False


class VideoUpdate(BaseModel):
    """Schema for updating a video"""
    title: Optional[str] = None
    description: Optional[str] = None
    processing_status: Optional[str] = None
    is_public: Optional[bool] = None


class VideoDatabase:
    """Database operations for videos with RAG support"""

    def __init__(self, supabase_client: Client, cohere_api_key: Optional[str] = None):
        self.supabase = supabase_client
        self.cohere_client = cohere.Client(cohere_api_key) if cohere_api_key else None

    def generate_embedding(self, text: str, model: str = "embed-english-v3.0", input_type: str = "search_document") -> List[float]:
        """Generate embedding for text using Cohere"""
        if not self.cohere_client:
            raise ValueError("Cohere client not initialized")
        response = self.cohere_client.embed(
            texts=[text],
            model=model,
            input_type=input_type
        )
        return response.embeddings[0]

    def chunk_text(self, text: str, chunk_size: int = 300, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks

    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
            r'youtube\.com\/embed\/([^&\n?#]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def check_video_exists(self, youtube_id: str = None, source_url: str = None) -> Optional[Dict[str, Any]]:
        """Check if video already exists (by YouTube ID or URL)"""
        if youtube_id:
            response = self.supabase.table("videos").select("*").eq("youtube_id", youtube_id).execute()
            if response.data:
                return response.data[0]
        if source_url:
            response = self.supabase.table("videos").select("*").eq("source_url", source_url).execute()
            if response.data:
                return response.data[0]
        return None

    def create_video(self, video_data: VideoCreate, user_id: str) -> Dict[str, Any]:
        """Create a new video with embedding"""
        embedding_text = video_data.title
        if video_data.description:
            embedding_text += f" {video_data.description}"

        embedding = None
        embedding_model = None
        if self.cohere_client:
            try:
                embedding = self.generate_embedding(embedding_text, input_type="search_document")
                embedding_model = "embed-english-v3.0"
            except Exception as e:
                print(f"Error generating embedding: {e}")

        insert_data = {
            **video_data.dict(exclude_none=True),
            "user_id": user_id,
            "embedding": embedding,
            "embedding_model": embedding_model
        }

        response = self.supabase.table("videos").insert(insert_data).execute()
        video = response.data[0] if response.data else None

        if video:
            self.link_user_to_video(user_id, video['id'])

        return video

    def link_user_to_video(self, user_id: str, video_id: str) -> Dict[str, Any]:
        """Link a user to a video (many-to-many)"""
        try:
            response = self.supabase.table("user_videos").insert({
                "user_id": user_id,
                "video_id": video_id
            }).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"User already linked to video: {e}")
            return None

    def user_has_access_to_video(self, user_id: str, video_id: str) -> bool:
        """Check if user has access to video"""
        response = self.supabase.table("user_videos").select("*").eq("user_id", user_id).eq("video_id", video_id).execute()
        return len(response.data) > 0

    def create_video_chunks(self, video_id: str, content: str, duration: Optional[int] = None) -> List[Dict[str, Any]]:
        """Create chunks from video content with embeddings and timestamps"""
        chunks = self.chunk_text(content, chunk_size=300, overlap=50)
        total_chunks = len(chunks)
        created_chunks = []

        time_per_chunk = (duration / total_chunks) if duration and total_chunks > 0 else None

        embeddings = []
        if self.cohere_client and chunks:
            try:
                response = self.cohere_client.embed(
                    texts=chunks,
                    model="embed-english-v3.0",
                    input_type="search_document"
                )
                embeddings = response.embeddings
            except Exception as e:
                print(f"Error batch embedding chunks: {e}")

        for idx, chunk_text in enumerate(chunks):
            embedding = embeddings[idx] if idx < len(embeddings) else None
            start_time = (idx * time_per_chunk) if time_per_chunk else None
            end_time = ((idx + 1) * time_per_chunk) if time_per_chunk else None

            chunk_data = {
                "video_id": video_id,
                "chunk_index": idx,
                "content": chunk_text,
                "embedding": embedding,
                "start_time": start_time,
                "end_time": end_time
            }

            response = self.supabase.table("video_chunks").insert(chunk_data).execute()
            if response.data:
                created_chunks.append(response.data[0])

        print(f"Created {len(created_chunks)} chunks for video {video_id}")
        return created_chunks

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a video by ID"""
        response = self.supabase.table("videos").select("*").eq("id", video_id).execute()
        return response.data[0] if response.data else None

    def get_video_chunks(self, video_id: str) -> List[Dict[str, Any]]:
        """Get all chunks for a video"""
        response = (
            self.supabase.table("video_chunks")
            .select("*")
            .eq("video_id", video_id)
            .order("chunk_index")
            .execute()
        )
        return response.data

    def get_video_with_chunks(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a video with all its chunks"""
        video = self.get_video(video_id)
        if video:
            video['chunks'] = self.get_video_chunks(video_id)
        return video

    def get_user_videos(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all videos for a user"""
        user_videos_response = (
            self.supabase.table("user_videos")
            .select("video_id")
            .eq("user_id", user_id)
            .execute()
        )
        video_ids = [uv['video_id'] for uv in user_videos_response.data]

        if not video_ids:
            return []

        response = (
            self.supabase.table("videos")
            .select("*")
            .in_("id", video_ids)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return response.data

    def search_videos_by_text(self, query: str, user_id: str, match_threshold: float = 0.6, match_count: int = 10) -> List[Dict[str, Any]]:
        """Search videos by semantic similarity"""
        if not self.cohere_client:
            raise ValueError("Cohere client not initialized")
        query_embedding = self.generate_embedding(query, input_type="search_query")
        response = self.supabase.rpc(
            "search_videos",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count,
                "target_user_id": user_id
            }
        ).execute()
        return response.data

    def search_chunks_by_text(self, query: str, match_threshold: float = 0.6, match_count: int = 10) -> List[Dict[str, Any]]:
        """Search all chunks by semantic similarity"""
        if not self.cohere_client:
            raise ValueError("Cohere client not initialized")
        query_embedding = self.generate_embedding(query, input_type="search_query")
        response = self.supabase.rpc(
            "search_all_chunks",
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count
            }
        ).execute()
        return response.data

    def search_similar_chunks(self, video_id: str, query: str, match_threshold: float = 0.7, match_count: int = 5) -> List[Dict[str, Any]]:
        """Search for similar chunks within a specific video"""
        if not self.cohere_client:
            raise ValueError("Cohere client not initialized")
        query_embedding = self.generate_embedding(query, input_type="search_query")
        response = self.supabase.rpc(
            "search_video_chunks",
            {
                "target_video_id": video_id,
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": match_count
            }
        ).execute()
        return response.data

    def answer_question(self, video_id: str, user_id: str, question: str) -> tuple[str, List[Dict[str, Any]]]:
        """Answer a question about a video using RAG"""
        if not self.user_has_access_to_video(user_id, video_id):
            raise PermissionError("User does not have access to this video")

        similar_chunks = self.search_similar_chunks(video_id, question, match_threshold=0.6, match_count=5)

        if not similar_chunks:
            return "I couldn't find relevant information in the video to answer that question.", []

        context_parts = []
        for chunk in similar_chunks:
            time_info = ""
            if chunk.get('start_time') and chunk.get('end_time'):
                time_info = f" ({chunk['start_time']:.1f}s - {chunk['end_time']:.1f}s)"
            context_parts.append(f"Chunk {chunk['chunk_index']}{time_info}:\n{chunk['content']}")

        context_text = "\n\n".join(context_parts)

        prompt = f"""You are a helpful video assistant. Answer the user's question based ONLY on the provided video content segments.
If the answer is not in the segments, say so clearly.
Be concise and accurate. Cite specific chunk numbers or timestamps if helpful.

Video Content Segments:
{context_text}

Question: {question}

Answer:"""

        # ✅ Updated from deprecated "command-r-plus" to "command-r-08-2024"
        response = self.cohere_client.chat(
            message=prompt,
            model="command-r-08-2024",
            temperature=0.3
        )

        return response.text, similar_chunks

    def delete_video(self, video_id: str, user_id: str) -> bool:
        """Delete a video and its chunks"""
        self.supabase.table("user_videos").delete().eq("user_id", user_id).eq("video_id", video_id).execute()

        links = self.supabase.table("user_videos").select("*").eq("video_id", video_id).execute()

        if not links.data:
            self.supabase.table("video_chunks").delete().eq("video_id", video_id).execute()
            response = self.supabase.table("videos").delete().eq("id", video_id).execute()
            return len(response.data) > 0

        return True