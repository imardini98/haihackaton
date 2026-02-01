from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_service import supabase_service
import json, time

security = HTTPBearer()

# #region agent log
LOG_PATH = r"e:\Hackathon\odask\haihackaton\backend\debug.log"
def _debug_log(hyp, loc, msg, data=None):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps({"hypothesisId":hyp,"location":loc,"message":msg,"data":data,"timestamp":int(time.time()*1000),"sessionId":"debug-session"})+"\n")
        print(f"DEBUG: {loc} - {msg}")
    except Exception as ex:
        print(f"DEBUG_LOG_ERROR: {ex}")

_debug_log("INIT", "dependencies.py:module_load", "Module loaded at import time", {})
# #endregion


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Validate JWT token and return current user."""
    # #region agent log
    _debug_log("A", "dependencies.py:get_current_user:entry", "Function entered", {"has_credentials": credentials is not None})
    # #endregion
    token = credentials.credentials

    try:
        user = await supabase_service.get_user(token)
        # #region agent log
        _debug_log("B", "dependencies.py:get_current_user:after_get_user", "Got user from supabase", {"user_type": str(type(user)), "user_repr": repr(user)[:200], "has_id_attr": hasattr(user, 'id') if user else None})
        # #endregion
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return user
    except Exception as e:
        # #region agent log
        _debug_log("A", "dependencies.py:get_current_user:exception", "Exception occurred", {"error_type": str(type(e)), "error_msg": str(e)[:200]})
        # #endregion
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Optional auth - returns user if token provided, None otherwise."""
    if not credentials:
        return None

    try:
        return await supabase_service.get_user(credentials.credentials)
    except Exception:
        return None
