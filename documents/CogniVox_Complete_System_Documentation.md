# CogniVox Complete System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Modern Architecture](#modern-architecture)
3. [UV-Based Development Setup](#uv-based-development-setup)
4. [Master Orchestrator](#master-orchestrator)
5. [Service Components](#service-components)
6. [Advanced Features](#advanced-features)
7. [Performance Optimizations](#performance-optimizations)
8. [Deployment Strategy](#deployment-strategy)
9. [API Documentation](#api-documentation)
10. [Security Framework](#security-framework)
11. [Monitoring and Health Checks](#monitoring-and-health-checks)
12. [Troubleshooting Guide](#troubleshooting-guide)

## System Overview

CogniVox is a next-generation conversational AI ecosystem designed for intelligent document processing, knowledge retrieval, and interactive chat capabilities. The system features a modern microservices architecture with advanced GPU optimization, unified agent systems, and lightning-fast UV-based setup.

### System Purpose
- **Advanced Document Processing**: Transform PDFs into searchable knowledge graphs using LlamaIndex
- **Conversational AI**: Multi-agent chat system with GPU optimization and persistent memory
- **Unified Intelligence**: Single-agent approach reducing LLM calls by 50%
- **Smart Caching**: Prevents re-analysis of processed documents
- **Real-time Interaction**: Live chat with streaming responses and 3D visualizations
- **Cross-Platform Support**: Windows, macOS, and Linux with unified setup

### Core Capabilities
- **LlamaIndex Integration**: Advanced document indexing and retrieval
- **GPU Acceleration**: Automatic CUDA detection with CPU fallback
- **Vector Storage**: ChromaDB and Neo4j integration for hybrid search
- **Multi-level Memory**: L0 (RAM), L2 (MongoDB) memory hierarchy
- **Real-time 3D UI**: Interactive globe visualizations and modern React components
- **Health Monitoring**: Comprehensive service discovery and monitoring
- **Master Orchestrator**: Coordinated service management with dependency resolution

### Key Modernization Features
- **UV Package Manager**: 10-100x faster Python dependency installation
- **Service Orchestration**: Master orchestrator with health monitoring and graceful shutdown
- **GPU Resource Management**: Singleton GPU manager with allocation tracking
- **Unified Agents**: 50% reduction in processing costs through agent consolidation
- **Smart Document Caching**: Prevents redundant document processing
- **Rich Terminal UI**: Beautiful progress bars, status tables, and interactive menus

## Modern Architecture

### High-Level Architecture

The CogniVox ecosystem follows a microservices architecture with modern development practices and advanced optimization features:

#### Service Composition
1. **Agentic-Frontend**: React 18 with TypeScript, 3D visualizations, and real-time chat
2. **Agentic-Backend**: FastAPI orchestrator with timezone utilities and admin endpoints
3. **Agentic-Memory**: Multi-agent engine with GPU optimization and unified intelligence
4. **Agentic-Graph-RAG**: LlamaIndex-powered document processing with smart caching

#### Communication Pattern
- **Frontend ↔ Backend**: REST APIs with JWT authentication and real-time streaming
- **Backend ↔ Memory**: HTTP API with enhanced timeout handling and health checks
- **Backend ↔ GraphRAG**: HTTP API with smart caching and dependency validation
- **Memory ↔ GraphRAG**: Direct integration with unified agent communication
- **Orchestrator ↔ All Services**: Health monitoring, dependency resolution, and graceful shutdown

### Advanced Service Architecture

```mermaid
graph TB
    subgraph "Development & Orchestration Layer"
        O[Master Orchestrator]
        O1[UV Package Manager]
        O2[Health Monitoring]
        O3[Service Discovery]
        O4[Graceful Shutdown]
        O5[Rich Terminal UI]
    end
    
    subgraph "User Interface Layer"
        A[React 18 Frontend]
        A1[3D Globe Visualizations]
        A2[Real-time Chat Interface]
        A3[Interactive Document Upload]
        A4[Responsive Material-UI]
        A5[Hot Module Replacement]
    end
    
    subgraph "API Gateway Layer"
        B[FastAPI Backend]
        B1[JWT Authentication]
        B2[Thread Management]
        B3[Admin Endpoints]
        B4[Timezone Utilities]
        B5[Health Monitoring]
    end
    
    subgraph "Processing Layer"
        C[Memory Service]
        C1[GPU Resource Manager]
        C2[Unified Agents]
        C3[Multi-level Memory]
        C4[Context Awareness]
        
        D[GraphRAG Service]
        D1[LlamaIndex Integration]
        D2[Smart Document Caching]
        D3[Unified Query Intelligence]
        D4[Hybrid Vector Search]
    end
    
    subgraph "Data Layer"
        E[PostgreSQL]
        F[MongoDB]
        G[Neo4j]
        H[ChromaDB]
        I[Ollama LLM Server]
    end
    
    O --> A
    O --> B
    O --> C
    O --> D
    
    A --> B
    B --> C
    B --> D
    C --> D
    
    B --> E
    C --> F
    D --> G
    D --> H
    C --> I
    D --> I
```

## UV-Based Development Setup

### Revolutionary Setup Speed (10-100x Faster)

The system uses UV package manager for lightning-fast Python dependency installation, reducing setup time from hours to minutes.

#### Quick Start (Complete Setup: 5-15 minutes)
```bash
# Clone the repository
git clone <repository-url>
cd Agentic

# Complete environment setup with master orchestrator
python run_all_services.py setup --auto-install

# Setup and run everything in one command
python run_all_services.py run --auto-install

# Check prerequisites and auto-install missing components
python run_all_services.py check --auto-install
```

#### Individual Service Setup
```bash
# Backend service (2-5 minutes)
cd Agentic-Backend
python setup.py        # UV-based setup with health checks
python run.py          # Start with monitoring

# Memory service (3-8 minutes with AI/ML dependencies)
cd Agentic-Memory
python setup.py        # AI/ML optimized setup with GPU detection
python run.py          # Start with GPU optimization

# GraphRAG service (5-10 minutes with LlamaIndex)
cd Agentic-Graph-RAG
python setup.py        # LlamaIndex and graph database setup
python run.py          # Start with Neo4j/ChromaDB checks

# Frontend service (3-5 minutes)
cd Agentic-frontend
python setup.py        # Node.js dependency management with npm
python run.py          # Start Vite development server with HMR
```

### Modern Setup Features

#### UV Package Manager Integration
- **Cross-Platform Installation**: Automatic UV installation for Windows/macOS/Linux
- **Virtual Environment Isolation**: Automatic environment creation and activation
- **Binary Package Preference**: Avoids compilation issues on Windows
- **Extended Timeouts**: Handles large AI/ML packages (PyTorch, LangChain)
- **Dependency Conflict Resolution**: Smart resolution of complex dependency trees

#### AI/ML Optimized Installation
- **PyTorch CPU Optimization**: Faster installation with smaller footprint
- **LangChain Ecosystem Management**: Coordinated installation of LangChain components
- **LlamaIndex Integration**: Proper setup of LlamaIndex and readers
- **GPU Detection**: Automatic CUDA environment configuration
- **Fallback Mechanisms**: Graceful degradation when components unavailable

#### Enhanced Run Scripts
All services feature modern run scripts with:
- **Health Checks**: Dependency validation before startup
- **GPU Detection**: Automatic GPU/CPU optimization
- **Service Discovery**: Environment setup for inter-service communication
- **Graceful Shutdown**: Signal handling for clean termination
- **Performance Monitoring**: Built-in timing and resource tracking

## Master Orchestrator

### Comprehensive Service Management

The master orchestrator provides centralized control over the entire ecosystem with beautiful Rich UI and intelligent service management.

#### Orchestrator Commands
```bash
# Complete infrastructure management
python run_all_services.py setup        # Initial setup all services
python run_all_services.py start        # Start all services with dependencies
python run_all_services.py stop         # Graceful stop all services
python run_all_services.py restart      # Rolling restart with health checks
python run_all_services.py status       # Real-time service status

# Development workflows
python run_all_services.py dev          # Start in development mode
python run_all_services.py logs         # Aggregate log viewing

# Individual service control
python run_all_services.py start backend    # Start specific service
python run_all_services.py stop frontend   # Stop specific service

# Infrastructure management
python run_all_services.py docker start    # Start Docker infrastructure
python run_all_services.py docker stop     # Stop Docker services
python run_all_services.py docker status   # Check Docker health
```

#### Advanced Orchestrator Features

**🎨 Beautiful Rich UI**
- **Progress Bars**: Real-time setup progress with spinners and completion tracking
- **Status Tables**: Professional service status display with health monitoring
- **Error Panels**: Enhanced error reporting with detailed diagnostics
- **Interactive Menus**: Hierarchical navigation with categories and breadcrumbs

**🔧 Automatic Prerequisite Detection**
- **UV Package Manager**: Auto-detection and installation (10-100x faster than pip)
- **Python Version**: Ensures Python 3.8+ is available across platforms
- **Node.js & npm**: Required for frontend development with version checking
- **Docker & Docker Daemon**: Containerized services with health validation
- **Git**: Version control system detection and recommendations

**🐳 Docker Infrastructure Management**
- **Automatic Service Startup**: PostgreSQL, MongoDB, Neo4j, Ollama, PgAdmin
- **Health Monitoring**: Real-time container status and connectivity checks
- **Credential Management**: Automated .env file generation and service discovery
- **Service Dependencies**: Proper startup order ensuring databases before applications
- **GPU Support**: NVIDIA GPU detection and configuration for Ollama

**🤖 AI Model Management**
- **Default Models**: qwen3:4b, llama3.1:latest, nomic-embed-text, mistral:latest
- **Automatic Installation**: Downloads and validates models during setup
- **Model Validation**: Ensures models are ready before starting applications
- **Smart Caching**: Prevents re-downloading of existing models

### Service Discovery and Health Monitoring

#### Real-time Health Checks
```python
class ServiceOrchestrator:
    """Modern service orchestration with real-time monitoring"""
    
    async def check_service_status(self) -> Dict[str, bool]:
        """Real-time service status with health validation"""
        status = {}
        current_time = time.strftime("%H:%M:%S")
        
        # Application Services with timing
        for service_name, service in self.services.items():
            start_time = time.time()
            is_healthy = service.is_running()  # Health check with timeout
            response_time = int((time.time() - start_time) * 1000)
            
            status[service_name] = {
                "healthy": is_healthy,
                "response_time_ms": response_time,
                "last_checked": current_time
            }
        
        return status
```

#### Dependency Management
- **Service Dependencies**: Automatic resolution of service startup order
- **Health Validation**: Continuous monitoring with automatic recovery
- **Graceful Degradation**: Fallback mechanisms when dependencies unavailable
- **Resource Allocation**: GPU and memory resource management

## Service Components

### 1. Agentic-Frontend (React 18 + 3D Visualizations)

**Modern React Architecture**
- **React 18**: Concurrent features, Suspense, and automatic batching
- **TypeScript**: Full type safety with strict configuration
- **Vite**: Lightning-fast development with Hot Module Replacement
- **Material-UI**: Professional component library with custom theming

**3D Visualizations & Interactive UI**
- **Three.js Integration**: Interactive globe and 3D elements
- **React Three Fiber**: Declarative 3D scene management
- **Framer Motion**: Smooth animations and transitions
- **Real-time Chat**: WebSocket-based communication with streaming

**Advanced Features**
- **File Upload**: Drag-and-drop PDF processing with progress indicators
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Theme System**: Dark/light mode with system preference detection
- **Context Management**: Efficient state management with React Context

**Key Components**
```typescript
// Interactive 3D Globe with satellite tracking
<EarthGlobe
  markers={documents}
  onMarkerClick={handleDocumentSelect}
  autoRotate={true}
  height={400}
/>

// Real-time chat with streaming responses
<Chat
  onMessage={sendMessage}
  messages={messages}
  isTyping={isGenerating}
  sourceDocuments={sourceObjects}
/>

// Modern file upload with validation
<FileUploadModal
  acceptedTypes={['.pdf']}
  maxSize={50 * 1024 * 1024} // 50MB
  onUploadSuccess={handleUploadSuccess}
/>
```

### 2. Agentic-Backend (FastAPI + Enhanced Features)

**Modern FastAPI Architecture**
- **Async/Await**: Full async support for high performance
- **Dependency Injection**: Clean separation of concerns
- **Automatic OpenAPI**: Interactive documentation with Swagger UI
- **CORS Middleware**: Configured for frontend integration

**Enhanced API Endpoints**
- **Authentication**: JWT with refresh tokens and role-based access
- **Thread Management**: Conversation threading with metadata
- **Admin Endpoints**: User management and request reset capabilities
- **Timezone Utilities**: Comprehensive timezone handling and conversion

**Advanced Features**
```python
# Timezone-aware API endpoints
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation with timezone awareness"""
    conversation_data.created_at = convert_to_utc(conversation_data.created_at)
    # ... implementation

# Admin-only endpoints with role validation
@router.post("/admin/reset_requests/{user_id}")
async def reset_requests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_role)
):
    """Reset user request counters (ADMIN only)"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    # ... implementation
```

**Database Architecture**
- **PostgreSQL**: Primary database with UUID primary keys and JSONB support
- **MongoDB**: Document storage for conversations and metadata
- **Alembic**: Database migrations with dependency checking
- **Connection Pooling**: Optimized database connections with health monitoring

### 3. Agentic-Memory (GPU-Optimized Multi-Agent System)

**GPU Resource Management**
- **Singleton GPU Manager**: Centralized GPU allocation with thread safety
- **Automatic Detection**: CUDA detection with CPU fallback
- **Resource Tracking**: Memory usage monitoring and allocation tracking
- **Cool-down Periods**: Prevents GPU thrashing with configurable timeouts

**Unified Agent System**
```python
class UnifiedQueryIntelligenceAgent(BaseAgent):
    """
    Optimized single-agent approach replacing multiple separate agents
    - 50% reduction in LLM calls
    - Consistent analysis context
    - Structured JSON output
    """
    
    @gpu_required(device_param="device_id")
    async def analyze_query(self, query: str, context: dict = None, 
                           device_id: Optional[int] = None) -> dict:
        """Single comprehensive query analysis with GPU acceleration"""
        # GPU-accelerated text processing when available
        if device_id is not None:
            embedding = text_encoder.encode(query, device_id=device_id)
        else:
            embedding = text_encoder.encode(query)  # CPU fallback
        
        analysis = await self.llm_client.generate(
            prompt=self.unified_prompt.format(query=query, context=context),
            temperature=self.temperature
        )
        return self._parse_structured_response(analysis)
```

**Multi-Level Memory System**
- **L0 Memory (RAM)**: Fast access for recent conversations
- **L2 Memory (MongoDB)**: Persistent storage with indexing
- **Context Awareness**: Intelligent context retrieval with relevance scoring
- **Smart Caching**: GPU-accelerated similarity search for context retrieval

**Performance Optimizations**
- **Document Caching**: Prevents re-analysis of processed documents
- **Batch Processing**: Efficient processing of multiple queries
- **Memory Compression**: Optimized storage of conversation history
- **Async Operations**: Non-blocking operations with proper error handling

### 4. Agentic-Graph-RAG (LlamaIndex + Smart Caching)

**LlamaIndex Integration**
```python
class LlamaIndexProcessor:
    """Advanced document processing with LlamaIndex"""
    
    def __init__(self):
        self.llamaindex_processor = LlamaIndexProcessor()
        self.pdf_reader = SimpleDirectoryReader()
        self.node_parser = SentenceSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            paragraph_separator="\n\n"
        )
        self.embedding_generator = OllamaEmbedding(
            model_name="nomic-embed-text"
        )
    
    async def process_document(self, pdf_path: str) -> ProcessingResult:
        """Process document with LlamaIndex pipeline"""
        # 1. Load document with enhanced reader
        documents = await self._load_document(pdf_path)
        
        # 2. Extract metadata using AI
        metadata = await self._extract_enhanced_metadata(documents[0])
        
        # 3. Intelligent chunking with sentence awareness
        nodes = self.node_parser.get_nodes_from_documents(documents)
        
        # 4. Generate embeddings with Ollama
        for node in nodes:
            embedding = await self.embedding_generator.get_text_embedding(
                node.get_content()
            )
            node.embedding = embedding
        
        return ProcessingResult(nodes=nodes, metadata=metadata)
```

**Smart Document Caching**
- **Hash-based Deduplication**: Prevents reprocessing of identical documents
- **Incremental Updates**: Only processes changed content
- **Metadata Caching**: Stores processing metadata for quick retrieval
- **Performance Monitoring**: Tracks processing times and cache hit rates

**Hybrid Search Capabilities**
- **Semantic Search**: Vector similarity with ChromaDB
- **Keyword Search**: Traditional text search with BM25
- **Hybrid Fusion**: Combines semantic and keyword results
- **Graph Traversal**: Neo4j-powered relationship exploration

**Advanced Features**
- **Export Capabilities**: JSON, GraphML, and RDF export formats
- **Visualization**: Interactive knowledge graph visualization
- **User Isolation**: Document access control per user
- **Batch Processing**: Efficient processing of multiple documents

## Advanced Features

### GPU Acceleration and Resource Management

#### Singleton GPU Manager
```python
class GPUManager:
    """Thread-safe singleton GPU resource manager"""
    
    def __init__(self):
        self._gpus: Dict[int, GPUResource] = {}
        self._enable_gpus = os.getenv("ENABLE_GPUS", "FALSE").upper() == "TRUE"
        self._allocation_timeout = float(os.getenv("GPU_ALLOCATION_TIMEOUT", "30.0"))
        
    @contextmanager
    def gpu_context(self, owner: str):
        """Context manager for automatic GPU allocation/release"""
        device_id = self.allocate_gpu(owner, wait=True, timeout=30)
        try:
            yield device_id
        finally:
            if device_id is not None:
                self.release_gpu(owner)
    
    def get_gpu_memory_usage(self, device_id: int) -> Dict[str, float]:
        """Get detailed GPU memory statistics"""
        stats = {}
        stats["total"] = torch.cuda.get_device_properties(device_id).total_memory / (1024**2)
        stats["allocated"] = torch.cuda.memory_allocated(device_id) / (1024**2)
        stats["reserved"] = torch.cuda.memory_reserved(device_id) / (1024**2)
        return stats
```

#### GPU-Accelerated Text Processing
```python
@gpu_required(device_param="device_id")
def compute_similarities(query: str, texts: List[str], 
                        device_id: Optional[int] = None) -> np.ndarray:
    """GPU-accelerated similarity computation"""
    if device_id is not None:
        device = torch.device(f'cuda:{device_id}')
        # Use GPU for encoding
        query_embedding = model.encode(query, device=device)
        text_embeddings = model.encode(texts, device=device)
    else:
        # CPU fallback
        query_embedding = model.encode(query)
        text_embeddings = model.encode(texts)
    
    similarities = cosine_similarity([query_embedding], text_embeddings)[0]
    return similarities
```

### Unified Agent Intelligence

#### 50% Reduction in LLM Calls
The system uses unified agents that combine multiple analysis steps into single, comprehensive operations:

```python
class UnifiedQueryIntelligenceAgent:
    """
    Replaces separate intent classification, query expansion, and validation agents
    """
    
    async def analyze_query(self, query: str) -> dict:
        """Single call returns: intent, expanded_query, validation, context_needs"""
        unified_prompt = """
        Analyze this query comprehensively:
        Query: {query}
        
        Return JSON with:
        {
            "intent": "question|request|conversation",
            "expanded_query": "enhanced version with synonyms",
            "requires_documents": true/false,
            "confidence": 0.0-1.0,
            "suggested_mode": "semantic|keyword|hybrid"
        }
        """
        
        response = await self.llm.generate(unified_prompt.format(query=query))
        return json.loads(response)
```

### Smart Document Caching

#### Intelligent Caching System
```python
class SmartDocumentCache:
    """Prevents reprocessing of documents with intelligent caching"""
    
    def __init__(self):
        self.cache_db = {}  # In production: Redis or similar
        
    def get_document_hash(self, pdf_path: str) -> str:
        """Generate hash from file content and metadata"""
        with open(pdf_path, 'rb') as f:
            content = f.read()
        file_stats = os.stat(pdf_path)
        hash_input = content + str(file_stats.st_mtime).encode()
        return hashlib.sha256(hash_input).hexdigest()
    
    async def get_or_process(self, pdf_path: str) -> dict:
        """Get cached result or process document"""
        doc_hash = self.get_document_hash(pdf_path)
        
        if doc_hash in self.cache_db:
            logger.info(f"Cache hit for document {pdf_path}")
            return self.cache_db[doc_hash]
        
        # Process document
        result = await self.processor.process_document(pdf_path)
        self.cache_db[doc_hash] = result
        logger.info(f"Cached new document processing result")
        return result
```

### Real-time Communication

#### Server-Sent Events for Streaming
```python
@router.post("/chat/stream")
async def stream_chat_response(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Stream chat responses in real-time"""
    
    async def generate_response():
        yield "data: {\"type\": \"thinking\", \"content\": \"Processing your query...\"}\n\n"
        
        # Process query with unified agent
        analysis = await unified_agent.analyze_query(request.message)
        
        yield f"data: {json.dumps({\"type\": \"analysis\", \"content\": analysis})}\n\n"
        
        # Generate response with streaming
        async for chunk in llm.stream_generate(request.message):
            yield f"data: {json.dumps({\"type\": \"response\", \"content\": chunk})}\n\n"
        
        yield "data: {\"type\": \"complete\"}\n\n"
    
    return StreamingResponse(generate_response(), media_type="text/plain")
```

## Performance Optimizations

### System-wide Performance Enhancements

#### 1. UV Package Manager Benefits
- **10-100x Faster Installation**: Parallel downloads and caching
- **Binary Package Preference**: Avoids compilation on Windows
- **Optimized Dependency Resolution**: Smart conflict resolution
- **Cross-platform Compatibility**: Unified experience across OS

#### 2. GPU Resource Optimization
- **Automatic GPU Detection**: CUDA availability with fallback
- **Memory Management**: Tracking and optimization of GPU memory
- **Resource Pooling**: Shared GPU resources across agents
- **Cool-down Periods**: Prevents GPU thrashing

#### 3. Database Optimizations
- **Connection Pooling**: Optimized database connections
- **Index Optimization**: Strategic indexes for common queries
- **Async Operations**: Non-blocking database operations
- **Query Caching**: Redis-like caching for frequent queries

#### 4. Memory Management
- **Multi-level Storage**: L0 (RAM) and L2 (MongoDB) hierarchy
- **Context Compression**: Efficient storage of conversation history
- **Garbage Collection**: Automatic cleanup of old data
- **Memory Monitoring**: Real-time memory usage tracking

### Performance Monitoring

#### Built-in Metrics Collection
```python
class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.metrics = {
            "response_times": [],
            "gpu_utilization": [],
            "memory_usage": [],
            "cache_hit_rates": []
        }
    
    @contextmanager
    def track_operation(self, operation_name: str):
        """Track operation performance"""
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.virtual_memory().used
            
            self.metrics["response_times"].append({
                "operation": operation_name,
                "duration": end_time - start_time,
                "memory_delta": end_memory - start_memory,
                "timestamp": datetime.utcnow()
            })
```

## Deployment Strategy

### Docker Infrastructure

#### Multi-Service Deployment
```yaml
# docker-compose.agentic-services.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: cognivox
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: cognivox
      MONGO_INITDB_ROOT_PASSWORD: cognivox
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
    
  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/password
      NEO4J_PLUGINS: '["apoc"]'
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Service Configuration
```python
# Orchestrator service configuration
self.services = {
    "backend": ServiceConfig(
        name="Backend API",
        directory="Agentic-Backend",
        run_command=["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        port=8000,
        dependencies=["postgres", "mongodb"],
        health_endpoint="/health"
    ),
    "memory": ServiceConfig(
        name="Memory Service",
        directory="Agentic-Memory", 
        run_command=["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"],
        port=8002,
        dependencies=["mongodb", "ollama"],
        health_endpoint="/api/health"
    ),
    "graphrag": ServiceConfig(
        name="Graph RAG Service",
        directory="Agentic-Graph-RAG",
        run_command=["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8003"],
        port=8003,
        dependencies=["neo4j", "ollama"],
        health_endpoint="/health"
    ),
    "frontend": ServiceConfig(
        name="Frontend",
        directory="Agentic-frontend",
        run_command=["npm", "run", "dev"],
        port=3000,
        dependencies=["backend"],
        health_endpoint="/api/health"
    )
}
```

### Production Deployment

#### Environment Configuration
```bash
# Production environment variables
NODE_ENV=production
PYTHONPATH=/app/src
LOG_LEVEL=INFO

# Database URLs
DATABASE_URL=postgresql://user:pass@postgres:5432/cognivox
MONGODB_URI=mongodb://user:pass@mongodb:27017/cognivox
NEO4J_URI=bolt://neo4j:7687
NEO4J_AUTH=neo4j/password

# AI Services
OLLAMA_HOST=http://ollama:11434
EMBEDDING_MODEL=nomic-embed-text
TEXT_GENERATION_MODEL=llama3.1

# GPU Configuration
ENABLE_GPUS=TRUE
GPU_COUNT=1
GPU_MEMORY_LIMIT=8GB

# Performance Tuning
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=300
```

## API Documentation

### Comprehensive API Endpoints

#### Authentication Endpoints
```python
# JWT Authentication with refresh tokens
POST /api/auth/register     # User registration with validation
POST /api/auth/token        # Login with credentials
GET  /api/auth/me          # Get current user profile
POST /api/auth/refresh     # Refresh JWT token
POST /api/auth/logout      # Logout and invalidate token
```

#### Chat and Conversation Management
```python
# Real-time chat with streaming
POST /api/chat/message              # Send chat message
GET  /api/chat/stream/{thread_id}   # Stream responses (SSE)
POST /api/chat/threads              # Create conversation thread
GET  /api/chat/threads              # List user threads
GET  /api/chat/threads/{id}         # Get specific thread
DELETE /api/chat/threads/{id}       # Delete thread
```

#### Document Processing
```python
# Advanced document management
POST /api/documents/upload          # Upload PDF documents
POST /api/documents/process         # Process documents with LlamaIndex
GET  /api/documents/                # List processed documents
GET  /api/documents/{id}            # Get document details
DELETE /api/documents/{id}          # Remove document from knowledge base
```

#### Knowledge Graph Operations
```python
# Graph and vector operations
POST /api/graph/query               # Query knowledge graph
GET  /api/graph/visualize           # Get graph visualization data
POST /api/graph/semantic-search     # Semantic search with vectors
POST /api/graph/hybrid-search       # Hybrid semantic + keyword search
GET  /api/graph/export              # Export graph data
```

#### Admin Endpoints (Role-Based)
```python
# Administrative functions
POST /api/admin/reset_requests/{user_id}    # Reset user request quotas
POST /api/admin/add_models_to_user/{user_id} # Assign models to users
GET  /api/admin/users                       # List all users
GET  /api/admin/analytics                   # System analytics
```

#### Health and Monitoring
```python
# System health and monitoring
GET /health                         # Service health check
GET /api/health                     # Detailed health with dependencies
GET /metrics                        # Prometheus metrics
GET /api/status                     # Real-time system status
```

### API Response Formats

#### Standardized Response Structure
```json
{
  "status": "success|error",
  "data": {
    "message": "Response content",
    "sources": [
      {
        "document_id": "doc_123",
        "page_number": 1,
        "relevance_score": 0.95,
        "content": "Relevant text excerpt"
      }
    ],
    "metadata": {
      "processing_time_ms": 250,
      "model_used": "llama3.1",
      "confidence": 0.87,
      "cached": false
    }
  },
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 156,
    "has_next": true
  },
  "timestamp": "2024-12-20T10:30:00Z"
}
```

## Security Framework

### Multi-layered Security Approach

#### 1. Authentication and Authorization
```python
# JWT with role-based access control
class JWTManager:
    def create_token(self, user: User) -> str:
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "type": "access"
        }
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

# Role-based access control
@require_role([UserRole.ADMIN])
async def admin_only_endpoint():
    """Endpoint accessible only to administrators"""
    pass
```

#### 2. Input Validation and Sanitization
```python
# Comprehensive input validation
class ChatMessage(BaseModel):
    content: str = Field(
        min_length=1, 
        max_length=10000,
        description="Message content"
    )
    thread_id: Optional[str] = Field(
        regex=r'^[a-zA-Z0-9_-]+$',
        description="Thread identifier"
    )
    
    @validator('content')
    def validate_content(cls, v):
        # Sanitize HTML and prevent XSS
        clean_content = bleach.clean(v, tags=[], strip=True)
        if len(clean_content.strip()) == 0:
            raise ValueError("Content cannot be empty after sanitization")
        return clean_content
```

#### 3. Rate Limiting and DDoS Protection
```python
# Rate limiting with Redis backend
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat/message")
@limiter.limit("10/minute")  # 10 requests per minute per IP
async def send_message(
    request: Request,
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Rate-limited chat endpoint"""
    pass
```

#### 4. Data Protection and Privacy
```python
# Data encryption at rest and in transit
class EncryptedField:
    def __init__(self, secret_key: str):
        self.cipher = Fernet(secret_key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Database field encryption
class User(Base):
    email = Column(String, nullable=False)  # Hashed in application
    encrypted_preferences = Column(Text)    # Encrypted sensitive data
```

#### 5. CORS and Security Headers
```python
# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://cognivox.example.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"]
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Monitoring and Health Checks

### Comprehensive Health Monitoring

#### 1. Service Health Checks
```python
class HealthChecker:
    """Comprehensive health monitoring for all services"""
    
    async def check_service_health(self, service_url: str) -> HealthStatus:
        """Check individual service health with detailed metrics"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{service_url}/health",
                    timeout=5.0
                )
                
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    health_data = response.json()
                    return HealthStatus(
                        is_healthy=True,
                        response_time_ms=int(response_time * 1000),
                        details=health_data,
                        dependencies=health_data.get("dependencies", {})
                    )
                else:
                    return HealthStatus(
                        is_healthy=False,
                        error=f"HTTP {response.status_code}",
                        response_time_ms=int(response_time * 1000)
                    )
                    
        except asyncio.TimeoutError:
            return HealthStatus(
                is_healthy=False,
                error="Timeout after 5 seconds",
                response_time_ms=5000
            )
        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                error=str(e),
                response_time_ms=int((time.time() - start_time) * 1000)
            )
```

#### 2. Database Health Monitoring
```python
async def check_database_health() -> dict:
    """Comprehensive database health checks"""
    health_status = {}
    
    # PostgreSQL health
    try:
        async with get_async_session() as session:
            result = await session.execute(text("SELECT 1"))
            await session.execute(text("SELECT COUNT(*) FROM users"))
            health_status["postgresql"] = {
                "status": "healthy",
                "tables_accessible": True,
                "connection_pool": {
                    "active": session.get_bind().pool.checkedout(),
                    "total": session.get_bind().pool.size()
                }
            }
    except Exception as e:
        health_status["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # MongoDB health
    try:
        await mongodb.admin.command('ping')
        collection_count = len(await mongodb.list_collection_names())
        health_status["mongodb"] = {
            "status": "healthy",
            "collections": collection_count,
            "server_status": await mongodb.admin.command('serverStatus')
        }
    except Exception as e:
        health_status["mongodb"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return health_status
```

#### 3. GPU and Resource Monitoring
```python
async def check_gpu_health() -> dict:
    """Monitor GPU resources and utilization"""
    gpu_status = {}
    
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            device_props = torch.cuda.get_device_properties(i)
            memory_allocated = torch.cuda.memory_allocated(i)
            memory_reserved = torch.cuda.memory_reserved(i)
            
            gpu_status[f"gpu_{i}"] = {
                "name": device_props.name,
                "memory": {
                    "total_mb": device_props.total_memory // (1024 ** 2),
                    "allocated_mb": memory_allocated // (1024 ** 2),
                    "reserved_mb": memory_reserved // (1024 ** 2),
                    "free_mb": (device_props.total_memory - memory_reserved) // (1024 ** 2)
                },
                "utilization": torch.cuda.utilization(i),
                "temperature": torch.cuda.temperature(i) if hasattr(torch.cuda, 'temperature') else None
            }
    else:
        gpu_status["message"] = "No CUDA-capable GPUs detected"
    
    return gpu_status
```

#### 4. Real-time Metrics Collection
```python
class MetricsCollector:
    """Prometheus-compatible metrics collection"""
    
    def __init__(self):
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        self.gpu_utilization = Gauge(
            'gpu_utilization_percent',
            'GPU utilization percentage',
            ['device_id']
        )
        self.memory_usage = Gauge(
            'memory_usage_bytes',
            'Memory usage in bytes',
            ['type']
        )
    
    @contextmanager
    def track_request(self, method: str, endpoint: str):
        """Track request metrics"""
        start_time = time.time()
        try:
            yield
            self.request_count.labels(method=method, endpoint=endpoint, status='success').inc()
    except Exception as e:
            self.request_count.labels(method=method, endpoint=endpoint, status='error').inc()
            raise
        finally:
            duration = time.time() - start_time
            self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
```

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Setup and Installation Issues

**Issue**: UV installation fails on Windows
```bash
# Error: PowerShell execution policy restrictions
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Solution**:
```bash
# Alternative installation methods
# Method 1: Direct PowerShell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Method 2: Manual download
# Download from https://github.com/astral-sh/uv/releases
# Add to PATH manually

# Method 3: Use orchestrator auto-install
python run_all_services.py setup --auto-install
```

**Issue**: PyTorch installation fails with UV
```bash
# Error: Failed to compile PyTorch from source
```

**Solution**:
```bash
# Use setup.py with optimized PyTorch installation
cd Agentic-Memory
python setup.py  # Automatically handles PyTorch CPU optimization

# Manual fix
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
```

#### 2. Service Communication Issues

**Issue**: Services can't communicate (connection refused)
```python
# Error: ConnectionError: [Errno 111] Connection refused
```

**Solutions**:
```python
# Check service health
python run_all_services.py status

# Verify service discovery
python run_all_services.py check

# Manual health check
curl http://localhost:8000/health    # Backend
curl http://localhost:8002/api/health # Memory
curl http://localhost:8003/health    # GraphRAG
```

**Issue**: Docker services not starting
```bash
# Error: Docker daemon not running
```

**Solutions**:
```bash
# Start Docker daemon
sudo systemctl start docker  # Linux
# On Windows: Start Docker Desktop

# Use orchestrator for Docker management
python run_all_services.py docker start

# Check Docker health
python run_all_services.py docker status
```

#### 3. GPU and Performance Issues

**Issue**: GPU not detected despite CUDA installation
```python
# Error: CUDA not available
```

**Solutions**:
```python
# Check GPU configuration
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU count: {torch.cuda.device_count()}")

# Environment configuration
export ENABLE_GPUS=TRUE
export GPU_COUNT=1

# Force GPU detection
python -c "from src.gpu_manager import GPUManager; gm = GPUManager(); print(gm.is_gpu_enabled())"
```

**Issue**: Memory leaks in long-running processes
```python
# Symptoms: Gradual memory increase over time
```

**Solutions**:
```python
# Enable memory monitoring
import tracemalloc
tracemalloc.start()

# Check current memory usage
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.1f} MB")

# Use GPU context managers
with gpu_manager.gpu_context("my_process") as device_id:
    if device_id is not None:
        # GPU operations with automatic cleanup
        result = process_with_gpu(data, device_id)
    # GPU automatically released here
```

#### 4. Database and Storage Issues

**Issue**: MongoDB connection failures
```python
# Error: ServerSelectionTimeoutError: No servers found
```

**Solutions**:
```python
# Check MongoDB status
docker ps | grep mongo
docker logs agentic-mongodb

# Restart MongoDB
python run_all_services.py docker restart mongodb

# Connection string validation
MONGODB_URI=mongodb://cognivox:cognivox@localhost:27017/cognivox
```

**Issue**: PostgreSQL migration failures
```bash
# Error: Alembic migration conflicts
```

**Solutions**:
```bash
# Reset migrations (development only)
cd Agentic-Backend
alembic downgrade base
alembic upgrade head

# Fix migration conflicts
alembic merge -m "merge_migrations" heads
alembic upgrade head
```

#### 5. Frontend and UI Issues

**Issue**: React development server fails to start
```bash
# Error: EADDRINUSE: address already in use :::3000
```

**Solutions**:
```bash
# Find and kill process using port 3000
netstat -ano | findstr :3000  # Windows
lsof -ti:3000 | xargs kill    # macOS/Linux

# Use auto-port detection
cd Agentic-frontend
python run.py --auto-port

# Or specify different port
python run.py --port 3001
```

**Issue**: 3D visualizations not rendering
```javascript
// Error: WebGL not supported
```

**Solutions**:
```javascript
// Check WebGL support
const canvas = document.createElement('canvas');
const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
if (!gl) {
    console.error('WebGL not supported');
}

// Fallback for older browsers
// Update GPU drivers
// Enable hardware acceleration in browser settings
```

### Performance Optimization Tips

#### 1. Database Query Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_threads_user_id ON threads(user_id);
CREATE INDEX idx_threads_updated_at ON threads(updated_at);
CREATE INDEX idx_documents_hash ON documents(file_hash);

-- Optimize conversation queries
CREATE INDEX idx_conversations_user_updated 
ON conversations(user_id, updated_at DESC);
```

#### 2. Memory Usage Optimization
```python
# Configure memory limits
MAX_CONTEXT_LENGTH = 4000  # Limit context size
MAX_HISTORY_ITEMS = 50     # Limit conversation history
CACHE_SIZE = 100          # Limit cache entries

# Use generators for large datasets
def get_documents_batch(user_id: int, batch_size: int = 100):
    offset = 0
    while True:
        batch = db.query(Document)\
            .filter(Document.user_id == user_id)\
            .offset(offset)\
            .limit(batch_size)\
            .all()
        
        if not batch:
            break
            
        yield batch
        offset += batch_size
```

#### 3. GPU Optimization
```python
# Optimize GPU memory usage
torch.cuda.empty_cache()  # Clear GPU cache

# Use mixed precision training
with torch.cuda.amp.autocast():
    embeddings = model.encode(texts)

# Batch operations for efficiency
def process_texts_batch(texts: List[str], batch_size: int = 32):
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        yield model.encode(batch)
```

---

## Conclusion

The CogniVox ecosystem represents a state-of-the-art conversational AI platform that combines modern development practices with advanced AI capabilities. This comprehensive documentation provides the foundation for understanding, developing, deploying, and maintaining the complete system.

### Key Technological Achievements
- **UV Package Manager Integration**: Revolutionary 10-100x faster setup times
- **GPU Resource Management**: Intelligent allocation with automatic fallback
- **Unified Agent Architecture**: 50% reduction in LLM processing costs
- **Smart Document Caching**: Prevents redundant processing overhead
- **Real-time 3D Visualizations**: Modern React 18 with Three.js integration
- **Master Orchestrator**: Centralized service management with health monitoring

### Production Readiness Features
- **Comprehensive Health Monitoring**: Real-time service discovery and status tracking
- **Graceful Shutdown Handling**: Clean termination with state preservation
- **Cross-Platform Compatibility**: Unified experience across Windows, macOS, and Linux
- **Enhanced Security**: JWT authentication, RBAC, input validation, and rate limiting
- **Performance Optimization**: GPU acceleration, memory management, and caching strategies
- **Rich Developer Experience**: Beautiful terminal UI, progress tracking, and error diagnostics

### Future Enhancement Opportunities
- **Advanced AI Models**: Integration with newer LLM architectures and multimodal capabilities
- **Enhanced Analytics**: Advanced user behavior tracking and system performance analytics
- **Mobile Applications**: Native iOS and Android applications with offline capabilities
- **Advanced Security**: OAuth2 providers, SSO integration, and zero-trust architecture
- **Edge Computing**: CDN integration and edge deployment for global performance
- **Auto-scaling**: Kubernetes deployment with horizontal pod autoscaling

For detailed technical information about individual components, refer to the component-specific documentation:
- [Frontend Documentation](./CogniVox_Agentic_Frontend_Technical_Documentation.md)
- [Backend Documentation](./CogniVox_Agentic_Backend_Technical_Documentation.md)
- [Memory Service Documentation](./CogniVox_Agentic_Memory_Technical_Documentation.md)
- [GraphRAG Documentation](./CogniVox_Agentic_GraphRAG_Technical_Documentation.md) 