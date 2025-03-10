from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db.base import Base
import os

SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gridfinity:development@localhost/gridfinity_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Get a database session.
    This function intentionally does not accept any parameters to avoid issues with 
    FastAPI's dependency injection system passing unexpected parameters.
    The query parameters are filtered by a middleware before reaching this function.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()