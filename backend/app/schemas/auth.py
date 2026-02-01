from typing import Optional
from pydantic import BaseModel


class SignUpRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str


class SignInRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetResponse(BaseModel):
    message: str


class PasswordUpdateRequest(BaseModel):
    new_password: str
