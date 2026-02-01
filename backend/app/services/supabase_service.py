from typing import Optional
from supabase import create_client, Client
from app.config import get_settings


class SupabaseService:
    _client: Optional[Client] = None
    _admin: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Lazy-load Supabase client with anon key (for auth operations)."""
        if self._client is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_anon_key:
                raise RuntimeError("Supabase URL and anon key must be configured")
            self._client = create_client(settings.supabase_url, settings.supabase_anon_key)
        return self._client

    @property
    def admin(self) -> Client:
        """Lazy-load Supabase client with service key (for admin operations)."""
        if self._admin is None:
            settings = get_settings()
            if not settings.supabase_url or not settings.supabase_service_key:
                raise RuntimeError("Supabase URL and service key must be configured")
            self._admin = create_client(settings.supabase_url, settings.supabase_service_key)
        return self._admin

    # Auth methods
    async def sign_up(self, email: str, password: str) -> dict:
        response = self.client.auth.sign_up({
            "email": email,
            "password": password
        })
        return response

    async def sign_in(self, email: str, password: str) -> dict:
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return response

    async def sign_out(self, access_token: str) -> None:
        self.client.auth.sign_out()

    async def get_user(self, access_token: str) -> Optional[dict]:
        response = self.client.auth.get_user(access_token)
        return response.user if response else None

    async def reset_password_for_email(self, email: str) -> None:
        """Send password reset email."""
        self.client.auth.reset_password_for_email(email)

    async def update_user_password(self, access_token: str, new_password: str) -> dict:
        """Update user password (requires valid session from reset link)."""
        # Set the session from the access token first
        self.client.auth.set_session(access_token, "")
        response = self.client.auth.update_user({"password": new_password})
        return response.user if response else None

    # Database methods
    # NOTE: Using client (anon key) instead of admin (service key) as a test
    # because the service key format appears to be rejected by the REST API
    def table(self, table_name: str):
        """Get a table reference for queries."""
        return self.client.table(table_name)

    async def insert(self, table_name: str, data: dict) -> Optional[dict]:
        response = self.client.table(table_name).insert(data).execute()
        return response.data[0] if response.data else None

    async def select(self, table_name: str, columns: str = "*", filters: Optional[dict] = None) -> list:
        query = self.client.table(table_name).select(columns)
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        return response.data

    async def update(self, table_name: str, data: dict, filters: dict) -> Optional[dict]:
        query = self.client.table(table_name).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return response.data[0] if response.data else None

    async def delete(self, table_name: str, filters: dict) -> bool:
        query = self.client.table(table_name).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return True


supabase_service = SupabaseService()
