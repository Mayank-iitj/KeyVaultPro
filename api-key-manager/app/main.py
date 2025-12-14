"""
API Key Management System - Main Application
Designed & Engineered by Mayank Sharma
https://mayyanks.app

A production-ready, secure API key management system built with Python.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.utils.config import settings
from app.database.connection import init_db
from app.database.models import Base
from app.auth.routes import router as auth_router
from app.keys.routes import router as keys_router
from app.logs.routes import router as logs_router
from app.middleware.api_key_validator import APIKeyValidatorMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.utils.background_tasks import run_scheduled_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    task = asyncio.create_task(run_scheduled_tasks())
    
    yield
    
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="API Key Management System",
    description="""
    A production-ready, secure API key management system.
    
    **Designed & Engineered by Mayank Sharma**
    
    🌐 https://mayyanks.app
    
    ## Features
    - Secure API key generation and storage
    - Fine-grained permissions (read, write, delete, admin)
    - Rate limiting with token bucket algorithm
    - IP and user agent restrictions
    - Automatic key rotation with grace periods
    - Comprehensive audit logging
    - AI-assisted anomaly detection
    - RBAC (Admin, Developer, Read-Only)
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.add_middleware(RateLimiterMiddleware)
app.add_middleware(APIKeyValidatorMiddleware)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(keys_router, prefix="/api/v1")
app.include_router(logs_router, prefix="/api/v1")

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "API Key Manager",
        "version": "1.0.0"
    })


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "API Key Management System",
        "author": "Mayank Sharma",
        "website": "https://mayyanks.app"
    }


@app.get("/api/v1/protected/test")
async def protected_endpoint(request: Request):
    api_key_id = getattr(request.state, "api_key_id", None)
    permissions = getattr(request.state, "permissions", [])
    
    return {
        "message": "Access granted to protected resource",
        "api_key_id": api_key_id,
        "permissions": permissions
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Dashboard - API Key Manager"
    })


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
