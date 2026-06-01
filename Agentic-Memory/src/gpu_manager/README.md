# GPU Manager for CogniVox

A robust GPU resource management system for optimizing GPU usage across the application. This module provides efficient GPU allocation, tracking, and deallocation to ensure optimal resource utilization.

## Features

- **Singleton GPU Manager**: Central control of GPU resources with thread-safe access
- **Dynamic Resource Allocation**: Intelligent allocation based on availability and usage patterns
- **Decorator Support**: Easy integration with functions through decorators
- **Context Managers**: Clean resource management with context managers
- **Memory Optimization**: Memory usage tracking and optimization
- **Cool-down Periods**: Prevent thrashing with configurable cool-down periods
- **Graceful Fallbacks**: Automatic CPU fallbacks when GPUs are unavailable
- **Text Processing Utilities**: GPU-accelerated text embedding and similarity

## Configuration

Configure GPU manager through environment variables in `.env`:

```
# GPU Configuration
ENABLE_GPUS=TRUE                # Enable GPU support (TRUE/FALSE)
GPU_COUNT=1                     # Number of GPUs to manage
GPU_MEMORY_LIMIT=2GB            # Memory limit per GPU (optional)
GPU_COOL_DOWN_PERIOD=1.0        # Cool-down period in seconds
GPU_ALLOCATION_TIMEOUT=30.0     # Max wait time for allocation in seconds
GPU_MEMORY_THRESHOLD_MB=500     # Memory threshold for CPU fallback

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Default embedding model
EMBEDDING_BATCH_SIZE=32           # Batch size for encoding
```

## Basic Usage

### Direct Allocation

```python
from src.gpu_manager import GPUManager

# Get the manager instance
gpu_manager = GPUManager()

# Allocate a GPU
device_id = gpu_manager.allocate_gpu("my_process")

# Use the GPU
if device_id is not None:
    # Do GPU-based work
    pass

# Release when done
gpu_manager.release_gpu("my_process")
```

### Using Context Manager

```python
from src.gpu_manager import GPUManager

gpu_manager = GPUManager()

# Automatic allocation and release
with gpu_manager.gpu_context("my_process") as device_id:
    if device_id is not None:
        # Do GPU-based work
        pass
    else:
        # Fallback to CPU
        pass
```

### Using Decorators

```python
from src.gpu_manager.decorators import gpu_required

@gpu_required(owner_param="user_id", device_param="device_id")
def process_data(data, user_id, device_id=None):
    if device_id is not None:
        # Do GPU-based processing
        pass
    else:
        # Fallback to CPU
        pass
```

## GPU-Accelerated Text Processing

The module includes GPU-accelerated text embedding and similarity operations:

```python
from src.gpu_manager.text_utils import text_encoder

# Encode texts
embeddings = text_encoder.encode(["Text one", "Text two"])

# Calculate similarities
query = "Search query"
texts = ["Text one", "Text two", "Text three"]
similarities = text_encoder.get_similarities(query, texts)

# Perform semantic search
results = text_encoder.semantic_search(query, texts, top_k=2)
```

## Integration with Agents

The GPU manager is designed to integrate with existing agents and components:

```python
from src.gpu_manager.decorators import gpu_required

class MyAgent:
    @gpu_required(device_param="device_id")
    def process_query(self, query, device_id=None):
        # Process with GPU if available
        if device_id is not None:
            # GPU processing
            pass
        else:
            # CPU fallback
            pass
```

## Examples

See `examples.py` for complete usage examples of:
- Basic GPU allocation
- Context manager usage
- Decorator usage
- Text encoding and similarity

## Requirements

- PyTorch (optional, for tensor operations)
- sentence-transformers (optional, for text encoding)
- NumPy (for numerical operations)

If these libraries are not available, the module will gracefully degrade to CPU-only operation. 