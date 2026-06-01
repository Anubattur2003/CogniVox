"""
Query Reasoning Agent

Extracts precise information from GraphRAG results based on user query and conversation context.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("query_reasoning")


class QueryReasoningAgent(BaseAgent):
    """
    Agent that performs query-specific reasoning to extract precise answers.
    
    This agent analyzes the user's query in the context of conversation history
    and extracts the EXACT piece of information that answers the query from
    GraphRAG results, preventing vague or overly broad responses.
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        temperature: float = 0.2,
        **kwargs
    ):
        """Initialize the Query Reasoning Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="query_reasoning",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "Query Reasoning Agent",
            "purpose": "Extract precise, query-specific information from retrieved documents",
            "capabilities": [
                "Conversational context analysis",
                "Precise information extraction",
                "Query intent understanding",
                "Structured reasoning generation"
            ],
            "reasoning_rules": {
                "understand_context": "Analyze query in context of conversation history",
                "extract_precise": "Extract ONLY the specific information that answers the query",
                "no_ranges": "If query asks for specific value, provide that value - not a range",
                "identify_category": "When ranges exist, identify which category applies to the query",
                "cite_logic": "Explain the reasoning: why this specific information answers the query",
                "handle_followups": "Recognize follow-up questions and extract relevant details"
            },
            "output_format": {
                "precise_answer": "string - the exact answer to the user's query",
                "reasoning": "string - explanation of why this is the correct answer",
                "confidence": "float - confidence score 0-1",
                "category_identified": "string - if applicable, which category/range the answer falls into",
                "sources_used": "array - specific sources that contain the answer"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def reason(
        self,
        query: str,
        graphrag_result: Dict[str, Any],
        context: str = "",
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Perform query-specific reasoning on GraphRAG results.
        
        Args:
            query: Current user query
            graphrag_result: Results from GraphRAG search
            context: Conversation context/history
            user_id: User identifier
            
        Returns:
            Reasoning result with precise answer and explanation
        """
        try:
            # Check if GraphRAG returned results
            if not graphrag_result or not graphrag_result.get("source_found"):
                return {
                    "precise_answer": "No information found in knowledge base.",
                    "reasoning": "GraphRAG did not return any relevant documents.",
                    "confidence": 0.0,
                    "category_identified": None,
                    "sources_used": []
                }
            
            # Build reasoning prompt
            reasoning_parts = []
            
            reasoning_parts.append(f"Current User Query: {query}")
            
            if context:
                reasoning_parts.append(f"\nConversation History:\n{context}")
                reasoning_parts.append("\nIMPORTANT: This may be a follow-up question. Understand it in context of the conversation.")
            
            # Add GraphRAG context and sources
            graphrag_context = graphrag_result.get("context", "")
            graphrag_sources = graphrag_result.get("sources", [])
            
            if graphrag_context:
                reasoning_parts.append(f"\nRetrieved Information from Knowledge Base:\n{graphrag_context}")
            
            if graphrag_sources:
                reasoning_parts.append(f"\nSource Documents ({len(graphrag_sources)} found):")
                for i, source in enumerate(graphrag_sources[:5], 1):
                    title = source.get("document_title", "Unknown")
                    content = source.get("content", "")
                    page = source.get("page", "N/A")
                    reasoning_parts.append(f"{i}. {title} (Page {page}):\n{content}")
            
            reasoning_prompt = "\n".join(reasoning_parts)
            reasoning_prompt += "\n\n" + """TASK: Analyze the above information and provide a PRECISE answer to the user's query.

CRITICAL INSTRUCTIONS:
1. If the query asks about a SPECIFIC value (e.g., "for 6 years?", "what about 4 years?"), extract ONLY that specific value
2. If the information is organized in ranges/categories, identify which category applies and extract that specific detail
3. DO NOT return the full range or all options - extract ONLY what the user asked for
4. If it's a follow-up question (short query like "for 6 years?"), use conversation context to understand what is being asked
5. Provide clear reasoning explaining WHY this specific piece of information answers the query

OUTPUT FORMAT (JSON):
{
    "precise_answer": "The exact, specific answer to the query (e.g., 'For 6 years of experience: Rs. 25,000/-')",
    "reasoning": "Explanation of why this is correct (e.g., 'User asked about 6 years. From the document, 6 years falls in the 4-8 years experience range, which has a referral bonus of Rs. 25,000/-.')",
    "confidence": 0.95,
    "category_identified": "The category/range if applicable (e.g., '4-8 years')",
    "sources_used": ["Employee Referral Programme, Page 5"]
}

Provide ONLY the JSON output, no additional text."""
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=reasoning_prompt)
            ]
            
            response = self.llm.invoke(messages)
            response_text = response.content.strip()
            
            # Parse JSON response
            try:
                import json
                import re
                
                # Extract JSON from response (handle cases where model adds extra text)
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    reasoning_result = json.loads(json_match.group())
                else:
                    # Fallback: treat entire response as precise answer
                    reasoning_result = {
                        "precise_answer": response_text,
                        "reasoning": "Extracted from GraphRAG results",
                        "confidence": 0.8,
                        "category_identified": None,
                        "sources_used": [s.get("document_title", "Unknown") for s in graphrag_sources[:2]]
                    }
                
                return reasoning_result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON reasoning output: {e}")
                # Fallback to plain text response
                return {
                    "precise_answer": response_text,
                    "reasoning": "Generated from retrieved documents",
                    "confidence": 0.7,
                    "category_identified": None,
                    "sources_used": [s.get("document_title", "Unknown") for s in graphrag_sources[:2]]
                }
            
        except Exception as e:
            logger.error(f"Query reasoning failed: {str(e)}")
            return {
                "precise_answer": "I encountered an error analyzing the query.",
                "reasoning": f"Error: {str(e)}",
                "confidence": 0.0,
                "category_identified": None,
                "sources_used": [],
                "error": str(e)
            }
