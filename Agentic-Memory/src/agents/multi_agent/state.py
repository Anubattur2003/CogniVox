"""
State definition for LangGraph multi-agent system.
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State shared across all agents in the workflow."""
    
    # Input
    user_message: str
    user_id: str
    context_prompt: str
    auth_token: Optional[str]
    n_results: int
    
    # Messages (for LangGraph)
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Query Analysis
    query_analysis: Dict[str, Any]
    needs_graphrag: bool
    needs_mcp: bool
    agent_plan: Dict[str, Any]
    
    # GraphRAG Results
    graphrag_result: Optional[Dict[str, Any]]
    graphrag_sources: List[Dict[str, Any]]
    graphrag_context: str
    
    # MCP Results
    mcp_result: Optional[Dict[str, Any]]
    mcp_tools_used: List[str]
    mcp_reasoning: Dict[str, Any]
    mcp_extracted_context: str
    
    # Synthesis
    synthesized_response: str
    reasoning_result: Optional[Dict[str, Any]]  # Query-specific reasoning from reasoning agent
    sources: List[Dict[str, Any]]
    thinking_steps: List[Dict[str, Any]]
    used_tools: List[str]
    
    # Validation
    validated_response: str
    validation_passed: bool
    validation_notes: List[str]

