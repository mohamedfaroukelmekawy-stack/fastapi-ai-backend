from fastapi import APIRouter, Depends
from app.core.security import get_current_user_id
from app.services.auth_service import AuthService
from app.schemas.schemas import UserCreate, UserResponse, TokenResponse
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate):
    """Register a new user"""
    return AuthService().register(data)


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get JWT token"""
    return AuthService().login(
        email=form_data.username,
        password=form_data.password,
    )


@router.get("/me", response_model=UserResponse)
def get_me(user_id: str = Depends(get_current_user_id)):
    """Get current logged in user"""
    return AuthService().get_me(user_id)
