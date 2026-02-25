import cohere
from fastapi import HTTPException

from app.core.config import settings
from app.repositories.chat_repo import ChatRepository
from app.schemas.schemas import ChatResponse, ChatMessageResponse


class ChatService:

    def __init__(self):
        self.repo = ChatRepository()
        # ✅ Compatible with your installed SDK
        self.client = cohere.Client(settings.COHERE_API_KEY)

    def chat(self, user_id: str, message: str) -> ChatResponse:

        # 1️⃣ Save user message
        self.repo.add_message(user_id, "user", message)

        # 2️⃣ Load history
        history = self.repo.get_user_history(user_id, limit=20)

        # 3️⃣ Build conversation text
        conversation = ""

        for msg in history[:-1]:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n"

        conversation += f"User: {message}\nAssistant:"

        # 4️⃣ Call Cohere (compatible API)
        try:
            response = self.client.chat(
                model="command-a-03-2025",
                message=conversation,
            )

            reply = response.text

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"LLM error: {str(e)}"
            )

        # 5️⃣ Save assistant reply
        self.repo.add_message(user_id, "assistant", reply)

        # 6️⃣ Return updated history
        updated_history = self.repo.get_user_history(user_id)

        return ChatResponse(
            reply=reply,
            history=[
                ChatMessageResponse(**msg)
                for msg in updated_history
            ],
        )

    def get_history(self, user_id: str):
        history = self.repo.get_user_history(user_id)
        return [ChatMessageResponse(**msg) for msg in history]

    def clear_history(self, user_id: str):
        return self.repo.clear_history(user_id)
