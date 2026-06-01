"""
Supervisor ReAct Agent implementation using LangChain.

This agent intelligently decides when to use GraphRAG tools vs direct responses
and provides thinking capabilities for complex reasoning.
"""
import json
import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple, Union
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama
from collections import defaultdict

from src.agents.base_agent import BaseAgent
from src.agents.tools.graphrag_tool import create_graphrag_tool
from src.utils.graphrag_client import GraphRAGClient
from .prompt import supervisor_system_prompt
from .config import SUPERVISOR_REACT_CONFIG



# Configure logging
logger = logging.getLogger("cogniVox")

class SupervisorReActAgent(BaseAgent):
    """
    Supervisor ReAct Agent that intelligently decides when to use tools
    like GraphRAG based on the query type and context.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",  # Using qwen3:4b as requested
        temperature: float = 0.1,
        provider: str = "ollama",
        api_key: str = None,
        system_prompt: str = None,
        graphrag_client: Optional[GraphRAGClient] = None,
        **kwargs
    ):
        """
        Initialize the Supervisor ReAct Agent.
        
        Args:
            model_name: Name of the Ollama model (default: qwen3:4b)
            temperature: Temperature for response generation
            provider: LLM provider (should be "ollama")
            api_key: API key (not needed for Ollama)
            system_prompt: Custom system prompt
            graphrag_client: GraphRAG client instance
            **kwargs: Additional configuration
        """
        # Use supervisor system prompt by default
        effective_system_prompt = system_prompt or supervisor_system_prompt
        
        super().__init__(
            agent_name="supervisor_react",
            model_name=model_name,
            provider=provider,
            api_key=api_key,
            temperature=temperature,
            system_prompt=effective_system_prompt,
            **kwargs
        )
        
        
        # Initialize GraphRAG client and tool
        self.graphrag_client = graphrag_client or GraphRAGClient()
        self.graphrag_tool = create_graphrag_tool(self.graphrag_client)
        
        # Initialize MCP client and tool
        from src.mcp.mcp_client import MCPClient
        from src.agents.tools.mcp_tool import create_mcp_tool
        self.mcp_client = MCPClient()
        self.mcp_tool = create_mcp_tool(self.mcp_client)
        
        # Initialize tools list with both GraphRAG and MCP
        self.tools = [self.graphrag_tool, self.mcp_tool]
        
        # Create the ReAct agent
        self._setup_react_agent()
        
        # Initialize conversation histories per user
        self.user_contexts: defaultdict = defaultdict(list)
        self.max_context_length = 10  # Keep last 10 exchanges per user
        
        # Track thinking states for frontend
        self.thinking_states: Dict[str, Dict[str, Any]] = {}
        
    def _setup_react_agent(self):
        """Setup the ReAct agent with tools and prompt."""
        try:
            # Create a ReAct prompt template with all required LangChain variables
            react_prompt = PromptTemplate.from_template(
                """You are CogniVox, an intelligent assistant that follows the ReAct pattern.

{system_prompt}

## Available Tools:
{tools}

## Tool Names:
{tool_names}

## IMPORTANT: ReAct Format Requirements
You MUST follow this exact pattern:

1. Thought: [your reasoning about what to do]
2. Action: [tool_name]
3. Action Input: [input_for_tool]
4. Observation: [you will receive tool output here]
5. Final Answer: [your response to the user]

**CRITICAL: When using the graphrag_search tool, you MUST always include the user_id parameter.**
For graphrag_search, use this format:
Action: graphrag_search
Action Input: {{"query": "your search query", "user_id": "{user_id}", "n_results": 20}}

**IMPORTANT RESPONSE RULES:**
- If GraphRAG tool returns relevant information, use ONLY that information in your response
- Do NOT add external knowledge when GraphRAG provides an answer
- If GraphRAG returns "No relevant information found", then provide a general helpful response
- Always end with "Final Answer:" followed by your complete response

## Context:
{context}

## Current User ID: {user_id}

## Current Conversation:
{input}

Begin your reasoning process:

{agent_scratchpad}"""
            )
            
            # Create the ReAct agent
            self.react_agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=react_prompt
            )
            
            # Create agent executor with verbose output for debugging
            self.agent_executor = AgentExecutor(
                agent=self.react_agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=SUPERVISOR_REACT_CONFIG["agent"]["max_iterations"],  # Use config value
                early_stopping_method="force",  # Force stop when Final Answer reached
                return_intermediate_steps=True  # Track iterations for monitoring
            )
            
            logger.info("Supervisor ReAct Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up ReAct agent: {str(e)}")
            raise
    
    def _update_thinking_state(self, user_id: str, thinking_data: Dict[str, Any]):
        """Update the thinking state for a user (for frontend display)."""
        self.thinking_states[user_id] = {
            "timestamp": thinking_data.get("timestamp"),
            "step": thinking_data.get("step", "reasoning"),
            "content": thinking_data.get("content", ""),
            "is_thinking": thinking_data.get("is_thinking", True)
        }
    
    def _extract_thinking_from_response(self, response: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Extract thinking steps from the agent response.
        
        Args:
            response: Raw agent response
            
        Returns:
            Tuple of (final_answer, thinking_steps)
        """
        thinking_steps = []
        final_answer = response
        
        # Look for thinking patterns in the response
        lines = response.split('\n')
        current_thought = ""
        
        for line in lines:
            line = line.strip()
            
            # Detect thinking patterns
            if line.startswith(('Thought:', 'Thinking:', 'Let me think:')):
                if current_thought:
                    thinking_steps.append({
                        "type": "thought",
                        "content": current_thought.strip()
                    })
                current_thought = line
                
            elif line.startswith('Action:'):
                if current_thought:
                    thinking_steps.append({
                        "type": "thought",
                        "content": current_thought.strip()
                    })
                    current_thought = ""
                
                thinking_steps.append({
                    "type": "action",
                    "content": line
                })
                
            elif line.startswith('Observation:'):
                thinking_steps.append({
                    "type": "observation", 
                    "content": line
                })
                
            elif current_thought:
                current_thought += f"\n{line}"
        
        # Add final thought if exists
        if current_thought:
            thinking_steps.append({
                "type": "thought",
                "content": current_thought.strip()
            })
        
        # Extract final answer with improved logic
        final_answer_lines = []
        
        # Look for "Final Answer:" explicitly
        lines = response.split('\n')
        capture_final = False
        
        for line in lines:
            if line.strip().startswith('Final Answer:'):
                # Start capturing from this line
                capture_final = True
                content = line.replace('Final Answer:', '').strip()
                if content:  # If there's content on the same line
                    final_answer_lines.append(content)
            elif capture_final:
                # Continue capturing until we hit another action or end
                if line.strip().startswith(('Thought:', 'Action:', 'Observation:')):
                    break
                final_answer_lines.append(line)
        
        # If we found a final answer, use it
        if final_answer_lines:
            final_answer = '\n'.join(final_answer_lines).strip()
        elif thinking_steps:
            # Fallback: look for content after the last observation
            response_lines = response.split('\n')
            post_observation_lines = []
            found_observation = False
            
            for line in reversed(response_lines):
                if line.strip().startswith('Observation:'):
                    found_observation = True
                    break
                elif found_observation:
                    post_observation_lines.insert(0, line)
            
            if post_observation_lines:
                final_answer = '\n'.join(post_observation_lines).strip()
        
        # Clean up the final answer
        if final_answer:
            # Remove any remaining ReAct keywords that might have leaked through
            final_answer = final_answer.replace('Invalid Format: Missing \'Action:\' after \'Thought:\'', '').strip()
            
        return final_answer, thinking_steps
    
    def _prepare_context(self, user_id: str, context_prompt: str = "") -> str:
        """
        Prepare context string from conversation history and provided context.
        
        Args:
            user_id: User identifier
            context_prompt: Additional context from external sources
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add conversation history
        if user_id in self.user_contexts and self.user_contexts[user_id]:
            context_parts.append("RECENT CONVERSATION:")
            for entry in self.user_contexts[user_id][-5:]:  # Last 5 exchanges
                context_parts.append(f"Human: {entry['user']}")
                context_parts.append(f"Assistant: {entry['assistant']}")
        
        # Add external context
        if context_prompt.strip():
            context_parts.append(f"\nADDITIONAL CONTEXT:\n{context_prompt}")
        
        return "\n".join(context_parts) if context_parts else "No previous context available."
    
    def _store_conversation(self, user_id: str, user_message: str, assistant_response: str):
        """Store conversation in user context."""
        self.user_contexts[user_id].append({
            "user": user_message,
            "assistant": assistant_response
        })
        
        # Trim context if too long
        if len(self.user_contexts[user_id]) > self.max_context_length:
            self.user_contexts[user_id] = self.user_contexts[user_id][-self.max_context_length:]
    
    def chat(
        self,
        user_message: str,
        user_id: str = "default",
        context_prompt: str = "",
        return_thinking: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process a chat message using the ReAct agent.
        
        Args:
            user_message: The user's message
            user_id: User identifier for context
            context_prompt: Additional context from external sources
            return_thinking: Whether to return thinking steps
            **kwargs: Additional parameters
            
        Returns:
            Dictionary containing response, thinking steps, and source documents
        """
        try:
            logger.info(f"Processing chat request for user {user_id}")
            
            # OPTIMIZATION: Import timeout configuration
            from .config import SUPERVISOR_REACT_CONFIG
            total_timeout = SUPERVISOR_REACT_CONFIG["agent"]["total_timeout"]
            
            # Start timing for timeout enforcement
            start_time = time.time()
            
            # Clear GraphRAG tool's last result at the start of each conversation
            # This prevents source documents from previous conversations being carried over
            if hasattr(self, 'graphrag_tool') and self.graphrag_tool:
                self.graphrag_tool.clear_last_result()
                logger.info("Cleared GraphRAG tool's last result to prevent source carryover")
            
            # Update thinking state - starting
            self._update_thinking_state(user_id, {
                "step": "starting",
                "content": "Analyzing your question...",
                "is_thinking": True
            })
            
            # Prepare context
            context = self._prepare_context(user_id, context_prompt)
            
            # Update thinking state - reasoning
            self._update_thinking_state(user_id, {
                "step": "reasoning", 
                "content": "Thinking about the best approach...",
                "is_thinking": True
            })
            
            # Prepare input for the agent
            agent_input = {
                "input": user_message,
                "context": context,
                "system_prompt": self.system_prompt,
                "user_id": user_id  # Include user_id for GraphRAG tool usage
            }
            
            # Execute the ReAct agent with timeout enforcement
            max_iters = SUPERVISOR_REACT_CONFIG['agent']['max_iterations']
            logger.info(f"Executing ReAct agent (max_iterations={max_iters}, timeout={total_timeout}s)...")
            
            def execute_with_timeout():
                """Execute agent with timeout protection"""
                try:
                    # Check timeout before execution
                    if time.time() - start_time > total_timeout:
                        raise TimeoutError(f"Agent execution timeout ({total_timeout}s)")
                    
                    result = self.agent_executor.invoke(agent_input)
                    
                    # Check timeout after execution
                    execution_time = time.time() - start_time
                    if execution_time > total_timeout:
                        logger.warning(f"Agent execution took {execution_time:.1f}s (exceeded {total_timeout}s timeout)")
                    else:
                        logger.info(f"Agent execution completed in {execution_time:.1f}s")
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"Agent execution failed after {execution_time:.1f}s: {str(e)}")
                    raise
            
            try:
                result = execute_with_timeout()
            except TimeoutError as timeout_error:
                logger.error(f"Agent execution timed out: {str(timeout_error)}")
                return {
                    "response": "I apologize, but your request is taking too long to process. Please try a simpler question or try again later.",
                    "thinking_steps": [],
                    "used_tools": [],
                    "sources": [],
                    "document_relevant": False,
                    "user_id": user_id,
                    "error": f"Timeout: {str(timeout_error)}"
                }
            except Exception as agent_error:
                error_msg = str(agent_error).lower()
                
                # Check if error is due to iteration limit
                if "iteration" in error_msg or "stopped" in error_msg:
                    logger.error(f"⚠️ Agent stopped due to iteration limit. Current max_iterations: {SUPERVISOR_REACT_CONFIG['agent']['max_iterations']}")
                    logger.error(f"Consider increasing max_iterations in config if this happens frequently")
                    # Try to extract partial response from error
                    fallback_response = "I apologize, but I couldn't complete my analysis in time. Please try asking your question in a simpler way."
                else:
                    logger.error(f"Agent execution failed: {str(agent_error)}")
                    fallback_response = "I encountered an issue processing your request. Please try rephrasing your question."
                
                # Try to provide a helpful fallback response
                return {
                    "response": fallback_response,
                    "thinking_steps": [],
                    "used_tools": [],
                    "sources": [],
                    "document_relevant": False,
                    "user_id": user_id,
                    "error": str(agent_error)
                }
            
            # Extract response and thinking steps
            raw_output = result.get("output", "I apologize, but I couldn't generate a proper response.")
            
            # Check if we used many iterations (for monitoring and alerting)
            intermediate_steps = result.get("intermediate_steps", [])
            iterations_used = len(intermediate_steps)
            warn_threshold = SUPERVISOR_REACT_CONFIG["agent"].get("warn_threshold", max_iters - 5)
            
            if iterations_used >= max_iters - 1:
                logger.error(f"🚨 CRITICAL: Agent used {iterations_used}/{max_iters} iterations (AT LIMIT!)")
                logger.error(f"   Consider increasing max_iterations for this query type")
            elif iterations_used >= warn_threshold:
                logger.warning(f"⚠️ Agent used {iterations_used}/{max_iters} iterations (approaching limit, threshold: {warn_threshold})")
                logger.warning(f"   Query may be complex - monitor for patterns")
            else:
                logger.info(f"✅ Agent completed in {iterations_used}/{max_iters} iterations")
            
            # Log the raw output for debugging
            logger.info(f"Raw agent output: {raw_output[:200]}...")
            
            # Update thinking state - completing
            self._update_thinking_state(user_id, {
                "step": "completing",
                "content": "Finalizing response...",
                "is_thinking": True
            })
            
            # Extract thinking steps if requested
            thinking_steps = []
            final_response = raw_output
            
            if return_thinking:
                final_response, thinking_steps = self._extract_thinking_from_response(raw_output)
            
            # If final_response is empty or contains errors, use raw output
            if not final_response or "Invalid Format" in final_response:
                logger.warning(f"Using raw output due to parsing issues: {raw_output[:200]}...")
                
                # Check if this is a "no information" scenario
                if "no information" in raw_output.lower() or "not contain" in raw_output.lower() or "don't have" in raw_output.lower():
                    final_response = "I don't have information about that in the knowledge base."
                    logger.info("Detected 'no information' scenario - providing clean response")
                else:
                    final_response = raw_output
                    # Clean up any error messages
                    final_response = final_response.replace("Invalid Format: Missing 'Action:' after 'Thought:'", "").strip()
                    final_response = final_response.replace("<think>", "").replace("</think>", "").strip()
                    
                    # If it's still empty or contains errors, provide a fallback
                    if not final_response or len(final_response) < 10:
                        final_response = "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."
            
            # Extract used tools
            used_tools = self._extract_used_tools(result)
            
            # Debug logging for source extraction
            logger.info(f"Used tools detected: {used_tools}")
            logger.info(f"GraphRAG tool name: {self.graphrag_tool.name}")
            logger.info(f"GraphRAG search in used_tools: {'graphrag_search' in used_tools}")
            
            # Extract source documents if GraphRAG tool was used
            source_documents = []
            
            # Alternative detection: Check if GraphRAG tool has recent results
            # This is more reliable than intermediate_steps which may be empty
            graphrag_tool_used = False
            try:
                # Check if the GraphRAG tool has a recent result
                last_graphrag_result = self.graphrag_tool.get_last_result()
                if last_graphrag_result and last_graphrag_result.get("sources"):
                    graphrag_tool_used = True
                    logger.info(f"GraphRAG tool used (detected via last_result): {len(last_graphrag_result['sources'])} sources")
                    
                    # Add to used_tools if not already detected
                    if "graphrag_search" not in used_tools:
                        used_tools.append("graphrag_search")
                        logger.info("Added graphrag_search to used_tools via alternative detection")
            except Exception as e:
                logger.error(f"Error checking GraphRAG tool last result: {str(e)}")
            
            # Determine if documents are relevant based on GraphRAG tool result FIRST
            document_relevant = False
            if "graphrag_search" in used_tools or graphrag_tool_used:
                try:
                    last_graphrag_result = self.graphrag_tool.get_last_result()
                    if last_graphrag_result:
                        # Use source_found flag from GraphRAG if available
                        document_relevant = last_graphrag_result.get("source_found", False)
                        logger.info(f"GraphRAG source_found flag: {document_relevant}")
                except Exception as e:
                    logger.error(f"Error getting GraphRAG source_found flag: {str(e)}")
                    document_relevant = False
            
            # Extract source documents ONLY if they are relevant
            if ("graphrag_search" in used_tools or graphrag_tool_used) and document_relevant:
                try:
                    # Get source documents from the GraphRAG tool
                    source_documents = self.graphrag_tool.get_last_sources()
                    logger.info(f"Extracted {len(source_documents)} relevant source documents from GraphRAG tool")
                    if source_documents:
                        logger.info(f"First source: {source_documents[0] if source_documents else 'None'}")
                except Exception as e:
                    logger.error(f"Error extracting source documents: {str(e)}")
                    source_documents = []
            else:
                if "graphrag_search" in used_tools or graphrag_tool_used:
                    logger.info("GraphRAG tool was used but documents are NOT relevant - skipping source extraction")
                else:
                    logger.info("GraphRAG tool was not used in this conversation")
            
            # Store conversation for context
            self._store_conversation(user_id, user_message, final_response)
            
            # Update thinking state - completed
            self._update_thinking_state(user_id, {
                "step": "completed",
                "content": "Response ready",
                "is_thinking": False
            })
            
            # Prepare response
            response_data = {
                "response": final_response,
                "thinking_steps": thinking_steps,
                "used_tools": used_tools,
                "sources": source_documents,  # Include source documents
                "document_relevant": document_relevant,  # Flag indicating if sources are relevant
                "user_id": user_id
            }
            
            logger.info(f"ReAct agent completed successfully for user {user_id} (document_relevant={document_relevant})")
            return response_data
            
        except Exception as e:
            logger.error(f"Error in ReAct agent chat: {str(e)}")
            
            # Update thinking state - error
            self._update_thinking_state(user_id, {
                "step": "error",
                "content": f"Error occurred: {str(e)}",
                "is_thinking": False
            })
            
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "thinking_steps": [],
                "used_tools": [],
                "sources": [],
                "document_relevant": False,  # No relevant documents in error case
                "user_id": user_id,
                "error": str(e)
            }
    
    def _extract_used_tools(self, agent_result: Dict[str, Any]) -> List[str]:
        """Extract which tools were used from agent result."""
        used_tools = []
        
        # Debug logging
        logger.info(f"Agent result keys: {list(agent_result.keys())}")
        
        # Check intermediate steps for tool usage
        intermediate_steps = agent_result.get("intermediate_steps", [])
        logger.info(f"Intermediate steps count: {len(intermediate_steps)}")
        
        for i, step in enumerate(intermediate_steps):
            logger.info(f"Step {i}: {type(step)} with length {len(step) if hasattr(step, '__len__') else 'N/A'}")
            if len(step) >= 2:
                action = step[0]
                logger.info(f"Action type: {type(action)}")
                logger.info(f"Action attributes: {dir(action)}")
                if hasattr(action, 'tool'):
                    tool_name = action.tool
                    logger.info(f"Found tool: {tool_name}")
                    used_tools.append(tool_name)
                else:
                    logger.info("Action has no 'tool' attribute")
        
        logger.info(f"Final used_tools: {used_tools}")
        return list(set(used_tools))  # Remove duplicates
    
    def get_thinking_state(self, user_id: str) -> Dict[str, Any]:
        """Get current thinking state for a user."""
        return self.thinking_states.get(user_id, {
            "step": "idle",
            "content": "",
            "is_thinking": False
        })
    
    def clear_context(self, user_id: str):
        """Clear conversation context for a user."""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
        if user_id in self.thinking_states:
            del self.thinking_states[user_id]
        logger.info(f"Cleared context for user {user_id}")
    
    def add_tool(self, tool: Tool):
        """Add a new tool to the agent."""
        self.tools.append(tool)
        self._setup_react_agent()  # Recreate agent with new tools
        logger.info(f"Added tool: {tool.name}")
    
    def list_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools] 