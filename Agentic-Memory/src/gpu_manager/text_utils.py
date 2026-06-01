"""
GPU-accelerated text processing utilities.

This module provides GPU-accelerated functions for common text operations
used in the memory and agent components of the application.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, Set
import time

# Configure logging
logger = logging.getLogger("cogniVox.gpu_manager")

# Try to import required libraries
try:
    import torch
    import numpy as np
    from sentence_transformers import SentenceTransformer
    NLP_LIBS_AVAILABLE = True
except ImportError:
    NLP_LIBS_AVAILABLE = False
    logger.warning("NLP libraries not available, GPU text utilities will be limited")

from .gpu_manager import GPUManager
from .utils import to_device, tensor_to_numpy, numpy_to_tensor, get_optimal_device
from .decorators import gpu_required

class GPUTextEncoder:
    """GPU-accelerated text encoder for embeddings and similarity operations"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GPUTextEncoder, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = None, show_progress_bar: bool = False):
        """
        Initialize the GPU text encoder with a sentence transformer model.
        
        Args:
            model_name (str, optional): Name of the sentence transformer model
            show_progress_bar (bool): Whether to show progress bars during batch processing
        """
        if self._initialized:
            return
            
        self._initialized = True
        self.gpu_manager = GPUManager()
        
        # Load configuration
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = None
        self.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
        self.device_id = None
        self.show_progress_bar = show_progress_bar if os.getenv("SHOW_ENCODING_PROGRESS", "FALSE").upper() != "FALSE" else False
        
        # Initialize model if possible
        self._initialize_model()
        
    def _initialize_model(self) -> bool:
        """
        Initialize the text encoder model.
        
        Returns:
            bool: True if successful
        """
        if not NLP_LIBS_AVAILABLE:
            logger.warning("NLP libraries not available, model initialization skipped")
            return False
            
        try:
            # Allocate GPU if available
            owner = "GPUTextEncoder.model"
            self.device_id = self.gpu_manager.allocate_gpu(owner)
            
            # Select the appropriate device
            device = torch.device(f'cuda:{self.device_id}' if self.device_id is not None else 'cpu')
            logger.info(f"Initializing text encoder model {self.model_name} on {device}")
            
            # Initialize model on selected device
            self.model = SentenceTransformer(self.model_name, device=device)
            return True
        except Exception as e:
            logger.error(f"Error initializing text encoder model: {str(e)}")
            if self.device_id is not None:
                self.gpu_manager.release_gpu(owner)
                self.device_id = None
            return False
            
    def shutdown(self):
        """Release GPU resources"""
        if self.device_id is not None:
            self.gpu_manager.release_gpu("GPUTextEncoder.model")
            self.device_id = None
            self.model = None
            self._initialized = False
    
    @gpu_required(owner_param=None, device_param="device_id")
    def encode(self, texts: List[str], batch_size: int = None, device_id: Optional[int] = None,
               show_progress_bar: Optional[bool] = None) -> np.ndarray:
        """
        Encode texts to embeddings.
        
        Args:
            texts (List[str]): List of texts to encode
            batch_size (int, optional): Batch size for encoding
            device_id (int, optional): GPU device ID
            show_progress_bar (bool, optional): Whether to show progress bar
            
        Returns:
            np.ndarray: Array of embeddings
        """
        if not NLP_LIBS_AVAILABLE or self.model is None:
            logger.warning("Model not available for encoding")
            return np.zeros((len(texts), 384))  # Default embedding size
            
        try:
            # Use provided device or model's device
            if device_id is not None and device_id != self.device_id:
                # If model is on a different device, move it
                device = torch.device(f'cuda:{device_id}')
                self.model.to(device)
                self.device_id = device_id
                
            # Set batch size
            batch_size = batch_size or self.batch_size
            
            # Determine whether to show progress bar
            show_progress = self.show_progress_bar if show_progress_bar is None else show_progress_bar
            
            # Encode texts
            start_time = time.time()
            embeddings = self.model.encode(texts, batch_size=batch_size, show_progress_bar=show_progress)
            elapsed = time.time() - start_time
            
            logger.debug(f"Encoded {len(texts)} texts in {elapsed:.2f}s ({len(texts)/elapsed:.1f} texts/s)")
            return embeddings
        except Exception as e:
            logger.error(f"Error encoding texts: {str(e)}")
            return np.zeros((len(texts), 384))  # Default embedding size
    
    @gpu_required(owner_param=None, device_param="device_id")
    def get_similarities(self, query: str, texts: List[str], device_id: Optional[int] = None,
                        show_progress_bar: Optional[bool] = None) -> np.ndarray:
        """
        Calculate similarities between a query and a list of texts.
        
        Args:
            query (str): Query text
            texts (List[str]): List of texts to compare against
            device_id (int, optional): GPU device ID
            show_progress_bar (bool, optional): Whether to show progress bar
            
        Returns:
            np.ndarray: Array of similarity scores (0-1)
        """
        if not texts:
            return np.array([])
            
        # Encode query and texts
        query_embedding = self.encode([query], device_id=device_id, show_progress_bar=False)
        texts_embeddings = self.encode(texts, device_id=device_id, 
                                      show_progress_bar=show_progress_bar)
        
        # Convert to tensors if using GPU
        if device_id is not None and NLP_LIBS_AVAILABLE:
            device = torch.device(f'cuda:{device_id}')
            query_embedding = torch.from_numpy(query_embedding).to(device)
            texts_embeddings = torch.from_numpy(texts_embeddings).to(device)
            
            # Calculate cosine similarities
            similarities = torch.nn.functional.cosine_similarity(query_embedding, texts_embeddings)
            return tensor_to_numpy(similarities)
        else:
            # Calculate similarities on CPU
            similarities = np.zeros(len(texts))
            for i, embedding in enumerate(texts_embeddings):
                dot_product = np.dot(query_embedding[0], embedding)
                norm_product = np.linalg.norm(query_embedding[0]) * np.linalg.norm(embedding)
                similarities[i] = dot_product / norm_product if norm_product > 0 else 0
                
            return similarities
    
    @gpu_required(owner_param=None, device_param="device_id")
    def semantic_search(self, query: str, texts: List[str], top_k: int = 5, 
                         threshold: float = 0.5, device_id: Optional[int] = None,
                         show_progress_bar: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Perform semantic search to find most similar texts.
        
        Args:
            query (str): Query text
            texts (List[str]): List of texts to search
            top_k (int): Number of top results to return
            threshold (float): Minimum similarity threshold
            device_id (int, optional): GPU device ID
            show_progress_bar (bool, optional): Whether to show progress bar
            
        Returns:
            List[Dict[str, Any]]: List of results with text and score
        """
        if not texts:
            return []
            
        # Get similarities
        similarities = self.get_similarities(query, texts, device_id=device_id, 
                                           show_progress_bar=show_progress_bar)
        
        # Sort by similarity and filter by threshold
        results = []
        for i, score in sorted(enumerate(similarities), key=lambda x: x[1], reverse=True):
            if score >= threshold and len(results) < top_k:
                results.append({
                    "index": i,
                    "text": texts[i],
                    "score": float(score)
                })
                
        return results
        
# Create singleton instance for easy import
text_encoder = GPUTextEncoder(show_progress_bar=False) 