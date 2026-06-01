import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional

def load_env() -> Dict[str, Any]:
    """
    Load environment variables from .env file
    
    Returns:
        Dict[str, Any]: Dictionary of environment variables
    """
    # Load environment variables from .env file
    load_dotenv()
    
    return {
        # Ollama Configuration
        "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "ollama_default_model": os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.1"),
    }

def get_env_var(key: str, default: Optional[Any] = None) -> Any:
    """
    Get a specific environment variable
    
    Args:
        key (str): Key of the environment variable
        default (Any, optional): Default value if not found
        
    Returns:
        Any: Value of the environment variable or default
    """
    env_vars = load_env()
    return env_vars.get(key, default) 