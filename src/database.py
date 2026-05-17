# src/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Reads your production string from env or falls back to your local Postgres port instance
DATABASE_URL = os.getenv(
    "LOGIKUR_DB_URL", 
    "postgresql://postgres:72826@localhost:5432/logikur_db"
)

# FIXED: Added pool_pre_ping to automatically repair dropped/stale connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FIXED: Imported declarative_base from standard sqlalchemy.orm to match modern compliance
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()