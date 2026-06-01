"""
Model Warming Service

Keeps Ollama models active and warm to prevent cold start delays.
Periodically sends keep-alive requests to maintain models in memory.
"""

import time
import asyncio
import logging
import threading
import os
from typing import List, Dict, Optional
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ModelWarmer:
    """
    Service to keep Ollama models warm and prevent cold starts.
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the model warmer.
        
        Args:
            ollama_base_url: Base URL for Ollama API
        """
        self.ollama_base_url = ollama_base_url.rstrip('/')
        self.models_to_warm = [
            "qwen2.5:7b",      # Unified thinking, general & agentic model
        ]
        # Configurable warming interval (default 3 minutes)
        self.warming_interval = int(os.getenv("MODEL_WARMING_INTERVAL", "180"))
        self.keep_alive_duration = os.getenv("MODEL_KEEP_ALIVE", "10m")
        self.is_running = False
        self.warming_thread = None
        self.last_warming = {}
        
    def start_warming(self):
        """Start the model warming service."""
        if self.is_running:
            logger.warning("Model warmer is already running")
            return
            
        self.is_running = True
        self.warming_thread = threading.Thread(target=self._warming_loop, daemon=True)
        self.warming_thread.start()
        logger.info(f"Model warmer started - will keep {self.models_to_warm} warm every {self.warming_interval}s")
        
        # Initial warming
        self._warm_all_models()
    
    def stop_warming(self):
        """Stop the model warming service."""
        self.is_running = False
        if self.warming_thread:
            self.warming_thread.join(timeout=5)
        logger.info("Model warmer stopped")
    
    def _warming_loop(self):
        """Main warming loop that runs in background thread."""
        while self.is_running:
            try:
                self._warm_all_models()
                time.sleep(self.warming_interval)
            except Exception as e:
                logger.error(f"Error in model warming loop: {str(e)}")
                time.sleep(30)  # Wait 30s before retrying on error
    
    def _warm_all_models(self):
        """Warm all registered models."""
        for model in self.models_to_warm:
            try:
                self._warm_model(model)
            except Exception as e:
                logger.error(f"Failed to warm model {model}: {str(e)}")
    
    def _warm_model(self, model_name: str):
        """
        Send a lightweight keep-alive request to a specific model.
        
        Args:
            model_name: Name of the model to warm
        """
        try:
            warm_start = time.time()
            
            # Send a minimal request to keep model in memory
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": "ping"}
                    ],
                    "stream": False,
                    "keep_alive": self.keep_alive_duration,  # Keep model loaded
                    "options": {
                        "num_predict": 1,  # Generate only 1 token
                        "temperature": 0.1
                    }
                },
                timeout=30
            )
            
            warm_time = time.time() - warm_start
            
            if response.status_code == 200:
                self.last_warming[model_name] = datetime.now()
                if warm_time > 5.0:
                    logger.warning(f"Model {model_name} took {warm_time:.2f}s to respond (possible cold start)")
                else:
                    logger.debug(f"Model {model_name} warmed successfully ({warm_time:.3f}s)")
            else:
                logger.error(f"Failed to warm {model_name}: HTTP {response.status_code}")
                
        except requests.Timeout:
            logger.error(f"Timeout warming model {model_name}")
        except Exception as e:
            logger.error(f"Error warming model {model_name}: {str(e)}")
    
    def warm_model_immediately(self, model_name: str):
        """
        Immediately warm a specific model (useful before processing).
        
        Args:
            model_name: Name of the model to warm immediately
        """
        if model_name in self.models_to_warm:
            logger.info(f"Immediately warming model {model_name}")
            self._warm_model(model_name)
        else:
            logger.warning(f"Model {model_name} not in warming list")
    
    def get_status(self) -> Dict:
        """Get the current status of the model warmer."""
        return {
            "is_running": self.is_running,
            "models_to_warm": self.models_to_warm,
            "warming_interval": self.warming_interval,
            "keep_alive_duration": self.keep_alive_duration,
            "last_warming": {
                model: timestamp.isoformat() if timestamp else None
                for model, timestamp in self.last_warming.items()
            },
            "ollama_url": self.ollama_base_url
        }
    
    def add_model(self, model_name: str):
        """Add a model to the warming list."""
        if model_name not in self.models_to_warm:
            self.models_to_warm.append(model_name)
            logger.info(f"Added {model_name} to warming list")
    
    def remove_model(self, model_name: str):
        """Remove a model from the warming list."""
        if model_name in self.models_to_warm:
            self.models_to_warm.remove(model_name)
            logger.info(f"Removed {model_name} from warming list")

# Global model warmer instance
model_warmer = ModelWarmer() 