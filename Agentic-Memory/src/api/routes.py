"""
API route handlers for the FastAPI application.
"""
import os
import time
import uuid
import logging
import requests
import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Header, Request
from datetime import datetime, timezone

from src.api.models import ChatMessage, ChatResponse, TranscriptionResponse
from src.api.dependencies import (
    chat_agent, 
    query_validator, 
    query_expander, 
    intent_classifier,
    profile_extractor,
    context_agent,
    supervisor_agent,
    summary_agent,
    enhancement_agent,
    title_agent,
    speech_to_text_agent,
    response_mode_router
)
from src.utils.model_warmer import model_warmer
from src.utils.ollama_config import ollama_config
from src.memory.chat_memory import chat_memory
from src.utils.execution_timer import execution_timer
from src.utils.thinking_tracker import thinking_tracker

# Configure logging
logger = logging.getLogger("cogniVox")

# Create router
router = APIRouter()

# Legacy function removed - now using Supervisor ReAct Agent
# which intelligently decides when to use GraphRAG tools vs direct responses

def _clean_document_title(title: str) -> str:
    """
    Clean document title to be business-appropriate without any technical details.
    
    Args:
        title: Raw document title
        
    Returns:
        Clean, business-friendly title
    """
    if not title:
        return "Company Document"
    
    import re
    
    # Remove any path components
    if "/" in title:
        title = title.split("/")[-1]
    
    # Remove file extensions
    title = re.sub(r'\.(pdf|docx?|txt|xlsx?|pptx?)$', '', title, flags=re.IGNORECASE)
    
    # Remove technical IDs and timestamps
    title = re.sub(r'_[a-f0-9]{6,}', '', title)  # hex IDs
    title = re.sub(r'_20\d{2}', '', title)  # years
    title = re.sub(r'_v?\d+\.?\d*', '', title)  # version numbers
    
    # Convert technical naming to business-friendly
    title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)  # camelCase to spaces
    title = title.replace("_", " ").replace("-", " ")  # underscores/hyphens to spaces
    title = re.sub(r'\s+', ' ', title)  # multiple spaces to single
    
    # Title case
    title = title.strip().title()
    
    # Handle common business document patterns
    title = re.sub(r'\bHr\b', 'HR', title)
    title = re.sub(r'\bIt\b', 'IT', title)
    title = re.sub(r'\bApi\b', 'API', title)
    title = re.sub(r'\bCeo\b', 'CEO', title)
    title = re.sub(r'\bCto\b', 'CTO', title)
    
    return title if title.strip() else "Company Document"

def _clean_document_content(content: str) -> str:
    """
    Clean document content to remove technical information while preserving meaning.
    
    Args:
        content: Raw document content
        
    Returns:
        Clean content without technical details
    """
    if not content:
        return content
    
    import re
    
    # Remove technical patterns that could leak infrastructure details
    technical_patterns = [
        r'gcp://[^\s"\')\]]+',
        r'https://storage\.googleapis\.com/[^\s"\')\]]+',
        r'https://[^\s"\')\]]*\?[A-Za-z0-9&=_%\-]+',  # URLs with parameters
        r'_[a-f0-9]{8,}',  # Document/file IDs
        r'/[^\s"\')*]+\.(?:pdf|docx?|txt|xlsx?|pptx?)',  # File paths
        r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b',  # UUIDs
        r'\bblob_[a-z0-9]+',  # blob names
        r'\bbucket[_\-]?[a-z0-9]+',  # bucket names
    ]
    
    for pattern in technical_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)
    
    # Clean up artifacts and ensure natural flow
    content = re.sub(r'\s+', ' ', content)
    content = re.sub(r'\(\s*\)', '', content)
    content = re.sub(r'\[\s*\]', '', content)
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r'\.\s*\.', '.', content)
    
    return content.strip()

def is_first_message_in_thread(chat_id: str, user_id: str) -> bool:
    """
    Check if this is the first message in a thread by looking at chat history.
    
    Args:
        chat_id: The chat ID to check
        user_id: The user ID for context
        
    Returns:
        True if this is the first message, False otherwise
    """
    if not chat_id or chat_id == 'unknown':
        return False
        
    try:
        # Check if there's any existing history for this chat
        # We need to check BEFORE the current message is stored
        history = chat_memory.get_chat_history(chat_id, limit=2)  # Get 2 to be safe
        
        # If no history exists or only 1 message (which could be the current one being processed)
        if not history or len(history) == 0:
            return True
        elif len(history) == 1:
            # If there's only 1 message, this could be the first message scenario
            # Check if it's a very recent message (within last 5 seconds) which indicates 
            # it might be the current message being processed
            try:
                last_message_time = history[0].get('timestamp')
                if last_message_time:
                    # Convert timestamp to datetime if it's a string
                    if isinstance(last_message_time, str):
                        last_message_time = datetime.fromisoformat(last_message_time.replace('Z', '+00:00'))
                    elif isinstance(last_message_time, dict) and '$date' in last_message_time:
                        last_message_time = datetime.fromisoformat(last_message_time['$date'].replace('Z', '+00:00'))
                    
                    # Ensure both datetimes are timezone-aware for proper comparison
                    current_time = datetime.now(timezone.utc)
                    if last_message_time.tzinfo is None:
                        last_message_time = last_message_time.replace(tzinfo=timezone.utc)
                    elif last_message_time.tzinfo != timezone.utc:
                        last_message_time = last_message_time.astimezone(timezone.utc)
                    
                    time_diff = current_time - last_message_time
                    if time_diff.total_seconds() < 10:  # Within 10 seconds
                        return True
            except Exception as e:
                logger.warning(f"Could not parse timestamp for first message detection: {str(e)}")
                # If we can't parse timestamp, treat as first message to be safe
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking if first message in thread {chat_id}: {str(e)}")
        # If we can't determine, assume it's the first message to ensure title generation
        return True





@router.get("/health") 
def health_check():
    """Check health of the API and dependencies with enhanced MongoDB monitoring and rate limiting"""
    # Add simple rate limiting to prevent health check spam
    import time
    current_time = time.time()
    if not hasattr(health_check, '_last_check'):
        health_check._last_check = 0
    
    # If called within 30 seconds, return cached result
    if current_time - health_check._last_check < 30:
        if hasattr(health_check, '_cached_result'):
            return health_check._cached_result
    
    health_check._last_check = current_time
    
    try:
        # Check MongoDB connection with detailed performance stats
        try:
            mongo_stats = chat_memory.get_mongodb_stats()
            mongo_health = chat_memory._check_mongodb_health()
            
            # Safely extract stats with defaults
            success_rate = mongo_stats.get('success_rate', 0.0)
            total_operations = mongo_stats.get('total_operations', 0)
            successful_operations = mongo_stats.get('successful_operations', 0)
            fallback_operations = mongo_stats.get('fallback_operations', 0)
            
            mongo_status = {
                "status": "healthy" if mongo_health else "unhealthy",
                "success_rate": f"{success_rate}%",
                "total_operations": total_operations,
                "successful_operations": successful_operations,
                "fallback_operations": fallback_operations,
                "meets_target": success_rate >= 85,
                "target": "85%+",
                "stats_status": mongo_stats.get('status', 'unknown')
            }
            
            # Add error info if present in stats
            if 'error' in mongo_stats:
                mongo_status['stats_error'] = mongo_stats['error']
                
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            mongo_status = {
                "status": "error",
                "error": str(e),
                "success_rate": "0%",
                "total_operations": 0,
                "successful_operations": 0,
                "fallback_operations": 0,
                "meets_target": False,
                "target": "85%+",
                "stats_status": "error"
            }
        
        # Check LLM service with better timeout handling
        llm_status = {}
        try:
            response = requests.get(
                f"{os.getenv('OLLAMA_API_BASE', 'http://localhost:11434')}/api/tags",
                timeout=5  # Increased timeout for health check
            )
            llm_status["status"] = "connected" if response.status_code == 200 else f"error: {response.status_code}"
        except requests.Timeout:
            llm_status["status"] = "error: connection timeout"
        except requests.ConnectionError:
            llm_status["status"] = "error: connection refused"
        except Exception as e:
            llm_status["status"] = f"error: {str(e)}"
            
        # Note: GraphRAG is now accessed through ReAct agent tools, not direct client
        
        # Check response mode router health
        router_health = response_mode_router.health_check()
        
        # Check model warmer status
        warmer_status = model_warmer.get_status()
        
        # Overall health status
        overall_healthy = (
            mongo_status.get("meets_target", False) and 
            "error" not in llm_status.get("status", "") and
            router_health.get("status") == "healthy"
        )
        
        result = {
            "status": "healthy" if overall_healthy else "degraded",
            "service": "CogniVox Memory API", 
            "mongodb_target_met": mongo_status.get("meets_target", False),
            "dependencies": {
                "mongodb": mongo_status,
                "llm_service": llm_status,
                "react_agent": "integrated - GraphRAG accessed via agent tools",
                "model_warmer": "running" if warmer_status["is_running"] else "stopped"
            },
            "response_modes": {
                "router_status": "healthy" if all(status.get("status") == "healthy" for status in router_health.values()) else "partial",
                "available_modes": list(router_health.keys()),
                "mode_details": router_health
            },
            "model_warming": {
                "service_status": "running" if warmer_status["is_running"] else "stopped",
                "models_to_warm": warmer_status["models_to_warm"],
                "warming_interval": warmer_status["warming_interval"],
                "last_warming": warmer_status["last_warming"]
            }
        }
        
        # Cache result for rate limiting
        health_check._cached_result = result
        return result
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/mongodb/stats")
def mongodb_stats():
    """Get detailed MongoDB performance statistics and health information"""
    try:
        stats = chat_memory.get_mongodb_stats()
        health = chat_memory._check_mongodb_health()
        
        # Calculate performance rating
        success_rate = stats['success_rate']
        if success_rate >= 85:
            performance_rating = "excellent"
            rating_emoji = "🟢"
        elif success_rate >= 70:
            performance_rating = "good"
            rating_emoji = "🟡"
        elif success_rate >= 50:
            performance_rating = "poor"
            rating_emoji = "🟠"
        else:
            performance_rating = "critical"
            rating_emoji = "🔴"
        
        return {
            "mongodb_health": {
                "status": "healthy" if health else "unhealthy",
                "performance_rating": f"{rating_emoji} {performance_rating}",
                "success_rate": f"{success_rate}%",
                "meets_target": success_rate >= 85,
                "target": "85%+"
            },
            "statistics": {
                "total_operations": stats['total_operations'],
                "successful_operations": stats['successful_operations'],
                "fallback_operations": stats['fallback_operations'],
                "retry_count": stats['retry_count'],
                "current_health": stats['current_health'],
                "last_health_check": stats['last_health_check']
            },
            "recommendations": [
                "MongoDB performing excellently ✅" if success_rate >= 85 else
                "MongoDB performance is acceptable but could be improved ⚠️" if success_rate >= 70 else
                "MongoDB performance is poor - check connection and database health ❌" if success_rate >= 50 else
                "CRITICAL: MongoDB performance is severely degraded - immediate attention required 🚨"
            ],
            "cache_info": {
                "cached_chats": len(chat_memory.memory_cache),
                "cache_status": "active"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting MongoDB stats: {str(e)}")
        return {
            "error": str(e),
            "mongodb_health": {
                "status": "error",
                "performance_rating": "🔴 unknown",
                "meets_target": False
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/mongodb/reconnect")
def mongodb_reconnect():
    """Force MongoDB reconnection attempt"""
    try:
        logger.info("🔄 Manual MongoDB reconnection requested")
        
        # Mark as unhealthy to force reconnection
        chat_memory.mongo_healthy = False
        
        # Attempt reconnection
        success = chat_memory._connect_mongodb_with_retry(max_attempts=3)
        
        stats = chat_memory.get_mongodb_stats()
        
        return {
            "reconnection_successful": success,
            "mongodb_status": "healthy" if success else "unhealthy",
            "current_stats": {
                "success_rate": f"{stats['success_rate']}%",
                "total_operations": stats['total_operations'],
                "meets_target": stats['success_rate'] >= 85
            },
            "message": "MongoDB reconnection successful ✅" if success else "MongoDB reconnection failed ❌",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during MongoDB reconnection: {str(e)}")
        return {
            "reconnection_successful": False,
            "error": str(e),
            "message": "MongoDB reconnection failed with error ❌",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(..., description="Audio file to transcribe (WAV, MP3, M4A, OGG, FLAC, WEBM)")
):
    """
    Transcribe audio file to text using Ollama's whisper-tiny model.
    
    This endpoint provides fast, accurate speech-to-text transcription using
    the locally hosted Ollama whisper model for complete offline functionality.
    """
    start_time = time.time()
    
    try:
        # Validate file upload
        if not audio_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No audio file provided"
            )
        
        # Check file size (limit to 25MB)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        if audio_file.size and audio_file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is 25MB, got {audio_file.size / (1024*1024):.1f}MB"
            )
        
        # Validate file format
        supported_formats = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm'}
        filename = audio_file.filename or "audio.wav"
        file_ext = filename.lower().split('.')[-1] if '.' in filename else 'wav'
        
        if f".{file_ext}" not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Read audio data
        logger.info(f"Processing audio file: {filename} ({audio_file.size} bytes)")
        audio_data = await audio_file.read()
        
        if not audio_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty audio file"
            )
        
        # Check if whisper model is available
        model_check = speech_to_text_agent.check_model_availability()
        if not model_check.get("available", False):
            # If model is not available, try to inform user about the setup
            available_models = model_check.get("all_models", [])
            error_detail = f"Whisper model 'dimavz/whisper-tiny' not found in Ollama. "
            
            if available_models:
                error_detail += f"Available models: {', '.join(available_models[:5])}. "
            
            error_detail += "Please run: 'ollama pull dimavz/whisper-tiny' to install the model."
            
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_detail
            )
        
        # Transcribe audio using the speech-to-text agent
        logger.info("Starting transcription...")
        transcription_result = speech_to_text_agent.transcribe_audio(audio_data, filename)
        
        # Check transcription success
        if not transcription_result.get("success", False):
            error_msg = transcription_result.get("error", "Transcription failed")
            logger.error(f"Transcription failed: {error_msg}")
            
            # Return partial result with error information
            return TranscriptionResponse(
                success=False,
                text="",
                processing_time=time.time() - start_time,
                model_used=speech_to_text_agent.whisper_model,
                error=error_msg
            )
        
        # Extract transcription data
        transcribed_text = transcription_result.get("text", "")
        confidence = transcription_result.get("confidence")
        language = transcription_result.get("language")
        processing_time = transcription_result.get("processing_time", time.time() - start_time)
        file_size_mb = transcription_result.get("file_size_mb")
        
        logger.info(f"Transcription successful: {len(transcribed_text)} characters in {processing_time:.2f}s")
        
        # Return successful transcription
        return TranscriptionResponse(
            success=True,
            text=transcribed_text,
            confidence=confidence,
            language=language,
            processing_time=processing_time,
            file_size_mb=file_size_mb,
            model_used=speech_to_text_agent.whisper_model
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Handle unexpected errors
        error_msg = f"Transcription service error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return TranscriptionResponse(
            success=False,
            text="",
            processing_time=time.time() - start_time,
            model_used=speech_to_text_agent.whisper_model,
            error=error_msg
        )

@router.get("/transcribe/status")
def transcribe_status():
    """
    Check the status of the transcription service and whisper model availability.
    """
    try:
        # Check model availability
        model_check = speech_to_text_agent.check_model_availability()
        
        # Get supported formats
        supported_formats = speech_to_text_agent.get_supported_formats()
        
        return {
            "service": "Speech-to-Text Transcription",
            "status": "available" if model_check.get("available", False) else "unavailable",
            "model": speech_to_text_agent.whisper_model,
            "model_available": model_check.get("available", False),
            "supported_formats": supported_formats,
            "max_file_size_mb": speech_to_text_agent.max_file_size_mb,
            "ollama_url": speech_to_text_agent.ollama_base_url,
            "all_models": model_check.get("all_models", [])[:10],  # Limit to first 10 models
            "setup_command": "ollama pull dimavz/whisper-tiny" if not model_check.get("available", False) else None
        }
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return {
            "service": "Speech-to-Text Transcription",
            "status": "error",
            "error": str(e)
        }

@router.post("/chat", response_model=ChatResponse)
def chat(
    http_request: Request,
    request: ChatMessage,
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """Process a chat message and return a response with GPU acceleration and performance monitoring"""
    # Import performance monitoring utilities
    from ..utils.performance_monitor import performance_monitor, gpu_accelerator, measure_performance
    
    start_time = time.time()
    
    user_id = request.user_id
    original_query = request.message
    response_mode = request.response_mode or "general"  # Default to general mode
    user_details = request.user_details or {}
    
    # Extract auth_token from multiple sources (payload, header parameter, or request headers)
    auth_token = request.auth_token
    
    # Try header parameter
    if not auth_token and authorization:
        # Extract token from "Bearer <token>" format
        if authorization.startswith("Bearer "):
            auth_token = authorization[7:]
    
    # Try direct request headers as fallback (check all possible header name variations)
    if not auth_token and http_request:
        # FastAPI normalizes headers - try multiple variations
        auth_header = (
            http_request.headers.get("Authorization") or 
            http_request.headers.get("authorization") or
            http_request.headers.get("AUTHORIZATION")
        )
        if auth_header and auth_header.startswith("Bearer "):
            auth_token = auth_header[7:]
        elif auth_header and not auth_header.startswith("Bearer "):
            # Sometimes header might not have Bearer prefix
            auth_token = auth_header
    
    # Debug logging for auth_token extraction
    if auth_token:
        logger.info(f"Extracted auth_token for user {user_id} (length: {len(auth_token)}, starts with: {auth_token[:10]}...)")
    else:
        logger.warning(f"No auth_token found for user {user_id}")
        logger.debug(f"  - request.auth_token: {request.auth_token}")
        logger.debug(f"  - authorization header param: {'present' if authorization else 'missing'}")
        if http_request:
            # Log all headers for debugging
            all_headers = dict(http_request.headers)
            auth_related = {k: v[:50] + "..." if len(v) > 50 else v for k, v in all_headers.items() if 'auth' in k.lower()}
            logger.debug(f"  - All auth-related headers: {auth_related}")
            logger.debug(f"  - All headers keys: {list(all_headers.keys())[:10]}...")
    
    # Add auth_token to user_details for passing to agents
    if auth_token:
        user_details['auth_token'] = auth_token
    
    # Extract chat_id from user_details if available
    chat_id = user_details.get('chat_id', 'unknown')
    
    # Extract n_results parameter if provided
    n_results = user_details.get('n_results', 20)  # Default to 20 for better context coverage
    
    # Basic request logging
    logger.info(f"Processing chat request for user {user_id}, chat {chat_id}, response_mode: {response_mode}")
            
    # Basic empty query check only - agents will handle detailed validation
    if not original_query or not original_query.strip():
        logger.warning("Empty query received")
        return ChatResponse(
            response="Please provide a non-empty query.",
            response_time=time.time() - start_time,
            variants={"summary": "Please provide a non-empty query."},
            chat_id=chat_id,
            sources=[],
            source_found=False
        )
            
    # Performance optimizations based on response mode
    performance_note = ""
    if response_mode == "general":
        performance_note = " (optimized: minimal context, no tools)"
    elif response_mode == "thinking":  
        performance_note = " (optimized: structured thinking, context on demand)"
    elif response_mode == "agentic":
        performance_note = " (full features: tools, reasoning, context)"
        
    logger.info(f"Processing {response_mode} mode{performance_note} - title gen disabled for speed")

    # Step 2: Prepare context for the selected agent (validation now handled in prompts for performance)
    try:
        # Start thinking tracking for frontend (only for modes that support it)
        thinking_session = None
        if response_mode in ["thinking", "agentic"]:
            thinking_session = thinking_tracker.start_thinking(
                user_id=user_id,
                    process_type=f"{response_mode}_processing",
                    description=f"Processing your question using {response_mode} mode..."
            )
            logger.info(f"Started thinking tracking for {response_mode} mode")
        
        # Add user context from user_details if query is about personal context
        context_prompt = ""
        personal_info_prompt = ""
        
        # Include personal context only if the query relates to user-specific information
        lower_query = original_query.lower()
        personal_context_keywords = ["subscription", "plan", "account", "profile", "role", "username"]
        is_personal_context_question = any(keyword in lower_query for keyword in personal_context_keywords)
        if user_details and is_personal_context_question:
            # Add context about the user
            user_context = [
                f"User ID: {user_id}",
                f"Username: {user_details.get('username', 'Unknown')}",
                f"Role: {user_details.get('role', 'user')}",
                f"Model: {user_details.get('model_name', 'Unknown')}",
                f"Chat ID: {chat_id}"
            ]
            personal_info_prompt = "USER CONTEXT:\n" + "\n".join(user_context)
            
            # Extract subscription information if available
            if user_details.get('subscription_plan'):
                personal_info_prompt += f"\nSubscription: {user_details.get('subscription_plan')}"
        
        # Update thinking state if active
        if thinking_session:
            thinking_tracker.update_thinking_step(
                thinking_session,
                "context_preparation",
                "Gathering conversation history and context in parallel..."
            )
        
        # PARALLEL PROCESSING OPTIMIZATION: Context fetching and agent preparation
        import concurrent.futures
        import time as perf_time
        
        context_prompt = personal_info_prompt
        context_fetch_time = 0
        
        # Parallel context fetching for faster response times
        def fetch_context_parallel():
            nonlocal context_prompt, context_fetch_time
            context_start = perf_time.time()
            
            if chat_id != 'unknown':
                # Only fetch history if needed (saves time for general mode)
                lower_query = original_query.lower()
                needs_history = (
                    response_mode in ["thinking", "agentic"] or  # Always for complex modes
                    any(term in lower_query for term in [  # Or if query references conversation
                        "previous", "earlier", "before", "last time", "last question",
                        "you said", "i said", "i asked", "i mentioned", "we discussed",
                        "history", "conversation"
                    ])
                )
                
                if needs_history:
                    # Get chat history context with GPU acceleration if available
                    history_context = context_agent.get_context(chat_id, user_id)
                    
                    if history_context:
                        context_prompt = f"{history_context}\n\n{personal_info_prompt}"
                        
            context_fetch_time = perf_time.time() - context_start
            logger.info(f"⚡ Context fetching completed in {context_fetch_time*1000:.1f}ms")
            return context_prompt
        
        def warm_up_agents():
            """Pre-warm agents to reduce cold start latency"""
            warm_start = perf_time.time()
            try:
                # Pre-initialize response mode router if not already done
                _ = response_mode_router.agents.get(response_mode)
                warm_time = perf_time.time() - warm_start
                logger.info(f"⚡ Agent warm-up completed in {warm_time*1000:.1f}ms")
                return True
            except Exception as e:
                logger.warning(f"⚠️ Agent warm-up failed: {e}")
                return False
        
        # Execute context fetching and agent warm-up in parallel
        parallel_start = perf_time.time()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"context_prep_{user_id}") as executor:
                context_future = executor.submit(fetch_context_parallel)
                warmup_future = executor.submit(warm_up_agents)
                
                # Wait for both operations with timeout
                context_prompt = context_future.result(timeout=5.0)
                warmup_result = warmup_future.result(timeout=2.0)
                
                parallel_time = perf_time.time() - parallel_start
                logger.info(f"⚡ Parallel context preparation completed in {parallel_time*1000:.1f}ms")
                
        except concurrent.futures.TimeoutError:
            logger.warning("⏰ Context preparation timeout, using fallback")
            context_prompt = personal_info_prompt
        except Exception as e:
            logger.warning(f"⚠️ Parallel context preparation failed: {e}, using fallback")
            context_prompt = personal_info_prompt
            
        # Add meta-question hint if needed for context-aware queries
        lower_query = original_query.lower()
        if any(term in lower_query for term in ["previous", "earlier", "you said", "i said"]):
            context_prompt += "\n\nIMPORTANT: The current query is asking about previous messages. Be sure to refer directly to the content in the conversation history above."
        
        # Update thinking state if active
        if thinking_session:
            thinking_tracker.update_thinking_step(
                thinking_session,
                "agent_processing",
                f"Processing with {response_mode} mode agent..."
            )
        
        # Step 3: Use Response Mode Router to process the query with performance monitoring
        with performance_monitor.measure_operation(
            operation_name="agent_processing",
            user_id=user_id,
            gpu_used=gpu_accelerator.enabled,
            parallel=True,
            metadata={"response_mode": response_mode, "chat_id": chat_id}
        ):
            router_result = response_mode_router.route_query(
                response_mode=response_mode,
                user_message=original_query,
                user_id=user_id,
                context_prompt=context_prompt,
                chat_id=chat_id,
                n_results=n_results,
                auth_token=auth_token  # Pass auth_token for MCP server access
            )
        
        # Check if routing was successful
        if not router_result.get("success", False):
            raise Exception(router_result.get("error", "Router processing failed"))
        
        # Extract results from router
        final_response = router_result.get("response", "I apologize, but I couldn't generate a proper response.")
        thinking_steps = router_result.get("thinking_steps", [])
        used_tools = router_result.get("used_tools", [])
        source_documents = router_result.get("sources", [])
        response_variants = router_result.get("variants", {
            "summary": final_response[:200] + "..." if len(final_response) > 200 else final_response,
            "detailed": final_response
        })
        
        # Log tool usage for monitoring
        if used_tools:
            logger.info(f"🔧 Tools used in this request: {', '.join(used_tools)}")
        else:
            logger.warning(f"⚠️ NO TOOLS USED - Agent responded directly from pretrained knowledge")
        
        # Debug logging for router results
        logger.info(f"Router result keys: {list(router_result.keys())}")
        logger.info(f"Response mode: {response_mode}")
        logger.info(f"Agent type: {router_result.get('agent_type', 'unknown')}")
        logger.info(f"Used tools: {used_tools}")
        logger.info(f"Source documents count: {len(source_documents)}")
        if source_documents:
            logger.info(f"First source keys: {list(source_documents[0].keys()) if source_documents[0] else 'None'}")
        
        # Update thinking state if active
        if thinking_session:
            thinking_tracker.update_thinking_step(
                thinking_session,
                "response_formatting",
                "Formatting response and extracting sources..."
            )
        
        # Only enhance thinking mode when tools are used (skip general mode for speed)
        if response_mode == "thinking" and used_tools:
            # Enhance the detailed response using the ResponseEnhancementAgent
            enhanced_detailed_response = enhancement_agent.enhance_response(final_response, used_tools, source_documents)
            final_response = enhanced_detailed_response
            
            # Generate a crisp summary from the detailed response using the SummaryGenerationAgent
            crisp_summary = summary_agent.generate_summary(enhanced_detailed_response, original_query)
            
            # Update response variants
            response_variants = {
                "summary": crisp_summary,
                "detailed": enhanced_detailed_response
            }
        else:
            # For other modes or when no tools were used, use the original response
            response_variants = {
                "summary": final_response[:200] + "..." if len(final_response) > 200 else final_response,
                "detailed": final_response
            }
        
        # Format source documents for frontend
        formatted_sources = []
        graphrag_used = "graphrag_search" in used_tools
        document_relevant = router_result.get("document_relevant", False)
        
        logger.info(f"GraphRAG used: {graphrag_used}, document_relevant: {document_relevant}")
        
        if graphrag_used and source_documents:
            logger.info(f"Processing {len(source_documents)} source documents from ReAct agent")
            
            # INTELLIGENT SOURCE FILTERING: Use structured document_relevant flag from agent
            # If document_relevant is False, don't include sources even if they exist
            if not document_relevant:
                logger.info(f"Agent determined sources are NOT relevant (document_relevant=False) - clearing {len(source_documents)} sources")
                formatted_sources = []
            else:
                # Documents are relevant, format them for frontend
                for source in source_documents:
                    # Keep ALL source document metadata for frontend functionality
                    # Only clean the document title for better UI display
                    formatted_source = {
                        "document_title": _clean_document_title(source.get("document_title", "Company Document")),
                        "content": source.get("content", ""),
                        "page": source.get("page", None),
                        "relevance": source.get("relevance", 0.0),
                        "file_path": source.get("file_path", ""),
                        "download_url": source.get("download_url", "")
                    }
                    
                    # Only include sources with actual content
                    if formatted_source["content"].strip():
                        formatted_sources.append(formatted_source)
                
                logger.info(f"Formatted {len(formatted_sources)} relevant source documents for frontend")
        
        elif graphrag_used and not source_documents:
            # GraphRAG was used but no sources were returned
            logger.info("GraphRAG tool was used but no source documents were returned")
        
        # Log final source status
        if not formatted_sources and graphrag_used:
            logger.info("GraphRAG tool was used but no valid/relevant source documents were included")
        
        # CRITICAL: Log exactly what's being sent to frontend for debugging
        logger.info(f"📤 FRONTEND RESPONSE SUMMARY:")
        logger.info(f"   - source_found: {document_relevant}")
        logger.info(f"   - sources count: {len(formatted_sources)}")
        logger.info(f"   - tools used: {used_tools if used_tools else 'None'}")
        
        if formatted_sources:
            logger.info(f"📤 Sending {len(formatted_sources)} RELEVANT sources to frontend:")
            for idx, src in enumerate(formatted_sources[:3]):  # Log first 3
                logger.info(f"   {idx+1}. {src.get('document_title', 'Unknown')} (page {src.get('page', 'N/A')})")
        else:
            if "graphrag_search" in used_tools:
                logger.info(f"📤 GraphRAG used but NO RELEVANT sources (source_found={document_relevant})")
            else:
                logger.info(f"📤 Direct response - no knowledge base search performed")
        
        # Store the interaction in the memory system for future context
        # Only if we have a valid chat_id (simplified for general mode)
        if chat_id != 'unknown':
            # Create lightweight metadata for general mode, detailed for others
            if response_mode == "general":
                metadata = {
                    "agent_type": "general_response",
                    "response_mode": "general",
                    "model": "mistral"
                }
            else:
                metadata = {
                    "agent_type": router_result.get("agent_type", response_mode),
                    "response_mode": response_mode,
                    "model": user_details.get('model_name', 'mistral'),
                    "tools_used": used_tools,
                    "graphrag_used": "graphrag_search" in used_tools,
                    "thinking_steps": len(thinking_steps)
                }
            
            # Store the interaction in the memory system with performance monitoring
            with performance_monitor.measure_operation(
                operation_name="memory_storage",
                user_id=user_id,
                gpu_used=False,  # Memory storage is CPU-based
                parallel=False,
                metadata={"chat_id": chat_id, "response_mode": response_mode}
            ):
                if chat_id != 'unknown':
                    context_agent.store_interaction(
                        chat_id=chat_id,
                        user_id=user_id,
                        message=original_query,
                        response=final_response,
                        metadata=metadata
                    )

                    print("MEMORY STATS:", context_agent.chat_memory.get_stats())
        
        # Finish thinking tracking if active
        if thinking_session:
            thinking_tracker.finish_thinking(
                thinking_session,
                final_result=final_response,
                success=True
            )
            
        # Calculate response time
        response_time = time.time() - start_time
            
        # Title generation disabled for performance optimization
        # Titles can be generated on frontend if needed
        generated_title = None
        logger.info("Title generation skipped for faster response times")
        
        # Format thinking steps for response
        formatted_thinking_steps = []
        for step in thinking_steps:
            formatted_thinking_steps.append({
                "type": step.get("type", "thought"),
                "content": step.get("content", ""),
                "timestamp": step.get("timestamp")
            })
        
        # FINAL SAFETY CHECK: Ensure sources are empty if document_relevant is False
        # This is the last line of defense before sending to frontend
        if not document_relevant and formatted_sources:
            logger.warning(f"⚠️ SAFETY CHECK: Clearing {len(formatted_sources)} sources because document_relevant=False")
            formatted_sources = []
        
        # Return formatted response with router information
        return ChatResponse(
            response=final_response,  # Use final response from router
            response_time=response_time,
            variants=response_variants,
            chat_id=chat_id,
            sources=formatted_sources,  # Guaranteed to be [] when document_relevant=False
            source_found=document_relevant,  # Boolean flag from GraphRAG
            generated_title=generated_title,
            thinking_steps=formatted_thinking_steps,
            used_tools=used_tools,
            agent_type=router_result.get("agent_type", response_mode)
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        
        # Update thinking tracker with error
        try:
            current_thinking = thinking_tracker.get_current_thinking(user_id)
            if current_thinking:
                thinking_tracker.finish_thinking(
                    current_thinking["session_id"], 
                    success=False
                )
        except:
            pass  # Don't let thinking tracker errors block error response
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )

@router.get("/chat/{chat_id}/history")
def get_chat_history(chat_id: str, limit: int = 20):
    """
    Retrieve chat history for a specific chat_id.
    
    Args:
        chat_id: The unique identifier for the chat
        limit: Maximum number of messages to retrieve
    """
    if not chat_id or chat_id == 'unknown':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid chat_id is required"
        )
    
    try:
        # Get chat history from the memory system
        history = chat_memory.get_chat_history(chat_id, limit)
        
        return {
            "chat_id": chat_id,
            "message_count": len(history),
            "history": history
        }
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.delete("/chat/{chat_id}/history")
def clear_chat_history(chat_id: str):
    """
    Clear chat history for a specific chat_id.
    
    Args:
        chat_id: The unique identifier for the chat
    """
    if not chat_id or chat_id == 'unknown':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid chat_id is required"
        )
    
    try:
        # Clear chat history from the memory system
        success = chat_memory.clear_chat_history(chat_id)
        
        if success:
            return {"status": "success", "message": f"Chat history for {chat_id} has been cleared"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to clear chat history"
            )
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat history: {str(e)}"
        )

@router.get("/memory/stats")
def get_memory_stats():
    """Get statistics about the memory system."""
    try:
        return chat_memory.get_stats()
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory stats: {str(e)}"
        )

@router.post("/chat/{chat_id}/sync")
def sync_chat_history(chat_id: str):
    """
    Force a synchronization of the chat history from MongoDB to local memory.
    This is useful when you want to ensure the latest context is available.
    
    Args:
        chat_id: The unique identifier for the chat
    """
    if not chat_id or chat_id == 'unknown':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid chat_id is required"
        )
    
    try:
        # Force refresh from MongoDB by clearing local cache first
        chat_memory.clear_chat_history(chat_id)
        
        # Get history from MongoDB
        history = chat_memory.get_chat_history_mongo(chat_id)
        
        return {
            "chat_id": chat_id,
            "synced_messages": len(history),
            "status": "success" if history else "no_messages_found"
        }
    except Exception as e:
        logger.error(f"Error syncing chat history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync chat history: {str(e)}"
        )

@router.get("/thinking/{user_id}")
def get_thinking_state(user_id: str):
    """
    Get the current thinking state for a user.
    
    Args:
        user_id: The user identifier
        
    Returns:
        Current thinking state or None if no active thinking
    """
    try:
        thinking_state = thinking_tracker.get_current_thinking(user_id)
        
        if thinking_state:
            return {
                "user_id": user_id,
                "thinking": thinking_state,
                "has_active_thinking": True
            }
        else:
            return {
                "user_id": user_id,
                "thinking": None,
                "has_active_thinking": False
            }
    except Exception as e:
        logger.error(f"Error getting thinking state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get thinking state: {str(e)}"
        )

@router.delete("/thinking/{user_id}")
def clear_thinking_state(user_id: str):
    """
    Clear thinking state for a user.
    
    Args:
        user_id: The user identifier
    """
    try:
        thinking_tracker.clear_user_thinking(user_id)
        
        return {
            "user_id": user_id,
            "status": "cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing thinking state: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear thinking state: {str(e)}"
        )

@router.get("/response-modes")
def get_response_modes():
    """
    Get information about available response modes and their capabilities.
    """
    try:
        available_modes = response_mode_router.get_available_modes()
        router_health = response_mode_router.health_check()
        
        return {
            "available_modes": available_modes,
            "health_status": router_health,
            "default_mode": "general",
            "supported_modes": ["general", "thinking", "agentic"]
        }
        
    except Exception as e:
        logger.error(f"Error getting response modes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response modes: {str(e)}"
        )

@router.post("/generate-title")
def generate_title_endpoint(request: dict):
    """
    Generate a title for a thread based on response and query.
    
    Expected request format:
    {
        "response": "The AI response text",
        "query": "The original user query",
        "chat_id": "The chat ID for logging"
    }
    """
    try:
        response_text = request.get("response", "")
        query_text = request.get("query", "")
        chat_id = request.get("chat_id", "unknown")
        
        if not response_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Response text is required for title generation"
            )
        
        title = title_agent.generate_title(response_text, query_text)
        
        return {
            "title": title,
            "chat_id": chat_id,
            "status": "success"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in title generation endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate title: {str(e)}"
        )

@router.get("/models/warmer/status")
def get_model_warmer_status():
    """
    Get the current status of the model warmer service.
    """
    try:
        status = model_warmer.get_status()
        return {
            "service": "Model Warmer",
            "status": "running" if status["is_running"] else "stopped",
            **status
        }
    except Exception as e:
        logger.error(f"Error getting model warmer status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model warmer status: {str(e)}"
        )

@router.post("/models/warmer/warm/{model_name}")
def warm_model_immediately(model_name: str):
    """
    Immediately warm a specific model to prevent cold start delays.
    
    Args:
        model_name: Name of the model to warm (mistral, qwen3:4b, etc.)
    """
    try:
        start_time = time.time()
        model_warmer.warm_model_immediately(model_name)
        warm_time = time.time() - start_time
        
        return {
            "model": model_name,
            "status": "warmed",
            "warming_time": round(warm_time, 3),
            "message": f"Model {model_name} warmed successfully"
        }
    except Exception as e:
        logger.error(f"Error warming model {model_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm model {model_name}: {str(e)}"
        )

@router.post("/models/warmer/warm-all")
def warm_all_models():
    """
    Immediately warm all registered models to prevent cold start delays.
    """
    try:
        start_time = time.time()
        model_warmer._warm_all_models()
        warm_time = time.time() - start_time
        
        status = model_warmer.get_status()
        
        return {
            "status": "all_models_warmed",
            "models": status["models_to_warm"],
            "total_warming_time": round(warm_time, 3),
            "last_warming": status["last_warming"],
            "message": "All models warmed successfully"
        }
    except Exception as e:
        logger.error(f"Error warming all models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to warm all models: {str(e)}"
        )

@router.get("/models/loaded")
def get_loaded_models():
    """
    Get currently loaded models from Ollama.
    """
    try:
        loaded_models = ollama_config.get_loaded_models()
        return {
            "service": "Ollama Model Status",
            "loaded_models": loaded_models.get("models", []),
            "count": len(loaded_models.get("models", [])),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting loaded models: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get loaded models: {str(e)}"
        )

@router.post("/models/optimize")
def optimize_ollama():
    """
    Optimize Ollama for multi-model usage by preloading all required models.
    """
    try:
        required_models = ["mistral", "qwen3:4b"]
        keep_alive = "15m"  # Keep models loaded for 15 minutes
        
        start_time = time.time()
        results = ollama_config.optimize_for_multi_model_usage(required_models, keep_alive)
        optimization_time = time.time() - start_time
        
        successful_models = [model for model, success in results.items() if success]
        failed_models = [model for model, success in results.items() if not success]
        
        return {
            "status": "optimization_complete",
            "optimization_time": round(optimization_time, 3),
            "required_models": required_models,
            "keep_alive": keep_alive,
            "results": results,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "success_rate": f"{len(successful_models)}/{len(required_models)}",
            "message": f"Optimized {len(successful_models)} out of {len(required_models)} models"
        }
    except Exception as e:
        logger.error(f"Error optimizing Ollama: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize Ollama: {str(e)}"
        )

@router.get("/performance/stats")
def get_performance_stats():
    """Get comprehensive performance statistics including GPU acceleration"""
    try:
        from ..utils.performance_monitor import performance_monitor, gpu_accelerator
        
        stats = performance_monitor.get_performance_stats()
        
        # Add GPU information
        gpu_info = {
            "gpu_enabled": gpu_accelerator.enabled,
            "gpu_device": str(gpu_accelerator.device) if gpu_accelerator.device else None,
            "rtx_3050_optimizations": gpu_accelerator.enabled
        }
        
        return {
            "service": "Performance Monitoring",
            "status": "success",
            "performance_stats": stats,
            "gpu_info": gpu_info,
            "optimization_summary": {
                "memory_operations": "Ultra-fast caching enabled",
                "gpu_acceleration": "RTX 3050 enabled" if gpu_accelerator.enabled else "CPU only",
                "parallel_processing": "Active",
                "timeout_optimization": "GraphRAG timeout increased to 600s",
                "expected_improvement": "90% faster responses (250s → 15-25s)"
            }
        }
    except Exception as e:
        logger.error(f"Error getting performance stats: {str(e)}")
        return {
            "service": "Performance Monitoring",
            "status": "error",
            "error": str(e)
        }

@router.get("/performance/metrics")
def get_recent_metrics():
    """Get recent performance metrics for analysis"""
    try:
        from ..utils.performance_monitor import performance_monitor
        
        metrics = performance_monitor.get_recent_metrics(limit=100)
        
        return {
            "service": "Performance Metrics",
            "status": "success",
            "recent_metrics": metrics,
            "total_metrics": len(metrics)
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return {
            "service": "Performance Metrics",
            "status": "error",
            "error": str(e)
        }

@router.post("/performance/clear")
def clear_performance_metrics():
    """Clear all performance metrics"""
    try:
        from ..utils.performance_monitor import performance_monitor
        
        performance_monitor.clear_metrics()
        
        return {
            "service": "Performance Metrics",
            "status": "success",
            "message": "All performance metrics cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing performance metrics: {str(e)}")
        return {
            "service": "Performance Metrics",
            "status": "error",
            "error": str(e)
        }

@router.post("/chat/stream")
async def chat_stream(request: Request, chat_message: ChatMessage):
    """
    Stream chat response token-by-token using Server-Sent Events (SSE).
    """
    from sse_starlette.sse import EventSourceResponse
    
    async def event_generator():
        # Yield starting status
        yield {"event": "status", "data": json.dumps({"status": "starting", "message": "Initiating agent..."})}
        
        if chat_message.response_mode == "general":
            try:
                agent = response_mode_router.agents.get("general")
                from ..agents.general_response_agent.prompt import GENERAL_RESPONSE_PROMPT
                from langchain_core.messages import HumanMessage, SystemMessage
                
                # Setup context
                context_prompt = ""
                if chat_message.user_details:
                    user_id = chat_message.user_id
                    chat_id = chat_message.user_details.get("chat_id", "unknown")
                    if chat_id != 'unknown':
                        history_context = context_agent.get_context(chat_id, user_id)
                        if history_context:
                            context_prompt = history_context
                
                system_message = SystemMessage(content=GENERAL_RESPONSE_PROMPT.format(
                    context_prompt=context_prompt if context_prompt else "No additional context provided.",
                    user_message=""
                ))
                user_msg = HumanMessage(content=chat_message.message)
                
                yield {"event": "status", "data": json.dumps({"status": "generating", "message": "Generating response..."})}
                
                # Stream from langchain LLM
                if hasattr(agent.llm, "astream"):
                    async for chunk in agent.llm.astream([system_message, user_msg]):
                        yield {"event": "token", "data": json.dumps({"token": chunk.content})}
                else:
                    # Fallback to sync stream
                    for chunk in agent.llm.stream([system_message, user_msg]):
                        yield {"event": "token", "data": json.dumps({"token": chunk.content})}
                        
            except Exception as e:
                logger.error(f"Error in streaming general response: {str(e)}")
                yield {"event": "error", "data": json.dumps({"error": str(e)})}
        else:
            # Thinking and Agentic modes run query routing and stream steps
            try:
                import anyio
                yield {"event": "status", "data": json.dumps({"status": "thinking", "message": f"Running {chat_message.response_mode} workflow..."})}
                
                context_prompt = ""
                if chat_message.user_details:
                    user_id = chat_message.user_id
                    chat_id = chat_message.user_details.get("chat_id", "unknown")
                    if chat_id != 'unknown':
                        history_context = context_agent.get_context(chat_id, user_id)
                        if history_context:
                            context_prompt = history_context

                # Run routing in a worker thread to keep FastAPI non-blocking
                from functools import partial

                result = await anyio.to_thread.run_sync(
                    partial(
                        response_mode_router.route_query,
                        response_mode=chat_message.response_mode,
                        user_message=chat_message.message,
                        user_id=chat_message.user_id,
                        context_prompt=context_prompt,
                        chat_id=chat_message.user_details.get("chat_id", "unknown")
                            if chat_message.user_details else "unknown",
                        auth_token=chat_message.auth_token,
                        n_results=chat_message.user_details.get("n_results", 20)
                            if chat_message.user_details else 20
                    )
                )
                
                if result.get("success", False):
                    response_text = result.get("response", "")

                    # Store interaction in memory
                    try:
                        if chat_message.user_details:
                            chat_id = chat_message.user_details.get("chat_id", "unknown")

                            if chat_id != "unknown":
                                context_agent.store_interaction(
                                    chat_id=chat_id,
                                    user_id=str(chat_message.user_id),
                                    message=chat_message.message,
                                    response=response_text,
                                    metadata={
                                        "response_mode": chat_message.response_mode
                                    }
                                )

                                logger.info(f"✅ Memory stored for chat {chat_id}")

                    except Exception as memory_error:
                        logger.error(f"❌ Memory storage failed: {str(memory_error)}")
                    
                    # Yield metadata
                    yield {"event": "metadata", "data": json.dumps({
                        "sources": result.get("sources", []),
                        "used_tools": result.get("used_tools", []),
                        "thinking_steps": result.get("thinking_steps", [])
                    })}
                    
                    # Smoothly type out response
                    chunk_size = 10
                    for i in range(0, len(response_text), chunk_size):
                        yield {"event": "token", "data": json.dumps({"token": response_text[i:i+chunk_size]})}
                        await asyncio.sleep(0.01)
                else:
                    yield {"event": "error", "data": json.dumps({"error": result.get("error", "Failed to generate agent response")})}
            except Exception as e:
                logger.error(f"Error in streaming complex response: {str(e)}")
                yield {"event": "error", "data": json.dumps({"error": str(e)})}
                
        yield {"event": "status", "data": json.dumps({"status": "done"})}
        
    return EventSourceResponse(event_generator()) 