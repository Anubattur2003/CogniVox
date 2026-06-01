# CogniVox Agentic System - Layered Architecture

## Overview
The CogniVox Agentic system follows a comprehensive layered architecture designed for intelligent document processing and query handling. Based on the execution logs analysis, this architecture supports both document ingestion/knowledge base creation and sophisticated query processing with parallel execution capabilities.

## Architecture Layers

### 1. User Interface Layer
**Technology**: React (TypeScript)
- **React Frontend**: Main user interface
- **File Upload Component**: Document ingestion interface
- **Query Interface**: User query input
- **Response Dashboard**: Results visualization and source document display

### 2. API Gateway Layer
**Technology**: FastAPI (Python)
- **Agentic Backend**: Main API gateway and orchestrator
- **Authentication Service**: User authentication and authorization
- **CORS Handler**: Cross-origin request management

### 3. Agentic Processing Layer
**Technology**: LangChain + Ollama + Custom Agents

#### Memory Service (Agentic-Memory)
- **Supervisor ReAct Agent**: Main orchestrating agent using ReAct methodology
- **Query Validation Agent**: Validates and preprocesses user queries
- **Context Awareness Agent**: Manages conversational context
- **Profile Extraction Agent**: Handles user profile data
- **Title Generation Agent**: Generates conversation titles

#### Intelligence Layer (Agentic-Graph-RAG)
- **Intent Classification Agent**: Classifies user query intentions
- **Query Expansion Agent**: Expands queries for better search results
- **Document Analysis Agent**: Analyzes documents during ingestion

### 4. Knowledge Processing Layer
**Technology**: LlamaIndex + Custom Search Engines

#### Graph-RAG Service
- **Document Processor**: Uses LlamaIndex for document processing
- **Embeddings Generator**: Creates vector representations
- **Vector Search Engine**: Semantic search capabilities
- **Graph Query Engine**: Knowledge graph querying
- **Hybrid Search Coordinator**: Orchestrates parallel search execution

#### Parallel Execution Engine
- **Semantic Search**: Vector-based similarity search
- **Keyword Search**: Traditional text-based search
- **User-Specific Search**: Personalized document retrieval
- **Global Search**: System-wide document search

### 5. Storage Layer
**Multi-Database Architecture**

#### Relational Database (PostgreSQL)
- **User Management**: User accounts and profiles
- **Authentication Data**: Login credentials and sessions
- **Document Metadata**: File information and associations

#### Document Storage (GCP Cloud Storage)
- **Document Repository**: Original PDF files
- **Secure Access**: Signed URL generation for document access

#### Vector Database (ChromaDB)
- **Document Embeddings**: Vector representations of document chunks
- **Vector Search Index**: Optimized for similarity search

#### Graph Database (Neo4j)
- **Knowledge Graph**: Entity relationships and knowledge structure
- **Entity Relationships**: Semantic connections between concepts

#### Cache Layer
- **MongoDB**: Chat history and session data (with SQLite fallback)
- **SQLite**: Local caching for offline capabilities

### 6. External Services
- **Ollama LLM Models**: Local language models for processing
- **LlamaIndex Processing**: Document parsing and chunking

## Execution Flows

### Document Ingestion Flow
1. **Frontend Upload** → User uploads document via React interface
2. **API Processing** → FastAPI backend receives and authenticates request
3. **Document Processing** → LlamaIndex extracts and processes text
4. **Embedding Generation** → Creates vector embeddings for chunks
5. **Multi-Storage** → Stores in:
   - GCP Storage (original document)
   - ChromaDB (embeddings)
   - Neo4j (knowledge graph)
   - PostgreSQL (metadata)

### Query Processing Flow
1. **Query Input** → User submits query via React interface
2. **API Routing** → FastAPI routes to Memory service
3. **Agent Orchestration** → Supervisor ReAct Agent coordinates:
   - Query validation through Query Validation Agent
   - Query expansion via Query Expansion Agent
   - Intent classification through Intent Classification Agent
4. **Parallel Search Execution**:
   - Semantic search in ChromaDB
   - Keyword search across databases
   - User-specific document filtering
   - Global knowledge retrieval
5. **Context Integration** → Combines search results with:
   - Chat history from MongoDB/SQLite
   - User profile from PostgreSQL
   - Previous conversation context
6. **Response Generation** → Uses Ollama LLM for final response
7. **Result Delivery** → Returns formatted response with source documents

## Key Technologies Summary

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React + TypeScript | User interface |
| Backend API | FastAPI + Python | API gateway |
| Agent Framework | LangChain + Custom Agents | Intelligent processing |
| Document Processing | LlamaIndex | Text extraction and chunking |
| LLM Engine | Ollama (Local) | Language model inference |
| Vector DB | ChromaDB | Semantic search |
| Graph DB | Neo4j | Knowledge relationships |
| Relational DB | PostgreSQL | User and metadata |
| Cache/Session | MongoDB + SQLite | Chat history and caching |
| File Storage | GCP Cloud Storage | Document repository |

## Parallel Execution Capabilities

The system implements sophisticated parallel execution at multiple levels:

1. **Hybrid Search Parallelization**: Simultaneous semantic and keyword searches
2. **Multi-Database Querying**: Parallel queries across ChromaDB, Neo4j, and PostgreSQL
3. **Agent Processing**: Concurrent agent execution for query expansion and intent classification
4. **Context Retrieval**: Parallel fetching of user context, chat history, and profile data

## High Availability Features

- **Database Redundancy**: MongoDB with SQLite fallback for chat history
- **Load Balancing**: Distributed search across multiple database systems
- **Caching Strategy**: Multi-level caching with SQLite and MongoDB
- **Service Isolation**: Microservices architecture with independent scaling

This layered architecture ensures robust, scalable, and intelligent document processing and query handling capabilities while maintaining high performance through parallel execution strategies. 