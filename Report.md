I’m going to scan the repository to extract concrete implemented features and architecture details across backend, frontend, memory, and GraphRAG services, so I can assemble a robust, resume-ready report grounded in the actual code.
Ran tool

I’m running a broad scan across backend, frontend, memory, and GraphRAG to extract concrete implemented endpoints, components, and services for an accurate feature report.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

Scanning key backend, memory, graph, and frontend files in parallel to ground the report in actual implemented code.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

Reading the main backend, memory, graph, and frontend files to extract concrete implemented features for the report.
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool
Ran tool

### Executive summary
Built a production-grade, multi-service AI platform with a typed React frontend, a FastAPI backend, an Agentic Memory service with tool-using LLMs, and a GraphRAG service for document ingestion and knowledge retrieval. Implemented secure auth, role-based model quotas, hybrid MongoDB/PostgreSQL threading, file-to-graph pipelines, and a modern UX with real-time chat, source-cited answers, and a 3D globe.

### System architecture
- **Services**: Backend API (FastAPI), Agentic Memory (FastAPI + LangChain/LangGraph), GraphRAG (FastAPI + Neo4j + Chroma), Orchestrator (Python CLI).
- **Data**: PostgreSQL (users, quotas/transactions), MongoDB (threads/sub-threads), Chroma vector store, Neo4j graph DB, optional GCP storage.
- **Frontend**: React 18 + TypeScript + Vite, modular pages, contexts, and services.

### Backend API (FastAPI)
- **Auth (JWT, OAuth2 Password)**
  - Issue tokens and return current user; on register: auto-assign default model and initialize requests.
```19:36:Agentic-Backend/app/api/endpoints/auth.py
@router.post("/token", response_model=Token)
async def login_for_access_token(...
```
```38:47:Agentic-Backend/app/api/endpoints/auth.py
@router.get("/me")
async def get_current_user(...
```
```49:121:Agentic-Backend/app/api/endpoints/auth.py
@router.post("/register", response_model=Token)
async def register_user(...
```
- **Threading and Chat**
  - Create threads (Mongo), link metadata in Postgres, add sub-threads, list threads/sub-threads, delete threads cascade, generate titles via Memory or local fallback. Timestamps handled as timezone-aware.
```185:233:Agentic-Backend/app/api/endpoints/chat.py
@router.post("/threads", response_model=Thread)
async def create_thread(...
```
```235:586:Agentic-Backend/app/api/endpoints/chat.py
@router.post("/threads/{chat_id}/sub_threads", response_model=SubThread)
async def create_sub_thread(...
```
```680:760:Agentic-Backend/app/api/endpoints/chat.py
@router.get("/threads", response_model=List[Dict[str, Any]])
async def get_all_threads(...
```
- **Admin/Quota management**
  - Reset per-model quotas and transactions; attach models to users and initialize quotas.
```12:47:Agentic-Backend/app/api/endpoints/admin/admin_requests.py
@router.post("/reset_requests/{user_id}")
async def reset_requests(...
```
```49:91:Agentic-Backend/app/api/endpoints/admin/admin_requests.py
@router.post("/add_models_to_user/{user_id}")
async def add_models_to_user(...
```
- **Model management**
  - Pull models from Ollama and persist metadata if absent locally.
```11:41:Agentic-Backend/app/api/endpoints/models.py
@router.post("/download_model/", response_model=ModelDownloadRequest)
def download_model(...
```
- **Health and CORS**
  - Health endpoint checks Postgres, Mongo, and Ollama; flexible CORS allow-list/wildcard.
```97:155:Agentic-Backend/app/main.py
@app.get("/health")
async def health_check(): ...
```
- **Configuration**
  - Centralized YAML config for app, DB, Mongo, JWT, defaults (e.g., `default_model_name`).

### Agentic Memory service
- **FastAPI service with robust error handling, CORS, and middleware** for performance/telemetry.
- **Supervisor ReAct Agent (LangChain + Ollama)**:
  - Tool-using agent that invokes GraphRAG only when beneficial; extracts thinking steps and source docs; tracks per-user context; clears tool carry-over between turns to avoid stale sources.
```29:77:Agentic-Memory/src/agents/supervisor_react_agent/agent.py
class SupervisorReActAgent(BaseAgent): ...
```
```88:153:Agentic-Memory/src/agents/supervisor_react_agent/agent.py
def _setup_react_agent(self): ...
```
```309:475:Agentic-Memory/src/agents/supervisor_react_agent/agent.py
def chat(...): ...
```
- **GPU readiness**
  - CUDA probe utility for environment checks.
```10:21:Agentic-Memory/src/gpu_manager/check_cuda.py
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
```

### GraphRAG service
- **Endpoints**
  - Health, query (returns answer, summary, sources, metadata), ingest files (background, multi-file), ingest directory, list/download documents, export/visualize graph, and comprehensive cleanup and stats APIs (with “nuclear” mode for Chroma).
```102:117:Agentic-Graph-RAG/src/api/app.py
@app.get("/health", response_model=StatusResponse)
async def health_check(): ...
```
```121:311:Agentic-Graph-RAG/src/api/app.py
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest): ...
```
```343:458:Agentic-Graph-RAG/src/api/app.py
@app.post("/ingest", response_model=IngestResponse)
async def ingest(...): ...
```
```756:1287:Agentic-Graph-RAG/src/api/app.py
@app.post("/database/cleanup"...)
async def cleanup_database(...): ...
```
- **Configuration**
  - Paths, vector store (Chroma), Neo4j, Ollama models, chunking, optional GCP storage.
```20:43:Agentic-Graph-RAG/src/config.py
ROOT_DIR = Path(__file__).parent.parent
...
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")
```
- **Client SDK**
  - Simple Python client for health, query, ingest, remove, visualize, export.
```13:35:Agentic-Graph-RAG/src/client/cognivox_client.py
class CogniVoxClient: ...
```

### Frontend (React + TypeScript + Vite)
- **Auth**
  - Central `AuthContext` with login (OAuth2 form), signup, token storage, periodic/focus-based token revalidation, and global token-expiration behavior for 401 responses.
```120:139:Agentic-frontend/src/contexts/AuthContext.tsx
const verifyToken = async (token: string): Promise<User | null> => { ... }
```
- **API layer**
  - Centralized endpoints for Backend and GraphRAG; authenticated `apiCall` with 401 handling; chat API (create thread, add sub-thread/query, list/delete threads), GraphRAG file upload integration.
```14:28:Agentic-frontend/src/services/api.ts
export const API_ENDPOINTS = { AUTH:..., CHAT:..., GRAPH_RAG:... }
```
```198:253:Agentic-frontend/src/services/api.ts
submitChatQuery(...): Promise<ApiResponse<ChatSubThread>> { ... }
```
```333:441:Agentic-frontend/src/services/api.ts
graphRagApi.uploadFiles(...): Promise<ApiResponse<GraphRAGIngestResponse>> { ... }
```
- **Chat UI**
  - Thread-aware chat with response modes, execution time visualization, markdown rendering, animated transitions, and source documents modal; calls backend which orchestrates Memory → GraphRAG.
```257:433:Agentic-frontend/src/components/pages/Chat/Chat.tsx
const Chat: React.FC = () => { ... }
```
- **Library**
  - Lists all threads for current user (from backend), grid/list views, favorites (client-side), delete with confirmation, quick create with API.
```30:1017:Agentic-frontend/src/components/pages/Library/Library.tsx
const Library: React.FC = () => { ... }
```
- **3D Globe**
  - Three.js/React Three Fiber globe with day/night textures, clouds, stars, moon orbit, fixed sun lighting, orbit controls.
```344:433:Agentic-frontend/src/components/3d-globe/EarthGlobe.tsx
const EarthGlobe: React.FC<EarthGlobeProps> = ({ ... }) => { ... }
```
- **Route protection**
  - `ProtectedRoute` guards routes by auth state, with loading state and redirect to login.
```9:28:Agentic-frontend/src/components/ProtectedRoute.tsx
const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => { ... }
```

### Orchestration and operations
- **Unified runner**
  - Thin entrypoint to orchestrator commands; services also expose run.py with health checks (per documentation).
```30:31:run_all_services.py
if __name__ == "__main__":
    main()
```

### Security and compliance
- **JWT-based auth, OAuth2 login form**
- **Role checks on sensitive endpoints** (admin quota resets/model assignment; chat creation guarded by role).
- **CORS policies** configurable per environment.
- **Frontend token revalidation** periodically and on window focus, auto-logout on 401.

### Performance and reliability
- **Thread creation and sub-thread writes** are hybrid: metadata in Postgres; content in Mongo for scale.
- **GraphRAG ingestion** uses background tasks and batched parallelism; directory-mode and multi-file ingestion.
- **Source-cited answers**: Memory agent extracts sources from GraphRAG tool output for UI rendering.
- **Resilience features**
  - Memory client fallbacks and response “dummy mode” for safe dev/test.
  - GraphRAG cleanup “nuclear mode” with isolated Chroma client to avoid locks.
  - Health endpoints covering data stores and Ollama.

### Notable implemented features (resume-ready)
- **End-to-end auth and user provisioning**: OAuth2 login, JWT issuance, current user API; automatic model assignment and request-quota initialization at registration.
- **Hybrid conversation threading**: Threads and sub-threads persisted across MongoDB and Postgres with timezone-safe timestamps and owner validation, including cascade delete and title auto-generation from model output.
- **Admin quotas and model management**: Admin APIs to reset request counters and attach models with default quotas; Ollama model pull integration for model bootstrap.
- **Agentic Memory with ReAct + tools**: LangChain-based Supervisor agent using an explicit ReAct prompt structure; intelligent GraphRAG invocation; extraction of tool sources; per-user context memory and thinking-state exposure for UI.
- **GraphRAG ingestion/query pipeline**: Multi-file and directory ingestion, hybrid search, result normalization with relevance/confidence; document listing, download (local/GCP), export/visualization; comprehensive cleanup and stats APIs.
- **Frontend UX for chat/library**: Modern animated chat with markdown and source chips; thread library with list/grid, favorites, delete confirmations; robust token lifecycle handling across the app.
- **3D Globe visualization**: React Three Fiber-based earth with accurate day/night visuals, clouds, stars, moon orbit, and smooth controls.

### Selected impact
- Reduced integration friction via a clear API layer and SDK (GraphRAG Python client).
- Increased reliability with robust health checks and fallbacks; safer operations through cleanup and stats APIs.
- User experience uplift: responsive chat with source grounding, animated UI, and document ingestion flows.
- Operational visibility: execution-time telemetry and environment-driven configuration.

### Keywords and tech stack
- FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, MongoDB, Neo4j, Chroma, LlamaIndex, LangChain/LangGraph, Ollama
- React 18, TypeScript, Vite, Framer Motion, React Three Fiber/Three.js, Tailwind CSS
- JWT, OAuth2, CORS, Background tasks, Async I/O, GCP storage (optional)

### Resume bullet points (copy-ready)
- Designed and built a multi-service AI platform (Backend + Memory + GraphRAG + React Frontend) with secure auth, role-based quotas, and hybrid conversation storage across PostgreSQL and MongoDB.
- Implemented an Agentic Memory service with a LangChain ReAct supervisor agent that intelligently invokes GraphRAG tools, returns source-cited answers, and maintains per-user context and thinking states.
- Created GraphRAG APIs for hybrid search and document ingestion (multi-file and directory), plus admin endpoints for cleanup, visualization, export, and data-store statistics.
- Delivered a typed React app: token lifecycle management, protected routes, real-time chat with markdown and citations, a library of threads with grid/list views and favorites, and a 3D globe built with React Three Fiber.
- Added admin capabilities to attach models to users, initialize request quotas, and reset usage across models and transactions; integrated Ollama model pull to bootstrap models.
- Hardened operations with comprehensive health checks (Postgres, Mongo, Ollama), robust CORS, fallback modes for external services, and a “nuclear” cleanup for vector stores to prevent lock contention.
- Drove performance and UX with background ingestion, batched parallelism, execution-time telemetry, and timezone-safe timestamps across read/write paths.

---

- Implemented: `auth`, `chat/threads` and `sub_threads`, admin `reset_requests` and `add_models_to_user`, models `download_model` endpoints; Memory service supervisor agent and GraphRAG tool integration; GraphRAG health/query/ingest/cleanup/stats suite; Frontend auth context and chat/library UI; 3D globe. 
- New/modernized features: API-based thread persistence and listing; response-mode-aware chat submissions; auto title generation with fallbacks; admin quota management; GraphRAG multi-file ingestion and ops tooling; frontend token revalidation and 401 auto-logout; animated UI + source-citation display.