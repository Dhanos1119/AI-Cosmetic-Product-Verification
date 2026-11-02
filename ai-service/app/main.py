import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes.analysis import router as analysis_router
from app.routes.auth import router as auth_router
from app.schemas.response import HealthResponse

app = FastAPI(
    title="CosmeticVerify AI Service",
    description="FastAPI AI Microservice for Cosmetic Product Verification, OCR, and Image Analysis",
    version="1.0.0"
)

# Parse allowed CORS origins from environment
default_origins = [
    "http://localhost:3000",
    "http://192.168.1.27:3000",
    "http://localhost:5000",
    "http://192.168.1.27:5000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5000"
]

env_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
allowed_origins = list(set([o.strip() for o in default_origins + env_origins if o.strip()]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler for Clean Error Formats
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": f"Server error: {str(exc)}"
        }
    )

# GET /health Endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def get_health():
    """
    GET /health check endpoint.
    """
    return {
        "status": "ok",
        "service": "AI Cosmetic Verification Service"
    }

# GET / Root Endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": "AI Cosmetic Verification Service",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "analyze": "/api/analyze (POST)"
        }
    }

# Register Routes
app.include_router(analysis_router)
app.include_router(auth_router)

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
