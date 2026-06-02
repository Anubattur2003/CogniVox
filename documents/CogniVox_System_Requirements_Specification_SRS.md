# Software Requirements Specification (SRS) for CogniVox 2.0

## Document Control & Metadata
*   **Project Name**: CogniVox (Agentic Conversational AI Platform)
*   **Version**: 2.0 (Asynchronous & Streaming Upgrade)
*   **Status**: Final Technical Specification
*   **Author**: Antigravity AI Architect Pair
*   **Date**: June 2026

---

## Table of Contents
1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Interface Requirements](#3-system-interface-requirements)
4. [Specific Functional Requirements](#4-specific-functional-requirements)
5. [Non-Functional Requirements (NFRs)](#5-non-functional-requirements)
6. [Design & Implementation Constraints](#6-design--implementation-constraints)
7. [System Evolution & Future Requirements](#7-system-evolution--future-requirements)

---

## 1. Introduction

### 1.1 Purpose & Scope
This Software Requirements Specification (SRS) document details the complete functional, non-functional, interface, and performance specifications for the **CogniVox 2.0 Conversational AI Ecosystem**. 

CogniVox is an enterprise-grade, self-hosted AI platform designed to securely process corporate documents, execute complex multi-agent reasoning tasks, integrate with enterprise data sources using the **Model Context Protocol (MCP)**, and stream token-by-token responses to a dynamic 3D React user interface without blocking system resources. 

The scope of the 2.0 version strictly defines the **Decoupled Asynchronous Processing Engine** powered by a Django API Gateway, a Redis message broker, Celery task runners, FastAPI cognitive microservices, and local GPU acceleration (via Ollama).

### 1.2 Intended Audience
This document is prepared for:
*   **System Architects**: To verify components, service boundaries, and asynchronous data topologies.
*   **Software Engineers**: To serve as the master implementation reference for API endpoints, database schemas, and state transitions.
*   **DevOps / System Administrators**: To manage infrastructure orchestration, Docker services, GPU resources, and deployment constraints.
*   **QA / Security Auditors**: To evaluate compliance with JWT authentication, role-based controls, input sanitization, and data isolation requirements.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term / Acronym | Definition |
| :--- | :--- |
| **SRS / SysRS** | Software / System Requirements Specification. |
| **SSE** | Server-Sent Events. A standard web technology allowing a server to push real-time HTTP events to a browser over a single connection. |
| **RAG** | Retrieval-Augmented Generation. Optimizing LLM outputs by querying custom vector-graphs. |
| **MCP** | Model Context Protocol. A standardized interface allowing agents to discover and interact with external data sources, services, and local scripts safely. |
| **JWT** | JSON Web Token. A secure, cryptographically signed token used to transmit user identity claims. |
| **DRF** | Django REST Framework. The gateway toolkit used for authentication, threads database management, and SSE routing. |
| **Ollama** | Local LLM server orchestrating open weights models (Mistral, Llama, Qwen, Nomic). |

---

## 2. Overall Description

### 2.1 Product Perspective
CogniVox operates as a decoupled, local-first microservices system. It sits securely behind the enterprise firewall, ensuring zero data leakage to public third-party APIs. It interfaces directly with local GPU runtimes and accesses corporate databases through sandboxed MCP servers.

```
       ┌────────────────────────┐
       │   React 18 Frontend    │
       └───────────┬────────────┘
                   │ HTTPS API / EventSource
                   ▼
       ┌────────────────────────┐
       │   Django API Gateway   │
       └───────────┬────────────┘
                   │ Celery Task Queue / Redis PubSub
                   ▼
       ┌────────────────────────┐
       │ FastAPI Memory Service │
       └───────────┬────────────┘
                   │ Local API Integration
                   ▼
      ┌────────────┴────────────┐
      │ FastAPI GraphRAG / LLM  │
      └─────────────────────────┘
```

### 2.2 Product Functions
The high-level capability objectives of the CogniVox platform include:
1.  **Asynchronous Chat Pipeline**: Decoupling incoming prompt requests from resource-heavy reasoning chains.
2.  **Real-Time Token Streaming**: Delivering live text outputs and step-by-step thinking graphs to the screen.
3.  **Entity-Graph Ingestion (GraphRAG)**: Parsing multi-page PDF documents, hashing contents, generating embeddings, and storing vector maps alongside entity-relation graphs.
4.  **Extensible Tool Integrations (MCP 2.0)**: Discovering, configuring, and invoking stdio/sse/http tools to allow agents to interact with external systems.
5.  **Administrative System Operations**: Resetting user quotas, assigning LLM access profiles, and inspecting MCP runtime logs.

### 2.3 User Classes & Characteristics
*   **Standard User**:
    *   *Permission Set*: Access to custom spaces, conversation threads, chat streaming, and document libraries.
    *   *Quota Constraint*: Strictly limited to the monthly request count defined by their subscription plan (Free/Plus/Pro).
*   **System Administrator (Pro/Admin)**:
    *   *Permission Set*: Full system privileges. Includes registering global MCP servers, modifying system-wide execution parameters, assigning access limits to users, and reading execution logs.
    *   *Quota Constraint*: Unlimited request quota.

### 2.4 Operating Environment
*   **Supported Client Platforms**: Modern web browsers (Chrome, Edge, Safari, Firefox) supporting HTML5, WebGL (for 3D globe visualizations), and EventSource (SSE).
*   **Supported Host Platforms**: Windows 11 (x64), Linux (Ubuntu 22.04+), macOS (Apple Silicon).
*   **Local Infrastructure Requirements**:
    *   Docker & Docker Compose.
    *   Redis Server (Port `6379`).
    *   MongoDB Server (Port `27017`).
    *   Neo4j Database (Bolt Port `7687`, HTTP Port `7474`).
    *   PostgreSQL / SQLite Database (Port `5432` / local db file).
    *   Ollama Server (Port `11434`).

---

## 3. System Interface Requirements

### 3.1 User Interfaces
The user interface must be clean, modern, dark-mode prioritized, and responsive.

*   **Chat Console UI**:
    *   Must display the conversation as a chronologically sorted sequence of messages.
    *   Agent messages must animate dynamically token-by-token.
    *   Must display expandable **"Thinking" blocks** highlighting the agent's multi-step ReAct sequence.
    *   Must list clickable source citation bubbles linking back to the exact PDF page of origin.
*   **3D Globe Visualizer**:
    *   Must render a WebGL-based Earth globe utilizing custom day/night shaders.
    *   Must plot geolocated servers, database clusters, and active query connections as glowing neon pathways.
*   **MCP Administration Panel**:
    *   Must display tabular lists of registered MCP servers, active tools, and real-time connection status flags.
    *   Must feature a toggled control to require explicit administrator approval for specific high-risk tools.

### 3.2 Hardware & GPU Interfaces
*   **GPU Resource Allocator**:
    *   Must implement a thread-safe singleton GPU Manager.
    *   Must automatically detect local CUDA devices (NVIDIA).
    *   Must fall back to CPU threads dynamically if CUDA is unavailable, modifying the Ollama inference context.
*   **VRAM Limit Enforcement**:
    *   Inference VRAM consumption must be capped. Large models must undergo mixed-precision quantization (e.g., Q4_0) when VRAM is lower than 8GB to prevent host system freezes.

### 3.3 Communications & API Interfaces
The system must expose REST APIs alongside a persistent Server-Sent Events (SSE) server.

*   **REST API Gateway**: Django REST Framework serving JSON objects. Must include strict JWT validations.
*   **Dual-Mode Authentication Handshake**:
    *   For standard APIs: Read JWT from `Authorization: Bearer <token>` header.
    *   For `EventSource` (SSE) APIs: Read JWT from the fallback query parameter `?token=<JWT_string>`.
*   **Redis PubSub Engine**: Real-time message exchange between background workers and the gateway. Must use unique channel names matching the Celery task ID (`stream_<task_id>`).

---

## 4. Specific Functional Requirements

### 4.1 Chat Thread & Asynchronous Submission (`submit_message`)
*   **REQ-FN-1.1**: The system must accept user prompts and create a new `ChatSubThread` record in the relational database with a `pending` status.
*   **REQ-FN-1.2**: The system must serialize user identifiers (`id`, `role`, `subscription_plan`) and cast UUID primary keys to clean strings.
*   **REQ-FN-1.3**: The system must dispatch the reasoning task asynchronously to Celery and return a `202 Accepted` status to the client in under 200ms.

### 4.2 Decoupled SSE Streaming Generator (`stream_message`)
*   **REQ-FN-2.1**: The system must establish a secure SSE connection (`text/event-stream`) between the client browser and the Django gateway using the Celery `task_id`.
*   **REQ-FN-2.2**: The gateway stream reader must subscribe to the unique Redis channel matching the `task_id` (`stream_<task_id>`).
*   **REQ-FN-2.3**: As the background worker pushes tokens into Redis, the gateway must instantly forward them as SSE events.
*   **REQ-FN-2.4**: Upon receiving the system's `[DONE]` marker, the gateway must gracefully output a `close` event and sever the EventSource stream.

### 4.3 Multi-Agent Supervisor & Memory (FastAPI Memory Service)
*   **REQ-FN-3.1**: The agent must execute a multi-step **ReAct (Reasoning and Acting)** loop, deciding which tools to call.
*   **REQ-FN-3.2**: The agent must retrieve short-term memory (recent messages) and long-term memory (historical MongoDB threads) to construct context.
*   **REQ-FN-3.3**: The service must support three distinct execution modes:
    *   `general`: Direct model responses skipping reasoning layers (optimized for standard queries).
    *   `thinking`: Enforces thinking and reasoning step exposures.
    *   `agentic`: Unlocks the full multi-agent ReAct loop with external tool authorization triggers.

### 4.4 GraphRAG Ingestion & Hybrid Search (FastAPI GraphRAG)
*   **REQ-FN-4.1**: The system must parse PDFs using an incremental splitter.
*   **REQ-FN-4.2**: The system must generate file hashes before parsing. If a hash collision occurs (identical file already ingested), the process must resolve from the cache, preventing redundant CPU processing.
*   **REQ-FN-4.3**: The system must generate semantic embeddings (`nomic-embed-text`) and store them in ChromaDB.
*   **REQ-FN-4.4**: The system must extract entities and relationships and save them in Neo4j using APOC plugin Cypher queries.
*   **REQ-FN-4.5**: The search engine must support Hybrid Search, fusing semantic cosine similarity vectors with traditional keyword indexing and Neo4j graph walks.

---

## 5. Non-Functional Requirements (NFRs)

### 5.1 Performance & Latency Requirements
*   **Submission Speed**: The API gateway must return the asynchronous `202 Accepted` status payload in **under 200ms** from request arrival.
*   **Time-to-First-Token (TTFT)**: Live token-by-token streaming must start rendering on the client screen in **under 1500ms** for general queries, and **under 3000ms** for agentic/thinking queries on standard GPU systems.
*   **Graph Retrieval Latency**: Vector similarity calculations combined with Neo4j entity walks must execute in **under 800ms** for search queries.
*   **UV Installation Speed**: Package setup scripts using `uv` must install the entire multi-service Python environment in **under 10 minutes** (a 10-100x speedup compared to standard `pip`).

### 5.2 Scalability & Decoupling
*   **Non-blocking Execution**: Long-running GPU tasks must not block Django's HTTP pool. decopling must ensure the gateway handles hundreds of concurrent users streaming responses.
*   **Parallel Celery Workers**: The system must support scaling background tasks by spinning up multiple parallel Celery worker threads communicating with the central Redis broker.

### 5.3 Security, Authorization & Privacy
*   **Relational Isolation**: Users must be isolated; database schemas must prevent standard users from reading, modifying, or deleting spaces or threads belonging to other users.
*   **Dual Authorization Protocols**: JWT signatures must use modern algorithms (e.g., HS256) and expire after a configurable duration (default: 30 minutes).
*   **Input Sanitization (XSS Defense)**: User prompts and system outputs must undergo strict HTML sanitization (utilizing Bleach) before they are stored in PostgreSQL/MongoDB or rendered in the frontend.
*   **Zero External Footprint**: The entire system must be self-hosted, ensuring no prompt history, vector index, or document is ever transmitted across external cloud services.

### 5.4 Reliability & Availability
*   **Broker Connection Retries**: Celery and Django must implement backoff strategies to reconnect to the Redis server automatically if the container encounters an unexpected shutdown.
*   **Data Integrity**: Relational operations (such as thread deletion or sub-thread creation) must run inside **Django database transactions** to prevent half-written orphans.

### 5.5 Portability & System Compatibility
*   **Cross-OS Installation**: Core installation and setup scripts must run natively across Windows, Linux, and macOS environments without requiring manual path corrections.

---

## 6. Design & Implementation Constraints

### 6.1 Architecture Constraints
*   **Vite Proxy Boundaries**: The frontend Vite server is the only layer exposed to standard client networks. All other backend services (FastAPI, Redis, PostgreSQL, Neo4j, Ollama) must run internally and communicate via secure proxy configurations.
*   **Python Package Locking**: To ensure build reproducibility, package setups must lock strict package versions using `uv.lock` or compiled `requirements.txt` assets.

### 6.2 Database Constraints
*   **PostgreSQL**: Strictly manages transactional, structured, and metadata relations (user auth records, space structures, thread titles).
*   **MongoDB**: Managed dynamically by the cognitive memory layer to capture arbitrary step histories, agent decisions, and raw dialogue arrays.
*   **ChromaDB**: Must be treated as transient/rebuildable. Re-indexing GraphRAG must reconstruct all vector vectors from stored database entities.

---

## 7. System Evolution & Future Requirements

Future versions of the CogniVox platform will expand the boundaries defined in this SRS to include:
*   **OAuth2 Identity Providers**: Standard SSO integration (Active Directory, Okta, Google Workspace).
*   **Local GPU Auto-scaling**: Dynamic service routing to scale local Ollama nodes based on API load.
*   **Native Mobile Clients**: Launching iOS and Android wrappers using secure websocket connections.
*   **Zero-Trust Multi-tenancy**: Complete separation of database engines per enterprise division or tenant.

---

## Conclusion & Approval

This System Requirements Specification defines a complete, performant, and secure structure for the CogniVox 2.0 platform. By separating heavy reasoning workloads from the web application gateway, the system achieves enterprise-grade responsiveness and security.
