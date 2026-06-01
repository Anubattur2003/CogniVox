"""
Dependency injection for API routes.
Provides centralized agent instances for the FastAPI application.
"""
from functools import lru_cache
from src.agents.ollama_chat_agent import OllamaChatAgent
from src.agents.query_validation_agent import QueryValidationAgent
from src.agents.query_expansion_agent import QueryExpansionAgent
from src.agents.intent_classifier_agent import IntentClassifierAgent
from src.agents.profile_extraction_agent import ProfileExtractionAgent
from src.agents.context_awareness_agent import ContextAwarenessAgent
from src.agents.supervisor_react_agent import SupervisorReActAgent
from src.agents.summary_generation_agent import SummaryGenerationAgent
from src.agents.response_enhancement_agent import ResponseEnhancementAgent
from src.agents.title_generation_agent import TitleGenerationAgent
from src.agents.speech_to_text_agent import SpeechToTextAgent
from src.agents.response_mode_router import ResponseModeRouter
from src.utils.model_warmer import model_warmer

@lru_cache()
def get_chat_agent() -> OllamaChatAgent:
    """Get cached instance of OllamaChatAgent."""
    return OllamaChatAgent()

@lru_cache()
def get_query_validator() -> QueryValidationAgent:
    """Get cached instance of QueryValidationAgent."""
    return QueryValidationAgent()

@lru_cache()
def get_query_expander() -> QueryExpansionAgent:
    """Get cached instance of QueryExpansionAgent."""
    return QueryExpansionAgent()

@lru_cache()
def get_intent_classifier() -> IntentClassifierAgent:
    """Get cached instance of IntentClassifierAgent."""
    return IntentClassifierAgent()

@lru_cache()
def get_profile_extractor() -> ProfileExtractionAgent:
    """Get cached instance of ProfileExtractionAgent."""
    return ProfileExtractionAgent()

@lru_cache()
def get_context_agent() -> ContextAwarenessAgent:
    """Get cached instance of ContextAwarenessAgent."""
    return ContextAwarenessAgent()

@lru_cache()
def get_supervisor_agent() -> SupervisorReActAgent:
    """Get cached instance of SupervisorReActAgent."""
    return SupervisorReActAgent()

@lru_cache()
def get_summary_generation_agent() -> SummaryGenerationAgent:
    """Get cached instance of SummaryGenerationAgent."""
    return SummaryGenerationAgent()

@lru_cache()
def get_response_enhancement_agent() -> ResponseEnhancementAgent:
    """Get cached instance of ResponseEnhancementAgent."""
    return ResponseEnhancementAgent()

@lru_cache()
def get_title_generation_agent() -> TitleGenerationAgent:
    """Get cached instance of TitleGenerationAgent."""
    return TitleGenerationAgent()

@lru_cache()
def get_speech_to_text_agent() -> SpeechToTextAgent:
    """Get cached instance of SpeechToTextAgent."""
    return SpeechToTextAgent()

@lru_cache()
def get_response_mode_router() -> ResponseModeRouter:
    """Get cached instance of ResponseModeRouter."""
    return ResponseModeRouter()

# Dependency instances for injection
chat_agent = get_chat_agent()
query_validator = get_query_validator()
query_expander = get_query_expander()
intent_classifier = get_intent_classifier()
profile_extractor = get_profile_extractor()
context_agent = get_context_agent()
supervisor_agent = get_supervisor_agent()
summary_agent = get_summary_generation_agent()
enhancement_agent = get_response_enhancement_agent()
title_agent = get_title_generation_agent() 
speech_to_text_agent = get_speech_to_text_agent() 
response_mode_router = get_response_mode_router() 