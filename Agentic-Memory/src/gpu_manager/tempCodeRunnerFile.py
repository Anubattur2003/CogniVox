"""
Simple test for GPU allocation.
"""
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the GPU Manager
from src.gpu_manager import GPUManager

# Test allocation
owner = "example_basic"
gpu_manager = GPUManager()
device_id = gpu_manager.allocate_gpu(owner)

if device_id is not None:
    print(f"Allocated GPU {device_id} to {owner}")
    # Do some work
    # ...
    # Release the GPU
    gpu_manager.release_gpu(owner)
    print(f"Released GPU {device_id}")
else:
    print("No GPU was allocated (GPU support may be disabled in .env)")
    print("Check if ENABLE_GPUS=TRUE is set in your .env file.")