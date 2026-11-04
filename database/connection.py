"""
Database Connection & Session Management Module
Configures SQLAlchemy engine, sessionmaker, and Base model.
Supports PostgreSQL (psycopg2) via DATABASE_URL or individual POSTGRES_* environment variables,
with fallback to SQLite for local development and unit testing.
"""

import os
import sys
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.resolve()
SITE_PACKAGES_DIR = BASE_DIR / "ai-service" / "venv" / "Lib" / "site-packages"

if str(BASE_DIR / "ai-service") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "ai-service"))
if SITE_PACKAGES_DIR.exists() and str(SITE_PACKAGES_DIR) not in sys.path:
    sys.path.insert(0, str(SITE_PACKAGES_DIR))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ai_env = BASE_DIR / "ai-service" / ".env"
root_env = BASE_DIR / ".env"

if ai_env.exists():
    load_dotenv(dotenv_path=ai_env)
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
load_dotenv()

pg_user = os.getenv("POSTGRES_USER")
pg_password = os.getenv("POSTGRES_PASSWORD")
pg_host = os.getenv("POSTGRES_HOST", "localhost")
pg_port = os.getenv("POSTGRES_PORT", "5432")
pg_db = os.getenv("POSTGRES_DB", "cosmetic_verification_db")

if os.getenv("DATABASE_URL"):
    DATABASE_URL = os.getenv("DATABASE_URL")
elif pg_user and pg_password and pg_db:
    DATABASE_URL = f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
else:
    DATABASE_URL = "sqlite:///data/cosmetic_verify.db"

# Handle Heroku/Supabase postgres:// scheme alias if present
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configure SQLite vs PostgreSQL connect args with resilient fallback
def _init_engine_and_db_url():
    global DATABASE_URL
    connect_args = {}
    if DATABASE_URL.startswith("postgresql"):
        try:
            test_engine = create_engine(
                DATABASE_URL,
                connect_args={"connect_timeout": 2},
                pool_pre_ping=True,
                echo=False
            )
            with test_engine.connect():
                pass
            return test_engine, DATABASE_URL
        except Exception as exc:
            sqlite_path = (BASE_DIR / "data" / "cosmetic_verify.db").resolve()
            sqlite_url = f"sqlite:///{sqlite_path}".replace("\\", "/")
            print(f"[DATABASE NOTICE] PostgreSQL connection failed ({exc}). Falling back to SQLite at {sqlite_url}")
            DATABASE_URL = sqlite_url
            connect_args = {"check_same_thread": False}
            fallback_engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
            return fallback_engine, DATABASE_URL
    else:
        connect_args["check_same_thread"] = False
        return create_engine(DATABASE_URL, connect_args=connect_args, echo=False), DATABASE_URL

engine, DATABASE_URL = _init_engine_and_db_url()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_masked_database_url() -> str:
    """Returns database URL with password masked for safe diagnostic reporting."""
    url = str(DATABASE_URL)
    return re.sub(r":([^:@]+)@", ":*****@", url)

def get_db():
    """FastAPI & Service dependency for DB session lifecycle management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
