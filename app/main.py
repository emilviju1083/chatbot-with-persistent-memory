
from fastapi import FastAPI

from app.database import Base, engine
from app import models
from app.routers import chat

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title="Chatbot with Persistent Memory",
    description="An AI chatbot using FastAPI, PostgreSQL and Ollama",
    version="1.0.0"
)

# Register chat routes
app.include_router(chat.router)


@app.get("/")
def home():
    return {
        "message": "Welcome to the Chatbot with Persistent Memory API!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
 