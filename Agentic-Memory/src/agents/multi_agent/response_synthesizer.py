"""
Response Synthesis Agent

Combines results from multiple agents into a coherent response.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("response_synthesizer")


class ResponseSynthesisAgent(BaseAgent):
    """
    Agent that synthesizes responses from multiple agent results.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",
        temperature: float = 0.7,
        **kwargs
    ):
        """Initialize the Response Synthesis Agent."""
        system_instruction = self._create_system_instruction()
        
        super().__init__(
            agent_name="response_synthesizer",
            model_name=model_name,
            temperature=temperature,
            system_prompt=system_instruction,
            **kwargs
        )
    
    def _create_system_instruction(self) -> str:
        """Create structured system instruction using TOON format."""
        instruction_data = {
            "role": "Response Synthesis Agent",
            "purpose": "Combine results from multiple agents into coherent response",
            "capabilities": [
                "Multi-source information integration",
                "Context-aware response generation",
                "Source attribution",
                "Response formatting"
            ],
            "synthesis_rules": {
                "prioritize_graphrag": "Use GraphRAG results as primary source when available",
                "integrate_mcp": "Incorporate MCP tool outputs naturally",
                "maintain_context": "Preserve conversation context",
                "cite_sources": "Always cite sources when using knowledge base",
                "be_crisp": "Be direct and concise - answer only what is asked, no unnecessary elaboration",
                "no_hallucination": "Stick strictly to provided information - do not add information not in sources",
                "straight_to_point": "Get straight to the user's intent - no fluff, no filler sentences"
            },
            "output_format": {
                "response": "string - final synthesized response",
                "sources": "array - source documents used",
                "thinking_steps": "array - synthesis reasoning steps",
                "used_tools": "array - tools that contributed to response"
            }
        }
        
        return format_system_instruction(instruction_data)
    
    def _clean_response(self, response: str) -> str:
        """
        Clean response by removing thinking blocks, redacted reasoning, and technical artifacts.
        
        Args:
            response: Raw response text
            
        Returns:
            Cleaned response text
        """
        import re
        
        # Remove redacted reasoning blocks
        response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove thinking patterns
        response = re.sub(r'Thought:.*?(?=Action:|Final Answer:|$)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Thinking:.*?(?=Action:|Final Answer:|$)', '', response, flags=re.DOTALL | re.IGNORECASE)
        response = re.sub(r'Let me think:.*?(?=Action:|Final Answer:|$)', '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove Action and Observation lines (keep only Final Answer)
        lines = response.split('\n')
        cleaned_lines = []
        skip_until_final = False
        
        for line in lines:
            line_lower = line.lower().strip()
            if line_lower.startswith('final answer:'):
                skip_until_final = False
                # Remove "Final Answer:" prefix
                content = line.replace('Final Answer:', '').replace('final answer:', '').strip()
                if content:
                    cleaned_lines.append(content)
            elif skip_until_final:
                continue
            elif line_lower.startswith(('action:', 'observation:', 'thought:', 'thinking:')):
                skip_until_final = True
                continue
            elif not skip_until_final:
                cleaned_lines.append(line)
        
        response = '\n'.join(cleaned_lines)
        
        # Remove any remaining technical artifacts
        response = re.sub(r'\[OK\]|\[FAIL\]|\[ERROR\]', '', response)
        
        # Clean up multiple newlines
        response = re.sub(r'\n{3,}', '\n\n', response)
        
        return response.strip()
    
    def synthesize(
        self,
        query: str,
        graphrag_result: Optional[Dict[str, Any]] = None,
        mcp_result: Optional[Dict[str, Any]] = None,
        reasoning_result: Optional[Dict[str, Any]] = None,  # NEW: Precise reasoning from QueryReasoningAgent
        context: str = "",
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """
        Synthesize response from multiple agent results.
        
        Args:
            query: Original user query
            graphrag_result: GraphRAG search results
            mcp_result: MCP tool execution results
            reasoning_result: Query-specific reasoning with precise answer
            context: Additional context
            user_id: User identifier
            
        Returns:
            Synthesized response with metadata
        """
        try:
            # Prepare synthesis prompt
            synthesis_parts = []
            
            synthesis_parts.append(f"Original Query: {query}")
            
            if context:
                synthesis_parts.append(f"\nConversation Context:\n{context}")
            
            # PRIORITIZE REASONING RESULT if available (most precise)
            if reasoning_result and reasoning_result.get("precise_answer"):
                precise_answer = reasoning_result.get("precise_answer", "")
                reasoning_explanation = reasoning_result.get("reasoning", "")
                confidence = reasoning_result.get("confidence", 0.0)
                
                synthesis_parts.append(f"\n🎯 PRECISE ANSWER (Confidence: {confidence:.2f}):\n{precise_answer}")
                
                if reasoning_explanation:
                    synthesis_parts.append(f"\nReasoning: {reasoning_explanation}")
                
                # Add sources if available
                sources_used = reasoning_result.get("sources_used", [])
                if sources_used:
                    synthesis_parts.append(f"\nSources: {', '.join(sources_used)}")
                
                synthesis_prompt = "\n".join(synthesis_parts)
                synthesis_prompt += "\n\nTASK: Format the PRECISE ANSWER above into a natural, conversational response."
                synthesis_prompt += "\n- Use the precise answer EXACTLY as provided"
                synthesis_prompt += "\n- Add source citation if sources are mentioned"
                synthesis_prompt += "\n- Keep it brief and to the point"
                synthesis_prompt += "\n- Do NOT add extra information not in the precise answer"
                
            elif graphrag_result and graphrag_result.get("source_found"):
                # Fallback to GraphRAG context if no reasoning available
                graphrag_context = graphrag_result.get("context", "")
                graphrag_sources = graphrag_result.get("sources", [])
                
                synthesis_parts.append(f"\nKnowledge Base Information:\n{graphrag_context}")
                synthesis_parts.append(f"\nSource Documents ({len(graphrag_sources)} found):")
                for i, source in enumerate(graphrag_sources[:5], 1):
                    title = source.get("document_title", "Unknown")
                    content = source.get("content", "")[:200]
                    synthesis_parts.append(f"{i}. {title}: {content}...")
            
            if mcp_result and mcp_result.get("success_count", 0) > 0:
                mcp_outputs = mcp_result.get("outputs", [])
                
                # Use extracted context if available (more structured and concise)
                extracted_context = mcp_result.get("extracted_context", "")
                if extracted_context:
                    synthesis_parts.append(f"\nTool Execution Results:\n{extracted_context}")
                else:
                    # Fallback: extract from individual outputs
                    synthesis_parts.append(f"\nTool Execution Results ({len(mcp_outputs)} tools executed):")
                    for output in mcp_outputs:
                        tool_name = output.get("tool", "Unknown")
                        if output.get("success"):
                            result = output.get("result", {})
                            # Extract meaningful content from result
                            if isinstance(result, dict):
                                if "content" in result:
                                    synthesis_parts.append(f"{tool_name}: {result['content']}")
                                elif "text" in result:
                                    synthesis_parts.append(f"{tool_name}: {result['text']}")
                                elif "data" in result:
                                    synthesis_parts.append(f"{tool_name}: {str(result['data'])[:500]}")
                                else:
                                    # Try to find any string-like values
                                    result_str = str(result)
                                    if len(result_str) < 1000:
                                        synthesis_parts.append(f"{tool_name}: {result_str}")
                                    else:
                                        synthesis_parts.append(f"{tool_name}: {result_str[:500]}...")
                            elif isinstance(result, str):
                                synthesis_parts.append(f"{tool_name}: {result[:500]}")
                            else:
                                synthesis_parts.append(f"{tool_name}: {str(result)[:500]}")
                
                # Add reasoning if available (helps LLM understand why tools were used)
                reasoning = mcp_result.get("reasoning", "")
                if reasoning:
                    synthesis_parts.append(f"\nNote: Tools were selected because: {reasoning}")
            
            synthesis_prompt = "\n".join(synthesis_parts)
            synthesis_prompt += "\n\nGenerate a CRISP, DIRECT response that:"
            synthesis_prompt += "\n1. Answers ONLY what the user asked - nothing more, nothing less"
            synthesis_prompt += "\n2. Gets straight to the point - no introductory fluff or filler sentences"
            synthesis_prompt += "\n3. Uses ONLY information from the provided sources - NO hallucinations or made-up facts"
            synthesis_prompt += "\n4. Is concise and to-the-point - avoid unnecessary elaboration or explanations"
            synthesis_prompt += "\n5. Integrates information naturally when multiple sources are available"
            synthesis_prompt += "\n6. Cites sources briefly when using knowledge base information (e.g., 'According to [source]...')"
            synthesis_prompt += "\n7. Is free of technical artifacts, system details, thinking blocks, or internal processing notes"
            synthesis_prompt += "\n8. Provides ONLY the final answer - no Thought:, Action:, Observation:, or reasoning markers"
            synthesis_prompt += "\n\nCRITICAL RULES:"
            synthesis_prompt += "\n- If the user asks a simple question, give a simple, direct answer"
            synthesis_prompt += "\n- If the user asks to use a tool, show the tool result directly without preamble"
            synthesis_prompt += "\n- Do NOT add context the user didn't ask for"
            synthesis_prompt += "\n- Do NOT explain your process or how you found the answer"
            synthesis_prompt += "\n- Do NOT include phrases like 'Based on the information provided' or 'I found that' - just state the answer"
            synthesis_prompt += "\n- Stick strictly to facts from sources - if information isn't available, say so directly"
            synthesis_prompt += "\n\nIMPORTANT: Your response should be clean, crisp, and ready for the user. No thinking process, no reasoning blocks, no technical markers, no unnecessary words."
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=synthesis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            synthesized_response = response.content.strip()
            
            # Clean response: Remove thinking blocks and redacted reasoning
            synthesized_response = self._clean_response(synthesized_response)
            
            # Handle MCP tool listing specially
            if mcp_result and mcp_result.get("is_list_result"):
                tools_data = None
                error_message = None
                
                # Check for errors first
                for output in mcp_result.get("outputs", []):
                    if output.get("tool") == "list_tools":
                        if output.get("success"):
                            tools_data = output.get("result", {})
                        else:
                            error_message = output.get("error", "Unknown error")
                        break
                
                # Check if there was an error in the MCP result itself
                if not tools_data and mcp_result.get("error"):
                    error_message = mcp_result.get("error")
                
                if error_message:
                    # Authentication/authorization error - provide clear message
                    if "401" in str(error_message) or "Unauthorized" in str(error_message) or "authentication" in str(error_message).lower():
                        synthesized_response = "Authentication required to access MCP tools."
                    elif "403" in str(error_message) or "Forbidden" in str(error_message) or "authorization" in str(error_message).lower():
                        synthesized_response = "Permission denied. Check your account permissions."
                    else:
                        synthesized_response = f"Error listing MCP tools: {error_message}"
                elif tools_data:
                    tools_list = tools_data.get("tools", [])
                    if tools_list:
                        # Check if user wants server names specifically
                        query_lower = query.lower()
                        wants_servers = any(keyword in query_lower for keyword in [
                            "server names", "list servers", "mcp servers", "available servers", "names of servers"
                        ])
                        
                        if wants_servers:
                            # Extract unique server names
                            server_names = set()
                            for tool in tools_list:
                                server_name = tool.get('server', 'Unknown')
                                if server_name and server_name != 'Unknown':
                                    server_names.add(server_name)
                            
                            if server_names:
                                server_list = sorted(list(server_names))
                                synthesized_response = "\n".join(server_list)
                            else:
                                synthesized_response = "No MCP servers found."
                        else:
                            # Format tool list response (crisp version)
                            server_groups = {}
                            for tool in tools_list:
                                server_name = tool.get('server', 'Unknown')
                                if server_name not in server_groups:
                                    server_groups[server_name] = []
                                server_groups[server_name].append(tool.get('name', 'Unknown'))
                            
                            # Build concise response
                            response_parts = []
                            for server_name, tool_names in sorted(server_groups.items()):
                                response_parts.append(f"{server_name}: {', '.join(tool_names[:5])}")
                                if len(tool_names) > 5:
                                    response_parts[-1] += f" (+{len(tool_names) - 5} more)"
                            
                            synthesized_response = "\n".join(response_parts)
                            if len(tools_list) > 0:
                                synthesized_response += f"\n\nTotal: {len(tools_list)} tool(s) across {len(server_groups)} server(s)."
                    else:
                        synthesized_response = "No MCP tools available. Check your server settings."
                else:
                    synthesized_response = "Unable to retrieve MCP tools. Check authentication."
            
            # Collect sources
            sources = []
            if graphrag_result and graphrag_result.get("sources"):
                sources.extend(graphrag_result["sources"])
            
            # Collect used tools
            used_tools = []
            if graphrag_result:
                used_tools.append("graphrag_search")
            if mcp_result and mcp_result.get("tools_used"):
                used_tools.extend(mcp_result["tools_used"])
            
            # Generate thinking steps (minimal, for tracking only)
            thinking_steps = []
            
            if graphrag_result:
                thinking_steps.append({
                    "type": "graphrag",
                    "content": f"Retrieved {len(sources)} documents from knowledge base",
                    "timestamp": None
                })
            
            if mcp_result:
                if mcp_result.get("is_list_result"):
                    thinking_steps.append({
                        "type": "mcp",
                        "content": "Listed available MCP tools",
                        "timestamp": None
                    })
                else:
                    thinking_steps.append({
                        "type": "mcp",
                        "content": f"Executed {mcp_result.get('success_count', 0)} MCP tools",
                        "timestamp": None
                    })
            
            return {
                "response": synthesized_response,
                "sources": sources,
                "thinking_steps": thinking_steps,
                "used_tools": used_tools
            }
            
        except Exception as e:
            logger.error(f"Response synthesis failed: {str(e)}")
            return {
                "response": "I apologize, but I encountered an error synthesizing the response.",
                "sources": [],
                "thinking_steps": [],
                "used_tools": [],
                "error": str(e)
            }

