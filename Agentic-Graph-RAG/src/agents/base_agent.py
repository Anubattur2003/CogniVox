import os
import logging
from typing import Optional, Dict, Any

# Try to import LangChain components
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

from src.config import OLLAMA_HOST, TEXT_GENERATION_MODEL

# Configure logger
logger = logging.getLogger("cogniVox.graphrag")

class BaseAgent:
    """
    Base class for all Agentic-Graph-RAG agents.
    
    Provides unified configuration handling, LLM creation utilities, and common functionality
    so that concrete agents can focus on their specific reasoning logic.
    """

    def __init__(
        self,
        agent_name: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        base_url: Optional[str] = None,
        system_prompt: Optional[str] = None,
        enable_caching: bool = True,
        cache_size: int = 100,
        **kwargs,
    ):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name identifier for this agent
            model_name: Ollama model to use (defaults to config)
            temperature: Temperature for response generation
            base_url: Ollama API base URL (defaults to config)
            system_prompt: System prompt for the agent
            enable_caching: Whether to enable response caching
            cache_size: Maximum number of cached responses
            **kwargs: Additional parameters
        """
        # Store basic identifiers
        self.agent_name = agent_name
        
        # Configuration with fallbacks
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", TEXT_GENERATION_MODEL)
        self.temperature = temperature if temperature is not None else 0.3
        
        # Handle base_url with proper fallbacks
        if base_url:
            self.base_url = base_url
        elif OLLAMA_HOST:
            self.base_url = OLLAMA_HOST
        else:
            self.base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.base_url = self.base_url.rstrip("/")
        
        # Store system prompt
        self.system_prompt = system_prompt
        
        # Caching configuration
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self._cache = {}
        
        # Additional parameters
        self.kwargs = kwargs
        
        # Initialize LLM if LangChain is available
        self.llm = None
        if HAS_LANGCHAIN:
            self._initialize_llm()
        
        logger.info(f"Initialized {agent_name} with model {self.model_name}")

    def _initialize_llm(self):
        """Initialize the LLM with given parameters if LangChain is available."""
        if not HAS_LANGCHAIN:
            logger.warning(f"{self.agent_name}: LangChain not available. Using direct API calls only.")
            return
            
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=self.temperature,
                base_url=self.base_url,
                api_path="/api/chat",
            )
            logger.debug(f"{self.agent_name}: LangChain LLM initialized successfully")
        except Exception as e:
            logger.error(f"{self.agent_name}: Error initializing LangChain LLM: {e}")
            self.llm = None

    def update_model(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs,
    ):
        """
        Dynamically update the underlying model configuration.
        
        Args:
            model_name: New model name
            temperature: New temperature
            **kwargs: Additional parameters
        """
        if model_name is not None:
            self.model_name = model_name
        if temperature is not None:
            self.temperature = temperature

        self.kwargs.update(kwargs)
        
        # Reinitialize LLM with new parameters
        if HAS_LANGCHAIN:
            self._initialize_llm()
            
        logger.info(f"{self.agent_name}: Model updated to {self.model_name}, temp={self.temperature}")
        return self

    def _generate_cache_key(self, input_data: Any) -> str:
        """Generate a cache key for the given input data."""
        import hashlib
        
        # Convert input to string and hash it
        input_str = str(input_data)
        cache_key = hashlib.md5(input_str.encode()).hexdigest()
        return f"{self.agent_name}_{cache_key}"

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get result from cache if available."""
        if self.enable_caching and cache_key in self._cache:
            logger.debug(f"{self.agent_name}: Using cached result for {cache_key[:8]}...")
            return self._cache[cache_key]
        return None

    def _store_in_cache(self, cache_key: str, result: Any):
        """Store result in cache with size limit."""
        if not self.enable_caching:
            return
            
        # Implement simple LRU by removing oldest entries when cache is full
        if len(self._cache) >= self.cache_size:
            # Remove the first (oldest) entry
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[cache_key] = result
        logger.debug(f"{self.agent_name}: Stored result in cache {cache_key[:8]}...")

    def clear_cache(self):
        """Clear the agent's cache."""
        self._cache.clear()
        logger.info(f"{self.agent_name}: Cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "agent_name": self.agent_name,
            "cache_enabled": self.enable_caching,
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size
        }

    def _make_api_call(self, prompt: str) -> str:
        """
        Make a direct API call to Ollama with enhanced error handling and fallback.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as a string
        """
        import requests
        
        try:
            api_url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": self.system_prompt or "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.temperature,
                "stream": False
            }
            
            logger.debug(f"{self.agent_name}: Making API call to {api_url} with model {self.model_name}")
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            # Enhanced response validation
            if response.status_code != 200:
                logger.error(f"{self.agent_name}: API returned status {response.status_code}: {response.text}")
                return self._try_fallback_model(prompt)
            
            try:
                result = response.json()
            except ValueError as json_error:
                logger.error(f"{self.agent_name}: Invalid JSON response: {json_error}")
                logger.error(f"Raw response: {response.text[:500]}")
                return self._try_fallback_model(prompt)
            
            # Extract content with better error handling
            content = result.get("message", {}).get("content", "")
            
            if not content or content.strip() == "":
                logger.warning(f"{self.agent_name}: Empty response from model {self.model_name}")
                logger.debug(f"Full response: {result}")
                return self._try_fallback_model(prompt)
            
            logger.debug(f"{self.agent_name}: Successfully received response ({len(content)} chars)")
            return content
            
        except requests.exceptions.Timeout:
            logger.error(f"{self.agent_name}: API call timed out after 30s")
            return self._try_fallback_model(prompt)
        except requests.exceptions.ConnectionError:
            logger.error(f"{self.agent_name}: Cannot connect to Ollama at {self.base_url}")
            raise
        except Exception as e:
            logger.error(f"{self.agent_name}: API call failed: {e}")
            return self._try_fallback_model(prompt)

    def _try_fallback_model(self, prompt: str) -> str:
        """
        Try fallback models if primary model fails.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as a string
        """
        fallback_models = ["llama3.1", "llama3.1:latest", "mistral", "gemma:2b"]
        original_model = self.model_name
        
        for fallback_model in fallback_models:
            if fallback_model == original_model:
                continue
                
            try:
                logger.info(f"{self.agent_name}: Trying fallback model {fallback_model}")
                
                api_url = f"{self.base_url}/api/chat"
                payload = {
                    "model": fallback_model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt or "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": self.temperature,
                    "stream": False
                }
                
                response = requests.post(api_url, json=payload, timeout=45)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("message", {}).get("content", "")
                    
                    if content and content.strip():
                        logger.warning(f"{self.agent_name}: Fallback successful with {fallback_model}")
                        # Update model for future calls
                        self.model_name = fallback_model
                        return content
                        
            except Exception as e:
                logger.debug(f"{self.agent_name}: Fallback model {fallback_model} also failed: {e}")
                continue
        
        # If all fallbacks fail, raise the original error
        logger.error(f"{self.agent_name}: All models failed, including fallbacks")
        raise Exception(f"No working model found. Primary model '{original_model}' and all fallbacks failed.")

    def _make_langchain_call(self, prompt: str) -> str:
        """
        Make a call using LangChain when available.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            The model's response as a string
        """
        if not self.llm:
            raise ValueError("LangChain LLM not initialized")
            
        try:
            messages = [
                SystemMessage(content=self.system_prompt or "You are a helpful assistant."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
            
        except Exception as e:
            logger.error(f"{self.agent_name}: LangChain call failed: {e}")
            raise

    def call_llm(self, prompt: str, use_cache: bool = True) -> str:
        """
        Call the LLM with the given prompt, handling caching and fallbacks.
        
        Args:
            prompt: The prompt to send to the model
            use_cache: Whether to use caching for this call
            
        Returns:
            The model's response as a string
        """
        # Check cache first if enabled
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(prompt)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # Try LangChain first if available
        response = None
        if HAS_LANGCHAIN and self.llm:
            try:
                response = self._make_langchain_call(prompt)
            except Exception as e:
                logger.warning(f"{self.agent_name}: LangChain call failed, falling back to API: {e}")

        # Fall back to direct API call
        if response is None:
            response = self._make_api_call(prompt)

        # Cache the result if caching is enabled
        if use_cache and cache_key:
            self._store_in_cache(cache_key, response)

        return response 