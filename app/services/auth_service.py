from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.schemas import UserCreate, UserResponse, TokenResponse


class AuthService:

    def __init__(self):
        self.repo = UserRepository()

    def register(self, data: UserCreate) -> UserResponse:
        # Check if email already exists
        existing = self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        user = self.repo.create(
            email=data.email,
            username=data.username,
            password=data.password,
        )
        return UserResponse(**user)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.repo.get_by_email(email)

        if not user or not verify_password(password, user["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )

        token = create_access_token({"sub": user["id"]})
        return TokenResponse(access_token=token)

    def get_me(self, user_id: str) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user)
