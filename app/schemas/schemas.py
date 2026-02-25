from datetime import datetime
from pydantic import BaseModel, EmailStr


# ─── User Schemas ────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    created_at: datetime


# ─── Auth Schemas ────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── Chat Schemas ────────────────────────────────
class ChatRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessageResponse]
