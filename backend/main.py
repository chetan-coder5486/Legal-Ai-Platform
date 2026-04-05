from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import upload
import threading

app = FastAPI(title="Legal AI Platform API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Legal AI Platform API Gateway is running."}

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(upload.router, prefix="/api", tags=["Documents"])

# Load model in background so server starts instantly
def preload_model():
    try:
        print("[startup] Loading ML model in background...")
        from backend.pipelines.contract_analyzer import get_model
        get_model()
        print("[startup] ML model ready.")
    except Exception as e:
        print(f"[startup] Model preload failed: {e}")

threading.Thread(target=preload_model, daemon=True).start()