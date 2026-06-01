"""
Decorators for GPU resource management.

This module provides function and method decorators to easily
manage GPU resources in the application.
"""
import functools
import inspect
import time
import logging
from typing import Any, Callable, Dict, Optional, Union, TypeVar, cast

from .gpu_manager import GPUManager

# Configure logging
logger = logging.getLogger("cogniVox.gpu_manager")

F = TypeVar('F', bound=Callable[..., Any])

def gpu_required(
    owner_param: Optional[str] = None, 
    wait: bool = True, 
    timeout: Optional[float] = None,
    device_param: str = "device_id"
) -> Callable[[F], F]:
    """
    Decorator that ensures a GPU is allocated for the function.
    
    The GPU device ID will be injected as a keyword argument with the name
    specified by device_param, or will replace an existing parameter with
    that name.
    
    Args:
        owner_param (str, optional): Name of the parameter that contains the owner ID.
            If None, a unique ID based on function name will be used.
        wait (bool): Whether to wait for a GPU if none is immediately available
        timeout (float, optional): Maximum wait time in seconds
        device_param (str): Name of the parameter to inject the device ID into
        
    Returns:
        Callable: Decorated function with automatic GPU allocation
    """
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get GPU Manager singleton
            gpu_manager = GPUManager()
            
            if not gpu_manager.is_gpu_enabled():
                # If GPUs are disabled, call the function with None for device_id
                if device_param not in sig.parameters and device_param not in kwargs:
                    kwargs[device_param] = None
                return func(*args, **kwargs)
            
            # Determine owner ID
            owner = None
            if owner_param is not None:
                # Get owner from parameter
                bound_args = sig.bind_partial(*args, **kwargs)
                if owner_param in bound_args.arguments:
                    owner = bound_args.arguments[owner_param]
            
            if owner is None:
                # Use function name as owner if not specified
                owner = f"{func.__module__}.{func.__qualname__}"
            
            # Allocate GPU
            logger.debug(f"Allocating GPU for {owner} (from {func.__qualname__})")
            device_id = gpu_manager.allocate_gpu(owner, wait, timeout)
            
            # Inject device ID into kwargs if not already present
            if device_param not in kwargs:
                kwargs[device_param] = device_id
                
            try:
                # Call the function with the GPU device ID
                return func(*args, **kwargs)
            finally:
                # Release the GPU after the function finishes
                if device_id is not None:
                    gpu_manager.release_gpu(owner)
                    logger.debug(f"Released GPU {device_id} for {owner} (from {func.__qualname__})")
                    
        return cast(F, wrapper)
    return decorator

def release_gpu_after(owner_param: str) -> Callable[[F], F]:
    """
    Decorator that releases any GPU allocated to the owner after the function completes.
    
    Args:
        owner_param (str): Name of the parameter that contains the owner ID
        
    Returns:
        Callable: Decorated function with automatic GPU release
    """
    def decorator(func: F) -> F:
        sig = inspect.signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get GPU Manager singleton
            gpu_manager = GPUManager()
            
            if not gpu_manager.is_gpu_enabled():
                return func(*args, **kwargs)
            
            # Determine owner ID
            bound_args = sig.bind_partial(*args, **kwargs)
            if owner_param not in bound_args.arguments:
                return func(*args, **kwargs)
                
            owner = bound_args.arguments[owner_param]
            
            try:
                # Call the function
                return func(*args, **kwargs)
            finally:
                # Release the GPU after the function finishes
                gpu_manager.release_gpu(owner)
                logger.debug(f"Released all GPUs for {owner} (from {func.__qualname__})")
                    
        return cast(F, wrapper)
    return decorator 