"""
Context Awareness Agent for enhancing AI responses with chat history.
"""
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from src.memory.chat_memory import chat_memory

# Configure logging
logger = logging.getLogger("cogniVox")

class ContextAwarenessAgent:
    """
    Agent that enhances AI responses with contextual awareness using
    the chat history stored in L0 memory.
    """
    
    def __init__(self, max_history_messages: int = 10):
        """
        Initialize the context awareness agent.
        
        Args:
            max_history_messages: Maximum number of previous messages to include
        """
        self.max_history_messages = max_history_messages
        logger.info(f"Context Awareness Agent initialized with max history of {max_history_messages} messages")
    
    def get_context(self, chat_id: str, user_id: str, include_metadata: bool = False) -> str:
        """
        Get formatted context for the current chat.
        
        Args:
            chat_id: Unique identifier for the chat thread
            user_id: Unique identifier for the user
            include_metadata: Whether to include metadata in the context
            
        Returns:
            Formatted context string ready to be prepended to prompts
        """
        if not chat_id:
            logger.warning("No chat_id provided to get_context")
            return ""
        
        try:
            # Log this attempt to get context
            logger.info(f"Fetching context for chat {chat_id}, user {user_id}")
            
            # Get raw chat history first to check what we're working with
            raw_history = chat_memory.get_chat_history(chat_id, self.max_history_messages)
            msg_count = len(raw_history)
            
            logger.info(f"Raw history contains {msg_count} messages for chat {chat_id}")
            
            if msg_count > 0:
                # Log a sample of the first message
                first_msg = raw_history[0].get("message", "No message content")
                first_msg_preview = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
                logger.info(f"First message in history: '{first_msg_preview}'")
                
                if msg_count > 1:
                    # Log a sample of the last message
                    last_msg = raw_history[-1].get("message", "No message content")
                    last_msg_preview = last_msg[:50] + "..." if len(last_msg) > 50 else last_msg
                    logger.info(f"Last message in history: '{last_msg_preview}'")
            
            # Get formatted context from memory
            try:
                context = chat_memory.get_formatted_context(
                    chat_id=chat_id,
                    limit=self.max_history_messages,
                    include_metadata=include_metadata
                )
            except Exception as format_error:
                logger.error(f"Error formatting context: {str(format_error)}")
                # If formatting fails but we have raw history, try to create simple context
                if raw_history:
                    context = "PREVIOUS CONVERSATION:\n\n"
                    for entry in raw_history:
                        context += f"USER: {entry.get('message', '')}\n"
                        context += f"ASSISTANT: {entry.get('response', '')}\n\n"
                else:
                    context = ""
            
            context_length = len(context)
            if context_length > 0:
                logger.info(f"Retrieved context for chat {chat_id} ({context_length} characters)")
                # Log a preview of the context
                context_preview = context[:150] + "..." if len(context) > 150 else context
                logger.info(f"Context preview: '{context_preview}'")
            else:
                logger.warning(f"No previous context found for chat {chat_id}")
                
            return context
        except Exception as e:
            logger.error(f"Error getting context: {str(e)}")
            logger.exception("Detailed error info:")
            return ""
    
    def store_interaction(self, chat_id: str, user_id: str,
                            message: str, response: str,
                            metadata: Optional[Dict[str, Any]] = None) -> bool:

        logger.info("=" * 60)
        logger.info("CONTEXT_AGENT STORE_INTERACTION CALLED")
        logger.info(f"chat_id={chat_id}")
        logger.info(f"user_id={user_id}")
        logger.info("=" * 60)

        if not chat_id or not user_id:
            logger.warning("Missing chat_id or user_id in store_interaction")
            return False

        try:

            logger.info("CALLING chat_memory.store_interaction()")

            success = chat_memory.store_interaction(
                chat_id=chat_id,
                user_id=user_id,
                message=message,
                response=response,
                metadata=metadata
            )

            logger.info(f"chat_memory returned: {success}")

            if success:
                logger.info(f"Stored interaction for chat {chat_id}")
            else:
                logger.warning(f"Failed to store interaction for chat {chat_id}")

            return success

        except Exception as e:
            logger.error(f"Error storing interaction: {str(e)}")
            return False
    
    def enhance_prompt_with_context(self, original_prompt: str, chat_id: str, 
                                   user_id: str, include_metadata: bool = False) -> str:
        """
        Enhance a prompt with context from chat history.
        
        Args:
            original_prompt: The original prompt to enhance
            chat_id: Unique identifier for the chat thread
            user_id: Unique identifier for the user
            include_metadata: Whether to include metadata in the context
            
        Returns:
            Enhanced prompt with context prepended
        """
        # Get the formatted context
        context = self.get_context(chat_id, user_id, include_metadata)
        
        # If no context, just return the original prompt
        if not context:
            return original_prompt
        
        # Combine context with the original prompt
        enhanced_prompt = f"{context}\n\nCURRENT QUERY:\n{original_prompt}"
        
        return enhanced_prompt
    
    def extract_key_topics(self, chat_id: str, limit: int = 5) -> List[str]:
        """
        Extract key topics from the chat history.
        
        Args:
            chat_id: Unique identifier for the chat thread
            limit: Maximum number of topics to extract
            
        Returns:
            List of key topics
        """
        # This is a simplified version - in a real implementation,
        # this could use NLP techniques to extract actual topics
        history = chat_memory.get_chat_history(chat_id)
        
        if not history:
            return []
            
        # For now, just return the first few words of each message as "topics"
        topics = []
        for entry in history:
            message = entry.get("message", "")
            if message:
                # Get first few words as a "topic"
                words = message.split()
                if len(words) > 3:
                    topic = " ".join(words[:3]) + "..."
                else:
                    topic = message
                
                if topic not in topics:
                    topics.append(topic)
                    if len(topics) >= limit:
                        break
        
        return topics
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the context awareness system.
        
        Returns:
            Dictionary of statistics
        """
        # Most stats come from the memory system
        memory_stats = chat_memory.get_stats()
        
        # Add agent-specific stats
        agent_stats = {
            "max_history_messages": self.max_history_messages,
        }
        
        # Combine stats
        return {**memory_stats, **agent_stats} 