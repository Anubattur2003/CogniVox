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
                "response": "Final user-facing answer only"
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

        response = re.sub(
            r"Sources:.*?(?=Thinking Steps:|Tools Contributed:|$)",
            "",
            response,
            flags=re.IGNORECASE | re.DOTALL
        )

        response = re.sub(
            r"Thinking Steps:.*?(?=Tools Contributed:|$)",
            "",
            response,
            flags=re.IGNORECASE | re.DOTALL
        )

        response = re.sub(
            r"Tools Contributed:.*$",
            "",
            response,
            flags=re.IGNORECASE | re.DOTALL
        )

        response = re.sub(
            r"Final Synthesized Response:",
            "",
            response,
            flags=re.IGNORECASE
        )
        
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
        user_id: str = "default",
        document_found: bool = True
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
            
            if not (reasoning_result and reasoning_result.get("precise_answer")):
                synthesis_prompt = "\n".join(synthesis_parts)

            if not document_found:
                synthesis_prompt += """

            IMPORTANT DOCUMENT STATUS:

            No relevant information was found in the uploaded documents.

            Rules:
            1. Do NOT pretend the answer came from uploaded documents.
            2. If you know the answer, clearly say:
            "This information was not found in the uploaded documents. Based on my general knowledge..."
            3. If you don't know, say:
            "I could not find this information in the uploaded documents and I do not know the answer."
            4. Never make up document sources.

            """

            synthesis_prompt += "\n\nRESPONSE STYLE RULES:"
            synthesis_prompt += "\n1. Generate a response appropriate to the user's question."
            synthesis_prompt += "\n2. For simple factual questions, keep answers short, direct, and concise."
            synthesis_prompt += "\n3. Do not add unnecessary explanations, reasoning, source summaries, or background information unless requested."
            synthesis_prompt += "\n4. For complex, analytical, educational, technical, or research-oriented questions, provide detailed explanations with proper structure."
            synthesis_prompt += "\n5. Match the level of detail to the user's question."
            synthesis_prompt += "\n6. Use information from provided sources accurately."
            synthesis_prompt += "\n7. Cite sources when document information is used."
            synthesis_prompt += "\n8. Do not include technical artifacts, system details, thinking blocks, internal processing notes, or implementation details."
            synthesis_prompt += "\n9. Provide only the final answer to the user."
            synthesis_prompt += "\n10. Never fabricate information, sources, citations, documents, or references."

            synthesis_prompt += "\n\nDOCUMENT AWARENESS RULES:"
            synthesis_prompt += "\n1. If relevant information is found in uploaded documents, answer using the document information."
            synthesis_prompt += "\n2. You may improve readability, formatting, and explanation using your language abilities."
            synthesis_prompt += "\n3. Never claim document information that is not actually present in the retrieved context."
            synthesis_prompt += "\n4. If information is NOT found in uploaded documents, clearly state that first."
            synthesis_prompt += "\n5. If you know the answer from general knowledge, explicitly label it as general knowledge."
            synthesis_prompt += "\n6. Use the format: 'This information was not found in the uploaded documents. Based on my general knowledge...'"
            synthesis_prompt += "\n7. Never present general knowledge as if it came from uploaded documents."
            synthesis_prompt += "\n8. If you are not confident in the answer, say: 'I could not find this information in the uploaded documents and I do not know the answer.'"
            synthesis_prompt += "\n9. If neither the documents nor your knowledge provide a reliable answer, do not guess."

            synthesis_prompt += "\n\nMEMORY RULES:"
            synthesis_prompt += "\n1. If information is available in conversation memory or chat history, use it."
            synthesis_prompt += "\n2. For memory-based questions, answer directly."
            synthesis_prompt += "\n3. Do not claim memory information came from uploaded documents."
            synthesis_prompt += "\n4. Example: If the user previously said 'My favorite color is blue', answer 'Your favorite color is blue.'"

            synthesis_prompt += "\n\nFINAL RESPONSE REQUIREMENTS:"
            synthesis_prompt += "\n- Be accurate."
            synthesis_prompt += "\n- Be concise when appropriate."
            synthesis_prompt += "\n- Be detailed only when the question requires it."
            synthesis_prompt += "\n- Clearly distinguish document-based answers, memory-based answers, and general-knowledge answers."
            synthesis_prompt += "\n- Never hallucinate."
            synthesis_prompt += "\n- Never pretend information came from a source when it did not."
            
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
            source_type = "unknown"

            if graphrag_result and graphrag_result.get("sources"):
                sources.extend(graphrag_result["sources"])

            # Determine source type
            if context and "PREVIOUS CONVERSATION HISTORY" in context:
                source_type = "memory"

            elif document_found and len(sources) > 0:
                source_type = "document"

            elif not document_found:
                source_type = "general_knowledge"
            
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
                "source_type": source_type,
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

