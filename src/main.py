from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from src.api.v1.router import api_router

app = FastAPI(
    title="DYGSOM Fraud API", description="Fraud detection API", version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {"message": "Welcome to DYGSOM Fraud API", "docs": "/docs"}


# Include API router
app.include_router(api_router, prefix="/api/v1")
