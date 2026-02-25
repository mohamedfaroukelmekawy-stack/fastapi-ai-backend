from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.chat_service import ChatService
from app.schemas.schemas import ChatRequest, ChatResponse, ChatMessageResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(data: ChatRequest, user_id: str = Depends(get_current_user_id)):
    """Send a message to the LLM"""
    return ChatService().chat(user_id, data.message)


@router.get("/history", response_model=list[ChatMessageResponse])
def get_history(user_id: str = Depends(get_current_user_id)):
    """Get your chat history"""
    return ChatService().get_history(user_id)


@router.delete("/history")
def clear_history(user_id: str = Depends(get_current_user_id)):
    """Clear your chat history"""
    return ChatService().clear_history(user_id)
