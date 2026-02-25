from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user_id
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/embedding", tags=["Embedding"])


class EmbeddingRequest(BaseModel):
    text: str


@router.post("/")
def create_embedding(
    data: EmbeddingRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Get text → generate embedding → store in Supabase"""
    return EmbeddingService().create_and_store(user_id, data.text)


@router.get("/")
def get_embeddings(user_id: str = Depends(get_current_user_id)):
    """Get all stored embeddings for current user"""
    return EmbeddingService().get_user_embeddings(user_id)
