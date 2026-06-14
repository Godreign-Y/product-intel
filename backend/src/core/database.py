"""Database connection and session helper for Neon PostgreSQL."""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We use the provided Neon URL as the primary database path
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_gdB67usHpOfx@ep-broad-tooth-aosvyt2m-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
)

# Configure SQLAlchemy engine with pool pinging enabled
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Session factory for local queries
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency generator to retrieve database sessions for API calls.

    Yields:
        Session: SQLAlchemy database session.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
