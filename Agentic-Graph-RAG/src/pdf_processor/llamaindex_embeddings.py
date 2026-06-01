"""
LlamaIndex-based embeddings generator for CogniVox.

This module provides embedding generation using LlamaIndex's embedding models,
ensuring compatibility with the existing system while leveraging LlamaIndex's capabilities.
"""
import logging
from typing import Dict, List, Any, Optional
from tqdm import tqdm

from llama_index.embeddings.ollama import OllamaEmbedding

from src.config import OLLAMA_HOST, EMBEDDING_MODEL

# Configure logging to suppress httpx INFO logs
logging.getLogger("httpx").setLevel(logging.WARNING)


class LlamaIndexEmbeddingsGenerator:
    """
    Generate text embeddings using LlamaIndex's Ollama embedding models.
    """
    
    def __init__(self, 
                 model_name: str = EMBEDDING_MODEL, 
                 host: str = OLLAMA_HOST):
        """
        Initialize the LlamaIndex embeddings generator.
        
        Args:
            model_name: Name of the Ollama embedding model.
            host: Ollama API host URL.
        """
        self.model_name = model_name
        self.host = host.rstrip("/")
        
        # Initialize LlamaIndex Ollama embedding model
        self.embedding_model = OllamaEmbedding(
            model_name=self.model_name,
            base_url=self.host,
        )
        
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding for a single text.
        
        Args:
            text: The input text.
            
        Returns:
            A list of floats representing the embedding.
        """
        if not text or not isinstance(text, str):
            print("Warning: Cannot generate embedding for empty or non-string text")
            return []
            
        try:
            # Use LlamaIndex's embedding model
            embedding = self.embedding_model.get_text_embedding(text)
            
            if embedding and all(isinstance(x, (int, float)) for x in embedding):
                return embedding
            else:
                print("Warning: Invalid embedding returned from LlamaIndex model")
                return []
                
        except Exception as e:
            print(f"Error generating embedding with LlamaIndex: {e}")
            return []
            
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts.
            
        Returns:
            List of embeddings.
        """
        try:
            # Try batch embedding
            return self.embedding_model.get_text_embedding_batch(texts)
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            # Fallback to per-text embedding
            return [self.generate_embedding(text) for text in texts]
    
    def process_chunks(self, chunks: List[Dict], batch_size: int = 4) -> List[Dict]:
        """
        Process text chunks and add embeddings using LlamaIndex.
        
        Args:
            chunks: List of dictionaries containing text chunks.
            batch_size: Size of each batch for processing.
            
        Returns:
            List of dictionaries with embeddings added.
        """
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
        
        if not valid_texts:
            return chunks
            
        embeddings = []
        total = len(valid_texts)
        
        try:
            with tqdm(total=total, desc="Generating embeddings", unit="chunk") as pbar:
                for i in range(0, total, batch_size):
                    batch_texts = valid_texts[i:i+batch_size]
                    try:
                        batch_embeddings = self.embedding_model.get_text_embedding_batch(batch_texts)
                    except Exception as batch_e:
                        print(f"Warning: Batch embedding failed, falling back to per-chunk: {batch_e}")
                        batch_embeddings = []
                        for text in batch_texts:
                            batch_embeddings.append(self.generate_embedding(text))
                    embeddings.extend(batch_embeddings)
                    pbar.update(len(batch_texts))
        except Exception as e:
            print(f"Error during embedding generation: {e}")
            # Fallback to per-chunk with tqdm - this should only run if the try block fails
            embeddings = []  # Reset embeddings since the try block failed
            with tqdm(total=total, desc="Generating embeddings", unit="chunk") as pbar:
                for i in range(0, total, batch_size):
                    batch_texts = valid_texts[i:i+batch_size]
                    batch_embeddings = self.generate_embeddings_batch(batch_texts)
                    embeddings.extend(batch_embeddings)
                    pbar.update(len(batch_texts))
        
        # Add embeddings to chunks
        for i, embedding in enumerate(embeddings):
            if i < len(valid_chunks) and embedding:
                valid_chunks[i]["embedding"] = embedding
            else:
                # If embedding generation failed, add a zero vector
                if i < len(valid_chunks):
                    # Create a zero vector of appropriate size
                    embedding_size = 384  # Default size
                    if embeddings and any(embeddings):
                        # Find first valid embedding to determine size
                        for emb in embeddings:
                            if emb and len(emb) > 0:
                                embedding_size = len(emb)
                                break
                    valid_chunks[i]["embedding"] = [0.0] * embedding_size
        
        return valid_chunks
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings generated by this model.
        
        Returns:
            Embedding dimension.
        """
        try:
            # Generate a test embedding to determine dimension
            test_embedding = self.generate_embedding("test")
            return len(test_embedding) if test_embedding else 384
        except Exception:
            return 384  # Default dimension for many embedding models 