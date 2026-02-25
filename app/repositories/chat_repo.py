from app.db.supabase import get_supabase


class ChatRepository:

    def __init__(self):
        self.db = get_supabase()
        self.table = "chat_history"

    def get_user_history(self, user_id: str, limit: int = 20):
        result = self.db.table(self.table)\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=False)\
            .limit(limit)\
            .execute()
        return result.data if result.data else []

    def add_message(self, user_id: str, role: str, content: str):
        result = self.db.table(self.table).insert({
            "user_id": user_id,
            "role": role,
            "content": content,
        }).execute()
        return result.data[0] if result.data else None

    def clear_history(self, user_id: str):
        self.db.table(self.table)\
            .delete()\
            .eq("user_id", user_id)\
            .execute()
        return {"message": "Chat history cleared"}
