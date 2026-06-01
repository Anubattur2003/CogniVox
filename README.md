# CogniVox Agentic Platform

> **🎉 NEW: Complete Infrastructure Orchestrator!**  
> Enhanced setup system with Docker management, AI model installation, and beautiful Rich UI for comprehensive environment setup.

**🚀 Quick Start for Fresh Repositories:**
```bash
# Complete environment setup (Docker + Apps + AI Models)
python run_all_services.py setup --auto-install

# Setup and run everything in one command
python run_all_services.py run --auto-install

# Check prerequisites before setup
python run_all_services.py check --auto-install
```

## ✨ Enhanced Orchestrator Features

### 🎨 Beautiful Rich UI
- **Progress Bars**: Real-time setup progress with spinners and completion tracking
- **Status Tables**: Professional service status display with health monitoring
- **Error Panels**: Enhanced error reporting with detailed diagnostics
- **Installation Guides**: Automatic display of missing prerequisite instructions

### 🔧 Automatic Prerequisite Detection
- **UV Package Manager**: Auto-detection and installation (10-100x faster than pip)
- **Python Version**: Ensures Python 3.8+ is available
- **Node.js & npm**: Required for frontend development
- **Docker & Docker Daemon**: For containerized services
- **Git**: Version control system

### 🐳 Docker Infrastructure Management
- **Automatic Service Startup**: PostgreSQL, MongoDB, Neo4j, Ollama, PgAdmin
- **Health Monitoring**: Real-time container status and connectivity checks
- **Credential Management**: Automated .env file generation and service discovery
- **Service Dependencies**: Proper startup order ensuring databases before applications
- **GPU Support**: NVIDIA GPU detection and configuration for Ollama

### 🤖 AI Model Management
- **Default Models**: qwen3:4b, llama3.1:latest, nomic-embed-text, mistral:latest
- **Automatic Installation**: Downloads and validates models during setup
- **Model Validation**: Ensures models are ready before starting applications
- **Ollama Integration**: Seamless local LLM inference setup

### 🚀 Complete Infrastructure Setup
- **Three-Phase Setup**: Docker services → AI models → Application services
- **Docker Infrastructure**: Automatic startup of PostgreSQL, MongoDB, Neo4j, Ollama, PgAdmin
- **AI Model Installation**: Default models (qwen3:4b, llama3.1:latest, nomic-embed-text, mistral)
- **Dependency Validation**: Ensures proper service startup order and requirements
- **`--auto-install`**: Automatically installs missing prerequisites
- **`--clean`**: Removes existing environments for fresh setup
- **`--verbose`**: Detailed output for troubleshooting
- **Prerequisites Guide**: Shows installation instructions for missing tools

### 📊 Enhanced Commands
```bash
# Prerequisites checking
python run_all_services.py check [--auto-install]

# Complete environment setup (Docker + Apps + AI Models)
python run_all_services.py setup [--auto-install] [--clean] [--verbose]
python run_all_services.py setup --services backend memory    # Specific services only
python run_all_services.py setup --skip-docker               # Skip Docker infrastructure
python run_all_services.py setup --skip-ollama               # Skip AI model installation

# Docker infrastructure management
python run_all_services.py docker start                      # Start all Docker services
python run_all_services.py docker stop                       # Stop all Docker services
python run_all_services.py ollama --install                  # Install AI models

# Start services
python run_all_services.py start [--services backend] [--dev]

# Beautiful status monitoring
python run_all_services.py status

# Stop services
python run_all_services.py stop [--services backend]

# Complete workflow (setup + start)
python run_all_services.py run [--dev] [--clean] [--auto-install] [--verbose]

# Configuration management
python run_all_services.py credentials                       # Show all credentials
python run_all_services.py urls                             # Show service URLs
python run_all_services.py config create                    # Create config files
```

---

## 📋 Table of Contents
- [Platform Overview](#-platform-overview)
- [Architecture & Components](#-architecture--components)
- [Quick Start Installation](#-quick-start-installation)
- [Detailed Setup Guide](#-detailed-setup-guide)
- [Module Documentation](#-module-documentation)
- [Configuration Management](#-configuration-management)
- [Development Workflow](#-development-workflow)
- [Service Management](#-service-management)
- [Troubleshooting](#-troubleshooting)
- [Production Deployment](#-production-deployment)

---

## 🏗️ Platform Overview

CogniVox Agentic Platform is a comprehensive AI-powered microservices ecosystem designed for advanced conversational AI with intelligent memory management, graph-based knowledge retrieval, and autonomous agent interactions.

### 🎯 Key Features
- **Multi-Modal AI Conversations** with persistent memory
- **Graph-Based Knowledge Retrieval** powered by Neo4j and **ChromaDB**
- **LlamaIndex-Enhanced Document Processing** with intelligent chunking & rich metadata
- **Unified Agent Architecture** (SupervisorReAct & Unified Query Intelligence) cutting LLM calls by 50%
- **GPU-Optimized Processing** with automatic CUDA detection and CPU fallback
- **Interactive 3D Frontend** featuring real-time globe visualisations (Three.js / React Three Fiber)
- **Scalable Microservices Architecture** with UV-based package management for 10-100× faster installs
- **Real-time AI Model Integration** via Ollama with automatic model installation & validation
- **Comprehensive Admin Interface** with role-based access control & analytics
- **Docker-Based Infrastructure** with health monitoring and Rich-UI orchestrator

### 🏛️ Technology Stack
- **Backend:** FastAPI (Python 3.8+)
- **Frontend:** React 18+ with TypeScript, Vite, TailwindCSS
- **Databases:** PostgreSQL, MongoDB, Neo4j
- **AI/ML:** Ollama (Local LLM), LangChain, **LangGraph**, **LlamaIndex**, Vector Embeddings
- **Vector Stores:** **ChromaDB** for high-performance similarity search
- **Infrastructure:** Docker, Docker Compose
- **Package Management:** UV (Python), npm (Node.js)
- **Security:** JWT Authentication, Role-Based Access Control

### ⚡ UV Package Manager Benefits
- **10-100x faster** than pip for Python package installation
- **Robust dependency resolution** with conflict detection
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Virtual environment management** built-in
- **Reproducible builds** with lockfile support
- **GPU-optimized** installations for AI/ML packages

---

## 🧩 Architecture & Components

### Core Microservices

#### 🔧 **Agentic-Backend** (Port 8000)
**Primary service handling authentication, user management, and AI orchestration**

**Structure:**
```
Agentic-Backend/
├── app/
│   ├── api/               # API routes and endpoints
│   ├── core/              # Core functionality (config, database, security)
│   ├── models/            # SQLAlchemy database models
│   ├── schemas/           # Pydantic request/response schemas
│   └── services/          # Business logic services
├── scripts/
│   └── cogni_vox_manager.py # Database management utility
├── alembic/               # Database migrations
├── config.yaml           # Main configuration file
├── requirements.txt       # Python dependencies
└── run.py                # Service entry point
```

**Key Features:**
- JWT-based authentication system
- User role management (Admin, User)
- AI model integration and management
- Subscription plan handling
- RESTful API with FastAPI
- Comprehensive database models

#### 🎨 **Agentic-Frontend** (Port 3000)
**Modern React-based user interface with responsive design**

**Structure:**
```
Agentic-frontend/
├── src/
│   ├── components/        # Reusable React components
│   ├── pages/            # Application pages/views
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API service integrations
│   ├── utils/            # Utility functions
│   └── styles/           # CSS and styling files
├── public/               # Static assets
├── package.json          # Node.js dependencies
├── vite.config.ts        # Vite build configuration
├── tailwind.config.js    # TailwindCSS configuration
└── tsconfig.json         # TypeScript configuration
```

**Key Features:**
- Modern React 18+ with TypeScript
- TailwindCSS for responsive design
- Vite for fast development and building
- Component-based architecture
- Real-time chat interface
- Dashboard and analytics

#### 🧠 **Agentic-Memory** (Port 8002)
**Intelligent memory management and context preservation service**

**Structure:**
```
Agentic-Memory/
├── src/
│   ├── api/              # Memory API endpoints
│   ├── core/             # Core memory management logic
│   ├── models/           # Memory data models
│   ├── services/         # Memory processing services
│   └── gpu_manager/      # GPU optimization utilities
├── chat_memory.db        # SQLite database for local storage
├── requirements.txt      # Python dependencies
└── run.py               # Service entry point
```

**Key Features:**
- Long-term conversation memory
- Context-aware information retrieval
- GPU-optimized processing
- Persistent storage with SQLite
- RESTful memory APIs

#### 📊 **Agentic-Graph-RAG** (Port 8003)
**Knowledge-Graph Retrieval-Augmented Generation service**

**Structure:**
```
Agentic-Graph-RAG/
├── src/
│   ├── agents/              # Unified & specialised agents (intent, expansion)
│   ├── pdf_processor/       # LlamaIndex & legacy PDF processing pipeline
│   ├── graph_db/            # Knowledge graph & vector-store adapters
│   ├── query_engine/        # Hybrid search & query processing
│   ├── api/                 # FastAPI application
│   └── cli/                 # CLI utilities (ingest, query, visualize, export)
├── config.yaml              # Service configuration
├── requirements.txt         # Python dependencies
└── run.py                   # Service entry point
```

**Key Features:**
- LlamaIndex-powered PDF ingestion with enhanced metadata extraction
- **Unified Query Intelligence Agent** for single-call intent & expansion analysis
- Smart document caching preventing redundant processing (60-80% reduction)
- Hybrid semantic / keyword / graph search with intelligent fusion
- ChromaDB vector storage with Ollama embeddings
- Neo4j knowledge graph construction & visualisation utilities
- REST & CLI interfaces with robust health monitoring

### Infrastructure Components

#### 🐳 **Docker Services** (docker-compose.agentic-services.yml)
**Containerized external services with persistent storage**

**Services:**
- **Neo4j** (Ports 7474, 7687) - Graph database
- **Ollama** (Port 11434) - Local LLM inference
- **MongoDB** (Port 27017) - Document database
- **PostgreSQL** (Port 5432) - Relational database
- **PgAdmin** (Port 5050) - Database administration

#### ⚙️ **docker-config/**
**Docker service configuration files**

```
docker-config/
├── postgres-config/
│   ├── postgresql.conf   # PostgreSQL server configuration
│   └── pg_hba.conf      # PostgreSQL authentication rules
└── mongodb-init/
    └── init-mongo.js     # MongoDB initialization script
```

---

## 🚀 Quick Start Installation

### One-Command Setup (Recommended)

```bash
# Complete environment setup (Docker + Applications + AI Models)
python run_all_services.py setup --auto-install

# Setup everything and start immediately
python run_all_services.py run --auto-install

# Development mode with hot reloading
python run_all_services.py run --dev --auto-install

# Clean setup (removes previous installations)
python run_all_services.py setup --clean --auto-install

# Skip Docker infrastructure (app services only)
python run_all_services.py setup --skip-docker --auto-install
```

**What the enhanced setup system does:**
1. ✅ **Phase 1: Docker Infrastructure** - Starts PostgreSQL, MongoDB, Neo4j, Ollama, PgAdmin
2. ✅ **Phase 2: AI Model Installation** - Downloads and installs LLM models (qwen3:4b, llama3.1:latest, etc.)
3. ✅ **Phase 3: Application Setup** - Configures all microservices with UV package manager
4. ✅ **Dependency Validation** - Ensures proper startup order and service requirements
5. ✅ **Environment Configuration** - Creates credentials, .env files, and service discovery
6. ✅ **Health Monitoring** - Validates all components are working correctly

### Individual Service Setup

Each service can be set up and run independently using UV package manager:

```bash
# Backend Service
cd Agentic-Backend
python setup.py          # Setup with UV
python run.py --dev       # Run in development mode

# Memory Service  
cd Agentic-Memory
python setup.py --clean   # Clean setup
python run.py --reload    # Run with auto-reload

# Graph RAG Service
cd Agentic-Graph-RAG  
python setup.py           # Setup with UV
python run.py --dev       # Run in development mode

# Frontend Service
cd Agentic-frontend
python setup.py           # Setup Node.js dependencies  
python run.py --open      # Run and open browser
```

**Complete infrastructure setup includes:**
1. ✅ UV package manager for 10-100x faster Python installs
2. ✅ Docker infrastructure services (databases, LLM server)
3. ✅ AI model installation and validation
4. ✅ Individual service isolation with virtual environments
5. ✅ Robust health checks and monitoring
6. ✅ Cross-platform compatibility (Windows/Linux/macOS)
7. ✅ Service dependency management and startup ordering
8. ✅ Graceful shutdown handling
9. ✅ Environment configuration and credentials management
10. ✅ GPU optimization for AI/ML services

**Estimated time:** 15-30 minutes for complete setup (including Docker and AI models)

---

## 📚 Detailed Setup Guide

### Prerequisites

#### Required Software
```powershell
# Check prerequisites
python --version     # Should be 3.8+
docker --version     # Docker Engine 20.10+
node --version       # Node.js 16+
npm --version        # npm 7+
git --version        # Git (recommended)
```

#### System Requirements
- **OS:** Windows 10/11, macOS, or Linux
- **RAM:** 8GB minimum, 16GB recommended
- **Storage:** 20GB free space
- **GPU:** NVIDIA GPU recommended for Ollama (CPU fallback available)

### Manual Installation Steps

#### Step 1: Environment Setup
```powershell
# Clone repository
git clone <repository-url>
cd Agentic

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate.ps1
# Linux/macOS:
source venv/bin/activate
```

#### Step 2: Install Dependencies
```powershell
# Install backend dependencies
pip install -r Agentic-Backend\requirements.txt

# Install memory service dependencies
pip install -r Agentic-Memory\requirements.txt

# Install graph-RAG dependencies
pip install -r Agentic-Graph-RAG\requirements.txt

# Install frontend dependencies
cd Agentic-frontend
npm install
cd ..
```

#### Step 3: Start Infrastructure Services
```powershell
# Start Docker services
docker compose -f docker-compose.agentic-services.yml --env-file agentic-services.env up -d

# Verify services are running
docker ps
```

#### Step 4: Initialize Databases
```powershell
# Initialize PostgreSQL and MongoDB
cd Agentic-Backend
python scripts\cogni_vox_manager.py --force-reset
```

#### Step 5: Install AI Models
```powershell
# Install default model
docker exec agentic-ollama ollama pull llama3.1

# Verify installation
docker exec agentic-ollama ollama list
```

---

## 🔧 Module Documentation

### setup_agentic_platform.py - Complete Setup Automation

**Advanced setup script with comprehensive error handling and validation**

#### Key Classes and Functions:

```python
class AgenticPlatformSetup:
    """Main orchestrator for platform setup"""
    
    def check_dependencies(self) -> bool:
        """Verify Python, Docker, and other prerequisites"""
        
    def setup_virtual_environment(self) -> bool:
        """Create venv and install all service dependencies"""
        
    def start_docker_services(self) -> bool:
        """Launch all Docker containers with health checks"""
        
    def install_ollama_models(self) -> bool:
        """Download and install AI models"""
        
    def initialize_databases(self) -> bool:
        """Create database schema and default data"""
        
    def validate_installation(self) -> bool:
        """Comprehensive system validation"""
```

#### Usage Options:
```powershell
# Complete setup
python setup_agentic_platform.py

# Skip components
python setup_agentic_platform.py --skip-dependency-check
python setup_agentic_platform.py --skip-docker-services
python setup_agentic_platform.py --skip-ollama-models
python setup_agentic_platform.py --skip-database-init

# Custom model installation
python setup_agentic_platform.py --default-model "llama3.2"
python setup_agentic_platform.py --additional-models "mistral" "phi3"

# Development mode
python setup_agentic_platform.py --verbose --force
```

### run_services.ps1 - Service Management Script

**PowerShell script for managing all microservices with advanced features**

#### Key Features:
- **Automatic port management** with conflict resolution
- **Health check monitoring** for all services
- **Virtual environment integration**
- **Dependency validation** and installation
- **Cross-platform compatibility**
- **Graceful shutdown handling**

#### Usage Examples:
```powershell
# Start all services
.\run_services.ps1

# Development mode with hot reload
.\run_services.ps1 -Reload

# Custom ports
.\run_services.ps1 -BackendPort 8001 -FrontendPort 3001

# Skip specific services
.\run_services.ps1 -Skip "memory,graph-rag"

# Automatic port resolution
.\run_services.ps1 -AutoPort

# Verbose output for debugging
.\run_services.ps1 -Verbose
```

#### Service Configuration:
```powershell
$serviceConfig = @(
    @{
        Name = "Agentic-Frontend"
        Directory = "Agentic-frontend"
        Port = $FrontendPort
        ServiceType = "Node"
    },
    @{
        Name = "Agentic-Backend" 
        Directory = "Agentic-Backend"
        Port = $BackendPort
        ServiceType = "Python"
    }
    # ... additional services
)
```

### Agentic-Backend - Core Service Architecture

#### Database Models (app/models/)

**User Management:**
```python
# app/models/user.py
class User(Base):
    id: int
    email: str
    username: str
    hashed_password: str
    role: UserRole  # ADMIN, USER
    is_active: bool
    created_at: datetime
    
class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
```

**AI Model Management:**
```python
# app/models/models.py
class Model(Base):
    id: int
    name: str
    category: Category  # LIGHT, MEDIUM, HEAVY
    default_requests: int
    is_visible: bool
    
class Category(Enum):
    LIGHT = "light"
    MEDIUM = "medium" 
    HEAVY = "heavy"
```

**Subscription System:**
```python
# app/models/subscription.py
class SubscriptionPlan(Base):
    id: int
    name: str
    default_requests: int
    
# Default plans: Free (100), Plus (1000), Pro (unlimited)
```

#### API Structure (app/api/)

**Authentication Endpoints:**
```python
# app/api/auth.py
POST /api/auth/login      # User login
POST /api/auth/register   # User registration
POST /api/auth/refresh    # Token refresh
GET  /api/auth/me         # Current user info
```

**Chat & AI Endpoints:**
```python
# app/api/chat.py  
POST /api/chat/send       # Send message to AI
GET  /api/chat/history    # Get conversation history
POST /api/chat/clear      # Clear chat history
```

#### Core Configuration (app/core/)

**Database Configuration:**
```python
# app/core/database.py
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

**Security Implementation:**
```python
# app/core/security.py
def get_password_hash(password: str) -> str
def verify_password(plain_password: str, hashed_password: str) -> bool
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None)
```

### cogni_vox_manager.py - Database Management Tool

**Comprehensive database management with interactive and CLI modes**

#### Key Operations:
```python
class CogniVoxDatabaseManager:
    def complete_reset(self) -> bool:
        """Full database reset with confirmation"""
        
    def test_database_status(self) -> bool:
        """Comprehensive database health check"""
        
    def create_admin_user(self, email=None, username=None, password=None):
        """Create administrative user account"""
        
    def init_subscription_plans(self):
        """Initialize Free, Plus, Pro plans"""
        
    def init_models(self):
        """Setup default AI models"""
```

#### CLI Usage:
```powershell
# Interactive mode with menu
python scripts\cogni_vox_manager.py

# Command line operations
python scripts\cogni_vox_manager.py --test           # Test connections
python scripts\cogni_vox_manager.py --reset          # Interactive reset
python scripts\cogni_vox_manager.py --force-reset    # Non-interactive reset
python scripts\cogni_vox_manager.py --admin          # Create admin only
python scripts\cogni_vox_manager.py --models         # Initialize models
python scripts\cogni_vox_manager.py --plans          # Initialize plans
```

### Agentic-Memory - Memory Management Service

#### Memory Architecture:
```python
# src/core/memory_manager.py
class MemoryManager:
    def store_conversation(self, user_id: str, conversation: dict)
    def retrieve_context(self, user_id: str, query: str) -> dict
    def update_user_context(self, user_id: str, context: dict)
    def get_conversation_history(self, user_id: str) -> List[dict]
```

#### GPU Optimization:
```python
# src/gpu_manager/utils.py
def optimize_memory_usage()
def batch_process_embeddings(texts: List[str])
def manage_gpu_resources()
```

### Agentic-Graph-RAG - Knowledge Graph Service

#### Graph Operations:
```python
# src/graph/neo4j_manager.py
class Neo4jManager:
    def create_knowledge_node(self, entity: str, properties: dict)
    def create_relationship(self, source: str, target: str, relationship: str)
    def query_graph(self, cypher_query: str) -> List[dict]
    def find_related_entities(self, entity: str, depth: int = 2)
```

#### RAG Implementation:
```python
# src/rag/retrieval_engine.py
class RetrievalEngine:
    def chunk_document(self, document: str) -> List[str]
    def create_embeddings(self, chunks: List[str]) -> np.ndarray
    def similarity_search(self, query: str, top_k: int = 5) -> List[dict]
    def generate_response(self, context: str, query: str) -> str
```

---

## ⚙️ Configuration Management

### Environment Variables (agentic-services.env)

```env
# Database Configuration
POSTGRES_USER=cognivox
POSTGRES_PASSWORD=cognivox
POSTGRES_DB=cognivox
POSTGRES_PORT=5432

MONGO_ROOT_USERNAME=cognivox
MONGO_ROOT_PASSWORD=cognivox
MONGO_APP_DATABASE=cognivox
MONGO_PORT=27017

# Service Ports
PGADMIN_PORT=5050
NEO4J_HTTP_PORT=7474
NEO4J_BOLT_PORT=7687
OLLAMA_PORT=11434

# GPU Configuration
GPU_DEVICES=all
```

### Backend Configuration (Agentic-Backend/config.yaml)

```yaml
# Application Settings
app:
  name: "CogniVox"
  environment: "development"
  debug: true
  secret_key: "your-secret-key"

# Database URLs
database:
  url: "postgresql://cognivox:cognivox@localhost:5432/cognivox"

mongodb:
  url: "mongodb://cognivox:cognivox@localhost:27017/cognivox?authSource=cognivox"
  db_name: "cognivox"

# JWT Configuration
jwt:
  secret_key: "your-jwt-secret"
  algorithm: "HS256"
  token_expiry_minutes: 60

# AI Model Settings
model:
  default_name: "llama3.1"
  default_requests: 100

# External Services
additional:
  ollama_url: "http://localhost:11434"
  max_sub_threads: 10
```

### Docker Service Configuration

#### PostgreSQL Configuration (docker-config/postgres-config/)

```ini
# postgresql.conf
listen_addresses = '*'
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
```

```ini
# pg_hba.conf
local   all             all                                     trust
host    all             all             0.0.0.0/0               md5
```

#### MongoDB Initialization (docker-config/mongodb-init/)

```javascript
// init-mongo.js
db = db.getSiblingDB('cognivox');
db.createUser({
  user: 'cognivox',
  pwd: 'cognivox',
  roles: [{ role: 'readWrite', db: 'cognivox' }]
});
```

---

## 🔄 Development Workflow

### Daily Development Routine

```bash
# 1. Complete environment setup (first time only)
python run_all_services.py setup --auto-install

# 2. Start all services in development mode
python run_all_services.py start --dev

# OR: Setup and start in one command
python run_all_services.py run --dev

# 3. Check service status and URLs
python run_all_services.py status
python run_all_services.py urls

# 4. Access development URLs:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
# Memory Service: http://localhost:8002/docs  
# Graph-RAG Service: http://localhost:8003/docs
# Neo4j Browser: http://localhost:7474
# PgAdmin: http://localhost:5050

# 5. Stop all services when done
# Press Ctrl+C or run:
python run_all_services.py stop
```

### Individual Service Development

```bash
# Setup and run individual services
# Each service uses its own UV-managed virtual environment

# Backend development
cd Agentic-Backend
python setup.py           # First time setup
python run.py --dev       # Run with auto-reload

# Frontend development  
cd Agentic-frontend
python setup.py           # Setup Node.js dependencies
python run.py --open      # Run and open browser

# Memory service development
cd Agentic-Memory
python setup.py           # Setup with UV
python run.py --dev       # Run in development mode

# Graph-RAG service development
cd Agentic-Graph-RAG
python setup.py           # Setup with UV
python run.py --dev       # Run with development features
```

### Database Development

```powershell
# Test database connections
cd Agentic-Backend
python scripts\cogni_vox_manager.py --test

# Reset development database
python scripts\cogni_vox_manager.py --force-reset

# Create test data
python scripts\cogni_vox_manager.py --admin --models --plans
```

---

## 🔧 Service Management

### Master Orchestrator Commands

The enhanced service orchestrator (`run_all_services.py`) provides comprehensive infrastructure and service management:

```bash
# Complete environment setup (Docker + Applications + AI Models)
python run_all_services.py setup --auto-install              # Full setup
python run_all_services.py setup --clean --auto-install      # Clean setup
python run_all_services.py setup --skip-docker               # Skip Docker infrastructure
python run_all_services.py setup --skip-ollama               # Skip AI model installation
python run_all_services.py setup --services backend memory   # Setup specific services

# Docker infrastructure management
python run_all_services.py docker start                      # Start all Docker services
python run_all_services.py docker stop                       # Stop all Docker services
python run_all_services.py ollama --install                  # Install AI models

# Start application services
python run_all_services.py start                             # Start all services
python run_all_services.py start --dev                       # Development mode
python run_all_services.py start --services frontend backend # Start specific services

# Stop services
python run_all_services.py stop                              # Stop all services
python run_all_services.py stop --services memory graphrag   # Stop specific services

# Status and monitoring
python run_all_services.py status                            # Health check all services
python run_all_services.py credentials                       # Show all credentials & URLs
python run_all_services.py urls                             # Show service URLs only

# Configuration management
python run_all_services.py config create                     # Create config files
python run_all_services.py config validate                   # Validate configurations

# Complete workflow (setup + start)
python run_all_services.py run --auto-install               # Production mode
python run_all_services.py run --dev --auto-install         # Development mode
python run_all_services.py run --clean --auto-install       # Clean setup first
```

### Individual Service Management

Each service has its own robust runner with health checks:

```bash
# Backend Service
cd Agentic-Backend
python run.py --host 0.0.0.0 --port 8000 --reload --dev

# Memory Service
cd Agentic-Memory  
python run.py --host 0.0.0.0 --port 8002 --dev --skip-checks

# Graph RAG Service
cd Agentic-Graph-RAG
python run.py --host 0.0.0.0 --port 8003 --workers 2 --dev

# Frontend Service
cd Agentic-frontend
python run.py --host localhost --port 3000 --open
```

### Health Monitoring

```bash
# Orchestrator health check
python run_all_services.py status

# Individual service health checks  
curl http://localhost:8000/health     # Backend
curl http://localhost:8002/health     # Memory
curl http://localhost:8003/health     # Graph-RAG
curl http://localhost:3000/           # Frontend

# Check infrastructure services
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Service URLs & Access Points

| Service | Development URL | Production Notes |
|---------|----------------|------------------|
| **Frontend** | http://localhost:3000 | React development server |
| **Backend** | http://localhost:8000 | FastAPI with auto-reload |
| **Backend Docs** | http://localhost:8000/docs | Swagger UI |
| **Memory Service** | http://localhost:8002 | Memory management API |
| **Graph-RAG** | http://localhost:8003 | Knowledge retrieval API |
| **Neo4j Browser** | http://localhost:7474 | Graph database UI (neo4j/password) |
| **PgAdmin** | http://localhost:5050 | PostgreSQL admin (admin@admin.com/admin) |
| **Ollama API** | http://localhost:11434 | LLM inference API |
| **MongoDB** | mongodb://localhost:27017 | Document database (cognivox/cognivox) |
| **PostgreSQL** | postgresql://localhost:5432 | Relational database (cognivox/cognivox) |

**💡 Get all URLs and credentials:**
```bash
python run_all_services.py urls         # Clean URL list
python run_all_services.py credentials  # Complete credentials table
```

### Logging and Monitoring

```powershell
# View Docker service logs
docker compose -f docker-compose.agentic-services.yml logs -f

# View specific service logs
docker logs agentic-postgres -f
docker logs agentic-ollama -f
docker logs agentic-neo4j -f

# Monitor service resources
docker stats
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Setup Script Failures

```bash
# Run orchestrator with verbose output for debugging
python run_all_services.py setup --verbose --auto-install

# Setup individual components for troubleshooting
python run_all_services.py docker start                    # Docker services only
python run_all_services.py ollama --install                # AI models only
python run_all_services.py setup --skip-docker --services backend  # App services only

# Check setup status and dependencies
python run_all_services.py status                         # Check all services
python run_all_services.py check --auto-install           # Check prerequisites

# Skip components if they fail
python run_all_services.py setup --skip-docker           # Skip Docker infrastructure
python run_all_services.py setup --skip-ollama           # Skip AI model installation

# Clean setup for troubleshooting
python run_all_services.py setup --clean --verbose --auto-install

# Individual service debugging
cd Agentic-Backend
python run.py --skip-checks                              # Skip dependency checks
```

#### UV Package Manager Issues

```bash
# Install UV if not available
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# Or on Windows: 
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Force UV installation in setup scripts
python setup.py --force-uv-install

# Check UV installation
uv --version
```

#### Port Conflicts

```powershell
# Find processes using ports
netstat -ano | findstr :5432
netstat -ano | findstr :8000

# Use automatic port assignment
.\run_services.ps1 -AutoPort

# Kill conflicting processes (Windows)
taskkill /PID <process_id> /F
```

#### Database Connection Issues

```powershell
# Test database connections
cd Agentic-Backend
python scripts\cogni_vox_manager.py --test

# Reset databases
python scripts\cogni_vox_manager.py --force-reset

# Check Docker services
docker ps
docker logs agentic-postgres
docker logs agentic-mongodb
```

#### Docker & Infrastructure Problems

```bash
# Use orchestrator for Docker management (recommended)
python run_all_services.py docker stop
python run_all_services.py docker start

# Check Docker service status
python run_all_services.py status
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Docker service troubleshooting
docker compose -f docker-compose.agentic-services.yml logs -f    # View logs
docker compose -f docker-compose.agentic-services.yml restart    # Restart services
docker compose -f docker-compose.agentic-services.yml down --volumes  # Clean restart

# AI Model Issues
python run_all_services.py ollama --install                     # Reinstall models
docker exec agentic-ollama ollama list                          # Check installed models
docker logs agentic-ollama -f                                   # Check Ollama logs

# Database Connection Issues
python run_all_services.py credentials                          # Check credentials
docker exec agentic-postgres pg_isready -U cognivox             # Test PostgreSQL
docker exec agentic-mongodb mongosh --eval "db.adminCommand('ping')"  # Test MongoDB
```

#### Python Dependency Conflicts

```powershell
# Check for conflicts
pip check

# Fix MongoDB driver issues
pip uninstall -y pymongo motor
pip install pymongo==4.5.0 motor==3.1.1

# Recreate virtual environment
rmdir /s venv
python setup_agentic_platform.py
```

### Performance Optimization

#### Memory Usage
```powershell
# Monitor memory usage
docker stats --no-stream

# Optimize Neo4j memory
# Edit docker-compose.agentic-services.yml:
# NEO4J_dbms_memory_heap_max__size=4G
# NEO4J_dbms_memory_pagecache_size=2G
```

#### AI Model Performance
```powershell
# Check GPU availability
docker exec agentic-ollama nvidia-smi

# Monitor model performance
docker exec agentic-ollama ollama ps

# Optimize model settings
docker exec agentic-ollama ollama show llama3.1
```

---

## 🚀 Production Deployment

### Security Hardening

```yaml
# Update agentic-services.env for production
POSTGRES_PASSWORD=<strong-password>
MONGO_ROOT_PASSWORD=<strong-password>
JWT_SECRET_KEY=<secure-random-key>

# Update config.yaml
app:
  environment: "production"
  debug: false
  secret_key: "<production-secret>"
```

### Environment Configuration

```powershell
# Set production environment variables
$env:ENVIRONMENT="production"
$env:DEBUG="false"
$env:JWT_SECRET_KEY="<secure-key>"

# Use production database URLs
$env:DATABASE_URL="postgresql://user:pass@prod-db:5432/cognivox"
$env:MONGODB_URL="mongodb://user:pass@prod-mongo:27017/cognivox"
```

### Deployment Checklist

- [ ] Update all default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up proper firewall rules
- [ ] Configure backup strategies
- [ ] Set up monitoring and logging
- [ ] Test all service endpoints
- [ ] Verify database connections
- [ ] Check AI model availability
- [ ] Configure reverse proxy (nginx)
- [ ] Set up CI/CD pipelines

### Docker Production Configuration

```yaml
# docker-compose.prod.yml
services:
  backend:
    build: ./Agentic-Backend
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    restart: unless-stopped
    
  frontend:
    build: ./Agentic-frontend
    environment:
      - NODE_ENV=production
    restart: unless-stopped
```

---

## 📚 Additional Resources

### Documentation Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Docker Documentation](https://docs.docker.com/)

### API Documentation
- **Backend API:** http://localhost:8000/docs
- **Memory Service:** http://localhost:8002/docs  
- **Graph-RAG Service:** http://localhost:8003/docs

### Support and Troubleshooting
- Check service logs for detailed error messages
- Use verbose flags for debugging setup issues
- Verify all prerequisites before installation
- Monitor system resources during operation

---

**🎯 Pro Tips:**
- The setup script is idempotent - safe to run multiple times
- Use skip flags to avoid redoing completed steps
- Always verify Docker services are running before starting microservices
- Keep default credentials for development, update for production
- Monitor memory usage when running all services locally 
