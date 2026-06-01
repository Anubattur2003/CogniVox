# Agentic Graph-RAG Service

Knowledge graph and retrieval-augmented generation service for document processing, semantic search, and intelligent knowledge extraction.

## Features

- **Document Processing**: PDF ingestion with multiple extraction methods (PyPDF2, pdfminer, OCR)
- **Knowledge Graphs**: Neo4j and ChromaDB integration for hierarchical storage
- **Vector Storage**: Advanced vector embeddings and similarity search
- **Hybrid Search**: Semantic, keyword, and hybrid search modes
- **Graph Visualization**: Interactive knowledge graph visualization
- **LlamaIndex Integration**: Advanced document indexing and retrieval
- **Export Capabilities**: JSON, GraphML, and RDF export formats
- **REST API**: Complete REST API with client SDK
- **Performance Optimization**: Unified agents and smart caching

## Quick Setup

This service uses UV package manager with specialized AI/ML and graph database dependencies.

### Individual Service Setup
```bash
cd Agentic-Graph-RAG
python setup.py        # Install dependencies with UV
python run.py          # Start the service
```

### Using Master Orchestrator
```bash
# From project root
python run_all_services.py setup    # Setup all services
python run_all_services.py start    # Start all services
```

### Docker Setup
```bash
# Start with Docker (includes Neo4j, ChromaDB)
docker-compose up -d

# Stop services
docker-compose down
```

## Service Details

- **Port**: 8003 (default)
- **Dependencies**: Neo4j, ChromaDB, Ollama, PyTorch
- **Documentation**: http://localhost:8003/docs
- **Health Check**: http://localhost:8003/health

## CLI Usage

### Document Management
```bash
# Process documents
cognivox ingest --pdf_path document.pdf

# Query knowledge graph  
cognivox query --query "Your question" --mode hybrid --n_results 5

# Visualize graph
cognivox visualize --output_format html

# Export data
cognivox export --format json

# Remove documents
cognivox remove --pdf_path document.pdf
```

### Run Options
```bash
# Basic startup
python run.py

# Custom port and development mode
python run.py --port 9000 --reload --log-level debug

# Auto-find available port
python run.py --auto-port
```

## API Endpoints

### Core Endpoints
- `GET /health` - Service health check
- `POST /query` - Query the knowledge graph
- `POST /ingest` - Ingest PDF documents
- `DELETE /documents/{document_id}` - Remove documents
- `GET /visualize` - Generate graph visualization
- `GET /export` - Export knowledge graph
- `POST /database/cleanup` - Database cleanup

### Client SDK Example
```python
from src.client.cognivox_client import CogniVoxClient

# Create client
client = CogniVoxClient("http://localhost:8003")

# Check health
health = client.health_check()

# Ingest document
result = client.ingest("document.pdf")

# Query knowledge graph
result = client.query("What are the main topics?")
print(result["answer"])
```

## Document Processing Architecture

The system implements a hierarchical document processing pipeline:

### Structure
- **Documents**: Top-level entities (PDF files)
- **Pages**: Individual pages within documents  
- **Chunks**: Text fragments for retrieval and querying

### Processing Flow
```
PDF Input → Page Extraction → Text Chunking → Vector Embeddings → Graph Storage
    ↓              ↓               ↓              ↓               ↓
Document       Page Nodes      Chunk Nodes   ChromaDB      Neo4j Graph
Metadata       Creation        + Metadata    Vectors       Relationships
```

### Neo4j Graph Schema
```
Node Types:
- Document: PDF metadata, title, author
- Page: Page number, document reference
- Chunk: Text content, embeddings, chunk metadata

Relationships:
- Document CONTAINS Page
- Page CONTAINS Chunk
```

## Search Modes

- **Semantic Search**: Vector-based similarity search using embeddings
- **Keyword Search**: Traditional text-based search with Neo4j
- **Hybrid Search**: Combined semantic and keyword search (recommended)

## Configuration

### Key Environment Variables
- `NEO4J_URI`: Neo4j database connection (default: bolt://localhost:7687)
- `CHROMA_HOST`: ChromaDB host and port (default: localhost:8000)
- `OLLAMA_BASE_URL`: Ollama API endpoint (default: http://localhost:11434)
- `ENABLE_GPU`: Enable GPU acceleration (default: false)

### Configuration File (config.yaml)
```yaml
# Database settings
neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "password"

# Vector storage
chromadb:
  host: "localhost"
  port: 8000

# Document processing
pdf:
  chunk_size: 1000
  chunk_overlap: 200
  use_llamaindex: true  # Enable advanced processing

# AI/ML settings
ollama:
  host: "http://localhost:11434"
  embedding_model: "nomic-embed-text"
```

## Database Cleanup

### Regular Cleanup (Server Running)
```bash
# Via API
curl -X POST "http://localhost:8003/database/cleanup?confirm=true"

# Via CLI
python -m src.cli.main cleanup --confirm
```

### Complete Reset (Server Stopped)
```bash
# Stop server first, then:
python utils/nuclear_cleanup.py --confirm
# Restart server
```

## Performance Features

- **Unified Query Intelligence**: Single agent for query analysis (50% cost reduction)
- **Smart Document Caching**: Prevents re-analysis of same documents  
- **Optimized Embeddings**: Efficient vector generation and storage
- **Hierarchical Storage**: Fast retrieval with graph relationships

## Main Documentation

For complete setup instructions, architecture details, and usage examples, see the [main README](../README.md).

## Service URLs (Docker)

- Neo4j Browser: http://localhost:7474 (neo4j/password)
- ChromaDB: http://localhost:8000
- Ollama: http://localhost:11434
- API Documentation: http://localhost:8003/docs 