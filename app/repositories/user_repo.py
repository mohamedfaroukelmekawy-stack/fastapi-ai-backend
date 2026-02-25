from app.db.supabase import get_supabase
from app.core.security import hash_password


class UserRepository:

    def __init__(self):
        self.db = get_supabase()
        self.table = "users"

    def get_by_email(self, email: str):
        result = self.db.table(self.table)\
            .select("*")\
            .eq("email", email)\
            .execute()
        return result.data[0] if result.data else None

    def get_by_id(self, user_id: str):
        result = self.db.table(self.table)\
            .select("*")\
            .eq("id", user_id)\
            .execute()
        return result.data[0] if result.data else None

    def create(self, email: str, username: str, password: str):
        result = self.db.table(self.table).insert({
            "email": email,
            "username": username,
            "hashed_password": hash_password(password),
        }).execute()
        return result.data[0] if result.data else None

