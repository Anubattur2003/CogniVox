"""
Ollama Configuration Helper

Provides utilities to configure Ollama for optimal performance and model management.
"""

import os
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OllamaConfig:
    """
    Helper class to configure Ollama for optimal performance.
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama configuration helper.
        
        Args:
            ollama_base_url: Base URL for Ollama API
        """
        self.ollama_base_url = ollama_base_url.rstrip('/')
    
    def get_loaded_models(self) -> Dict[str, Any]:
        """
        Get currently loaded models from Ollama.
        
        Returns:
            Dict containing loaded models information
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/ps", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get loaded models: HTTP {response.status_code}")
                return {"models": []}
        except Exception as e:
            logger.error(f"Error getting loaded models: {str(e)}")
            return {"models": []}
    
    def get_available_models(self) -> Dict[str, Any]:
        """
        Get all available models from Ollama.
        
        Returns:
            Dict containing available models information
        """
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get available models: HTTP {response.status_code}")
                return {"models": []}
        except Exception as e:
            logger.error(f"Error getting available models: {str(e)}")
            return {"models": []}
    
    def preload_model(self, model_name: str, keep_alive: str = "10m") -> bool:
        """
        Preload a model into memory with specified keep-alive duration.
        
        Args:
            model_name: Name of the model to preload
            keep_alive: How long to keep the model loaded (e.g., "10m", "1h")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Preloading model {model_name} with keep_alive={keep_alive}")
            
            # Use the generate endpoint to load the model without generating content
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": "",  # Empty prompt to just load the model
                    "stream": False,
                    "keep_alive": keep_alive
                },
                timeout=60
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully preloaded model {model_name}")
                return True
            else:
                logger.error(f"Failed to preload model {model_name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error preloading model {model_name}: {str(e)}")
            return False
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Unloading model {model_name}")
            
            response = requests.post(
                f"{self.ollama_base_url}/api/generate",
                json={
                    "model": model_name,
                    "keep_alive": 0  # Immediately unload
                },
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully unloaded model {model_name}")
                return True
            else:
                logger.error(f"Failed to unload model {model_name}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading model {model_name}: {str(e)}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dict containing model information
        """
        try:
            response = requests.post(
                f"{self.ollama_base_url}/api/show",
                json={"name": model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get model info for {model_name}: HTTP {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {str(e)}")
            return {}
    
    def optimize_for_multi_model_usage(self, models: list, keep_alive: str = "15m") -> Dict[str, bool]:
        """
        Optimize Ollama for multi-model usage by preloading all required models.
        
        Args:
            models: List of model names to preload
            keep_alive: How long to keep models loaded
            
        Returns:
            Dict mapping model names to preload success status
        """
        results = {}
        
        logger.info(f"Optimizing Ollama for multi-model usage: {models}")
        
        for model in models:
            results[model] = self.preload_model(model, keep_alive)
        
        return results

# Global instance
ollama_config = OllamaConfig() 