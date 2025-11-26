"""
Modelos de base de datos - Solo para administradores.
"""
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Roles disponibles."""
    ADMIN = "admin"


class User(SQLModel, table=True):
    """Modelo de administrador en la base de datos."""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    role: UserRole = Field(default=UserRole.ADMIN)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AdminLogin(SQLModel):
    """Schema para login de admin."""
    email: str
    password: str


class AdminResponse(SQLModel):
    """Respuesta con datos del admin (sin password)."""
    id: int
    email: str
    name: str
    role: UserRole


class Token(SQLModel):
    """Token JWT de respuesta."""
    access_token: str
    token_type: str = "bearer"
    user: AdminResponse


class TokenData(SQLModel):
    """Datos decodificados del token."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

