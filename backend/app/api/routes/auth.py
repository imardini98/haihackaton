from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.auth import (
    SignUpRequest,
    SignInRequest,
    AuthResponse,
    UserResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordUpdateRequest
)
from app.services.supabase_service import supabase_service
from app.api.dependencies import get_current_user

security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """Register a new user."""
    try:
        response = await supabase_service.sign_up(request.email, request.password)

        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        return AuthResponse(
            access_token=response.session.access_token if response.session else "",
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Sign in an existing user."""
    try:
        response = await supabase_service.sign_in(request.email, request.password)

        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        return AuthResponse(
            access_token=response.session.access_token,
            user_id=response.user.id,
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email
    )


@router.post("/password-reset", response_model=PasswordResetResponse)
async def request_password_reset(request: PasswordResetRequest):
    """Request a password reset email."""
    try:
        await supabase_service.reset_password_for_email(request.email)
        return PasswordResetResponse(
            message="If an account exists with this email, a password reset link has been sent."
        )
    except Exception as e:
        # Don't reveal whether email exists or not for security
        return PasswordResetResponse(
            message="If an account exists with this email, a password reset link has been sent."
        )


@router.post("/password-update", response_model=PasswordResetResponse)
async def update_password(
    request: PasswordUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update password (requires valid access token from reset link)."""
    try:
        await supabase_service.update_user_password(
            access_token=credentials.credentials,
            new_password=request.new_password
        )
        return PasswordResetResponse(message="Password updated successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update password: {str(e)}"
        )
