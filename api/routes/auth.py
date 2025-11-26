"""
Endpoints de autenticación
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from api.database.config import get_session
from api.database.models import User, AdminLogin, AdminResponse, Token, UserRole
from api.services.auth_service import (
    authenticate_admin,
    get_user_by_id,
    create_access_token,
    decode_token,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ==================== DEPENDENCIAS ====================

async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Obtiene el admin actual desde el token JWT."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(session, token_data.user_id)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado"
        )
    
    return user


# ==================== ENDPOINTS ====================

@router.post("/login", response_model=Token, summary="Login de administrador")
async def login(
    credentials: AdminLogin,
    session: Session = Depends(get_session)
):
    """
    Autentica un administrador y devuelve un token JWT.
    """
    user = authenticate_admin(session, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value
    })
    
    return Token(
        access_token=token,
        user=AdminResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )
    )


@router.get("/me", response_model=AdminResponse, summary="Perfil del admin actual")
async def get_me(current_user: User = Depends(get_current_admin)):
    """Devuelve la información del administrador autenticado."""
    return AdminResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role
    )
