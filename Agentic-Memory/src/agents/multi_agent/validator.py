"""
Validation Agent

Validates final responses for quality, safety, and completeness.
"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("validator")


class ValidationAgent(BaseAgent):
    """
    Agent that validates responses before returning to user.
    """
    
    def __init__(
        self,
        model_name: str = "gemma2:2b",
        temperature: float = 0.1,
        **kwargs
    ):
        """Initialize the Validation Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="validator",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "Response Validation Agent",
            "purpose": "Validate responses for quality, safety, and completeness",
            "validation_criteria": {
                "completeness": "Response fully addresses the query - nothing missing, nothing extra",
                "accuracy": "Information is accurate and well-sourced - no hallucinations",
                "safety": "No harmful, inappropriate, or sensitive content",
                "clarity": "Response is clear and well-structured",
                "conciseness": "Response is crisp and direct - no unnecessary words or filler",
                "no_hallucination": "No information added that wasn't in the sources",
                "no_technical_artifacts": "No system paths, IDs, or technical details",
                "straight_to_point": "Gets directly to user's intent - no fluff or preamble"
            },
            "output_format": {
                "passed": "boolean - validation passed",
                "response": "string - validated/cleaned response",
                "notes": "array - validation notes or improvements"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def validate(
        self,
        query: str,
        response: str,
        sources: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate a response.
        
        Args:
            query: Original user query
            response: Response to validate
            sources: Source documents used
            
        Returns:
            Validation result with cleaned response
        """
        try:
            validation_prompt = f"""Validate the following response to ensure it meets quality standards.

Original Query: {query}

Response to Validate:
{response}

Sources Used: {len(sources) if sources else 0} documents

Check for:
1. Completeness - Does it fully answer the query? (Not missing anything, but also not adding extra)
2. Accuracy - Is the information correct? (No hallucinations or made-up facts)
3. Conciseness - Is it crisp and direct? (No unnecessary words, filler sentences, or preamble)
4. Straight to Point - Does it get directly to user's intent? (No "Based on...", "I found that...", etc.)
5. Safety - No harmful or inappropriate content
6. Clarity - Is it well-structured and clear?
7. No Technical Artifacts - No system paths, IDs, or technical details
8. No Hallucination - Only uses information from sources, nothing added

Provide validation result in JSON format:
{{
  "passed": true/false,
  "response": "validated/cleaned response text",
  "notes": ["validation note 1", "validation note 2"]
}}

CRITICAL VALIDATION RULES:
- Remove any introductory phrases like "Based on the information provided", "I found that", "According to my analysis"
- Remove any process explanations like "Let me search for...", "I'll check...", "After analyzing..."
- Remove any filler sentences that don't directly answer the query
- Ensure response is crisp - if user asks a simple question, give a simple answer
- If response is verbose, make it more concise while keeping all essential information
- Remove thinking blocks, reasoning steps, Thought:, Action:, or Observation: markers
- Ensure no hallucinations - only use information from provided sources

IMPORTANT: The response field should contain ONLY the clean, crisp, final answer. If the original response is verbose or has unnecessary content, provide a more concise version that still fully answers the query.

If validation fails, provide an improved, more concise response."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=validation_prompt)
            ]
            
            validation_response = self.llm.invoke(messages)
            validation_text = validation_response.content.strip()
            
            # Parse JSON response
            import json
            try:
                # Extract JSON from markdown if present
                if "```json" in validation_text:
                    json_start = validation_text.find("```json") + 7
                    json_end = validation_text.find("```", json_start)
                    validation_text = validation_text[json_start:json_end].strip()
                elif "```" in validation_text:
                    json_start = validation_text.find("```") + 3
                    json_end = validation_text.find("```", json_start)
                    validation_text = validation_text[json_start:json_end].strip()
                
                validation_result = json.loads(validation_text)
                
                validated_response = validation_result.get("response", response)
                passed = validation_result.get("passed", True)
                notes = validation_result.get("notes", [])
                
                # If validation failed but no improved response provided, use original
                if not passed and validated_response == response:
                    logger.warning("Validation failed but no improved response provided")
                    # Try to clean common technical artifacts
                    validated_response = self._clean_technical_artifacts(response)
                
                return {
                    "passed": passed,
                    "response": validated_response,
                    "notes": notes
                }
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse validation JSON, using original response")
                # Fallback: basic cleaning
                cleaned_response = self._clean_technical_artifacts(response)
                return {
                    "passed": True,
                    "response": cleaned_response,
                    "notes": ["JSON parsing failed, applied basic cleaning"]
                }
                
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            # Fallback: basic cleaning
            cleaned_response = self._clean_technical_artifacts(response)
            return {
                "passed": True,
                "response": cleaned_response,
                "notes": [f"Validation error: {str(e)}"]
            }
    
    def _clean_technical_artifacts(self, text: str) -> str:
        """Remove technical artifacts, thinking blocks, and unnecessary verbosity from response."""
        import re
        
        # Remove thinking blocks and redacted reasoning
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove thinking patterns
        text = re.sub(r'Thought:.*?(?=Action:|Final Answer:|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'Thinking:.*?(?=Action:|Final Answer:|$)', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove Action and Observation lines (keep only content after Final Answer)
        lines = text.split('\n')
        cleaned_lines = []
        skip_until_final = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('final answer:'):
                skip_until_final = False
                content = line.replace('Final Answer:', '').replace('final answer:', '').strip()
                if content:
                    cleaned_lines.append(content)
            elif skip_until_final or line_lower.startswith(('action:', 'observation:', 'thought:', 'thinking:')):
                continue
            else:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove common verbose introductory phrases
        verbose_patterns = [
            r'Based on the information provided[,\s]*',
            r'According to my analysis[,\s]*',
            r'I found that[,\s]*',
            r'Let me[,\s]*',
            r'I\'ll[,\s]*',
            r'After analyzing[,\s]*',
            r'After checking[,\s]*',
            r'After searching[,\s]*',
            r'Let me search for[,\s]*',
            r'Let me check[,\s]*',
            r'I can see that[,\s]*',
            r'It appears that[,\s]*',
            r'From the information available[,\s]*',
        ]
        
        for pattern in verbose_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove file paths
        text = re.sub(r'/[^\s"\')*]+\.(?:pdf|docx?|txt|xlsx?|pptx?)', '', text)
        
        # Remove UUIDs
        text = re.sub(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', '', text)
        
        # Remove hash codes
        text = re.sub(r'_[a-f0-9]{6,}', '', text)
        
        # Remove storage URLs
        text = re.sub(r'gcp://[^\s"\')\]]+', '', text)
        text = re.sub(r'https://storage\.googleapis\.com/[^\s"\')\]]+', '', text)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

