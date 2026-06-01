"""
Utility functions for GPU-based operations.

This module provides helper functions for working with GPU tensors,
memory management, and common GPU operations.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Tuple, Union
import gc
import numpy as np

# Configure logging
logger = logging.getLogger("cogniVox.gpu_manager")

# Try to import torch and related libraries
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, GPU utilities will be limited")

def is_gpu_available() -> bool:
    """
    Check if GPU is available for use.
    
    Returns:
        bool: True if GPU is available
    """
    if not TORCH_AVAILABLE:
        return False
    return torch.cuda.is_available()

def get_gpu_memory_usage(device_id: Optional[int] = None) -> Dict[str, float]:
    """
    Get GPU memory usage statistics.
    
    Args:
        device_id (int, optional): GPU device ID. If None, shows all devices.
        
    Returns:
        Dict[str, float]: Dictionary with memory usage statistics (in MB)
    """
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return {"error": "GPU not available"}
        
    if device_id is not None:
        # Single device stats
        try:
            stats = {}
            device = torch.device(f'cuda:{device_id}')
            stats["total"] = torch.cuda.get_device_properties(device_id).total_memory / (1024**2)
            stats["reserved"] = torch.cuda.memory_reserved(device_id) / (1024**2)
            stats["allocated"] = torch.cuda.memory_allocated(device_id) / (1024**2)
            stats["free"] = stats["total"] - stats["reserved"]
            stats["available"] = stats["reserved"] - stats["allocated"]
            return stats
        except Exception as e:
            logger.error(f"Error getting memory usage for device {device_id}: {str(e)}")
            return {"error": str(e)}
    else:
        # All devices stats
        stats = {}
        for i in range(torch.cuda.device_count()):
            stats[f"device_{i}"] = get_gpu_memory_usage(i)
        return stats

def clear_gpu_memory(device_id: Optional[int] = None) -> bool:
    """
    Clear GPU memory (cached tensors) for specified device.
    
    Args:
        device_id (int, optional): GPU device ID. If None, clears all devices.
        
    Returns:
        bool: True if successful
    """
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return False
        
    try:
        # Force garbage collection first
        gc.collect()
        
        if device_id is not None:
            # Clear specific device
            with torch.cuda.device(device_id):
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
        else:
            # Clear all devices
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
            
        logger.debug(f"Cleared GPU memory for {'all devices' if device_id is None else f'device {device_id}'}")
        return True
    except Exception as e:
        logger.error(f"Error clearing GPU memory: {str(e)}")
        return False

def to_device(data: Any, device_id: Optional[int] = None) -> Any:
    """
    Move tensors, lists, tuples or dictionaries of tensors to specified device.
    
    Args:
        data: Tensor, list, tuple or dict to move to device
        device_id (int, optional): GPU device ID. If None, uses CPU.
        
    Returns:
        Data moved to specified device
    """
    if not TORCH_AVAILABLE:
        return data
        
    device = torch.device(f'cuda:{device_id}' if device_id is not None else 'cpu')
    
    if isinstance(data, torch.Tensor):
        return data.to(device)
    elif isinstance(data, (list, tuple)):
        return [to_device(item, device_id) for item in data]
    elif isinstance(data, dict):
        return {k: to_device(v, device_id) for k, v in data.items()}
    else:
        return data

def numpy_to_tensor(array: np.ndarray, device_id: Optional[int] = None) -> Any:
    """
    Convert numpy array to PyTorch tensor on specified device.
    
    Args:
        array (np.ndarray): Numpy array to convert
        device_id (int, optional): GPU device ID. If None, uses CPU.
        
    Returns:
        torch.Tensor: PyTorch tensor on specified device
    """
    if not TORCH_AVAILABLE:
        logger.warning("PyTorch not available, returning original array")
        return array
        
    device = torch.device(f'cuda:{device_id}' if device_id is not None else 'cpu')
    return torch.from_numpy(array).to(device)

def tensor_to_numpy(tensor: Any) -> np.ndarray:
    """
    Convert PyTorch tensor to numpy array (detached from computation graph).
    
    Args:
        tensor: PyTorch tensor to convert
        
    Returns:
        np.ndarray: Numpy array
    """
    if not TORCH_AVAILABLE:
        return tensor
        
    if isinstance(tensor, torch.Tensor):
        return tensor.detach().cpu().numpy()
    return tensor

def get_optimal_device(preferred_device_id: Optional[int] = None) -> Tuple[str, Optional[int]]:
    """
    Get the optimal device based on availability and memory usage.
    
    Args:
        preferred_device_id (int, optional): Preferred GPU device ID
        
    Returns:
        Tuple[str, Optional[int]]: Tuple of (device_type, device_id)
            where device_type is either 'cuda' or 'cpu'
    """
    if not TORCH_AVAILABLE or not torch.cuda.is_available():
        return 'cpu', None
        
    device_count = torch.cuda.device_count()
    if device_count == 0:
        return 'cpu', None
        
    # If preferred device is specified and available, use it
    if preferred_device_id is not None and preferred_device_id < device_count:
        return 'cuda', preferred_device_id
        
    # Find device with most free memory
    max_free = -1
    best_device = 0
    
    for i in range(device_count):
        stats = get_gpu_memory_usage(i)
        if "free" in stats and stats["free"] > max_free:
            max_free = stats["free"]
            best_device = i
            
    # If all GPUs are heavily utilized, consider using CPU
    memory_threshold_mb = float(os.getenv("GPU_MEMORY_THRESHOLD_MB", "500"))
    if max_free < memory_threshold_mb:
        logger.warning(f"All GPUs have less than {memory_threshold_mb}MB free memory, using CPU")
        return 'cpu', None
        
    return 'cuda', best_device 