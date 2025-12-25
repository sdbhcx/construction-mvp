"""
Authentication schemas
"""
from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Login request schema
    """
    phone: str
    password: str


class PasswordResetRequest(BaseModel):
    """
    Password reset request schema
    """
    phone: str


class PasswordReset(BaseModel):
    """
    Password reset schema
    """
    new_password: str
    confirm_new_password: str
    token: str