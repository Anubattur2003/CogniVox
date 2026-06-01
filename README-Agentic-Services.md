Agentic Services Technical Overview

Purpose

This README provides a cohesive, Agentic-style technical overview of the platform services in this repository: Agentic-frontend, Agentic-Graph-RAG, Agentic-Memory, Cognivox-Landing, agentic_django, and the shared service stack orchestrated by docker-compose.agentic-services.yml. It also documents the Model Context Protocol (MCP) layer that standardizes agent-to-tool interactions across the system. This document contains no source code and is intended for architects, developers, and operators.

Agentic Architecture at a Glance

The system follows an Agentic, layered architecture optimized for autonomy, observability, and evolvability:

- Presentation Layer: Web UIs for user journeys, insights, and agent orchestration (Cognivox-Landing, Agentic-frontend).
- API and Orchestration Layer: Core backends, agent endpoints, capability brokering, security, and policy (agentic_django).
- Knowledge and Reasoning Layer: Graph-based retrieval, semantic search, planning, and tool-use (Agentic-Graph-RAG).
- Memory and Context Layer: Short-term, long-term, and vectorized memory for continuity and retrieval (Agentic-Memory).
- Foundation Services Layer: Datastores, admin consoles, and local LLM runtime (PostgreSQL, MongoDB, Neo4j, PgAdmin, Ollama).
- Integration and Transport: Service mesh/networking, health checks, volumes, and environment management (docker-compose.agentic-services.yml).
- MCP Layer (Cross-Cutting): Standardizes agent-to-tool interactions, resource discovery, and capability exposure.

Core Services

Agentic-frontend

- Role: Primary application UI for authenticated users to operate agents, monitor runs, and visualize knowledge/memory outcomes.
- Runtime & Access: Vite dev server on port 3000 with HTTPS enabled via a basic SSL plugin; strict port enforcement and development CORS.
- Backend Proxying: Proxies `/api` to the backend at `http://localhost:8000`, normalizing trailing slashes for Django endpoints.
- UI Stack: React 18, MUI, framer-motion, and React Three Fiber for interactive visualizations.
- Interaction Model: Consumes backend APIs for authentication (JWT), chat/agent sessions, memory inspection, and graph insights; emits telemetry for observability.

Agentic-Graph-RAG

- Role: Provides graph-first retrieval-augmented generation, combining entity/relation graphs (Neo4j) with vector retrieval (Chroma) and optional LlamaIndex processing.
- Capabilities: PDF ingestion with multiple extraction methods; tunable chunking; hybrid search (semantic + keyword); graph visualization; export to JSON/GraphML/RDF.
- Interfaces & Ports: REST API with health/docs; default service port 8003. Local Docker compose includes Neo4j and Ollama for development.
- Configuration: YAML config for database, vector store, PDF pipeline, and Ollama; environment variables for service endpoints.

Agentic-Memory

- Role: Advanced memory management service with multi-level storage (in-memory and MongoDB) and intelligent context awareness using LangChain/LangGraph.
- Agent Set: Context awareness, intent classification, query expansion and validation, response enhancement, profile extraction, and speech-to-text.
- Interfaces & Ports: REST API with health/docs on port 8002.
- LLM Providers: Multiple providers supported; default is Ollama with `qwen3:4b`, with optional OpenAI/Anthropic/Google configuration.
- Storage & Controls: MongoDB for persistence; rate limiting, input validation, GPU acceleration flags, and metrics toggles.

Cognivox-Landing

- Role: Public/entry UI that frames the value proposition, product navigation, and quick starts; routes users toward authenticated application surfaces in Agentic-frontend.
- Runtime: Vite-based React app with Tailwind utilities, motion/visual effects, and router support.
- Emphasis: Lightweight, fast-loading, accessible content with links into deeper workflows.

agentic_django

- Role: Core backend providing authentication, authorization, API endpoints, orchestration of agent capabilities, and integration with storage and graph services.
- API Surface: Namespaced under `/api/` with subpaths for `auth`, `chat`, `admin`, and `system`. JWT token obtain/refresh/verify endpoints provided. Health routed via the core app namespace.
- Security & Middleware: DRF with JWT authentication; broad CORS for local dev; hardened password hashers (including Argon2); custom maintenance mode, API usage stats, and audit logging middleware.
- Data & Services: PostgreSQL via single URL; MongoDB URL and DB name for external integrations; configurable Ollama base URL; memory service default at `http://localhost:8002`.
- HTTPS Dev: A helper script generates self-signed certs (including LAN IP SANs) and runs an HTTPS dev server; falls back to HTTP if dependencies are missing.
- Extensibility: Integrates additional tools via the MCP layer and surfaces new agent skills without tight coupling.

Shared Service Stack (docker-compose.agentic-services.yml)

- Purpose: Defines foundational services and networks for local development and deployment on a single host.
- Included Services:
  - Neo4j: Graph database for knowledge graphs and relationship reasoning (HTTP and Bolt endpoints). External volumes preserve data and plugins across resets.
  - Ollama: Local LLM runtime for model hosting and offline experimentation. GPU access is requested where available.
  - MongoDB: Document datastore suitable for flexible content and event storage; initialization support for user/database bootstrap.
  - PostgreSQL: Relational datastore for structured, transactional needs, compatible with popular extensions.
  - PgAdmin: Administrative UI for PostgreSQL, preconfigured for convenient local access.
- Operations Characteristics:
  - Health checks: Each service defines simple, container-level liveness checks for predictable orchestration.
  - Externalized volumes: Persistent data and logs survive container recreation by design.
  - Single network: A named, reusable network ensures stable service discovery across runs.

Concrete Endpoints & Ports (Local Defaults)

- Backend (agentic_django): 8000; API root `/api/`; JWT token endpoints; health via core app.
- Memory (Agentic-Memory): 8002; health/docs endpoints.
- Graph-RAG: 8003; health/docs endpoints; depends on Neo4j and optional Chroma.
- Frontend (Agentic-frontend): 3000 (HTTPS); proxies `/api` to backend with trailing-slash normalization.
- Neo4j: 7474 (HTTP UI), 7687 (Bolt) with default `neo4j/password` per local compose.
- Ollama: 11434; consumed by backend, Memory, and Graph-RAG services.

MCP Layer (Model Context Protocol)

- Purpose: Provide a standard way for agents and clients to discover, call, and reason about external tools and data sources through a consistent protocol.
- Components:
  - MCP Server: Adapts real services (databases, tools, knowledge sources) into a uniform capability surface for agents.
  - MCP Client: Consumes capabilities exposed by servers, enabling agents and UIs to call tools and fetch resources without bespoke integrations.
  - Protocol: Defines message types, capability discovery, schema/metadata exchange, and error semantics for robust agent-tool loops.
- Benefits in this System:
  - Interoperability: Backends can expose memory, graph, retrieval, and admin operations uniformly to agents and UIs.
  - Evolvability: New tools can be introduced or swapped behind an MCP server without broad refactors.
  - Observability: Standardized request/response envelopes support consistent logging, tracing, and policy enforcement.
- Typical Integration Points:
  - agentic_django acts as the broker, mapping authenticated requests to MCP servers and enforcing policy.
  - Agentic-Graph-RAG exposes retrieval/graph operations through MCP for agent use during planning and execution.
  - Agentic-Memory offers memory CRUD/search via MCP, enabling agents to persist and retrieve context safely.

Data and Control Flows

- User Journeys:

  - Entry via Cognivox-Landing into Agentic-frontend for authenticated sessions.
  - Users initiate tasks or chats; frontend calls agentic_django APIs.
  - agentic_django validates user/session, consults policy, and orchestrates tool use via MCP.
  - MCP calls fan out to memory or graph services; optional local LLM inference via Ollama; results are persisted and returned to the UI.

- Agentic Execution Loop (Conceptual):
  - Perception: Retrieve context/memory and relevant graph substructures.
  - Planning: Select tools and order of operations; potentially refine plans iteratively.
  - Action: Invoke MCP-exposed capabilities; capture outputs and provenance.
  - Reflection: Update memory and adjust plan based on outcomes; produce final, grounded results with citations and traces.

Security and Compliance Considerations

- Identity & Access: Centralized auth in agentic_django; service-to-service access constrained by network and per-service credentials. DRF enforces authenticated defaults across APIs.
- Data Protection: Sensitive data should be encrypted at rest where supported and scoped by least privilege at the application level.
- Policy & Governance: MCP envelopes and backend APIs should carry request metadata for auditability, rate limiting, and content policy checks.
- Tenant Safety: Ensure separation of user data across sessions and projects; validate inputs to graph/memory operations to prevent injection or poisoning.

Operations and Environments

- Local Development: docker-compose.agentic-services.yml stands up graph, databases, admin consoles, and local LLM runtime. External volumes preserve state across restarts for faster iteration.
- Health & Diagnostics: Rely on built-in health checks and admin UIs (PgAdmin, Neo4j Browser). Surface additional readiness endpoints in agentic_django for higher-level health.
- Resource Tuning: Adjust memory/heap for Neo4j and resource reservations for Ollama based on host capacity and model size. Monitor GPU/CPU and disk IO utilization.
- Backups & Durability: Because volumes are external, incorporate regular host-level snapshots or database-native backups for PostgreSQL and MongoDB. Export Neo4j databases before upgrades.

Inter-Service Contracts (High Level)

- Frontend ↔ Backend: Authenticated RESTful/JSON APIs for sessions, tasks, chat runs, memory inspection, and graph insights. Real-time updates can be layered where supported.
- Backend ↔ Knowledge/Memory: Service calls to Agentic-Graph-RAG and Agentic-Memory, mediated by MCP for capability discovery and invocation.
- Backend ↔ Foundation Services: Direct database connections to PostgreSQL/MongoDB; Bolt/HTTP to Neo4j; local HTTP to Ollama.

Reliability and Observability

- Traces: Tag requests with correlation IDs across frontend, backend, and MCP calls to reconstruct agent runs end-to-end.
- Metrics: Capture request rates, latencies, cache hit rates, model load times, and graph query costs. Track memory growth and compaction efficiency.
- Logs: Prefer structured logs with request context; differentiate user, agent, and system events for actionable triage.

Windows and GPU Notes

- Windows Host: Compose stack runs on a Windows host; ensure correct permissions for external volumes and verify ports are free. GPU access for Ollama typically relies on compatible drivers and, when applicable, a Linux backend (e.g., WSL2) for best acceleration support.
- Networking: Named Docker network provides consistent DNS-based service discovery between containers and application services.

Service Quick Facts

- Neo4j: Backing store for graphs and relationship reasoning; uses persistent volumes for data, logs, and plugins.
- Ollama: Local model runtime; makes models and tags visible via a health endpoint; benefits from GPU when available.
- MongoDB: Document database for flexible, schema-light content and event streams; supports initialization scripts.
- PostgreSQL: Relational database for strong consistency needs and application metadata.
- PgAdmin: Administrative console for PostgreSQL management and inspection.

Assumptions and Constraints

- Virtual Environments: Python subprojects include their own virtual environments; maintain isolation to avoid dependency conflicts.
- No Code in This Document: This README intentionally avoids source code examples and command snippets.
- Extensibility: New tools can be registered behind MCP without changing core UI/UX or backend contracts, preserving upgrade paths.

Selected References (Contextual)

- Model Context Protocol (MCP): Industry efforts standardizing agent ↔ tool interfaces to enable safer, composable tool use in LLM systems.
- Graph-RAG: Graph-enhanced retrieval methods improve grounding and multi-hop reasoning over entity/relationship structures.
- Local LLM Runtimes: On-device runtimes (e.g., Ollama) enable privacy-preserving, offline model execution for development and certain production use cases.

Change Ownership

- This document summarizes the current architecture across services and the shared stack. Keep it synchronized with service READMEs and docker-compose.agentic-services.yml when capabilities or infrastructure change.
