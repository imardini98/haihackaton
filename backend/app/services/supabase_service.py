from typing import Optional
from supabase import create_client, Client
from app.config import get_settings
import json, time

# #region agent log
LOG_PATH = r"e:\Hackathon\odask\haihackaton\backend\debug.log"
def _debug_log(hyp, loc, msg, data=None):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"hypothesisId":hyp,"location":loc,"message":msg,"data":data,"timestamp":int(time.time()*1000),"sessionId":"debug-session"})+"\n")
        print(f"DEBUG: {loc} - {msg}")
    except Exception as ex:
        print(f"DEBUG_LOG_ERROR: {ex}")
# #endregion


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
        # #region agent log
        _debug_log("G", "supabase_service.py:admin:access", "Admin property accessed", {"_admin_is_none": self._admin is None})
        # #endregion
        if self._admin is None:
            settings = get_settings()
            # #region agent log
            _debug_log("G", "supabase_service.py:admin:init", "Creating admin client", {
                "url": settings.supabase_url,
                "key_prefix": settings.supabase_service_key[:50] + "..." if settings.supabase_service_key else None,
                "key_length": len(settings.supabase_service_key) if settings.supabase_service_key else 0
            })
            # #endregion
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
        # #region agent log
        _debug_log("C", "supabase_service.py:get_user:entry", "Getting user", {"token_prefix": access_token[:20] + "..." if access_token else None})
        # #endregion
        try:
            response = self.client.auth.get_user(access_token)
            # #region agent log
            _debug_log("C", "supabase_service.py:get_user:response", "Got response", {"response_type": str(type(response)), "has_user": hasattr(response, 'user') if response else False, "user_type": str(type(response.user)) if response and hasattr(response, 'user') else None})
            # #endregion
            return response.user if response else None
        except Exception as e:
            # #region agent log
            _debug_log("C", "supabase_service.py:get_user:error", "Error getting user", {"error_type": str(type(e)), "error_msg": str(e)[:200]})
            # #endregion
            raise

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
    def table(self, table_name: str):
        """Get a table reference for queries."""
        return self.admin.table(table_name)

    async def insert(self, table_name: str, data: dict) -> Optional[dict]:
        # #region agent log
        _debug_log("F", "supabase_service.py:insert:entry", "Insert called", {"table": table_name, "data_keys": list(data.keys())})
        # #endregion
        try:
            response = self.admin.table(table_name).insert(data).execute()
            # #region agent log
            _debug_log("F", "supabase_service.py:insert:success", "Insert succeeded", {"has_data": bool(response.data)})
            # #endregion
            return response.data[0] if response.data else None
        except Exception as e:
            # #region agent log
            _debug_log("F", "supabase_service.py:insert:error", "Insert failed", {"error": str(e)[:300], "error_type": str(type(e))})
            # #endregion
            raise

    async def select(self, table_name: str, columns: str = "*", filters: Optional[dict] = None) -> list:
        # #region agent log
        _debug_log("D", "supabase_service.py:select:entry", "Select called", {"table": table_name, "filters": filters})
        _debug_log("G", "supabase_service.py:select:before_admin", "About to access self.admin", {"has_admin_attr": hasattr(self, '_admin')})
        # #endregion
        admin_client = self.admin
        # #region agent log
        _debug_log("G", "supabase_service.py:select:after_admin", "Got admin client", {"admin_type": str(type(admin_client))})
        # #endregion
        try:
            query = admin_client.table(table_name).select(columns)
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            response = query.execute()
            # #region agent log
            _debug_log("D", "supabase_service.py:select:success", "Select succeeded", {"count": len(response.data) if response.data else 0})
            # #endregion
            return response.data
        except Exception as e:
            # #region agent log
            _debug_log("D", "supabase_service.py:select:error", "Select failed", {"error": str(e)[:300], "error_type": str(type(e))})
            # #endregion
            raise

    async def update(self, table_name: str, data: dict, filters: dict) -> Optional[dict]:
        query = self.admin.table(table_name).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return response.data[0] if response.data else None

    async def delete(self, table_name: str, filters: dict) -> bool:
        query = self.admin.table(table_name).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return True


supabase_service = SupabaseService()
