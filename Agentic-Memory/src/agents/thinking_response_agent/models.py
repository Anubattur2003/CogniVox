"""
Pydantic models for structured thinking response output.
Ensures reliable parsing of thinking agent responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class ThinkingStep(BaseModel):
    """A single step in the thinking process."""
    
    step_type: str = Field(
        description="Type of thinking step (analysis, reasoning, consideration)",
        examples=["analysis", "reasoning", "consideration", "evaluation"]
    )
    content: str = Field(
        description="The content of this thinking step"
    )
    step_number: int = Field(
        description="Sequential number of this step",
        ge=1
    )


class ThinkingResponse(BaseModel):
    """Structured output for thinking mode responses."""
    
    safety_check: str = Field(
        description="Result of safety evaluation (safe/unsafe)"
    )
    
    thinking_steps: List[ThinkingStep] = Field(
        description="List of thinking steps showing the reasoning process",
        min_items=1
    )
    
    final_answer: str = Field(
        description="Clean, polished final answer without any thinking process markers"
    )
    
    confidence_level: str = Field(
        description="Confidence in the response (high/medium/low)",
        examples=["high", "medium", "low"]
    )
    
    assumptions_made: Optional[List[str]] = Field(
        default=None,
        description="Any assumptions made during reasoning"
    )


class ThinkingResponseError(BaseModel):
    """Error response for thinking mode."""
    
    error_type: str = Field(description="Type of error")
    error_message: str = Field(description="Human-readable error message")
    safety_violated: bool = Field(default=False, description="Whether safety guidelines were violated") 