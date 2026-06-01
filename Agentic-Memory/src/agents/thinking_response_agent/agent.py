"""
Thinking Response Agent

Performs sophisticated internal reasoning and step-by-step thinking to provide well-reasoned responses.
Uses advanced thinking processes internally but delivers clean, polished answers to users.
"""

import logging
import json
import re
import time
from typing import Dict, Any, Optional, List
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError
from ..base_agent import BaseAgent
from .prompt import THINKING_RESPONSE_PROMPT
from .models import ThinkingResponse, ThinkingResponseError, ThinkingStep



logger = logging.getLogger(__name__)

class ThinkingResponseAgent(BaseAgent):
    """
    Agent that performs sophisticated internal reasoning and step-by-step thinking.
    Uses advanced thinking processes to provide well-reasoned, polished responses.
    """
    
    def __init__(self, model_name: str = "qwen2.5:7b"):
        """
        Initialize the Thinking Response Agent.
        
        Args:
            model_name: The Ollama model to use for responses (using larger model for better reasoning)
        """
        super().__init__(
            agent_name="thinking_response_agent",
            model_name=model_name,
            provider="ollama",
            temperature=0.7
        )
        # self.llm is initialized by BaseAgent using the config-aware helper
        logger.info(f"Thinking Response Agent initialized with model: {model_name}")
        
    def process_query(
        self, 
        user_message: str, 
        user_id: str = None, 
        context_prompt: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a user query using sophisticated internal reasoning to provide a well-reasoned response.
        
        Args:
            user_message: The user's question or request
            user_id: User identifier for context
            context_prompt: Additional context information
            **kwargs: Additional parameters
            
        Returns:
            Dict containing the clean final response and metadata (thinking is internal)
        """
        try:
            logger.info(f"Thinking Response Agent processing query for user {user_id}")
            

            # Create system and user messages
            system_message = SystemMessage(content=THINKING_RESPONSE_PROMPT.format(
                context_prompt=context_prompt if context_prompt else "No additional context provided.",
                user_message=""
            ))
            user_msg = HumanMessage(content=user_message)
            
            # Get structured response from chat model
            start_time = time.time()
            
            # Get response from chat model and parse manually
            response = self.llm.invoke([system_message, user_msg])
            processing_time = time.time() - start_time
            
            if not response or not response.content:
                raise Exception("Chat model failed to generate response")
            
            response_text = response.content.strip()
            logger.info(f"Raw response received ({len(response_text)} chars)")
            
            # Try to parse JSON response
            try:
                structured_response = self._parse_thinking_response(response_text)
                
                # Check safety
                if structured_response.safety_check == "unsafe":
                    logger.warning(f"Unsafe query detected for user {user_id}")
                    return {
                        "success": False,
                        "error": "Query violates safety guidelines",
                        "response": "I cannot assist with that request as it violates safety guidelines.",
                        "agent_type": "thinking_response"
                    }
                
                # Convert thinking steps to the expected format
                thinking_steps = [
                    {
                        "type": "reasoning_step",
                        "step_number": step.step_number,
                        "title": step.step_type.title(),
                        "content": step.content,
                        "timestamp": None
                    }
                    for step in structured_response.thinking_steps
                ]
                
                logger.info(f"Thinking agent completed - parsed response with {len(thinking_steps)} thinking steps")
                
                return {
                    "success": True,
                    "response": structured_response.final_answer,
                    "agent_type": "thinking_response",
                    "model_used": self.model_name,
                    "processing_time": processing_time,
                    "thinking_steps": thinking_steps,
                    "used_tools": [],
                    "sources": [],
                    "reasoning_visible": False,
                    "confidence_level": structured_response.confidence_level,
                    "assumptions_made": structured_response.assumptions_made or [],
                    "structured_response": True
                }
                
            except (ValidationError, json.JSONDecodeError, Exception) as e:
                # Fallback to simple text extraction
                logger.warning(f"JSON parsing failed, using fallback text extraction: {str(e)}")
                
                final_answer = self._extract_simple_answer(response_text)
                
                logger.info(f"Fallback response completed - extracted answer ({len(final_answer)} chars)")
                
                return {
                    "success": True,
                    "response": final_answer,
                    "agent_type": "thinking_response",
                    "model_used": self.model_name,
                    "processing_time": processing_time,
                    "thinking_steps": [{"type": "reasoning", "content": "Used fallback text extraction", "step_number": 1, "title": "Fallback"}],
                    "used_tools": [],
                    "sources": [],
                    "reasoning_visible": False,
                    "structured_response": False
                }
            
        except Exception as e:
            logger.error(f"Error in Thinking Response Agent: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error while processing your request. Please try again.",
                "agent_type": "thinking_response"
            }
    
    def _parse_thinking_response(self, response_text: str) -> ThinkingResponse:
        """
        Parse a thinking response from raw text, handling various output formats.
        
        Args:
            response_text: Raw response text from the LLM
            
        Returns:
            ThinkingResponse object
            
        Raises:
            Exception: If parsing fails
        """
        try:
            # Clean the response text - remove thinking tags and extract JSON
            cleaned_text = self._clean_response_text(response_text)
            
            # Try to parse as direct JSON
            try:
                response_data = json.loads(cleaned_text)
            except json.JSONDecodeError:
                # Try to extract JSON from mixed content
                json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
                if json_match:
                    response_data = json.loads(json_match.group())
                else:
                    raise Exception("No valid JSON found in response")
            
            # Validate required fields and provide defaults
            safety_check = response_data.get("safety_check", "safe")
            final_answer = response_data.get("final_answer", "")
            confidence_level = response_data.get("confidence_level", "medium")
            
            # Parse thinking steps
            thinking_steps_data = response_data.get("thinking_steps", [])
            thinking_steps = []
            
            for i, step_data in enumerate(thinking_steps_data):
                if isinstance(step_data, dict):
                    thinking_steps.append(ThinkingStep(
                        step_type=step_data.get("step_type", "reasoning"),
                        content=step_data.get("content", ""),
                        step_number=step_data.get("step_number", i + 1)
                    ))
                else:
                    # Handle case where step is just a string
                    thinking_steps.append(ThinkingStep(
                        step_type="reasoning",
                        content=str(step_data),
                        step_number=i + 1
                    ))
            
            # Ensure we have at least one thinking step
            if not thinking_steps:
                thinking_steps.append(ThinkingStep(
                    step_type="reasoning",
                    content="Analyzed the query and provided a response",
                    step_number=1
                ))
            
            # Create ThinkingResponse object
            return ThinkingResponse(
                safety_check=safety_check,
                thinking_steps=thinking_steps,
                final_answer=final_answer if final_answer else "I apologize, but I couldn't generate a proper response.",
                confidence_level=confidence_level,
                assumptions_made=response_data.get("assumptions_made", [])
            )
            
        except Exception as e:
            logger.error(f"Failed to parse thinking response: {str(e)}")
            # Create a minimal valid response
            return ThinkingResponse(
                safety_check="safe",
                thinking_steps=[ThinkingStep(
                    step_type="fallback",
                    content="Used fallback parsing due to response format issues",
                    step_number=1
                )],
                final_answer=self._extract_simple_answer(response_text),
                confidence_level="low",
                assumptions_made=["Response required fallback parsing"]
            )
    
    def _clean_response_text(self, response_text: str) -> str:
        """
        Clean response text to extract JSON, removing thinking tags and other artifacts.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Cleaned text ready for JSON parsing
        """
        # Remove qwen3 thinking tags
        
        # Remove <think> tags and their content
        text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
        
        # Remove other common thinking patterns
        text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
        text = re.sub(r'思考：.*?(?=\n|$)', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = text.strip()
        
        return text

    def _extract_simple_answer(self, response_text: str) -> str:
        """
        Simple fallback method to extract a clean answer when structured output fails.
        
        Args:
            response_text: The complete response text
            
        Returns:
            Clean answer text
        """
        try:
            # Remove JSON-like structures that might be malformed
            if response_text.strip().startswith('{') and response_text.strip().endswith('}'):
                # Try to extract final_answer field from malformed JSON
                try:
                    # Look for final_answer field
                    import re
                    final_answer_match = re.search(r'"final_answer"\s*:\s*"([^"]*)"', response_text)
                    if final_answer_match:
                        return final_answer_match.group(1)
                except:
                    pass
            
            # Look for common patterns in fallback responses
            lines = response_text.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and JSON artifacts
                if (line and 
                    not line.startswith(('{', '}', '"', '[', ']')) and
                    not line.endswith((',', '"')) and
                    'thinking_steps' not in line.lower() and
                    'safety_check' not in line.lower()):
                    clean_lines.append(line)
            
            if clean_lines:
                # Join meaningful lines
                result = ' '.join(clean_lines)
                return result[:1000]  # Limit length
            
            # Ultimate fallback: return first substantial line
            for line in lines:
                line = line.strip()
                if len(line) > 10 and not line.startswith(('{', '}', '"')):
                    return line
            
            return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            
        except Exception as e:
            logger.error(f"Error in simple answer extraction: {str(e)}")
            return "I apologize, but I encountered an error processing your request."
    
    def validate_input(self, user_message: str) -> bool:
        """
        Validate input for thinking response processing.
        
        Args:
            user_message: The user's message
            
        Returns:
            True if input is valid
        """
        return bool(user_message and user_message.strip())
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dict describing agent capabilities
        """
        return {
            "name": "Thinking Response Agent",
            "description": "Performs sophisticated internal reasoning to provide well-reasoned, polished responses",
            "response_type": "thinking",
            "supports_thinking": True,
            "supports_tools": False,
            "supports_sources": False,
            "internal_reasoning": True,
            "visible_reasoning": False,
            "optimal_for": ["complex_analysis", "detailed_reasoning", "well_thought_responses", "analytical_questions"]
        } 