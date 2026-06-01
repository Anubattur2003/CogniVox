import os
from typing import Dict, List, Any, Optional

import numpy as np
import torch
from tqdm import tqdm
import requests

from src.config import OLLAMA_HOST, EMBEDDING_MODEL, USE_CUDA


class OllamaEmbeddingsGenerator:
    """
    Generate text embeddings using Ollama models.
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, host: str = OLLAMA_HOST):
        """
        Initialize the embeddings generator.
        
        Args:
            model_name: Name of the Ollama embedding model.
            host: Ollama API host URL.
        """
        self.model_name = model_name
        self.host = host.rstrip("/")
        self.device = "cuda" if USE_CUDA and torch.cuda.is_available() else "cpu"
        
    def _check_model_availability(self) -> bool:
        """
        Check if the specified model is available in Ollama.
        
        Returns:
            True if the model is available, False otherwise.
        """
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(model["name"] == self.model_name for model in models)
            return False
        except Exception as e:
            print(f"Error checking model availability: {e}")
            return False
            
    def _pull_model(self) -> bool:
        """
        Pull the model if it's not available.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": self.model_name}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error pulling model: {e}")
            return False
            
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.
        
        Args:
            text: The input text.
            
        Returns:
            A list of floats representing the embedding.
        """
        # Handle empty text
        if not text or not isinstance(text, str):
            print("Cannot generate embedding for empty or non-string text")
            return []
            
        try:
            response = requests.post(
                f"{self.host}/api/embed",
                json={"model": self.model_name, "input": text},
                timeout=30  # Add timeout to prevent hanging requests
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                # Verify the embedding is valid
                if embedding and all(isinstance(x, (int, float)) for x in embedding):
                    return embedding
                else:
                    print(f"Invalid embedding returned from API")
                    return []
            else:
                print(f"Error generating embedding (HTTP {response.status_code}): {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Request exception during embedding generation: {e}")
            return []
        except Exception as e:
            print(f"Unexpected exception during embedding generation: {e}")
            return []
            
    def generate_embeddings(self, texts: List[str], batch_size: int = 1) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts.
            batch_size: Number of texts to process in one batch.
            
        Returns:
            List of embeddings.
        """
        # Ensure the model is available
        if not self._check_model_availability():
            print(f"Model {self.model_name} not available. Attempting to pull...")
            if not self._pull_model():
                raise RuntimeError(f"Failed to pull model {self.model_name}")
                
        # Process texts in batches
        embeddings = []
        
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = [self.generate_embedding(text) for text in batch_texts]
            embeddings.extend(batch_embeddings)
            
        return embeddings
    
    def process_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Process text chunks and add embeddings.
        
        Args:
            chunks: List of dictionaries containing text chunks.
            
        Returns:
            List of dictionaries with embeddings added.
        """
        # Skip processing if no chunks
        if not chunks:
            return []
            
        # Extract texts from chunks, filtering out empty or non-string texts
        valid_chunks = []
        valid_texts = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if text and isinstance(text, str):
                valid_chunks.append(chunk)
                valid_texts.append(text)
        
        # Return early if no valid texts
        if not valid_texts:
            return chunks
            
        # Generate embeddings
        embeddings = self.generate_embeddings(valid_texts)
        
        # Add embeddings to chunks, checking for valid embeddings
        for i, embedding in enumerate(embeddings):
            if i < len(valid_chunks) and embedding:  # Ensure index is valid and embedding is not empty
                valid_chunks[i]["embedding"] = embedding
            else:
                # If embedding generation failed, add a zero vector
                if i < len(valid_chunks):
                    # Create a zero vector of appropriate size (default to 384 if we can't determine)
                    embedding_size = 384
                    if embeddings and any(embeddings) and len(embeddings[0]) > 0:
                        embedding_size = len(embeddings[0])
                    valid_chunks[i]["embedding"] = [0.0] * embedding_size
        
        return valid_chunks
