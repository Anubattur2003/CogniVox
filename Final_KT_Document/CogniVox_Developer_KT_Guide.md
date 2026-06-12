# CogniVox: Developer Knowledge Transfer Guide

**Version:** 2.0  
**Classification:** Internal Technical Reference  
**Audience:** Software Developers, DevOps Engineers, Technical Support  
**Last Updated:** January 2026

---

## Introduction

Welcome to the CogniVox development team. This comprehensive Knowledge Transfer (KT) document is designed to bring you from zero familiarity to complete understanding of the CogniVox platform. Whether you are a new team member, a contractor joining the project, or a developer from another team needing to integrate with CogniVox, this guide provides everything you need to understand, develop, debug, and deploy the platform.

This document is structured as a progressive learning path. We recommend reading it sequentially on your first pass, then using it as a reference for specific topics as you work on the project. Each section builds on previous sections, introducing concepts in a logical order.

---

## Table of Contents

1. [Quick Start Guide](#quick-start-guide)
2. [Project Structure Overview](#project-structure-overview)
3. [Development Environment Setup](#development-environment-setup)
4. [Service Architecture Deep Dive](#service-architecture-deep-dive)
5. [Configuration Management](#configuration-management)
6. [Database Schemas & Models](#database-schemas--models)
7. [Agent Development Patterns](#agent-development-patterns)
8. [API Reference](#api-reference)
9. [Frontend Architecture](#frontend-architecture)
10. [Debugging & Logging](#debugging--logging)
11. [Testing Strategies](#testing-strategies)
12. [Deployment Procedures](#deployment-procedures)
13. [Common Troubleshooting](#common-troubleshooting)
14. [Development Workflows](#development-workflows)
15. [Code Conventions & Standards](#code-conventions--standards)

---

## Quick Start Guide

This section gets you running CogniVox locally in the shortest time possible. Detailed explanations follow in subsequent sections.

### Prerequisites

Ensure you have the following installed:

- **Python 3.11+** (we use 3.11.x for consistency)
- **Node.js 18+** (LTS version recommended)
- **Docker Desktop** with Docker Compose
- **NVIDIA GPU** with 6GB+ VRAM (RTX 3050 or better)
- **NVIDIA Container Toolkit** (for GPU access in Docker)
- **Git** for version control

### Step 1: Clone the Repository

```bash
git clone <repository-url> Agentic-Cognivox-Django-demo
cd Agentic-Cognivox-Django-demo
```

### Step 2: Start Infrastructure Services

Start the database and infrastructure services first:

```bash
docker-compose -f docker-compose.agentic-services.yml up -d
```

This starts:
- Neo4j (ports 7474, 7687)
- MongoDB (port 27017)
- PostgreSQL (port 5432)
- PgAdmin (port 5050)
- Ollama (port 11434)

Wait for all services to be healthy:

```bash
docker-compose -f docker-compose.agentic-services.yml ps
```

### Step 3: Pull Required Ollama Models

```bash
# Connect to Ollama container and pull models
# Note: Since the system is configured to run individual containers for each model under a multi-container proxy setup, pull the models on their respective containers:
docker exec -it ollama-qwen2-5-7b ollama pull qwen2.5:7b
docker exec -it ollama-gemma2-2b ollama pull gemma2:2b
docker exec -it ollama-mistral ollama pull mistral:latest
docker exec -it ollama-nomic-embed-text ollama pull nomic-embed-text

# (Alternative) If using a single shared Ollama container named agentic-ollama:
# docker exec -it agentic-ollama ollama pull qwen2.5:7b
# docker exec -it agentic-ollama ollama pull gemma2:2b
# docker exec -it agentic-ollama ollama pull mistral:latest
# docker exec -it agentic-ollama ollama pull nomic-embed-text
```

### Step 4: Set Up Django Backend

```bash
cd agentic_django

# Create virtual environment
py -3.11 -m venv .venv --prompt django

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver 0.0.0.0:8000
```
# Create and run Celery worker
```bash
cd agentic_django

.\.venv\Scripts\activate

celery -A agentic_django worker -P solo -l info
```

### Step 5: Set Up Agentic-Memory Service

Open a new terminal:

```bash
cd Agentic-Memory

# Create virtual environment
py -3.11 -m venv .venv --prompt memory

# Activate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run service
python run.py
```

Service starts on port 8002.

### Step 6: Set Up Agentic-Graph-RAG Service

Open another new terminal:

```bash
cd Agentic-Graph-RAG

# Create virtual environment
py -3.11 -m venv .venv --prompt graphrag

# Activate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run service
python run.py
```

Service starts on port 8001.

### Step 7: Set Up Frontend

Open another new terminal:

```bash
cd Agentic-frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend starts on port 5173.

### Step 8: Access the Application

- **Frontend:** http://localhost:5173
- **Django Admin:** http://localhost:8000/admin
- **Neo4j Browser:** http://localhost:7474
- **PgAdmin:** http://localhost:5050

---

## Project Structure Overview

Understanding the project structure is fundamental to working effectively with CogniVox. Here is the complete directory layout with explanations:

```
Agentic-Cognivox-Django-demo/
├── agentic_django/                 # Django Backend (API Gateway)
│   ├── agentic_django/             # Django project settings
│   │   ├── settings.py             # Django configuration
│   │   ├── urls.py                 # Root URL routing
│   │   └── wsgi.py                 # WSGI entry point
│   ├── authentication/             # User auth module
│   │   ├── middleware.py           # Security middleware stack
│   │   ├── models.py               # User model extensions
│   │   ├── permissions.py          # RBAC permission classes
│   │   ├── security.py             # Crypto utilities (Argon2, JWT)
│   │   ├── serializers.py          # DRF serializers
│   │   ├── urls.py                 # Auth API routes
│   │   └── views.py                # Auth API views
│   ├── chat/                       # Chat management module
│   │   ├── models.py               # Space, Thread, Message models
│   │   ├── serializers.py          # Chat serializers
│   │   ├── urls.py                 # Chat API routes
│   │   └── views.py                # Chat ViewSets
│   ├── core/                       # Shared utilities module
│   │   ├── models.py               # UserRole, AuditLog, APIUsageStats
│   │   ├── serializers.py          # Core serializers
│   │   └── utils.py                # Shared utility functions
│   ├── mcpserver/                  # MCP integration module
│   │   ├── mcp_client.py           # FastMCP client implementation
│   │   ├── models.py               # MCPServerConfig, MCPTools, etc.
│   │   ├── serializers.py          # MCP serializers
│   │   ├── urls.py                 # MCP API routes
│   │   └── views.py                # MCP ViewSets
│   ├── config.yaml                 # Django service configuration
│   ├── manage.py                   # Django management script
│   ├── requirements.txt            # Python dependencies
│   ├── run_https.py                # HTTPS server script
│   └── ssl_certs/                  # SSL certificates
│
├── Agentic-Memory/                 # Memory Service (Multi-Agent Orchestration)
│   ├── src/
│   │   ├── agents/                 # Agent implementations
│   │   │   ├── base_agent.py       # BaseAgent class
│   │   │   ├── multi_agent/        # Multi-agent orchestration
│   │   │   │   ├── orchestrator.py # LangGraph orchestrator
│   │   │   │   ├── query_analyzer.py
│   │   │   │   ├── reasoning_agent.py
│   │   │   │   ├── response_synthesizer.py
│   │   │   │   ├── mcp_coordinator.py
│   │   │   │   ├── validator.py
│   │   │   │   └── state.py        # AgentState TypedDict
│   │   │   ├── intent_classifier_agent/
│   │   │   ├── context_awareness_agent/
│   │   │   ├── speech_to_text_agent/
│   │   │   └── ...                 # Other specialized agents
│   │   ├── api/                    # FastAPI endpoints
│   │   ├── gpu_manager/            # GPU memory management
│   │   ├── mcp/                    # MCP client for Memory service
│   │   ├── memory/                 # Conversation memory
│   │   └── utils/                  # Utility modules
│   ├── config.yaml                 # Service configuration
│   ├── run.py                      # Service entry point
│   └── requirements.txt            # Python dependencies
│
├── Agentic-Graph-RAG/              # RAG Service (Document Intelligence)
│   ├── src/
│   │   ├── agents/                 # RAG-specific agents
│   │   │   ├── base_agent.py       # BaseAgent for RAG
│   │   │   ├── combined_query_agent/
│   │   │   ├── document_analysis_agent/
│   │   │   └── intent_classification_agent/
│   │   ├── api/                    # FastAPI endpoints
│   │   ├── graph_db/               # Neo4j integration
│   │   ├── pdf_processor/          # Document processing
│   │   │   ├── llamaindex_processor.py
│   │   │   ├── llamaindex_embeddings.py
│   │   │   ├── text_processor.py
│   │   │   └── pdf_extractor.py
│   │   ├── query_engine/           # Hybrid retrieval
│   │   └── visualization/          # Graph visualization
│   ├── config.yaml                 # Service configuration
│   ├── run.py                      # Service entry point
│   └── requirements.txt            # Python dependencies
│
├── Agentic-frontend/               # React Frontend
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── Sidebar/
│   │   │   ├── MainArea/
│   │   │   ├── ChatInput/
│   │   │   ├── MCPPanel/
│   │   │   └── ...
│   │   ├── contexts/               # React contexts
│   │   ├── pages/                  # Page components
│   │   ├── services/               # API clients
│   │   ├── App.tsx                 # Main application
│   │   └── main.tsx                # Entry point
│   ├── package.json                # Node dependencies
│   └── vite.config.ts              # Vite configuration
│
├── docker-compose.agentic-services.yml  # Infrastructure services
└── docker-config/                  # Docker configuration files
    ├── mongodb-init/               # MongoDB initialization
    └── postgres-config/            # PostgreSQL configuration
```

---

## Development Environment Setup

This section provides detailed setup instructions for each component with troubleshooting guidance.

### Python Environment Best Practices

Each Python service (agentic_django, Agentic-Memory, Agentic-Graph-RAG) maintains its own virtual environment. This isolation prevents dependency conflicts between services.

**Creating Virtual Environments:**

```bash
# Always use the same Python version across services
python --version  # Should show 3.11.x

# Create venv in each service directory
cd agentic_django
python -m venv .venv

cd ../Agentic-Memory
python -m venv .venv

cd ../Agentic-Graph-RAG
python -m venv .venv
```

**IDE Configuration (VS Code):**

Create `.vscode/settings.json` in the project root:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/agentic_django/.venv/Scripts/python",
    "python.analysis.extraPaths": [
        "${workspaceFolder}/agentic_django",
        "${workspaceFolder}/Agentic-Memory/src",
        "${workspaceFolder}/Agentic-Graph-RAG/src"
    ]
}
```

### Docker Infrastructure Details

**docker-compose.agentic-services.yml** defines all infrastructure:

**Neo4j:**
- Web browser: http://localhost:7474 (username: neo4j, password: password)
- Bolt protocol: bolt://localhost:7687
- GPU acceleration enabled for graph analytics

**MongoDB:**
- Connection: mongodb://appuser:apppassword@localhost:27017/appdb
- No web interface by default (use MongoDB Compass if needed)

**PostgreSQL:**
- Connection: postgresql://cognivox:cognivox@localhost:5432/cognivox
- PgAdmin: http://localhost:5050 (admin@admin.com / admin)

**Ollama:**
- API: http://localhost:11434
- Flash Attention and Q4_0 quantization enabled
- Models persist in named volume across restarts

### Environment Variables

Each service uses `.env` files for sensitive configuration. Create these from templates:

**agentic_django/.env:**
```
SECRET_KEY=your-secure-secret-key
DEBUG=True
DATABASE_URL=postgresql://cognivox:cognivox@localhost:5432/cognivox
MONGODB_URL=mongodb://appuser:apppassword@localhost:27017/appdb
```

**Agentic-Memory/.env:**
```
OLLAMA_HOST=http://localhost:11434
MONGODB_URL=mongodb://appuser:apppassword@localhost:27017/appdb
ENCRYPTION_KEY=your-32-byte-fernet-key-here
```

**Agentic-Graph-RAG/.env:**
```
OLLAMA_HOST=http://localhost:11434
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

---

## Service Architecture Deep Dive

### Django Backend (agentic_django)

The Django backend serves as the API gateway, handling all external client requests and routing them to appropriate downstream services.

**Request Flow:**

```
Frontend Request
    ↓
Django URL Router (urls.py)
    ↓
Middleware Stack (authentication, rate limiting, audit logging)
    ↓
ViewSet/View (handles business logic)
    ↓
Serializer (validates and transforms data)
    ↓
Model (database operations) or Service Client (downstream calls)
    ↓
Response Serialization
    ↓
Middleware Stack (security headers, timing)
    ↓
Response to Client
```

**Key Middleware Classes (authentication/middleware.py):**

1. **ProcessTimeMiddleware:** Adds X-Process-Time header to all responses
2. **JWTAuthenticationMiddleware:** Validates JWT tokens and injects user into request
3. **RateLimitMiddleware:** Enforces per-user, per-endpoint rate limits
4. **AuditLogMiddleware:** Logs all requests for security/compliance
5. **SecurityHeadersMiddleware:** Adds CSP, X-Frame-Options, etc.
6. **CORSMiddleware:** Handles cross-origin requests

**MemoryServiceClient (chat/views.py):**

This client class handles communication with the Agentic-Memory service:

```python
class MemoryServiceClient:
    def __init__(self, base_url=None):
        # Loads from config.yaml if not provided
        
    def generate_chat_response(self, user_id, message, response_mode, ...):
        # POSTs to Memory service /chat endpoint
        # Returns streaming or complete response
        
    def generate_thread_title(self, response, query, chat_id):
        # POSTs to Memory service /generate-title endpoint
```

### Agentic-Memory Service

The Memory service is the intelligence hub, coordinating multiple specialized agents to process user queries.

**Entry Point (run.py):**

The service starts a FastAPI application with endpoints for chat, speech-to-text, and agent interactions.

**Multi-Agent Orchestrator (src/agents/multi_agent/orchestrator.py):**

```python
class MultiAgentOrchestrator:
    def __init__(self, model_name, temperature, enable_parallel):
        # Initializes specialized agents from config
        # Query Analyzer, MCP Reasoning, Response Synthesizer, etc.
        
    def _build_graph(self):
        # Constructs LangGraph StateGraph
        # Defines nodes for each agent
        # Defines edges with conditional routing
        
    def process(self, user_message, user_id, context_prompt, auth_token):
        # Executes the graph from entry point
        # Returns final response with sources
```

**State Management (src/agents/multi_agent/state.py):**

```python
class AgentState(TypedDict):
    user_message: str
    user_id: str
    context: str
    query_analysis: Dict[str, Any]
    mcp_plan: Dict[str, Any]
    graphrag_result: Dict[str, Any]
    reasoning_result: Dict[str, Any]
    mcp_result: Dict[str, Any]
    synthesized_response: str
    validated_response: str
    final_response: str
    sources: List[Dict[str, Any]]
    error: Optional[str]
```

### Agentic-Graph-RAG Service

The RAG service handles document processing and knowledge retrieval.

**Document Processing Pipeline (src/pdf_processor/):**

1. **pdf_extractor.py:** Extracts text from PDFs (including OCR for scanned documents)
2. **text_processor.py:** Semantic chunking with configurable size/overlap
3. **llamaindex_embeddings.py:** Generates embeddings via Ollama/Nomic
4. **llamaindex_processor.py:** Orchestrates the full ingestion pipeline

**Retrieval Pipeline (src/query_engine/):**

1. Query received from Memory service
2. Hybrid search: Vector similarity + BM25 keyword matching
3. Graph traversal: Related entities from Neo4j
4. Reranking: BGE Reranker for final ordering
5. Context assembly with source attribution

### Inter-Service Communication

Services communicate via HTTP REST APIs:

**Django → Memory Service:**
```
POST http://localhost:8002/chat
{
    "user_id": "user123",
    "message": "What is machine learning?",
    "response_mode": "rag",
    "auth_token": "jwt-token-here"
}
```

**Memory Service → Graph-RAG Service:**
```
POST http://localhost:8001/retrieve
{
    "query": "What is machine learning?",
    "n_results": 10,
    "mode": "hybrid"
}
```

---

## Configuration Management

CogniVox uses YAML configuration files for each service, with environment variables for sensitive values.

### Django Configuration (agentic_django/config.yaml)

```yaml
app:
  name: "CogniVox"
  environment: "development"  # development, staging, production
  debug: true                 # Disable in production
  secret_key: "..."          # Override via env var

database:
  url: "postgresql://..."    # Override via env var

server:
  host: "0.0.0.0"
  port: 8000
  allowed_hosts: "*"         # Restrict in production

jwt:
  secret_key: "..."
  algorithm: "HS256"
  token_expiry_minutes: 60

mongodb:
  url: "mongodb://..."
  db_name: "appdb"

additional:
  max_sub_threads: 10
  ollama_url: "http://localhost:11434"

model:
  default_name: "qwen3:4b"
  default_requests: 100      # Default quota per user
```

### Memory Service Configuration (Agentic-Memory/config.yaml)

```yaml
llm:
  default_provider: "ollama"
  default_model: "mistral:latest"
  default_temperature: 0.7
  default_timeout: 60
  
  ollama:
    base_url: "http://localhost:11434/mistral"
    model_urls:
      "mistral:latest": "http://localhost:11434/mistral"
      "qwen2.5:7b": "http://localhost:11434/qwen2-5-7b"
      "gemma2:2b": "http://localhost:11434/gemma2-2b"
      "nomic-embed-text": "http://localhost:11434/nomic-embed-text"

agents:
  query_analyzer:
    provider: "ollama"
    model: "qwen2.5:7b"
    temperature: 0.1
    timeout: 60
    
  mcp_reasoning:
    provider: "ollama"
    model: "qwen2.5:7b"
    temperature: 0.1
    
  response_synthesizer:
    provider: "ollama"
    model: "gemma2:2b"
    temperature: 0.7
    
  validator:
    enabled: false           # Enable for quality mode
    provider: "ollama"
    model: "gemma2:2b"

memory:
  chat_memory:
    max_messages_per_chat: 1000
    cleanup_interval_hours: 24
    
  mcp_cache:
    enabled: true
    ttl_seconds: 300         # 5 minute cache

gpu:
  enable_gpu_acceleration: true
  device_ids: [0]
  fallback_to_cpu: true
  memory_limit_gb: 6

api:
  host: "0.0.0.0"
  port: 8002
  enable_cors: true

security:
  enable_rate_limiting: true
  max_requests_per_minute: 60
  enable_input_validation: true
  max_input_length: 10000
```

### Graph-RAG Configuration (Agentic-Graph-RAG/config.yaml)

```yaml
db:
  type: neo4j
  host: localhost
  port: 7687
  user: neo4j
  password: password
  database: neo4j

vector_store:
  type: chromadb
  path: "./data/db/vectors"

pdf:
  chunk_size: 1000
  chunk_overlap: 200
  extraction_method: auto    # auto, pdfminer, pypdf2, ocr
  use_llamaindex: true

storage:
  bucket_path: "Bucket"      # Local document storage

query:
  default_mode: hybrid       # semantic, keyword, hybrid
  default_results: 5

visualization:
  default_format: html
  node_limit: 100
```

### Modifying Configuration

**Best Practices:**

1. Never commit secrets to version control
2. Use environment variables for sensitive values
3. Maintain separate config files for development/staging/production
4. Document all configuration options

**Adding a New Configuration Option:**

1. Add the option to the appropriate `config.yaml`
2. Update the config loading code (usually in `src/config.py`)
3. Use the new option where needed
4. Document the option in this KT guide
5. Add to `.env.example` if it's a secret

---

## Database Schemas & Models

### PostgreSQL Schema (Django Models)

**User Model (authentication/models.py):**

```python
class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=UserRole.choices)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Chat Models (chat/models.py):**

```python
class Space(models.Model):
    """Folder-like organization for chat threads"""
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ChatThread(models.Model):
    """Individual chat conversation"""
    user = models.ForeignKey(User)
    space = models.ForeignKey(Space, null=True)
    title = models.CharField(max_length=200)
    is_favorite = models.BooleanField(default=False)
    parent_thread = models.ForeignKey('self', null=True)  # For sub-threads
    created_at = models.DateTimeField(auto_now_add=True)
```

**MCP Models (mcpserver/models.py):**

```python
class MCPServerConfig(models.Model):
    """Configuration for an MCP server"""
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    transport_type = models.CharField()  # stdio, sse, http
    command = models.CharField()         # For stdio
    url = models.URLField()              # For sse/http
    encrypted_credentials = models.TextField()
    is_active = models.BooleanField(default=True)
    last_synced = models.DateTimeField(null=True)

class MCPTool(models.Model):
    """Discovered tool from an MCP server"""
    server = models.ForeignKey(MCPServerConfig)
    name = models.CharField(max_length=100)
    description = models.TextField()
    input_schema = models.JSONField()

class MCPResource(models.Model):
    """Discovered resource from an MCP server"""
    server = models.ForeignKey(MCPServerConfig)
    uri = models.CharField(max_length=500)
    name = models.CharField(max_length=100)
    mime_type = models.CharField()
```

**Audit Models (core/models.py):**

```python
class AuditLog(models.Model):
    """Security audit trail"""
    user = models.ForeignKey(User, null=True)
    action = models.CharField(max_length=50)
    endpoint = models.CharField(max_length=200)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

class APIUsageStats(models.Model):
    """Daily usage aggregation"""
    user = models.ForeignKey(User)
    endpoint = models.CharField(max_length=200)
    date = models.DateField()
    request_count = models.IntegerField(default=0)
```

### MongoDB Collections

**Chat History Collection:**

```javascript
// Collection: chat_history
{
    "_id": ObjectId("..."),
    "user_id": "user123",
    "thread_id": "thread456",
    "messages": [
        {
            "role": "user",
            "content": "What is machine learning?",
            "timestamp": ISODate("2026-01-22T10:00:00Z")
        },
        {
            "role": "assistant",
            "content": "Machine learning is...",
            "timestamp": ISODate("2026-01-22T10:00:05Z"),
            "sources": [
                {
                    "document": "ML_Fundamentals.pdf",
                    "page": 5,
                    "chunk_id": "chunk_123"
                }
            ]
        }
    ],
    "metadata": {
        "created_at": ISODate("..."),
        "last_message_at": ISODate("..."),
        "message_count": 2
    }
}
```

**User Profile Collection:**

```javascript
// Collection: user_profiles
{
    "_id": ObjectId("..."),
    "user_id": "user123",
    "preferences": {
        "response_length": "detailed",
        "language": "en"
    },
    "context": {
        "recent_topics": ["machine learning", "python"],
        "expertise_level": "intermediate"
    },
    "updated_at": ISODate("...")
}
```

### Neo4j Graph Schema

**Node Types:**

```cypher
// Document Node
(:Document {
    id: "doc_123",
    name: "ML_Fundamentals.pdf",
    path: "/documents/ml/",
    ingested_at: datetime(),
    chunk_count: 25
})

// Chunk Node
(:Chunk {
    id: "chunk_123",
    text: "Machine learning is a subset of...",
    embedding_id: "emb_123",
    position: 5,
    page: 2
})

// Entity Node (extracted from documents)
(:Entity {
    name: "Machine Learning",
    type: "CONCEPT",
    description: "A subset of artificial intelligence..."
})
```

**Relationship Types:**

```cypher
// Document contains Chunks
(:Document)-[:CONTAINS]->(:Chunk)

// Chunk mentions Entity
(:Chunk)-[:MENTIONS {confidence: 0.95}]->(:Entity)

// Entity relates to Entity
(:Entity)-[:RELATED_TO {type: "is_subset_of"}]->(:Entity)

// Chunk follows Chunk (sequential)
(:Chunk)-[:FOLLOWED_BY]->(:Chunk)
```

---

## Agent Development Patterns

This section covers how to develop new agents or modify existing ones.

### BaseAgent Pattern

All agents inherit from BaseAgent, which provides common functionality:

**Memory Service BaseAgent (Agentic-Memory/src/agents/base_agent.py):**

```python
class BaseAgent:
    def __init__(
        self,
        agent_name: str,
        model_name: str = None,
        temperature: float = None,
        base_url: str = None,
        system_prompt: str = None,
        enable_caching: bool = True,
        cache_size: int = 100
    ):
        self.agent_name = agent_name
        self.model_name = model_name or get_default_model()
        self.temperature = temperature or 0.7
        self._cache = {}
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LangChain ChatOllama client"""
        
    def call_llm(self, prompt: str, use_cache: bool = True) -> str:
        """Call LLM with caching and fallback support"""
        
    def update_model(self, model_name: str = None, temperature: float = None):
        """Dynamically update model configuration"""
```

### Creating a New Agent

**Step 1: Create Agent Directory**

```
Agentic-Memory/src/agents/
└── my_new_agent/
    ├── __init__.py
    └── my_new_agent.py
```

**Step 2: Implement Agent Class**

```python
# my_new_agent.py
from src.agents.base_agent import BaseAgent
from src.utils.toon_format import format_system_instruction
from src.utils.agent_logger import get_agent_logger

logger = get_agent_logger("my_new_agent")

class MyNewAgent(BaseAgent):
    """
    Description of what this agent does.
    """
    
    def __init__(
        self,
        model_name: str = "qwen2.5:7b",
        temperature: float = 0.3,
        **kwargs
    ):
        super().__init__(
            agent_name="my_new_agent",
            model_name=model_name,
            temperature=temperature,
            **kwargs
        )
        self.system_instruction = self._create_system_instruction()
        logger.info(f"✅ MyNewAgent initialized with {model_name}")
    
    def _create_system_instruction(self) -> str:
        """Create the system prompt for this agent."""
        return format_system_instruction({
            "role": "Describe the agent's role",
            "objective": "What is the agent trying to achieve",
            "output_format": "Expected output structure",
            "constraints": ["List of constraints"]
        })
    
    def process(self, input_data: dict) -> dict:
        """
        Main processing method.
        
        Args:
            input_data: Input data dictionary
            
        Returns:
            Result dictionary
        """
        logger.info(f"Processing: {input_data.get('query', '')[:50]}...")
        
        # Build prompt
        prompt = f"""
{self.system_instruction}

Input: {input_data}

Provide your response:
"""
        
        # Call LLM
        response = self.call_llm(prompt)
        
        # Parse and return result
        return {
            "result": response,
            "agent": self.agent_name
        }
```

**Step 3: Register in __init__.py**

```python
# my_new_agent/__init__.py
from .my_new_agent import MyNewAgent

__all__ = ["MyNewAgent"]
```

**Step 4: Add Configuration (config.yaml)**

```yaml
agents:
  my_new_agent:
    provider: "ollama"
    model: "qwen2.5:7b"
    temperature: 0.3
    timeout: 30
```

**Step 5: Integrate with Orchestrator (if needed)**

If the agent should be part of the multi-agent workflow, add it to the orchestrator:

```python
# In orchestrator.py

def __init__(self, ...):
    # ... existing initialization
    self.my_new_agent = MyNewAgent(
        model_name=config.get("model"),
        temperature=config.get("temperature")
    )

def _build_graph(self):
    # Add node for new agent
    graph.add_node("my_new_agent", self._my_new_agent_node)
    
    # Add edges as needed
    graph.add_edge("some_previous_node", "my_new_agent")
```

### TOON Format for System Prompts

Use the TOON format for structured system instructions:

```python
from src.utils.toon_format import format_system_instruction

system_prompt = format_system_instruction({
    "role": "You are a query analyzer for an AI assistant",
    "objective": "Classify user queries and determine required processing",
    "output_format": """
{
    "intent": "knowledge|tool|general",
    "requires_rag": true/false,
    "requires_mcp": true/false,
    "query_type": "question|command|greeting|..."
}
""",
    "constraints": [
        "Always respond in valid JSON",
        "Be conservative in classification",
        "Prefer RAG for knowledge queries"
    ],
    "examples": [
        {"input": "What is ML?", "output": {"intent": "knowledge", ...}},
        {"input": "Run the report", "output": {"intent": "tool", ...}}
    ]
})
```

---

## API Reference

### Django Backend APIs

**Authentication Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register/ | User registration |
| POST | /api/auth/login/ | User login, returns JWT |
| POST | /api/auth/logout/ | Logout, invalidates token |
| POST | /api/auth/token/refresh/ | Refresh access token |
| POST | /api/auth/password/reset/ | Request password reset |
| POST | /api/auth/password/reset/confirm/ | Confirm password reset |
| GET | /api/auth/me/ | Get current user details |

**Chat Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/chat/spaces/ | List user's spaces |
| POST | /api/chat/spaces/ | Create new space |
| PUT | /api/chat/spaces/{id}/ | Update space |
| DELETE | /api/chat/spaces/{id}/ | Delete space |
| GET | /api/chat/threads/ | List user's threads |
| POST | /api/chat/threads/ | Create new thread |
| GET | /api/chat/threads/{id}/ | Get thread details |
| DELETE | /api/chat/threads/{id}/ | Delete thread |
| POST | /api/chat/threads/{id}/sub-threads/ | Create sub-thread (send message) |
| PUT | /api/chat/threads/{id}/favorite/ | Toggle favorite |
| PUT | /api/chat/threads/{id}/move-to-space/ | Move to different space |

**MCP Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/mcp/servers/ | List user's MCP servers |
| POST | /api/mcp/servers/ | Add new MCP server |
| PUT | /api/mcp/servers/{id}/ | Update server config |
| DELETE | /api/mcp/servers/{id}/ | Remove server |
| POST | /api/mcp/servers/{id}/test/ | Test server connection |
| POST | /api/mcp/servers/{id}/sync/ | Sync capabilities |
| GET | /api/mcp/tools/ | List all available tools |
| POST | /api/mcp/tools/{id}/execute/ | Execute a tool |
| GET | /api/mcp/resources/ | List all resources |
| POST | /api/mcp/resources/{id}/read/ | Read a resource |

### Memory Service APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /chat | Process chat message |
| POST | /generate-title | Generate thread title |
| POST | /speech-to-text | Convert audio to text |
| GET | /health | Health check |
| GET | /agents | List available agents |

**Chat Request:**

```json
POST /chat
{
    "user_id": "user123",
    "message": "What is machine learning?",
    "response_mode": "rag",
    "context_prompt": "",
    "auth_token": "jwt-token",
    "n_results": 20
}
```

**Chat Response:**

```json
{
    "response": "Machine learning is...",
    "sources": [
        {
            "document": "ML_Fundamentals.pdf",
            "page": 5,
            "chunk_id": "chunk_123",
            "relevance": 0.92
        }
    ],
    "processing_time": 2.5,
    "agents_used": ["query_analyzer", "graphrag", "reasoning", "synthesizer"]
}
```

### Graph-RAG Service APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /ingest | Ingest document(s) |
| POST | /retrieve | Retrieve relevant chunks |
| GET | /documents | List ingested documents |
| DELETE | /documents/{id} | Delete document |
| GET | /graph/visualize | Visualize knowledge graph |
| GET | /health | Health check |

**Retrieve Request:**

```json
POST /retrieve
{
    "query": "What is machine learning?",
    "n_results": 10,
    "mode": "hybrid",
    "filters": {
        "document_type": "pdf"
    }
}
```

**Retrieve Response:**

```json
{
    "results": [
        {
            "chunk_id": "chunk_123",
            "text": "Machine learning is a subset of...",
            "document": "ML_Fundamentals.pdf",
            "page": 5,
            "relevance": 0.92,
            "related_entities": ["Machine Learning", "AI"]
        }
    ],
    "processing_time": 0.5
}
```

---

## Frontend Architecture

### Component Hierarchy

```
App.tsx
├── AuthWrapper
└── Layout.tsx
    ├── Sidebar/
    │   ├── SpaceList
    │   ├── ThreadList
    │   └── NewChatButton
    ├── Header/
    │   ├── UserMenu
    │   └── SettingsButton
    └── MainArea/
        ├── MessageList
        │   ├── UserMessage
        │   └── AssistantMessage
        ├── ChatInput/
        │   ├── TextInput
        │   ├── VoiceButton
        │   └── SendButton
        └── MCPPanel/ (optional)
            ├── ServerList
            └── ToolList
```

### State Management

**React Contexts:**

- **AuthContext:** User authentication state, login/logout functions
- **ThemeContext:** Light/dark theme management
- **ChatContext:** Active thread, messages, spaces

**Example Context Usage:**

```typescript
// contexts/AuthContext.tsx
export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    
    const login = async (email: string, password: string) => {
        const response = await api.post('/auth/login/', { email, password });
        localStorage.setItem('token', response.data.access);
        setUser(response.data.user);
    };
    
    // ... logout, refresh, etc.
    
    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
```

### API Service Layer

```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        if (error.response?.status === 401) {
            // Attempt token refresh or redirect to login
        }
        return Promise.reject(error);
    }
);

export default api;
```

### Streaming Response Handling

For chat responses, the frontend handles streaming:

```typescript
// In ChatInput component
const sendMessage = async (message: string) => {
    const response = await fetch(`${API_URL}/chat/threads/${threadId}/sub-threads/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ message }),
    });
    
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        // Append chunk to current message
        setCurrentResponse(prev => prev + chunk);
    }
};
```

---

## Debugging & Logging

### Logging Configuration

Each service uses Python's logging module with structured formatting:

**Memory Service Logger (utils/agent_logger.py):**

```python
def get_agent_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"cognivox.{name}")
    logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    
    return logger
```

**Log Levels:**
- **DEBUG:** Detailed diagnostic information
- **INFO:** General operational messages
- **WARNING:** Potential issues that don't stop execution
- **ERROR:** Failures that need attention

### Debug Mode

Enable debug mode in config.yaml:

```yaml
development:
  debug_mode: true
  enable_profiling: false
  enable_metrics: true
```

This enables:
- Detailed error messages with stack traces
- Request/response logging
- Agent reasoning step logging

### Debugging Agent Behavior

Add logging to understand agent decisions:

```python
class MyAgent(BaseAgent):
    def process(self, input_data):
        logger.debug(f"Input received: {json.dumps(input_data, indent=2)}")
        
        prompt = self._build_prompt(input_data)
        logger.debug(f"Prompt built: {prompt[:200]}...")
        
        response = self.call_llm(prompt)
        logger.debug(f"LLM response: {response[:200]}...")
        
        result = self._parse_response(response)
        logger.info(f"Agent result: {result.get('intent')}")
        
        return result
```

### Common Debug Commands

**Check Ollama models:**
```bash
docker exec agentic-ollama ollama list
```

**Check service logs:**
```bash
# Django
cd agentic_django && python manage.py runserver --verbosity 2

# Memory service
cd Agentic-Memory && python run.py  # Check console output

# View container logs
docker logs agentic-neo4j --tail 100
docker logs agentic-ollama --tail 100
```

**Test Database connections:**
```bash
# PostgreSQL
docker exec -it agentic-postgres psql -U cognivox -d cognivox

# MongoDB
docker exec -it agentic-mongodb mongosh -u appuser -p apppassword appdb

# Neo4j
# Use browser at http://localhost:7474
```

---

## Testing Strategies

### Unit Testing

**Django Tests:**
```bash
cd agentic_django
python manage.py test authentication
python manage.py test chat
python manage.py test mcpserver
```

**Agent Tests:**
```python
# tests/test_query_analyzer.py
import pytest
from src.agents.multi_agent.query_analyzer import QueryAnalysisAgent

class TestQueryAnalyzer:
    def setup_method(self):
        self.agent = QueryAnalysisAgent()
    
    def test_knowledge_query_classification(self):
        result = self.agent.analyze("What is machine learning?")
        assert result["intent"] == "knowledge"
        assert result["requires_rag"] == True
    
    def test_greeting_classification(self):
        result = self.agent.analyze("Hello!")
        assert result["intent"] == "general"
        assert result["requires_rag"] == False
```

### Integration Testing

Test full workflows:

```python
# tests/test_chat_flow.py
import pytest
import requests

BASE_URL = "http://localhost:8000/api"

class TestChatFlow:
    def test_full_conversation(self):
        # Login
        login_resp = requests.post(f"{BASE_URL}/auth/login/", json={
            "email": "test@example.com",
            "password": "testpass123"
        })
        token = login_resp.json()["access"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create thread
        thread_resp = requests.post(
            f"{BASE_URL}/chat/threads/", 
            json={"title": "Test Thread"},
            headers=headers
        )
        thread_id = thread_resp.json()["id"]
        
        # Send message
        msg_resp = requests.post(
            f"{BASE_URL}/chat/threads/{thread_id}/sub-threads/",
            json={"message": "What is Python?"},
            headers=headers
        )
        
        assert msg_resp.status_code == 200
        assert "response" in msg_resp.json()
```

### Load Testing

Use tools like locust for load testing:

```python
# locustfile.py
from locust import HttpUser, task, between

class CogniVoxUser(HttpUser):
    wait_time = between(1, 3)
    token = None
    
    def on_start(self):
        response = self.client.post("/api/auth/login/", json={
            "email": "loadtest@example.com",
            "password": "testpass123"
        })
        self.token = response.json()["access"]
    
    @task
    def send_chat(self):
        self.client.post(
            "/api/chat/threads/1/sub-threads/",
            json={"message": "Hello, how are you?"},
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

---

## Deployment Procedures

### Production Preparation

**Security Checklist:**
- [ ] Change all default passwords
- [ ] Generate new secret keys
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS only
- [ ] Set DEBUG=False
- [ ] Configure rate limiting
- [ ] Set up log aggregation
- [ ] Configure backup procedures

### Docker Production Deployment

**Create production docker-compose:**

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  django:
    build: ./agentic_django
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - static_files:/app/static
    restart: always
    
  memory:
    build: ./Agentic-Memory
    environment:
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    restart: always
    
  # ... other services

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/ssl/certs
      - static_files:/var/www/static
    restart: always
```

### Monitoring Setup

**Prometheus metrics endpoint:**

Each service exposes `/metrics` endpoint when metrics are enabled.

**Health checks:**

```bash
# Kubernetes-style health probes
curl http://localhost:8000/health/      # Django
curl http://localhost:8002/health       # Memory
curl http://localhost:8001/health       # Graph-RAG
```

---

## Common Troubleshooting

### Issue: Ollama Model Not Loading

**Symptoms:** "Model not found" or slow response times

**Solutions:**
1. Check if model is pulled: `docker exec agentic-ollama ollama list`
2. Pull model if missing: `docker exec agentic-ollama ollama pull <model>`
3. Check GPU memory: Model may be too large for available VRAM
4. Check keep_alive setting in config.yaml

### Issue: Database Connection Refused

**Symptoms:** Connection errors to PostgreSQL/MongoDB/Neo4j

**Solutions:**
1. Verify containers are running: `docker ps`
2. Check container logs: `docker logs <container-name>`
3. Verify port mappings in docker-compose.yml
4. Check firewall rules if accessing remotely

### Issue: JWT Token Invalid

**Symptoms:** 401 Unauthorized errors

**Solutions:**
1. Check token expiration (default 60 minutes)
2. Verify SECRET_KEY matches between frontend and backend
3. Clear browser localStorage and re-login
4. Check for clock skew between client and server

### Issue: Memory Service Not Responding

**Symptoms:** Chat requests timeout or fail

**Solutions:**
1. Check Memory service logs for errors
2. Verify Ollama is responding: `curl http://localhost:11434/api/tags`
3. Check GPU memory usage: `nvidia-smi`
4. Restart Memory service

### Issue: Document Ingestion Fails

**Symptoms:** Documents not appearing in knowledge base

**Solutions:**
1. Check Graph-RAG service logs
2. Verify file format is supported
3. Check disk space for vector storage
4. Verify Neo4j connection

---

## Development Workflows

### Feature Development

1. Create feature branch: `git checkout -b feature/my-feature`
2. Implement changes with tests
3. Run local tests
4. Create pull request
5. Code review
6. Merge to develop
7. Deploy to staging
8. Final testing
9. Merge to main
10. Deploy to production

### Bug Fixing

1. Reproduce bug in local environment
2. Create failing test
3. Fix bug
4. Verify test passes
5. Check for regression
6. Create PR with fix and test

### Adding New Dependencies

1. Add to requirements.txt or package.json
2. Test locally
3. Update Dockerfile if needed
4. Document in README
5. Update this KT guide if significant

---

## Code Conventions & Standards

### Python Style

- Follow PEP 8
- Use type hints
- Docstrings for all public methods
- Max line length: 100 characters
- Use f-strings for formatting

### TypeScript Style

- Use TypeScript strict mode
- Define interfaces for all data structures
- Prefer const over let
- Use async/await over promises

### Git Commit Messages

```
type(scope): subject

body (optional)

footer (optional)
```

Types: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(chat): add sub-thread creation endpoint

Implements the FastAPI-compatible endpoint for creating sub-threads
within existing chat threads.

Closes #123
```

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests included and passing
- [ ] Documentation updated
- [ ] No sensitive data in commits
- [ ] Error handling appropriate
- [ ] Logging added for debugging
- [ ] Security considerations addressed

---

## Conclusion

This Knowledge Transfer guide provides a comprehensive foundation for working with the CogniVox platform. As you gain experience with the codebase, you'll develop deeper understanding of the patterns and practices that make the system effective.

**Key Takeaways:**

1. CogniVox is a microservices architecture with clear separation of concerns
2. Django handles API gateway, Memory service handles AI orchestration, Graph-RAG handles document intelligence
3. Configuration is managed through YAML files with environment variables for secrets
4. Agents follow a consistent pattern with BaseAgent inheritance
5. Security is implemented at multiple layers throughout the stack

**Next Steps:**

1. Set up your local development environment
2. Explore the codebase following this guide
3. Run the test suites to verify your setup
4. Pick up a starter task to gain hands-on experience
5. Ask questions—the team is here to help

Welcome to the CogniVox team!
