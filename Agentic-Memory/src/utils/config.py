"""
Configuration utility for loading agent-specific settings from config.yaml
"""
import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Cache the loaded config
_config_cache: Optional[Dict[str, Any]] = None


def get_config_path() -> str:
    """Get the path to config.yaml"""
    # Try current directory first
    current_dir = Path.cwd()
    config_path = current_dir / "config.yaml"
    
    if config_path.exists():
        return str(config_path)
    
    # Try parent directories (up to 3 levels)
    for i in range(3):
        current_dir = current_dir.parent
        config_path = current_dir / "config.yaml"
        if config_path.exists():
            return str(config_path)
    
    # Fallback to default location
    return "config.yaml"


def load_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load configuration from config.yaml
    
    Args:
        force_reload: Force reload config even if cached
        
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if _config_cache is not None and not force_reload:
        return _config_cache
    
    config_path = get_config_path()
    
    try:
        with open(config_path, "r") as f:
            _config_cache = yaml.safe_load(f)
        return _config_cache
    except FileNotFoundError:
        print(f"Warning: config.yaml not found at {config_path}, using defaults")
        return {}
    except Exception as e:
        print(f"Error loading config.yaml: {e}, using defaults")
        return {}


def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """
    Get configuration for a specific agent
    
    Args:
        agent_name: Name of the agent (e.g., 'query_analyzer', 'response_synthesizer')
        
    Returns:
        Agent configuration dictionary
    """
    config = load_config()
    agents = config.get("agents", {})
    return agents.get(agent_name, {})


def get_agent_model(agent_name: str, default: str = "qwen3:4b") -> str:
    """
    Get model name for a specific agent
    
    Args:
        agent_name: Name of the agent
        default: Default model if not specified
        
    Returns:
        Model name (e.g., 'llama3:8b', 'mistral:7b')
    """
    agent_config = get_agent_config(agent_name)
    
    # Check if model is specified
    model = agent_config.get("model")
    if model:
        return model
    
    # Fall back to default LLM model
    config = load_config()
    llm_config = config.get("llm", {})
    return llm_config.get("default_model", default)


def get_agent_temperature(agent_name: str, default: float = 0.1) -> float:
    """
    Get temperature for a specific agent
    
    Args:
        agent_name: Name of the agent
        default: Default temperature
        
    Returns:
        Temperature value
    """
    agent_config = get_agent_config(agent_name)
    return agent_config.get("temperature", default)


def get_agent_timeout(agent_name: str, default: int = 30) -> int:
    """
    Get timeout for a specific agent
    
    Args:
        agent_name: Name of the agent
        default: Default timeout in seconds
        
    Returns:
        Timeout in seconds
    """
    agent_config = get_agent_config(agent_name)
    return agent_config.get("timeout", default)


def is_validator_enabled() -> bool:
    """
    Check if validator agent is enabled
    
    Returns:
        True if validator is enabled, False otherwise
    """
    validator_config = get_agent_config("validator")
    return validator_config.get("enabled", False)


def get_ollama_keep_alive() -> str:
    """
    Get Ollama keep_alive setting to prevent model unloading
    
    Returns:
        Keep alive duration (e.g., '30m', '1h')
    """
    config = load_config()
    ollama_config = config.get("llm", {}).get("ollama", {})
    return ollama_config.get("keep_alive", "30m")


def get_mcp_cache_config() -> Dict[str, Any]:
    """
    Get MCP capability caching configuration
    
    Returns:
        Cache configuration with 'enabled', 'ttl_seconds', 'max_cache_size'
    """
    config = load_config()
    memory_config = config.get("memory", {})
    mcp_cache = memory_config.get("mcp_cache", {})
    
    return {
        "enabled": mcp_cache.get("enabled", True),
        "ttl_seconds": mcp_cache.get("ttl_seconds", 300),
        "max_cache_size": mcp_cache.get("max_cache_size", 100)
    }


def get_gpu_config() -> Dict[str, Any]:
    """
    Get GPU configuration
    
    Returns:
        GPU configuration dictionary
    """
    config = load_config()
    return config.get("gpu", {
        "enable_gpu_acceleration": False,
        "device_ids": [0],
        "fallback_to_cpu": True,
        "memory_limit_gb": 4
    })


# For backwards compatibility
def load_agent_config() -> Dict[str, Any]:
    """
    Load agent configurations (alias for backward compatibility)
    
    Returns:
        Agents dictionary from config
    """
    config = load_config()
    return config.get("agents", {})
