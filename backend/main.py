from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv(), encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import upload

app = FastAPI(title="Legal AI Platform API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
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
