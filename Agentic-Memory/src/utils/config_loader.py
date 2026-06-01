"""
Configuration Loader for CogniVox Agentic-Memory Service

This module provides a unified configuration management system that supports:
1. YAML configuration files
2. Environment variables
3. Direct API key passing
4. Multiple LLM providers (Ollama, OpenAI, Anthropic, Google, etc.)
5. LangChain init_chat_model integration
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from langchain.chat_models import init_chat_model

# Configure logger
logger = logging.getLogger("cogniVox.config")

def normalize_model_name_for_url(model_name: str) -> str:
    """
    Normalize model name for URL path usage.
    Replaces ':' and '.' with '-' for nginx path-based routing.
    
    Examples:
        qwen2.5:7b -> qwen2-5-7b
        gemma2:2b -> gemma2-2b
        mistral:7b -> mistral-7b
    
    Args:
        model_name: Original model name
    
    Returns:
        Normalized model name for URL paths
    """
    return model_name.replace(":", "-").replace(".", "-")

class ConfigLoader:
    """
    Unified configuration loader for the Agentic-Memory service.
    
    Supports loading configuration from:
    1. YAML files
    2. Environment variables
    3. Direct parameter passing
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        
        logger.info(f"Configuration loaded from: {self.config_path}")
    
    def _find_config_file(self) -> str:
        """
        Find the configuration file in common locations.
        
        Returns:
            Path to the configuration file
        """
        # Common locations to search for config.yaml
        search_paths = [
            "config.yaml",
            "config.yml",
            "src/config.yaml",
            "src/config.yml",
            "../config.yaml",
            "../config.yml",
            os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "..", "config.yml"),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        # If no config file found, create a default path
        default_path = os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml")
        logger.warning(f"No config file found. Using default path: {default_path}")
        return default_path
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the YAML file.
        
        Returns:
            Configuration dictionary
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) or {}
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration when no config file is available.
        
        Returns:
            Default configuration dictionary
        """
        return {
            "llm": {
                "default_provider": "ollama",
                "default_model": "qwen3:4b",
                "default_temperature": 0.7,
                "default_timeout": 30,
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "timeout": 30
                }
            },
            "agents": {},
            "api": {
                "host": "0.0.0.0",
                "port": 8002
            }
        }
    
    def get_llm_config(self, agent_name: Optional[str] = None, 
                       provider: Optional[str] = None,
                       model: Optional[str] = None,
                       api_key: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """
        Get LLM configuration for a specific agent or general use.
        
        Args:
            agent_name: Name of the agent (for agent-specific config)
            provider: LLM provider override
            model: Model name override
            api_key: API key override
            **kwargs: Additional configuration overrides
            
        Returns:
            LLM configuration dictionary
        """
        # Start with default LLM config
        llm_config = self.config.get("llm", {})
        
        # Get agent-specific config if provided
        agent_config = {}
        if agent_name:
            agent_config = self.config.get("agents", {}).get(agent_name, {})
        
        # Determine provider (priority: parameter > agent config > default)
        final_provider = (
            provider or 
            agent_config.get("provider") or 
            llm_config.get("default_provider", "ollama")
        )
        
        # Determine model (priority: parameter > agent config > default)
        final_model = (
            model or 
            agent_config.get("model") or 
            llm_config.get("default_model", "llama3.1")
        )
        
        # Get provider-specific config
        provider_config = llm_config.get(final_provider, {})
        
        # Build final configuration
        final_config = {
            "provider": final_provider,
            "model": final_model,
            "temperature": (
                kwargs.get("temperature") or
                agent_config.get("temperature") or
                provider_config.get("temperature") or
                llm_config.get("default_temperature", 0.7)
            ),
            "timeout": (
                kwargs.get("timeout") or
                agent_config.get("timeout") or
                provider_config.get("timeout") or
                llm_config.get("default_timeout", 30)
            )
        }
        
        # Add provider-specific configuration
        if final_provider == "ollama":
            # Get model-specific base URL if available
            base_url = self.get_base_url_for_model(
                model_name=final_model,
                provider_config=provider_config,
                kwargs_base_url=kwargs.get("base_url")
            )
            
            final_config.update({
                "base_url": base_url,
                "api_path": provider_config.get("api_path", "/api/chat")
            })
        elif final_provider in ["openai", "anthropic", "google"]:
            # Handle API key (priority: parameter > config > environment)
            final_config["api_key"] = (
                api_key or
                provider_config.get("api_key") or
                self._get_env_api_key(final_provider)
            )
            
            if final_provider == "openai":
                final_config["base_url"] = provider_config.get("base_url", "https://api.openai.com/v1")
            elif final_provider == "anthropic":
                final_config["base_url"] = provider_config.get("base_url", "https://api.anthropic.com")
            
            final_config["max_tokens"] = (
                kwargs.get("max_tokens") or
                provider_config.get("max_tokens", 4096)
            )
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in final_config:
                final_config[key] = value
        
        return final_config
    
    def _get_env_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key from environment variables based on provider.
        
        Args:
            provider: LLM provider name
            
        Returns:
            API key from environment or None
        """
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY"
        }
        
        env_key = env_key_map.get(provider.lower())
        if env_key:
            return os.getenv(env_key)
        
        return None
    
    def create_chat_model(self, agent_name: Optional[str] = None,
                         provider: Optional[str] = None,
                         model: Optional[str] = None,
                         api_key: Optional[str] = None,
                         **kwargs):
        """
        Create a chat model using LangChain's init_chat_model.
        
        Args:
            agent_name: Name of the agent (for agent-specific config)
            provider: LLM provider override
            model: Model name override
            api_key: API key override
            **kwargs: Additional configuration overrides
            
        Returns:
            Initialized chat model
        """
        config = self.get_llm_config(
            agent_name=agent_name,
            provider=provider,
            model=model,
            api_key=api_key,
            **kwargs
        )
        
        try:
            # Prepare parameters for init_chat_model
            init_params = {
                "model": config["model"],
                "model_provider": config["provider"],
                "temperature": config["temperature"]
            }
            
            # Add provider-specific parameters
            if config["provider"] == "ollama":
                init_params["base_url"] = config["base_url"]
            elif config["provider"] in ["openai", "anthropic", "google"]:
                if config.get("api_key"):
                    # Set environment variable for the session
                    env_key = self._get_env_key_for_provider(config["provider"])
                    if env_key:
                        os.environ[env_key] = config["api_key"]
                
                if config.get("max_tokens"):
                    init_params["max_tokens"] = config["max_tokens"]
                
                if config.get("base_url") and config["provider"] == "openai":
                    init_params["base_url"] = config["base_url"]
            
            # Add any additional parameters
            for key, value in kwargs.items():
                if key not in init_params and key not in ["agent_name", "provider", "model", "api_key"]:
                    init_params[key] = value
            
            logger.info(f"Creating chat model with provider: {config['provider']}, model: {config['model']}")
            
            # Create and return the model
            return init_chat_model(**init_params)
            
        except Exception as e:
            logger.error(f"Error creating chat model: {str(e)}")
            
            # Fallback to Ollama if available
            if config["provider"] != "ollama":
                logger.warning("Falling back to Ollama provider")
                try:
                    return init_chat_model(
                        model="llama3.1",
                        model_provider="ollama",
                        base_url=config.get("base_url", "http://localhost:11434"),
                        temperature=config["temperature"]
                    )
                except Exception as fallback_e:
                    logger.error(f"Fallback to Ollama also failed: {str(fallback_e)}")
            
            raise e
    
    def _get_env_key_for_provider(self, provider: str) -> Optional[str]:
        """
        Get the environment variable key for a given provider.
        
        Args:
            provider: LLM provider name
            
        Returns:
            Environment variable key or None
        """
        env_key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY"
        }
        
        return env_key_map.get(provider.lower())
    
    def get_base_url_for_model(self, model_name: str, 
                               provider_config: Dict[str, Any],
                               kwargs_base_url: Optional[str] = None) -> str:
        """
        Get base URL for a specific model, supporting model-specific URLs.
        
        This method checks for model-specific URL mappings in the config
        to route different models to dedicated Ollama instances.
        
        Args:
            model_name: Name of the model (e.g., "qwen2.5:7b")
            provider_config: Provider configuration dictionary
            kwargs_base_url: Base URL override from kwargs
            
        Returns:
            Base URL for the model
        """
        # Priority 1: kwargs override
        if kwargs_base_url:
            return kwargs_base_url
        
        # Priority 2: model-specific URL from config
        model_urls = provider_config.get("model_urls", {})
        if model_urls and model_name in model_urls:
            return model_urls[model_name]
        
        # Priority 3: default base_url
        return provider_config.get("base_url", "http://localhost:11434")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        return self.config.get("agents", {}).get(agent_name, {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """
        Get API configuration.
        
        Returns:
            API configuration dictionary
        """
        return self.config.get("api", {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """
        Get memory configuration.
        
        Returns:
            Memory configuration dictionary
        """
        return self.config.get("memory", {})
    
    def get_gpu_config(self) -> Dict[str, Any]:
        """
        Get GPU configuration.
        
        Returns:
            GPU configuration dictionary
        """
        return self.config.get("gpu", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        return self.config.get("logging", {})
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.config = self._load_config()
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {str(e)}")
            return False
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration in memory (not saved to file).
        
        Args:
            updates: Dictionary of configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            def deep_update(base_dict, update_dict):
                for key, value in update_dict.items():
                    if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                        deep_update(base_dict[key], value)
                    else:
                        base_dict[key] = value
            
            deep_update(self.config, updates)
            logger.info("Configuration updated in memory")
            return True
        except Exception as e:
            logger.error(f"Error updating configuration: {str(e)}")
            return False


# Global configuration instance
_global_config = None

def get_config(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Get the global configuration instance.
    
    Args:
        config_path: Path to configuration file (only used on first call)
        
    Returns:
        ConfigLoader instance
    """
    global _global_config
    
    if _global_config is None:
        _global_config = ConfigLoader(config_path)
    
    return _global_config

def create_chat_model_from_config(agent_name: Optional[str] = None, **kwargs):
    """
    Convenience function to create a chat model using the global configuration.
    
    Args:
        agent_name: Name of the agent (for agent-specific config)
        **kwargs: Additional configuration overrides
        
    Returns:
        Initialized chat model
    """
    config = get_config()
    return config.create_chat_model(agent_name=agent_name, **kwargs) 