# Agentic Memory Service

Advanced memory management service with multi-level storage and intelligent context awareness using LangChain and LangGraph.

## Features

- **Multi-Level Memory**: RAM (L0) and MongoDB (L2) storage layers
- **Context Awareness**: Intelligent context management and retrieval
- **Agent System**: Multiple specialized agents for different memory tasks
- **GPU Acceleration**: Optional GPU support for AI/ML operations
- **Vector Embeddings**: Semantic similarity and text embedding
- **LangGraph Workflows**: Complex memory processing workflows

## Quick Setup

This service uses UV package manager with optimized AI/ML dependency installation.

### Individual Service Setup
```bash
cd Agentic-Memory
python setup.py        # Install AI/ML dependencies with UV
python run.py          # Start the service
```

### Using Master Orchestrator
```bash
# From project root
python run_all_services.py setup    # Setup all services
python run_all_services.py start    # Start all services
```

## Service Details

- **Port**: 8002
- **Dependencies**: MongoDB, Ollama, PyTorch (optional)
- **Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health

## Agent Architecture

- **Context Awareness Agent**: Manages contextual understanding
- **Intent Classifier Agent**: Classifies user intents
- **Query Expansion Agent**: Expands and refines queries
- **Response Enhancement Agent**: Improves response quality
- **Summary Generation Agent**: Creates response summaries
- **Profile Extraction Agent**: Extracts user profiles

## Main Documentation

For complete setup instructions, architecture details, and usage examples, see the [main README](../README.md).

## Configuration

Key environment variables:
- `MONGODB_URI`: MongoDB connection string
- `OLLAMA_BASE_URL`: Ollama API endpoint
- `ENABLE_GPUS`: Enable GPU acceleration
- `GPU_COUNT`: Number of GPUs to use

See `config.yaml` for full configuration options. 