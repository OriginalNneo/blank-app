from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from decouple import config

from app.routers import auth, budget, soa
from app.services.database import init_db

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    # Add any cleanup logic here if needed

app = FastAPI(
    title="TGYN Admin Portal API",
    description="Backend API for Teck Ghee Youth Network Admin Portal",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(budget.router, prefix="/api/budget", tags=["Budget"])
app.include_router(soa.router, prefix="/api/soa", tags=["SOA"])

@app.get("/")
async def root():
    return {"message": "TGYN Admin Portal API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(config("PORT", default=8000)),
        reload=True
    )