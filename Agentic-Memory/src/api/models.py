"""
Pydantic models for request and response validation.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class SourceDocument(BaseModel):
    """Source document model for RAG responses"""
    document_title: str = Field(..., description="Title of the source document")
    content: str = Field(..., description="Content excerpt from the source document")
    relevance: float = Field(default=0.0, description="Relevance score of the document to the query")
    file_path: Optional[str] = Field(default="", description="Path to the source file if available")
    download_url: Optional[str] = Field(default=None, description="Download URL for the source document if available")
    page: Optional[int] = Field(default=None, description="Page number in the source document if available")

class ChatMessage(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="The user's message")
    response_mode: Optional[str] = Field(default="general", description="Response mode: 'general', 'thinking', or 'agentic'")
    user_details: Optional[Dict[str, Any]] = Field(default=None, description="Additional user details from the authorization")
    auth_token: Optional[str] = Field(default=None, description="JWT authentication token for MCP server access")

class ThinkingStep(BaseModel):
    """Model for representing thinking steps in ReAct agent processing"""
    type: str = Field(..., description="Type of thinking step (thought, action, observation)")
    content: str = Field(..., description="Content of the thinking step")
    timestamp: Optional[str] = Field(default=None, description="Timestamp of the thinking step")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The assistant's response")
    response_time: float = Field(..., description="Response time in seconds")
    variants: Dict[str, str] = Field(default_factory=dict, description="Response variants (summary, detailed, etc.)")
    chat_id: Optional[str] = Field(default=None, description="The chat ID from the request, for tracking purposes")
    sources: List[SourceDocument] = Field(default_factory=list, description="List of document sources")
    source_found: bool = Field(default=False, description="Whether relevant documents were found in the knowledge base")
    generated_title: Optional[str] = Field(default=None, description="Auto-generated title for the thread (only for first message)")
    thinking_steps: List[ThinkingStep] = Field(default_factory=list, description="Thinking steps from ReAct agent processing")
    used_tools: List[str] = Field(default_factory=list, description="List of tools used by the agent")
    agent_type: str = Field(default="supervisor_react", description="Type of agent that processed the request") 

class TranscriptionResponse(BaseModel):
    """Response model for speech-to-text transcription"""
    success: bool = Field(..., description="Whether transcription was successful")
    text: str = Field(..., description="Transcribed text from audio")
    confidence: Optional[float] = Field(default=None, description="Confidence score of transcription")
    language: Optional[str] = Field(default=None, description="Detected language of the audio")
    processing_time: float = Field(..., description="Time taken for transcription in seconds")
    file_size_mb: Optional[float] = Field(default=None, description="Size of uploaded audio file in MB")
    model_used: str = Field(..., description="Model used for transcription")
    error: Optional[str] = Field(default=None, description="Error message if transcription failed") 