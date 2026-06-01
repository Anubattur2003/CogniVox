"""
Middleware functions for the FastAPI application.
"""
import time
import logging
from fastapi import Request

# Configure performance logging
performance_logger = logging.getLogger('performance')
handler = logging.FileHandler('api_performance.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
performance_logger.addHandler(handler)
performance_logger.setLevel(logging.INFO)

async def add_process_time_header(request: Request, call_next):
    """
    Middleware to track API request processing time and add it to response headers.
    Also logs performance metrics.
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log API call performance
    performance_logger.info(
        f"API call to {request.url.path} took {process_time:.4f} seconds",
        extra={
            "path": request.url.path,
            "method": request.method,
            "process_time": process_time
        }
    )
    
    return response 