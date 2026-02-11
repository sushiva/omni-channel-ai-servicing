"""
FastAPI Application for Omni-Channel AI Servicing.

Main entry point for the REST API that exposes customer service capabilities.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.api.routes import router
from src.monitoring.logger import get_logger

logger = get_logger("app.main")

# Create FastAPI application
app = FastAPI(
    title="Omni-Channel AI Servicing",
    description="""
    AI-powered customer service platform that automatically classifies, routes,
    and processes customer requests across multiple channels.
    
    ## Features
    - 🤖 Automatic intent classification
    - 🔀 Intelligent workflow routing
    - 🛡️ Policy enforcement and validation
    - 📧 Multi-channel support (email, chat, voice, mobile, web)
    - 📊 Full observability and tracing
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your security requirements
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    logger.info("Starting Omni-Channel AI Servicing application")
    logger.info("API documentation available at: /docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Omni-Channel AI Servicing application")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Omni-Channel AI Servicing",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "endpoints": {
            "service_request": "/api/v1/service-request",
            "health": "/health",
            "intents": "/api/v1/intents"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

