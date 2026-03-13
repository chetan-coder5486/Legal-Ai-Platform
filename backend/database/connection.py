import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import chromadb

# PostgreSQL config (Fallback to SQLite for local ease if not provided)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./legal_ai.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ChromaDB Vector Store config
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vector_collection = chroma_client.get_or_create_collection(name="legal_cases")
