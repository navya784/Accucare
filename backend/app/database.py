import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Same folder convention as CHROMA_DIR in rag_engine.py - lives in backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, "cdss.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# check_same_thread=False is required for SQLite when used with FastAPI,
# since FastAPI can handle a request in a different thread than the one
# that created the connection. This is safe for SQLite in a dev/single-
# process setup like this one.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency - yields a DB session per-request and always
    closes it afterward, even if the request raises an exception."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()