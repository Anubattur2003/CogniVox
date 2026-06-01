"""
Main FastAPI application setup.
"""
import os
import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from src.api.routes import router
from src.api.middleware import add_process_time_header
from src.utils.model_warmer import model_warmer
from src.utils.ollama_config import ollama_config

# Configure logging
log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
logging.basicConfig(level=log_level)
logger = logging.getLogger("cogniVox")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    # Load environment variables
    load_dotenv()
    
    # Initialize FastAPI app
    app = FastAPI(
        title="CogniVox API",
        description="Agentic Memory Chat System with multi-level memory and intelligent context management",
        version="1.0.0"
    )
    
    # CORS configuration
    if os.getenv("ENABLE_CORS", "TRUE").upper() == "TRUE":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify the allowed origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add performance middleware
    app.middleware("http")(add_process_time_header)
    
    # Error handling
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )
    
    # Include routes
    app.include_router(router)
    
    # Application lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Start background services on application startup."""
        logger.info("Starting CogniVox API application...")
        
        # Optimize Ollama for multi-model usage
        try:
            logger.info("Optimizing Ollama for multi-model usage...")
            required_models = ["mistral", "qwen3:4b"]
            results = ollama_config.optimize_for_multi_model_usage(required_models, "15m")
            successful = [model for model, success in results.items() if success]
            logger.info(f"Successfully preloaded models: {successful}")
        except Exception as e:
            logger.error(f"Failed to optimize Ollama: {str(e)}")
        
        # Start model warmer to prevent cold starts
        try:
            model_warmer.start_warming()
            logger.info("Model warmer started successfully")
        except Exception as e:
            logger.error(f"Failed to start model warmer: {str(e)}")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on application shutdown."""
        logger.info("Shutting down CogniVox API application...")
        
        # Stop model warmer
        try:
            model_warmer.stop_warming()
            logger.info("Model warmer stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop model warmer: {str(e)}")
    
    return app 