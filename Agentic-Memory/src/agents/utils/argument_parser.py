"""
Argument Parser for MCP Tools

This module provides robust argument extraction and validation for MCP tool execution.
Uses LLM-based extraction for better accuracy than regex patterns.
"""
import json
import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger("cogniVox")


class ArgumentParser:
    """
    Robust argument parser using LLM-based extraction and JSON schema validation.
    """
    
    def __init__(self, llm: Optional[ChatOllama] = None):
        """Initialize the argument parser with an LLM instance."""
        self._llm = llm  # Store but don't create until needed
        self._llm_initialized = llm is not None
    
    @property
    def llm(self) -> ChatOllama:
        """Lazy-load LLM instance only when actually needed."""
        if not self._llm_initialized:
            logger.info("Initializing LLM for argument parser (one-time cost)")
            self._llm = ChatOllama(
                model="qwen3:4b",
                temperature=0.1
            )
            self._llm_initialized = True
        return self._llm
    
    def extract_arguments_from_query(
        self,
        query: str,
        tool_name: str,
        tool_schema: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Extract tool arguments from user query using LLM.
        
        Args:
            query: User query string
            tool_name: Name of the tool
            tool_schema: JSON schema for tool parameters
            
        Returns:
            Tuple of (extracted_arguments, warnings)
        """
        try:
            properties = tool_schema.get("properties", {})
            required = tool_schema.get("required", [])
            
            if not properties:
                logger.info(f"Tool '{tool_name}' has no parameters")
                return {}, []
            
            # Build extraction prompt using Chain-of-Thought
            extraction_prompt = self._build_extraction_prompt(
                query, tool_name, properties, required
            )
            
            messages = [
                SystemMessage(content="You are a parameter extraction expert. Extract tool parameters from user queries accurately."),
                HumanMessage(content=extraction_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse JSON response
            try:
                # Look for JSON in code blocks or raw
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
                if json_match:
                    arguments = json.loads(json_match.group(1))
                else:
                    json_obj_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_obj_match:
                        arguments = json.loads(json_obj_match.group(0))
                    else:
                        arguments = {}
                
                # Ensure it's a dict
                if not isinstance(arguments, dict):
                    logger.warning(f"LLM returned non-dict: {type(arguments)}")
                    arguments = {}
                
                # Validate and warn about issues
                warnings = []
                is_valid, errors = self.validate_arguments(arguments, tool_schema)
                if not is_valid:
                    warnings.extend(errors)
                
                return arguments, warnings
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                return {}, [f"Failed to extract arguments: {str(e)}"]
                
        except Exception as e:
            logger.error(f"Error in argument extraction: {str(e)}")
            return {}, [f"Extraction error: {str(e)}"]
    
    def _build_extraction_prompt(
        self,
        query: str,
        tool_name: str,
        properties: Dict[str, Any],
        required: List[str]
    ) -> str:
        """
        Build a Chain-of-Thought prompt for argument extraction.
        
        Uses advanced prompting techniques:
        - Structured reasoning (step-by-step)
        - Few-shot examples
        - Clear output format
        """
        # Format parameter descriptions
        param_descriptions = []
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            is_required = " (REQUIRED)" if param_name in required else " (optional)"
            
            param_descriptions.append(
                f"  - {param_name} ({param_type}){is_required}: {param_desc}"
            )
        
        params_text = "\n".join(param_descriptions)
        
        prompt = f"""Extract parameters for the tool '{tool_name}' from the user query.

User Query: "{query}"

Tool Parameters:
{params_text}

STEP-BY-STEP EXTRACTION PROCESS:

1. READ the query carefully and identify what the user wants to do
2. MATCH parameter descriptions to parts of the query
3. EXTRACT values that correspond to each parameter:
   - Look for explicit parameter mentions (e.g., "path: /tmp/file.txt")
   - Look for implicit values (e.g., "save to /tmp/file.txt" → path="/tmp/file.txt")
   - Match parameter types (URLs, paths, IDs, names, etc.)
4. VALIDATE required parameters are present
5. CONVERT types if needed (string to number, etc.)

FEW-SHOT EXAMPLES:

Example 1:
Query: "Save 'Hello World' to /tmp/test.txt"
Tool parameters: content (string, REQUIRED), path (string, REQUIRED)
Extracted: {{"content": "Hello World", "path": "/tmp/test.txt"}}

Example 2:
Query: "Get weather for London"
Tool parameters: city (string, REQUIRED), units (string, optional, default: celsius)
Extracted: {{"city": "London"}}

Example 3:
Query: "Create user john@example.com with role admin"
Tool parameters: email (string, REQUIRED), role (string, optional)
Extracted: {{"email": "john@example.com", "role": "admin"}}

NOW EXTRACT FROM THE ACTUAL QUERY:

Output ONLY a JSON object with the extracted parameters. Do not include explanations.
If a required parameter cannot be found, include it with value null.

JSON OUTPUT:
"""
        return prompt
    
    def validate_arguments(
        self,
        arguments: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate arguments against JSON schema.
        
        Args:
            arguments: Extracted arguments
            schema: JSON schema with properties and required fields
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check required parameters
        for param_name in required:
            if param_name not in arguments or arguments[param_name] is None:
                errors.append(f"Missing required parameter: {param_name}")
        
        # Validate types
        for param_name, param_value in arguments.items():
            if param_name in properties:
                param_info = properties[param_name]
                expected_type = param_info.get("type", "string")
                
                if not self._check_type(param_value, expected_type):
                    errors.append(
                        f"Parameter '{param_name}' has wrong type. "
                        f"Expected {expected_type}, got {type(param_value).__name__}"
                    )
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        if value is None:
            return True  # null is valid for any type
        
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type, str)
        return isinstance(value, expected_python_type)
    
    def enrich_arguments_with_defaults(
        self,
        arguments: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fill in default values from schema where applicable.
        
        Args:
            arguments: Current arguments
            schema: JSON schema with default values
            
        Returns:
            Enriched arguments with defaults
        """
        enriched = arguments.copy()
        properties = schema.get("properties", {})
        
        for param_name, param_info in properties.items():
            if param_name not in enriched or enriched[param_name] is None:
                if "default" in param_info:
                    enriched[param_name] = param_info["default"]
                    logger.info(f"Using default value for '{param_name}': {param_info['default']}")
        
        return enriched
    
    def suggest_argument_fixes(
        self,
        arguments: Dict[str, Any],
        schema: Dict[str, Any],
        validation_errors: List[str]
    ) -> Dict[str, str]:
        """
        Suggest fixes for invalid arguments.
        
        Args:
            arguments: Current arguments
            schema: JSON schema
            validation_errors: List of validation errors
            
        Returns:
            Dictionary of parameter -> suggestion
        """
        suggestions = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for error in validation_errors:
            if "Missing required parameter:" in error:
                param_name = error.split(": ")[-1]
                if param_name in properties:
                    param_info = properties[param_name]
                    param_desc = param_info.get("description", "")
                    suggestions[param_name] = (
                        f"Please provide {param_name} ({param_desc})"
                    )
            
            elif "wrong type" in error:
                # Extract parameter name from error
                match = re.search(r"'(\w+)'", error)
                if match:
                    param_name = match.group(1)
                    if param_name in properties:
                        expected_type = properties[param_name].get("type", "string")
                        suggestions[param_name] = (
                            f"Convert {param_name} to {expected_type}"
                        )
        
        return suggestions
    
    def coerce_types(
        self,
        arguments: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attempt to coerce argument types to match schema.
        
        Args:
            arguments: Current arguments
            schema: JSON schema
            
        Returns:
            Arguments with types coerced where possible
        """
        coerced = {}
        properties = schema.get("properties", {})
        
        for param_name, param_value in arguments.items():
            if param_name not in properties:
                coerced[param_name] = param_value
                continue
            
            expected_type = properties[param_name].get("type", "string")
            
            try:
                if expected_type == "integer":
                    coerced[param_name] = int(param_value)
                elif expected_type == "number":
                    coerced[param_name] = float(param_value)
                elif expected_type == "boolean":
                    if isinstance(param_value, str):
                        coerced[param_name] = param_value.lower() in ("true", "1", "yes", "on")
                    else:
                        coerced[param_name] = bool(param_value)
                elif expected_type == "string":
                    coerced[param_name] = str(param_value)
                else:
                    coerced[param_name] = param_value
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to coerce '{param_name}' to {expected_type}: {e}")
                coerced[param_name] = param_value
        
        return coerced


# Global instance for convenience
_parser_instance = None

def get_argument_parser(llm: Optional[ChatOllama] = None) -> ArgumentParser:
    """Get or create global ArgumentParser instance."""
    global _parser_instance
    if _parser_instance is None or llm is not None:
        _parser_instance = ArgumentParser(llm)
    return _parser_instance
