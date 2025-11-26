"""
Configuración de la base de datos SQLite con SQLModel.
"""
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

# Ruta de la base de datos SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/chatbot.db")

# Crear engine
engine = create_engine(
    DATABASE_URL, 
    echo=False,  
    connect_args={"check_same_thread": False}  
)


def create_db_and_tables():
    """Crea todas las tablas definidas en los modelos."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency para obtener una sesión de base de datos."""
    with Session(engine) as session:
        yield session

