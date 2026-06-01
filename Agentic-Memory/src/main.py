"""
Main module for starting the FastAPI application.
"""
import uvicorn
import os
import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import router

# Configure logging with colored agent formatter
from src.utils.agent_logger import setup_agent_logger

# Setup main logger with colors
logger = setup_agent_logger("cogniVox", use_colors=True)

# Create the application
app = FastAPI(
    title="CogniVox API",
    description="AI Conversation API with memory functionality",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["chat"])

# Add global exception handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception in request {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred"}
    )

@app.on_event("startup")
async def startup_event():
    """Log when the application starts up"""
    logger.info("=" * 60)
    logger.info(f"  CogniVox - Agentic Memory System")
    logger.info("=" * 60)
    port = int(os.getenv("PORT", 8002))
    logger.info(f"Starting CogniVox Agentic Memory API on port {port}")
    logger.info("=" * 60)

if __name__ == "__main__":
    # Start the application with uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True) 
