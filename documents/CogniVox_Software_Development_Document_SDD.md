# Software Development Document (SDD) for CogniVox 2.0

## Document Control & System Context
*   **Project**: CogniVox Conversational AI Platform
*   **Version**: 2.0 (Asynchronous & Streaming Infrastructure)
*   **Author**: Lead Systems Architect & Developer Pair
*   **Date**: June 2026
*   **Objective**: Define the software design, database schemas, coding standards, component logic, and developer conventions for the CogniVox codebase.

---

## Table of Contents
1. [Architectural Blueprint](#1-architectural-blueprint)
2. [Component & Subsystem Design](#2-component--subsystem-design)
3. [Database & Storage Schema Design](#3-database--storage-schema-design)
4. [Detailed Execution & Sequence Designs](#4-detailed-execution--sequence-designs)
5. [Coding Standards & Development Conventions](#5-coding-standards--development-conventions)
6. [Operational Setup & Developer Environments](#6-operational-setup--developer-environments)
7. [Testing & Quality Assurance Guidelines](#7-testing--quality-assurance-guidelines)

---

## 1. Architectural Blueprint

CogniVox employs a decoupled, service-oriented architecture (SOA) constructed using four primary subsystems, a distributed background worker pool, and a multi-protocol data tier. All system endpoints sit securely behind a unified frontend gateway proxy, ensuring a strict sandboxed environment.

```
+-------------------------------------------------------------------------+
|                         Client Web Browser                              |
|   (React 18 UI / 3D Globe Visualizer / SSE EventSource Listener)        |
+------------------------------------+------------------------------------+
                                     | Proxy via Vite Dev Server
                                     ▼
+------------------------------------+------------------------------------+
|                Django REST Gateway Service (Port 8000)                 |
|   (Route controller, JWT Security, Space/Thread DB, Celery Dispatch)   |
+-----------------+------------------+------------------+-----------------+
                  |                  |                  |
      Celery Task |                  | Redis PubSub     | SQL Operations
      Enqueuing   |                  | Streaming        | (ORM)
                  ▼                  ▼                  ▼
+-----------------+------------------+------------------+-----------------+
|                       Redis 7 Message Broker                            |
+-----------------+-------------------------------------------------------+
                  |
                  ▼ Dequeue Task
+-----------------+-------------------------------------------------------+
|                    Celery Background Worker Pool                         |
|   (Task execution, HTTP Client, Redis PubSub Publisher, DB updater)     |
+-----------------+-------------------------------------------------------+
                  |
                  ▼ HTTP Stream Request
+-----------------+-------------------------------------------------------+
|                  FastAPI Cognitive Memory Service (Port 8001)           |
|   (ReAct Agent, Short/Long Memory, MongoDB Collections, MCP Client)     |
+-----------------+-------------------------------------------------------+
                  |
                  ▼ HTTP Graph Request
+-----------------+-------------------------------------------------------+
|                 FastAPI GraphRAG Document Service (Port 8002)           |
|   (LlamaIndex Pipelines, ChromaDB Vector Index, Neo4j Graph DB)         |
+-------------------------------------------------------------------------+
```

---

## 2. Component & Subsystem Design

### 2.1 Web UI Subsystem (`Agentic-frontend`)
An interactive, high-performance web interface designed for real-time human-agent cooperation.
*   **Dynamic Chat Sub-client (`Chat.tsx`)**: Spawns non-blocking asynchronous requests, subscribes to gateway streaming sockets using native browser `EventSource`, and updates the typing buffer on screen using smooth frame transitions.
*   **3D Globe Visualizer (`EarthGlobe.tsx`)**: Constructed declaratively using **React Three Fiber (R3F)** and **Three.js**. Handles satellite orbits, geolocated node plotting, and neon connection trajectories on a custom Day/Night Earth shader sphere.
*   **MCP Administration Console (`MCPServerTab.tsx`)**: Visualizes registered server configurations, dynamic tools schema definitions, tool execution logging registers, and exposes control switches to enable or disable individual tools.

### 2.2 API Gateway Subsystem (`agentic_django`)
A secure, high-scale application web gateway that isolates core cognitive services from external clients.
*   **Authentication views (`authentication/views.py`)**: Resolves JWT validations, issues refresh/access codes, and handles sign-up pipelines.
*   **Thread & Subthread ViewSet (`chat/views.py`)**: Stores user-scoped workspaces (Spaces), multi-session threads (ChatThread), and individual prompt exchanges (ChatSubThread) inside relational database tables.
*   **Asynchronous Task Dispatcher**: Creates pending database records, packs user profiles into string-safe dictionaries, triggers Celery tasks, and serves instantaneous `202 Accepted` status payloads in under 200ms.
*   **SSE Streaming Proxy**: Serves as a thin, highly scaleable streaming server that reads from local Redis PubSub buffers and yields SSE bytes to browser listeners.

### 2.3 Cognitive Memory Subsystem (`Agentic-Memory`)
The system's central reasoning engine. It processes prompt intentions, organizes context, and executes tools.
*   **Agent Router (`routes.py`)**: Decides the routing mode based on query difficulty:
    *   `general`: Bypasses reasoning steps to directly stream LLM outputs.
    *   `thinking`: Invokes thinking states, exposing step-by-step logic chains to the UI.
    *   `agentic`: Triggers a comprehensive multi-agent ReAct loop allowing model execution of registered MCP tools.
*   **ReAct Orchestrator (`src/agents/`)**: Implements reasoning loops that output standardized JSON structures containing thinking descriptions, tool selections, and final arguments.
*   **Unified Context Manager**: Combines temporary in-memory contexts with historical threads queried from MongoDB documents.
*   **MCP Client Hub**: Communicates with external MCP servers over Stdio, Server-Sent Events, or HTTP endpoints. It discovers capabilities, validates JSON schemas, and coordinates task execution.

### 2.4 Document Processing & GraphRAG Subsystem (`Agentic-Graph-RAG`)
Manages structural corporate document ingestion, vector calculations, and relational knowledge lookups.
*   **LlamaIndex Pipeline (`llamaindex_processor.py`)**: Employs sentence boundary chunk splitters, generates semantic vector profiles, and extracts metadata properties.
*   **Deduplication Content Cache (`SmartDocumentCache`)**: Hashes files prior to processing to completely skip parsing on identical documents, saving CPU and storage overhead.
*   **Hybrid Vector-Graph Retriever**: Executes semantic vector retrieval from **ChromaDB** alongside relational entity-link traversal inside **Neo4j** to fuse dense knowledge context.

---

## 3. Database & Storage Schema Design

### 3.1 Relational Gateway Database (PostgreSQL / SQLite)

```
  +-------------------------+            +-------------------------+
  |    subscription_plans   |            |          users          |
  +-------------------------+            +-------------------------+
  | id (PK, Auto)           |◄───────────| id (PK, Auto)           |
  | name (CharField, Unique)|            | username (CharField)     |
  | price (Decimal)         |            | email (EmailField)      |
  | max_requests (Integer)  |            | role (CharField)        |
  | duration_days (Integer) |            | subscription_plan_id(FK)|
  +-------------------------+            | is_active (BooleanField) |
                                         +------------┬------------+
                                                      │
                                                      │ 1
                                                      │
                                                      ▼ 0..*
  +-------------------------+            +-------------------------+
  |      chat_sub_threads   |            |      chat_threads       |
  +-------------------------+            +-------------------------+
  | id (PK, UUID)           |            | id (PK, UUID)           |
  | parent_thread_id (FK)  |◄───────────| title (CharField)       |
  | query (TextField)       |            | space_id (FK)           |
  | answer (TextField)      |            | user_id (FK)            |
  | response_mode (CharField)|            | created_at (DateTimeField|
  | status (CharField)      |            +-------------------------+
  | execution_time (Float)  |
  +-------------------------+
```

<h3>3.2 Document Storage Database (MongoDB)</h3>
MongoDB stores raw conversational memories, step-by-step reasoning maps, and analytical metrics.

*   **Collection**: `chat_histories`
    ```json
    {
      "_id": "ObjectId",
      "user_id": "string",
      "chat_id": "string",
      "messages": [
        {
          "role": "user | assistant | system",
          "content": "string",
          "timestamp": "ISODate"
        }
      ]
    }
    ```
*   **Collection**: `thinking_steps`
    ```json
    {
      "_id": "ObjectId",
      "task_id": "string",
      "user_id": "string",
      "steps": [
        {
          "step_type": "context_preparation | tool_execution | synthesis",
          "status": "pending | completed | failed",
          "description": "string",
          "timestamp": "ISODate"
        }
      ]
    }
    ```

### 3.3 Vector Embeddings Store (ChromaDB)
*   **Collection**: `documents_semantic_vectors`
    *   **Dimension**: 1536 or 768 (depending on local embedding model choice e.g. `nomic-embed-text`).
    *   **Distance Metric**: Cosine Similarity.
    *   **Metadata Schema**:
        ```json
        {
          "document_id": "string",
          "file_hash": "string",
          "page_number": "integer",
          "chunk_index": "integer"
        }
        ```

### 3.4 Relational Entity Graph Database (Neo4j)
Neo4j maps structural document elements to capture real-world networks.
*   **Nodes**:
    *   `(:Document {id: String, name: String, hash: String, created_at: String})`
    *   `(:Chunk {id: String, text: String, page_number: Integer})`
    *   `(:Entity {name: String, type: String, description: String})`
*   **Relationships**:
    *   `(:Document)-[:HAS_CHUNK]->(:Chunk)`
    *   `(:Chunk)-[:MENTIONS]->(:Entity)`
    *   `(:Entity)-[:RELATED_TO {description: String, weight: Float}]->(:Entity)`

---

## 4. Detailed Execution & Sequence Designs

### 4.1 Asynchronous Query Submission & Decoupled Streaming Flow

This sequence diagrams shows the exact mechanics behind non-blocking asynchronous submissions and token streaming:

```
React Frontend (UI)          Django Gateway (DRF)           Redis Broker            Celery Worker
       │                              │                          │                        │
       │  (1) POST /chat/submit/      │                          │                        │
       ├─────────────────────────────►│                          │                        │
       │                              │  (2) Create SubThread    │                        │
       │                              │      Status: pending     │                        │
       │                              ├────────────────┐         │                        │
       │                              │                │         │                        │
       │                              │◄───────────────┘         │                        │
       │                              │                          │                        │
       │                              │  (3) Enqueue Task        │                        │
       │                              ├─────────────────────────►│                        │
       │                              │                          │                        │
       │  (4) HTTP 202 Accepted       │                          │                        │
       │◄─────────────────────────────┤                          │                        │
       │   {task_id, sub_thread_id}   │                          │                        │
       │                              │                          │                        │
       │  (5) GET /chat/stream/       │                          │                        │
       │      ?token=JWT              │                          │                        │
       ├─────────────────────────────►│                          │                        │
       │   (EventSource Socket)       │                          │                        │
       │                              │  (6) Subscribe Channel   │                        │
       │                              ├─────────────────────────►│                        │
       │                              │   "stream_<task_id>"     │                        │
       │                              │                          │                        │
       │                              │                          │  (7) Dequeue Task      │
       │                              │                          │◄───────────────────────┤
       │                              │                          │                        │
       │                              │                          │  (8) Execute Stream    │
       │                              │                          │      Inference         │
       │                              │                          │      (Calls FastAPI)   │
       │                              │                          │◄───────────────────────┤
       │                              │                          │                        │
       │                              │                          │  (9) Publish Token     │
       │                              │                          │◄───────────────────────┤
       │                              │                          │  (Publish to channel)  │
       │                              │                          ├────────────────────────┐
       │                              │                          │                        │
       │                              │  (10) Receive Token      │                        │
       │                              │◄─────────────────────────┤                        │
       │  (11) SSE "data: {token}"    │                          │                        │
       │◄─────────────────────────────┤                          │                        │
       │                              │                          │                        │
       │                              │                          │  (12) Task Finished    │
       │                              │                          │◄───────────────────────┤
       │                              │                          │  (Save DB & Publish    │
       │                              │                          │   "[DONE]")            │
       │                              │                          ├────────────────────────┐
       │                              │                          │                        │
       │                              │  (13) Receive "[DONE]"   │                        │
       │                              │◄─────────────────────────┤                        │
       │  (14) SSE "event: close"     │                          │                        │
       │◄─────────────────────────────┤                          │                        │
       │  (Connection severed)        │                          │                        │
```

---

## 5. Coding Standards & Development Conventions

To maintain a secure, robust, and clean development ecosystem, all engineers must adhere strictly to these engineering standards:

### 5.1 Python Standards (Django, FastAPI, Celery)
*   **Asynchronous Contexts**: Use async-native network requests (e.g., `httpx.AsyncClient` or starlette response structures) inside FastAPI code. Avoid using synchronous `requests` inside the main event loop to prevent thread starvation.
*   **Database Transaction Safety**: Wrap DB modification procedures (such as thread deletion or multi-subthread updates) inside transactional contexts to ensure absolute atomic integrity.
    ```python
    from django.db import transaction
    
    with transaction.atomic():
        sub_thread = serializer.save()
        thread.updated_at = timezone.now()
        thread.save()
    ```
*   **Strict Celery Serializer Boundaries**: Raw database objects (e.g., UUID primary keys, user profiles) must **never** be passed as raw objects into `.delay()` parameters. They must undergo clean serialization (e.g., wrapped into `str(uuid_id)` or dictionary schemas) to prevent Celery JSON serialization failures.
*   **Dependency Injection**: Leverage FastAPI dependencies natively to control route authentication and connection pools.

### 5.2 TypeScript & React Standards
*   **Absolute Component Decoupling**: Isolate rendering concerns from endpoint logic. Expose explicit APIs through customized hooks or standalone service interfaces (e.g. `api.ts`, `mcpApi.ts`).
*   **Status Code Adaptability**: UI components must support flexible status code validations. Never restrict network queries strictly to `200/201` checks when asynchronous background endpoints return `202 Accepted` statuses.
*   **Complete Type Enforcement**: Maintain strict typescript compiles. Do not use generic fallback types (e.g., `any`) inside API specifications, interface props, or stream handlers.

---

## 6. Operational Setup & Developer Environments

### 6.1 Package Ingestion & Virtual Environments
The CogniVox platform enforces the use of the high-speed **`uv`** package manager. It is 10-100x faster than standard `pip` and manages complex virtual environments with locked binary dependencies.

```bash
# 1. Provision virtual environment
uv venv

# 2. Activate environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# 3. Ingest locked package manifest
uv pip install -r requirements.txt
```

### 6.2 Service Orchestrator Automation (`run_all_services.py`)
Developer configurations, container setups, health checks, and execution scripts are organized inside the orchestrator:
*   `python run_all_services.py setup` - Auto-detects dependencies, installs `uv`, creates service venvs, and pulls models.
*   `python run_all_services.py start-infra` - Spawns PostgreSQL, MongoDB, Redis, and Neo4j inside Docker containers.
*   `python run_all_services.py run` - Launches Django, Celery, Memory, GraphRAG, and React in parallel.
*   `python run_all_services.py stop` - Sends graceful shutdown signals to all active subprocesses.

---

## 7. Testing & Quality Assurance Guidelines

All code modifications must undergo strict verification checks to verify architectural safety, type integrity, and system health.

### 7.1 Automated Integration Checks
*   **Django Model Integrity**: Execute gateway checks before deployment:
    ```bash
    python manage.py check
    ```
*   **Database Migration Validation**: Ensure database schemas match model structures without conflicts:
    ```bash
    python manage.py makemigrations --check --dry-run
    ```
*   **Frontend Compile Integrity**: Verify complete type safety inside the React application:
    ```bash
    npx tsc --noEmit
    ```

### 7.2 Manual Streaming Verification Checklist
1.  Verify the local Redis container is listening: `docker ps`.
2.  Launch Celery worker pool and check task registration outputs.
3.  Open the browser network inspector and trigger a prompt.
4.  Assert that `/api/chat/submit/` resolves instantly with a `202 Accepted` status, returning a `task_id` and a `sub_thread_id`.
5.  Assert that `/api/chat/stream/<task_id>/` accepts the JWT query parameter (`?token=`), returns status `200`, sets `Content-Type: text/event-stream`, and streams token events until outputting the `close` indicator.
6.  Query the sub-thread database record and confirm that the full parsed response, metrics, and source annotations were saved on task completion.
