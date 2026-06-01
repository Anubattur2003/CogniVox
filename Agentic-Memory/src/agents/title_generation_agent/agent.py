"""
Title Generation Agent for generating crisp, descriptive thread titles.
"""
import logging
from typing import Optional, Any
from src.agents.base_agent import BaseAgent
from .prompt import title_generation_prompt

# Configure logging
logger = logging.getLogger("cogniVox")

class TitleGenerationAgent(BaseAgent):
    """
    Agent responsible for generating crisp, descriptive titles for chat threads.
    
    This agent analyzes conversation content and creates concise, meaningful titles
    that capture the main topic or question being discussed.
    """
    
    def __init__(
        self,
        model_name: str = "llama3.1",
        provider: str = "ollama",
        temperature: float = 0.3,
        **kwargs
    ):
        """
        Initialize the Title Generation Agent.
        
        Args:
            model_name: The LLM model to use for title generation
            provider: The provider for the LLM (default: ollama)
            temperature: Sampling temperature for more focused titles
            **kwargs: Additional arguments passed to BaseAgent
        """
        super().__init__(
            agent_name="title_generation",
            model_name=model_name,
            provider=provider,
            temperature=temperature,
            system_prompt=title_generation_prompt,
            **kwargs
        )
        
        self.max_title_words = 10
        self.min_title_words = 3
        
        logger.info(f"Title Generation Agent initialized with model {model_name}")
    
    def generate_title(self, response: str, query: str = "") -> str:
        """
        Generate a crisp 5-10 word title based on the AI response and original query.
        
        Args:
            response: The AI-generated response
            query: The original user query (optional, for context)
            
        Returns:
            A crisp 5-10 word title
        """
        try:
            # Prepare the input for title generation
            title_input = self._prepare_title_input(response, query)
            
            # Generate title using the LLM
            result = self.llm.invoke(title_input)
            
            # Extract and clean the title
            if hasattr(result, 'content'):
                title = result.content
            else:
                title = str(result)
            
            # Clean and validate the title
            clean_title = self._clean_and_validate_title(title, query)
            
            logger.info(f"Generated title: '{clean_title}'")
            return clean_title
            
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return self._generate_fallback_title(query, response)
    
    def _prepare_title_input(self, response: str, query: str) -> str:
        """
        Prepare the input text for title generation.
        
        Args:
            response: The AI response
            query: The original query
            
        Returns:
            Formatted input for the LLM
        """
        input_text = f"""Based on this conversation:

Query: {query}
Response: {response}

Generate a crisp, descriptive title that captures the main topic or question being discussed. The title should be:
- 5-10 words maximum
- Clear and specific
- Professional and informative
- Without quotes or special formatting

Examples of good titles:
- "Python List Comprehension Performance Tips"
- "MongoDB Connection Configuration Issues" 
- "Machine Learning Model Deployment Strategies"
- "JavaScript Async Functions Best Practices"

Generate only the title, nothing else:"""
        
        return input_text
    
    def _clean_and_validate_title(self, title: str, query: str = "") -> str:
        """
        Clean and validate the generated title.
        
        Args:
            title: The raw generated title
            query: The original query for fallback
            
        Returns:
            Cleaned and validated title
        """
        if not title:
            return self._generate_fallback_title(query)
        
        # Clean up the title (remove quotes, extra whitespace, etc.)
        clean_title = title.strip().strip('"').strip("'").strip()
        
        # Remove common unwanted prefixes/suffixes
        unwanted_phrases = [
            "title:", "the title is:", "generated title:", 
            "here's the title:", "title -", "- title"
        ]
        
        for phrase in unwanted_phrases:
            if clean_title.lower().startswith(phrase):
                clean_title = clean_title[len(phrase):].strip()
            if clean_title.lower().endswith(phrase):
                clean_title = clean_title[:-len(phrase)].strip()
        
        # Ensure title is not too long (max 10 words)
        words = clean_title.split()
        if len(words) > self.max_title_words:
            clean_title = " ".join(words[:self.max_title_words])
        
        # Check if title is too short or generic
        if (len(words) < self.min_title_words or 
            clean_title.lower() in ["new conversation", "chat", "question", "answer", "discussion"]):
            return self._generate_fallback_title(query)
        
        return clean_title
    
    def _generate_fallback_title(self, query: str = "", response: str = "") -> str:
        """
        Generate a fallback title when LLM generation fails.
        
        Args:
            query: The original query
            response: The AI response
            
        Returns:
            Fallback title
        """
        try:
            if query:
                # Use first 5 words of query
                query_words = query.split()[:5]
                title = " ".join(query_words)
                
                # Add "Discussion" if it doesn't end with a question mark
                if not title.endswith("?"):
                    title += " Discussion"
                
                return title
            elif response:
                # Use first few words of response
                response_words = response.split()[:5]
                return " ".join(response_words) + " Topic"
            else:
                return "New Chat Thread"
                
        except Exception as e:
            logger.error(f"Error in fallback title generation: {str(e)}")
            return "New Chat Thread"
    
    def validate_title(self, title: str) -> dict:
        """
        Validate a generated title against quality criteria.
        
        Args:
            title: The title to validate
            
        Returns:
            Dictionary with validation results
        """
        words = title.split()
        word_count = len(words)
        
        validation_result = {
            "is_valid": True,
            "issues": [],
            "word_count": word_count,
            "character_count": len(title)
        }
        
        # Check word count
        if word_count < self.min_title_words:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Too few words ({word_count} < {self.min_title_words})")
        
        if word_count > self.max_title_words:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Too many words ({word_count} > {self.max_title_words})")
        
        # Check for generic titles
        generic_titles = ["new conversation", "chat", "question", "answer", "discussion"]
        if title.lower() in generic_titles:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Title too generic")
        
        # Check character length (reasonable bounds)
        if len(title) > 100:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Title too long")
        
        if len(title) < 10:
            validation_result["is_valid"] = False
            validation_result["issues"].append("Title too short")
        
        return validation_result
    
    def update_title_parameters(self, max_words: int = None, min_words: int = None):
        """
        Update title generation parameters.
        
        Args:
            max_words: New maximum word count
            min_words: New minimum word count
        """
        if max_words is not None:
            self.max_title_words = max_words
            logger.info(f"Updated max_title_words to {max_words}")
        
        if min_words is not None:
            self.min_title_words = min_words
            logger.info(f"Updated min_title_words to {min_words}")
    
    def generate_multiple_titles(self, response: str, query: str = "", count: int = 3) -> list:
        """
        Generate multiple title options for selection.
        
        Args:
            response: The AI response
            query: The original query
            count: Number of titles to generate
            
        Returns:
            List of generated titles
        """
        titles = []
        
        for i in range(count):
            try:
                # Vary the temperature slightly for each generation
                original_temp = self.temperature
                self.temperature = original_temp + (i * 0.1)
                self.llm = self._create_llm()
                
                title = self.generate_title(response, query)
                if title not in titles:  # Avoid duplicates
                    titles.append(title)
                
                # Restore original temperature
                self.temperature = original_temp
                self.llm = self._create_llm()
                
            except Exception as e:
                logger.error(f"Error generating title {i+1}: {str(e)}")
                continue
        
        return titles if titles else [self._generate_fallback_title(query, response)] 