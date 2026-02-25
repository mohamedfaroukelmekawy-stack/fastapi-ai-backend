from fastapi import HTTPException
from app.core.config import settings
from app.db.supabase import get_supabase
import cohere

co = cohere.Client(settings.COHERE_API_KEY)


class EmbeddingService:

    def __init__(self):
        self.db = get_supabase()

    def create_and_store(self, user_id: str, text: str) -> dict:
        # Generate embedding from Cohere
        try:
            response = co.embed(
                texts=[text],
                model="embed-english-v3.0",
                input_type="search_document"
            )
            embedding = response.embeddings[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

        # Store in Supabase
        result = self.db.table("embeddings").insert({
            "user_id": user_id,
            "text": text,
            "embedding": embedding
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to store embedding")

        return {
            "id": result.data[0]["id"],
            "text": text,
            "embedding_size": len(embedding),
            "message": "Embedding created and stored successfully"
        }

    def get_user_embeddings(self, user_id: str) -> list:
        result = self.db.table("embeddings")\
            .select("id, text, created_at")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()
        return result.data if result.data else []
