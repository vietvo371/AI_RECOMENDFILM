from fastapi import FastAPI
from app.api import endpoints
from app.core.config import settings

app = FastAPI(
    title="Movie Chatbot API",
    description="AI Chatbot for movie recommendations",
    version="1.0.0"
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    # Initialize services
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Cleanup resources
    pass 