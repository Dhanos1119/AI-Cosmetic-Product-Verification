"""
Authentication API Router for FastAPI AI Service
Provides /api/auth/signup and /api/auth/login endpoints with database persistence.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from database.user_service import register_user, authenticate_user, init_user_table

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Ensure users table is initialized on router load
init_user_table()


class SignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    fullName: Optional[str] = Field(None, description="Full name of user")
    name: Optional[str] = Field(None, description="Alternative full name field")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_endpoint(payload: SignupRequest):
    """
    Registers a new user in the PostgreSQL database.
    Email is normalized with trim().lower().
    Password is securely hashed.
    """
    full_name = payload.fullName or payload.name or ""
    result = register_user(
        full_name=full_name,
        email=payload.email,
        password=payload.password
    )

    if not result.get("success"):
        status_code = result.get("status_code", status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_endpoint(payload: LoginRequest):
    """
    Authenticates an existing user against the PostgreSQL database.
    Verifies PBKDF2 password hash.
    """
    result = authenticate_user(
        email=payload.email,
        password=payload.password
    )

    if not result.get("success"):
        status_code = result.get("status_code", status.HTTP_401_UNAUTHORIZED)
        raise HTTPException(status_code=status_code, detail=result.get("message"))

    return result
