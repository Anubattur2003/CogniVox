"""
GPU Manager for optimal GPU resource allocation and management.

This module provides a singleton GPU manager that handles allocation
and deallocation of GPU resources with efficient resource tracking.
"""
import os
import time
import logging
import threading
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum, auto
from contextlib import contextmanager
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("cogniVox.gpu_manager")

# Load environment variables
load_dotenv()

class GPUStatus(Enum):
    """Enum for GPU status"""
    AVAILABLE = auto()
    IN_USE = auto()
    COOLING_DOWN = auto()
    OFFLINE = auto()

class GPUResource:
    """Class representing a managed GPU resource"""
    
    def __init__(self, device_id: int, memory_limit: Optional[int] = None):
        """
        Initialize a GPU resource.
        
        Args:
            device_id (int): The GPU device ID
            memory_limit (int, optional): Memory limit in MB, None for no limit
        """
        self.device_id = device_id
        self.memory_limit = memory_limit
        self.status = GPUStatus.AVAILABLE
        self.owner: Optional[str] = None
        self.allocation_time: Optional[float] = None
        self.total_usage_time = 0.0
        self.usage_count = 0
        self.cool_down_start: Optional[float] = None
        self.cool_down_period = float(os.getenv("GPU_COOL_DOWN_PERIOD", "1.0"))  # seconds
        
    def allocate(self, owner: str) -> bool:
        """
        Allocate this GPU to an owner.
        
        Args:
            owner (str): Identifier for who is using the GPU
            
        Returns:
            bool: True if allocation was successful
        """
        if self.status != GPUStatus.AVAILABLE:
            return False
            
        self.status = GPUStatus.IN_USE
        self.owner = owner
        self.allocation_time = time.time()
        self.usage_count += 1
        logger.info(f"GPU {self.device_id} allocated to {owner}")
        return True
        
    def release(self) -> None:
        """
        Release this GPU from its current owner.
        """
        if self.status == GPUStatus.IN_USE and self.allocation_time is not None:
            usage_time = time.time() - self.allocation_time
            self.total_usage_time += usage_time
            logger.info(f"GPU {self.device_id} released by {self.owner} after {usage_time:.2f}s")
            
            # Set to cooling down if cool down is enabled
            if self.cool_down_period > 0:
                self.status = GPUStatus.COOLING_DOWN
                self.cool_down_start = time.time()
            else:
                self.status = GPUStatus.AVAILABLE
                
            self.owner = None
            self.allocation_time = None
            
    def check_cool_down(self) -> None:
        """
        Check if the cool down period is over and update status.
        """
        if (self.status == GPUStatus.COOLING_DOWN and 
            self.cool_down_start is not None and 
            time.time() - self.cool_down_start >= self.cool_down_period):
            
            self.status = GPUStatus.AVAILABLE
            self.cool_down_start = None
            logger.debug(f"GPU {self.device_id} is now available after cooling down")
            
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the GPU resource to a dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the resource
        """
        return {
            "device_id": self.device_id,
            "status": self.status.name,
            "owner": self.owner,
            "memory_limit": self.memory_limit,
            "allocation_time": self.allocation_time,
            "total_usage_time": self.total_usage_time,
            "usage_count": self.usage_count
        }

class GPUManager:
    """Singleton GPU Manager that handles GPU resource allocation and tracking"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GPUManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
            
    def __init__(self):
        """Initialize the GPU manager if not already initialized"""
        with self._lock:
            if self._initialized:
                return
                
            self._initialized = True
            self._gpus: Dict[int, GPUResource] = {}
            self._waiting_queue: List[Tuple[str, threading.Event]] = []
            self._monitor_thread = None
            self._shutdown_event = threading.Event()
            
            # Load configuration from environment variables
            self._gpu_count = int(os.getenv("GPU_COUNT", "1"))
            self._memory_limit = self._parse_memory_limit(os.getenv("GPU_MEMORY_LIMIT", None))
            self._enable_gpus = os.getenv("ENABLE_GPUS", "FALSE").upper() == "TRUE"
            self._allocation_timeout = float(os.getenv("GPU_ALLOCATION_TIMEOUT", "30.0"))  # seconds
            
            # Initialize GPU resources if enabled
            if self._enable_gpus:
                self._initialize_gpus()
                self._start_monitor()
            else:
                logger.info("GPU management is disabled. Set ENABLE_GPUS=TRUE to enable.")
            
    def _parse_memory_limit(self, limit_str: Optional[str]) -> Optional[int]:
        """Parse memory limit from string to integer (MB)"""
        if not limit_str:
            return None
            
        try:
            if limit_str.endswith("GB"):
                return int(float(limit_str[:-2]) * 1024)
            elif limit_str.endswith("MB"):
                return int(limit_str[:-2])
            else:
                return int(limit_str)
        except ValueError:
            logger.warning(f"Invalid GPU memory limit format: {limit_str}, using no limit")
            return None
            
    def _initialize_gpus(self) -> None:
        """Initialize GPU resources based on configuration"""
        try:
            # Import GPU libraries only if GPUs are enabled
            import torch
            
            # Check actual available GPUs
            available_gpus = torch.cuda.device_count()
            if available_gpus == 0:
                logger.warning("No CUDA-capable GPUs detected. GPU support will be disabled.")
                self._enable_gpus = False
                return
                
            actual_gpu_count = min(self._gpu_count, available_gpus)
            logger.info(f"Initializing {actual_gpu_count} of {available_gpus} available GPUs")
            
            # Create GPU resources
            for i in range(actual_gpu_count):
                self._gpus[i] = GPUResource(device_id=i, memory_limit=self._memory_limit)
                logger.info(f"Registered GPU {i} with memory limit: {self._memory_limit or 'None'} MB")
                
        except ImportError:
            logger.warning("PyTorch not available. GPU support will be disabled.")
            self._enable_gpus = False
        except Exception as e:
            logger.error(f"Failed to initialize GPUs: {str(e)}")
            self._enable_gpus = False
            
    def _start_monitor(self) -> None:
        """Start the GPU monitoring thread"""
        if not self._enable_gpus:
            return
            
        def monitor_loop():
            while not self._shutdown_event.is_set():
                try:
                    with self._lock:
                        # Update GPU statuses
                        for gpu in self._gpus.values():
                            gpu.check_cool_down()
                            
                        # Process waiting queue if GPUs are available
                        if self._waiting_queue and any(gpu.status == GPUStatus.AVAILABLE for gpu in self._gpus.values()):
                            owner, event = self._waiting_queue.pop(0)
                            # Attempt allocation
                            if self._allocate_gpu_internal(owner):
                                event.set()
                                
                except Exception as e:
                    logger.error(f"Error in GPU monitor thread: {str(e)}")
                    
                # Sleep before next check
                time.sleep(0.1)
                
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("GPU monitoring thread started")
        
    def shutdown(self) -> None:
        """Shutdown the GPU manager and release all resources"""
        with self._lock:
            if not self._initialized or not self._enable_gpus:
                return
                
            self._shutdown_event.set()
            
            # Release all GPUs
            for gpu in self._gpus.values():
                if gpu.status == GPUStatus.IN_USE:
                    gpu.release()
                    
            # Clear waiting queue and signal all waiting threads
            for _, event in self._waiting_queue:
                event.set()
            self._waiting_queue.clear()
            
            logger.info("GPU Manager shutdown complete")
            
    def _allocate_gpu_internal(self, owner: str) -> Optional[int]:
        """
        Internal method to allocate an available GPU.
        
        Args:
            owner (str): Identifier for who is allocating the GPU
            
        Returns:
            Optional[int]: Device ID of allocated GPU or None if none available
        """
        # Find available GPU with least usage
        available_gpus = [gpu for gpu in self._gpus.values() if gpu.status == GPUStatus.AVAILABLE]
        if not available_gpus:
            return None
            
        # Sort by usage count to balance load
        gpu = min(available_gpus, key=lambda g: g.usage_count)
        if gpu.allocate(owner):
            return gpu.device_id
        return None
        
    def allocate_gpu(self, owner: str, wait: bool = True, timeout: Optional[float] = None) -> Optional[int]:
        """
        Allocate a GPU to the specified owner.
        
        Args:
            owner (str): Identifier for who is allocating the GPU
            wait (bool): Whether to wait if no GPUs are available
            timeout (float, optional): Maximum time to wait in seconds
                
        Returns:
            Optional[int]: Device ID of allocated GPU or None if not available/timeout
        """
        if not self._enable_gpus:
            logger.warning("GPU allocation requested but GPU support is disabled")
            return None
            
        with self._lock:
            # Try immediate allocation
            device_id = self._allocate_gpu_internal(owner)
            if device_id is not None or not wait:
                return device_id
                
            # Setup waiting
            timeout = timeout or self._allocation_timeout
            event = threading.Event()
            self._waiting_queue.append((owner, event))
            
        # Wait outside the lock
        if event.wait(timeout):
            # We were signaled, try to get our GPU
            with self._lock:
                for gpu in self._gpus.values():
                    if gpu.owner == owner:
                        return gpu.device_id
                        
        # Timeout or signaled but GPU already taken
        with self._lock:
            # Remove from waiting queue if still there
            self._waiting_queue = [(o, e) for o, e in self._waiting_queue if o != owner]
        return None
        
    def release_gpu(self, owner: str) -> bool:
        """
        Release GPU(s) allocated to the specified owner.
        
        Args:
            owner (str): Identifier for who is releasing the GPU
            
        Returns:
            bool: True if any GPU was released
        """
        if not self._enable_gpus:
            return False
            
        with self._lock:
            released = False
            for gpu in self._gpus.values():
                if gpu.owner == owner:
                    gpu.release()
                    released = True
            return released
            
    def get_gpu_status(self) -> List[Dict[str, Any]]:
        """
        Get the status of all managed GPUs.
        
        Returns:
            List[Dict[str, Any]]: List of GPU status dictionaries
        """
        with self._lock:
            return [gpu.to_dict() for gpu in self._gpus.values()]
            
    def get_allocated_gpu(self, owner: str) -> Optional[int]:
        """
        Get the device ID of a GPU allocated to the specified owner.
        
        Args:
            owner (str): Identifier for who owns the GPU
            
        Returns:
            Optional[int]: Device ID or None if no GPU allocated to owner
        """
        with self._lock:
            for gpu in self._gpus.values():
                if gpu.owner == owner:
                    return gpu.device_id
            return None
            
    @contextmanager
    def gpu_context(self, owner: str, wait: bool = True, timeout: Optional[float] = None):
        """
        Context manager for GPU allocation and automatic release.
        
        Args:
            owner (str): Identifier for who is using the GPU
            wait (bool): Whether to wait if no GPUs are available
            timeout (float, optional): Maximum time to wait in seconds
            
        Yields:
            Optional[int]: Device ID of allocated GPU or None if not available
        """
        device_id = None
        try:
            device_id = self.allocate_gpu(owner, wait, timeout)
            yield device_id
        finally:
            if device_id is not None:
                self.release_gpu(owner)
                
    def is_gpu_enabled(self) -> bool:
        """
        Check if GPU support is enabled.
        
        Returns:
            bool: True if GPU support is enabled
        """
        return self._enable_gpus 