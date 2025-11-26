"""
Servicio de autenticación  - Solo para admins.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select
from dotenv import load_dotenv
import os

load_dotenv()

from api.database.models import User, TokenData, UserRole

SECRET_KEY = os.getenv("SECRET_KEY", "chatbot-ucaldas-secret-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Debug: verificar que SECRET_KEY está cargada
if not os.getenv("SECRET_KEY"):
    print("⚠️ SECRET_KEY no configurada, usando valor por defecto")  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Crea un token JWT."""
    print(f"🔐 Creando token con SECRET_KEY: {SECRET_KEY[:10]}...")
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """Decodifica y valida un token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return TokenData(
            user_id=int(user_id),
            email=payload.get("email"),
            role=payload.get("role")
        )
    except JWTError as e:
        print(f"❌ Error JWT: {e}")
        return None


def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
    """Busca un usuario por ID."""
    return session.get(User, user_id)


def authenticate_admin(session: Session, email: str, password: str) -> Optional[User]:
    """Autentica un administrador con email y password."""
    statement = select(User).where(User.email == email, User.role == UserRole.ADMIN)
    user = session.exec(statement).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def create_default_admin(session: Session):
    """Crea el usuario admin por defecto si no existe."""
    statement = select(User).where(User.role == UserRole.ADMIN)
    if session.exec(statement).first():
        return  
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    
    if not admin_email or not admin_password:
        print("⚠️ Variables ADMIN_EMAIL y ADMIN_PASSWORD no configuradas en .env")
        return
    
    admin = User(
        email=admin_email,
        name="Administrador",
        role=UserRole.ADMIN,
        hashed_password=get_password_hash(admin_password)
    )
    session.add(admin)
    session.commit()
    print(f"✅ Admin creado: {admin_email}")

