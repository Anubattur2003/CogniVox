# CogniVox Agentic Memory Technical Documentation

## Overview

The Agentic Memory Service serves as the conversational AI engine of the CogniVox ecosystem, providing intelligent query processing, GPU-optimized operations, and sophisticated multi-level memory management. Built with modern LangChain/LangGraph architecture, the service features a SupervisorReAct agent for intelligent tool usage, GPU acceleration capabilities, and UV-based lightning-fast setup.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [UV-Based Modern Setup](#uv-based-modern-setup)
3. [SupervisorReAct Agent System](#supervisorreact-agent-system)
4. [GPU Optimization Framework](#gpu-optimization-framework)
5. [Multi-Level Memory Architecture](#multi-level-memory-architecture)
6. [LangChain Integration](#langchain-integration)
7. [Advanced Performance Features](#advanced-performance-features)
8. [Service Integration](#service-integration)
9. [Health Monitoring](#health-monitoring)
10. [Configuration Management](#configuration-management)

## Architecture Overview

### Core Responsibilities
- **SupervisorReAct Agent**: Intelligent decision-making for tool usage and response generation
- **Multi-Level Memory Management**: L0 (RAM), L1 (SQLite), L2 (MongoDB) memory hierarchy
- **GPU Resource Management**: Singleton GPU manager with allocation tracking and CPU fallback
- **Context Intelligence**: Smart context retrieval with semantic similarity and relevance scoring
- **Real-time Processing**: Streaming responses with conversation threading and state management
- **GraphRAG Integration**: Intelligent knowledge base querying through dedicated tools

### Modern Architecture Features
- **UV Package Management**: 10-100x faster AI/ML dependency installation with optimized PyTorch setup
- **GPU Auto-Detection**: Automatic CUDA detection with graceful CPU fallback and memory optimization
- **LangChain Ecosystem**: Full integration with LangChain Core, Community, and LangGraph workflows
- **Health Monitoring**: Comprehensive dependency validation and real-time service monitoring
- **Smart Caching**: Multi-level caching with performance tracking and automatic cache promotion
- **Graceful Degradation**: Automatic fallback mechanisms for external service failures

## UV-Based Modern Setup

### Lightning-Fast Setup (3-8 minutes)
```bash
cd Agentic-Memory

# UV-based setup with AI/ML optimization
python setup.py

# Start with GPU detection and health monitoring
python run.py
```

### AI/ML Optimized Setup Features
The enhanced `setup.py` script provides:
- **Python Version Validation**: Requires Python 3.9+ with 3.11+ optimization for LangChain compatibility
- **UV Installation**: Automatic UV installation with PowerShell support for Windows
- **PyTorch CPU Optimization**: Optimized PyTorch installation with CPU-specific optimizations for faster setup
- **LangChain Ecosystem Management**: Coordinated installation of LangChain Core, Community, and LangGraph
- **MongoDB Driver Compatibility**: Optimized Motor and PyMongo installations with connection pooling
- **Virtual Environment Isolation**: Python 3.11 preference with system Python fallback
- **Extended Timeouts**: Special handling for large AI/ML packages (PyTorch, LangChain)

### Enhanced Run Script Capabilities
The modernized `run.py` provides:
- **UV Environment Detection**: Automatic detection and activation of UV-managed environments
- **GPU Availability Checking**: CUDA detection with device enumeration and memory validation
- **AI/ML Dependency Validation**: Comprehensive checks for PyTorch, LangChain, and related libraries
- **MongoDB Health Validation**: Connection testing with authentication and performance checks
- **Ollama Service Integration**: Model availability verification and API connectivity testing
- **Environment Configuration**: Automatic setup of service discovery and inter-service communication
- **Memory Optimization**: Dynamic memory settings based on available system resources
- **Graceful Shutdown**: Signal handling with conversation state preservation and resource cleanup

### Command Line Options
```bash
# Basic startup with auto-detection
python run.py

# Force CPU mode (disable GPU acceleration)
python run.py --cpu-only

# Development mode with debug logging and auto-reload
python run.py --reload --log-level debug

# Custom port and worker configuration
python run.py --port 9002 --workers 2

# Memory optimization for large models
python run.py --max-memory 8GB

# Skip external service checks for faster startup
python run.py --skip-checks
```

## SupervisorReAct Agent System

### Intelligent Decision-Making Architecture

#### SupervisorReAct Agent Implementation
```python
class SupervisorReActAgent(BaseAgent):
    """
    Advanced ReAct agent that intelligently decides when to use GraphRAG tools
    vs direct responses, providing sophisticated reasoning and tool integration.
    """
    
    def __init__(
        self,
        model_name: str = "qwen3:4b",  # Optimized for performance
        temperature: float = 0.1,     # Low temperature for consistent decisions
        provider: str = "ollama",
        graphrag_client: Optional[GraphRAGClient] = None,
        **kwargs
    ):
        """Initialize with performance-optimized configuration"""
        super().__init__(
            agent_name="supervisor_react",
            model_name=model_name,
            provider=provider,
            temperature=temperature,
            system_prompt=supervisor_system_prompt,
            **kwargs
        )
        
        # Initialize GraphRAG integration
        self.graphrag_client = graphrag_client or GraphRAGClient()
        self.graphrag_tool = create_graphrag_tool(self.graphrag_client)
        self.tools = [self.graphrag_tool]
        
        # Setup ReAct agent with LangChain
        self._setup_react_agent()
        
        # Initialize user context management
        self.user_contexts = defaultdict(list)
        self.max_context_length = 10
        self.thinking_states = {}
    
    def chat(
        self,
        user_message: str,
        user_id: str = "default",
        context_prompt: str = "",
        return_thinking: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process chat message with intelligent tool usage and thinking tracking
        """
        try:
            # Clear previous tool results to prevent source carryover
            if hasattr(self, 'graphrag_tool') and self.graphrag_tool:
                self.graphrag_tool.clear_last_result()
            
            # Update thinking state for real-time frontend tracking
            self._update_thinking_state(user_id, {
                "step": "analyzing",
                "content": "Analyzing your question and determining approach...",
                "is_thinking": True
            })
            
            # Prepare context and agent input
            context = self._prepare_context(user_id, context_prompt)
            agent_input = {
                "input": user_message,
                "context": context,
                "system_prompt": self.system_prompt,
                "user_id": user_id
            }
            
            # Execute ReAct agent with error handling
            result = self.agent_executor.invoke(agent_input)
            
            # Extract and process results
            raw_output = result.get("output", "I apologize, but I couldn't generate a proper response.")
            final_response, thinking_steps = self._extract_thinking_from_response(raw_output)
            
            # Extract tool usage and sources
            used_tools = self._extract_used_tools(result)
            source_documents = self._extract_source_documents()
            
            return {
                "response": final_response,
                "thinking_steps": thinking_steps,
                "used_tools": used_tools,
                "sources": source_documents,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"SupervisorReAct agent processing failed: {str(e)}")
            return self._create_fallback_response(user_message, user_id, str(e))
```

#### Intelligent Tool Usage Decision Making
```python
# ReAct Prompt Template with Advanced Logic
react_prompt_template = """You are CogniVox, an intelligent assistant that follows the ReAct pattern.

## Available Tools:
{tools}

## Decision Framework:
**Use GraphRAG Search Tool when:**
- Questions about specific documents, papers, or technical content
- Company policies, procedures, or documentation queries
- Domain-specific knowledge requiring factual information
- Research topics needing expert knowledge
- Technical queries about products, services, or methodologies

**Respond Directly when:**
- General greetings and casual conversation
- Personal opinions or subjective questions
- Current events or real-time information
- Basic calculations or simple programming questions
- Meta-questions about the conversation itself

## ReAct Format (MUST follow exactly):
1. Thought: [reasoning about what to do]
2. Action: [tool_name or direct_response]
3. Action Input: {{"query": "search query", "user_id": "{user_id}", "n_results": 5}}
4. Observation: [tool output]
5. Final Answer: [complete response to user]

## Context: {context}
## Current User ID: {user_id}
## Current Query: {input}

Begin your reasoning:
{agent_scratchpad}"""
```

### Multi-Agent Collaboration

#### Agent System Architecture
```python
class AgentPipeline:
    """Coordinated agent pipeline with intelligent processing"""
    
    def __init__(self):
        # Core agents with specific responsibilities
        self.supervisor_agent = SupervisorReActAgent()
        self.query_validator = QueryValidationAgent()
        self.context_agent = ContextAwarenessAgent()
        self.intent_classifier = IntentClassifierAgent()
        self.enhancement_agent = ResponseEnhancementAgent()
        self.summary_agent = SummaryGenerationAgent()
    
    async def process_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        context: dict = None
    ) -> dict:
        """Coordinated message processing pipeline"""
        
        # Step 1: Query validation and security
        validation = self.query_validator.validate_query(message)
        if not validation.get('isValid', False):
            return self._create_validation_error_response(validation)
        
        # Step 2: Context retrieval and intelligence
        context_prompt = await self.context_agent.get_context_prompt(
            user_id, conversation_id, message
        )
        
        # Step 3: SupervisorReAct processing with tool decisions
        agent_result = self.supervisor_agent.chat(
            user_message=message,
            user_id=user_id,
            context_prompt=context_prompt,
            return_thinking=True
        )
        
        # Step 4: Response enhancement and variant generation
        final_response = agent_result.get("response", "")
        thinking_steps = agent_result.get("thinking_steps", [])
        used_tools = agent_result.get("used_tools", [])
        source_documents = agent_result.get("sources", [])
        
        # Enhance response with additional context
        enhanced_response = self.enhancement_agent.enhance_response(
            final_response, used_tools, source_documents
        )
        
        # Generate crisp summary
        summary = self.summary_agent.generate_summary(
            enhanced_response, message
        )
        
        return {
            "response": enhanced_response,
            "variants": {
                "summary": summary,
                "detailed": enhanced_response
            },
            "thinking_steps": thinking_steps,
            "used_tools": used_tools,
            "sources": source_documents,
            "processing_stats": self._get_processing_stats()
        }
```

## GPU Optimization Framework

### Singleton GPU Manager

#### Advanced GPU Resource Management
```python
class GPUManager:
    """Thread-safe singleton GPU manager with intelligent allocation"""
    
    _instance = None
    _lock = threading.RLock()
    
    def __init__(self):
        """Initialize GPU manager with comprehensive configuration"""
        with self._lock:
            if self._initialized:
                return
                
            # Configuration from environment
            self._gpu_count = int(os.getenv("GPU_COUNT", "1"))
            self._memory_limit = self._parse_memory_limit(os.getenv("GPU_MEMORY_LIMIT"))
            self._enable_gpus = os.getenv("ENABLE_GPUS", "FALSE").upper() == "TRUE"
            self._allocation_timeout = float(os.getenv("GPU_ALLOCATION_TIMEOUT", "30.0"))
            self._cool_down_period = float(os.getenv("GPU_COOL_DOWN_PERIOD", "1.0"))
            
            # Initialize GPU resources
            self._gpus: Dict[int, GPUResource] = {}
            self._waiting_queue: List[Tuple[str, threading.Event]] = []
            
            if self._enable_gpus:
                self._initialize_gpus()
                self._start_monitor()
            
            self._initialized = True
    
    @contextmanager
    def gpu_context(self, owner: str):
        """Context manager for automatic GPU allocation and release"""
        device_id = self.allocate_gpu(owner, wait=True, timeout=30)
        try:
            yield device_id
        finally:
            if device_id is not None:
                self.release_gpu(owner)
    
    def get_gpu_memory_usage(self, device_id: int) -> Dict[str, float]:
        """Get detailed GPU memory statistics"""
        if not torch.cuda.is_available() or device_id >= torch.cuda.device_count():
            return {"error": "GPU not available"}
        
        stats = {}
        stats["total"] = torch.cuda.get_device_properties(device_id).total_memory / (1024**2)
        stats["allocated"] = torch.cuda.memory_allocated(device_id) / (1024**2)
        stats["reserved"] = torch.cuda.memory_reserved(device_id) / (1024**2)
        stats["free"] = stats["total"] - stats["reserved"]
        stats["utilization"] = (stats["allocated"] / stats["total"]) * 100
        
        return stats
```

#### GPU-Accelerated Text Processing
```python
from src.gpu_manager.decorators import gpu_required

class ContextRelevanceAgent(BaseAgent):
    """Agent with GPU-accelerated context relevance scoring"""
    
    @gpu_required(device_param="device_id")
    def extract_relevant_context(
        self, 
        query: str, 
        history: List[Dict[str, Any]], 
        device_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """GPU-accelerated context relevance extraction"""
        
        if device_id is not None and self.use_gpu_similarity:
            try:
                # GPU-accelerated semantic similarity
                semantic_results = self._get_semantic_relevance_gpu(
                    query, history, device_id
                )
                if semantic_results:
                    logger.info(f"Selected {len(semantic_results)} items using GPU semantic similarity")
                    return semantic_results, {
                        "method": "gpu_semantic_similarity",
                        "device_id": device_id,
                        "items_count": len(semantic_results)
                    }
            except Exception as e:
                logger.warning(f"GPU similarity failed: {e}, falling back to CPU")
        
        # CPU fallback with LLM reasoning
        return self._extract_context_with_llm(query, history)
    
    def _get_semantic_relevance_gpu(
        self, 
        query: str, 
        history: List[Dict], 
        device_id: int
    ) -> List[Dict]:
        """GPU-accelerated semantic relevance scoring"""
        from src.gpu_manager.text_utils import text_encoder
        
        # Extract text content from history
        history_texts = [item.get("content", "") for item in history]
        
        # GPU-accelerated similarity computation
        similarities = text_encoder.get_similarities(
            query, history_texts, device_id=device_id
        )
        
        # Select top relevant items
        max_items = self.agent_config.get("max_relevant_items", 5)
        top_indices = similarities.argsort()[-max_items:][::-1]
        
        return [history[i] for i in top_indices if similarities[i] > 0.3]
```

## Multi-Level Memory Architecture

### Three-Tier Memory System

#### L0 Memory (RAM Cache)
```python
class L0Memory:
    """High-speed in-memory cache for immediate context access"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.access_times = {}
        self.default_ttl = default_ttl
        self.performance_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
    
    async def store(self, key: str, data: dict, ttl: int = None):
        """Store data with TTL and LRU eviction"""
        ttl = ttl or self.default_ttl
        
        # Evict expired entries
        await self._cleanup_expired()
        
        # LRU eviction if at capacity
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
            self.performance_stats["evictions"] += 1
        
        # Store new entry
        self.cache[key] = {
            "data": data,
            "expires_at": time.time() + ttl,
            "created_at": time.time()
        }
        self.access_times[key] = time.time()
    
    async def retrieve(self, key: str) -> Optional[dict]:
        """Retrieve data with access time tracking"""
        if key in self.cache:
            entry = self.cache[key]
            
            # Check expiration
            if time.time() > entry["expires_at"]:
                del self.cache[key]
                del self.access_times[key]
                self.performance_stats["misses"] += 1
                return None
            
            # Update access time for LRU
            self.access_times[key] = time.time()
            self.performance_stats["hits"] += 1
            return entry["data"]
        
        self.performance_stats["misses"] += 1
        return None
    
    def get_performance_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.performance_stats["hits"] + self.performance_stats["misses"]
        hit_rate = (self.performance_stats["hits"] / total_requests) * 100 if total_requests > 0 else 0
        
        return {
            **self.performance_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self.cache),
            "max_size": self.max_size
        }
```

#### L1 Memory (SQLite Persistent Cache)
```python
class L1Memory:
    """SQLite-based persistent cache for session data with compression"""
    
    def __init__(self, db_path: str = "data/memory/l1_cache.db"):
        self.db_path = db_path
        self.compression_enabled = True
        asyncio.create_task(self.init_database())
    
    async def init_database(self):
        """Initialize optimized SQLite database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Enable performance optimizations
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=10000")
            await db.execute("PRAGMA temp_store=MEMORY")
            
            # Create optimized schema
            await db.execute("""
                CREATE TABLE IF NOT EXISTS context_cache (
                    key TEXT PRIMARY KEY,
                    data BLOB,
                    created_at INTEGER,
                    accessed_at INTEGER,
                    expires_at INTEGER,
                    priority INTEGER DEFAULT 1,
                    size_bytes INTEGER,
                    compressed BOOLEAN DEFAULT 0
                )
            """)
            
            # Create performance indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_priority 
                ON context_cache(expires_at, priority)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_accessed_cleanup
                ON context_cache(accessed_at) WHERE expires_at < ?
            """, (time.time(),))
            
            await db.commit()
    
    async def store(
        self, 
        key: str, 
        data: dict, 
        ttl: int = 86400,
        priority: int = 1
    ):
        """Store data with optional compression"""
        serialized_data = json.dumps(data).encode('utf-8')
        compressed = False
        
        # Compress if enabled and data is large enough
        if self.compression_enabled and len(serialized_data) > 1024:
            serialized_data = gzip.compress(serialized_data)
            compressed = True
        
        expires_at = time.time() + ttl
        size_bytes = len(serialized_data)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO context_cache 
                (key, data, created_at, accessed_at, expires_at, priority, size_bytes, compressed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                key, serialized_data, time.time(), time.time(), 
                expires_at, priority, size_bytes, compressed
            ))
            await db.commit()
    
    async def retrieve(self, key: str) -> Optional[dict]:
        """Retrieve and decompress data"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT data, compressed, expires_at 
                FROM context_cache 
                WHERE key = ? AND expires_at > ?
            """, (key, time.time())) as cursor:
                
                row = await cursor.fetchone()
                if not row:
                    return None
                
                data_blob, compressed, expires_at = row
                
                # Update access time
                await db.execute("""
                    UPDATE context_cache 
                    SET accessed_at = ? 
                    WHERE key = ?
                """, (time.time(), key))
                await db.commit()
                
                # Decompress if needed
                if compressed:
                    data_blob = gzip.decompress(data_blob)
                
                return json.loads(data_blob.decode('utf-8'))
```

#### L2 Memory (MongoDB Persistent Storage)
```python
class L2Memory:
    """MongoDB-based long-term memory with advanced indexing"""
    
    def __init__(self, mongodb_client):
        self.client = mongodb_client
        self.db = self.client.cognivox_memory
        self.conversations = self.db.conversations
        self.user_profiles = self.db.user_profiles
        self.context_embeddings = self.db.context_embeddings
        self.performance_metrics = self.db.performance_metrics
        
        # Ensure indexes for performance
        asyncio.create_task(self._ensure_indexes())
    
    async def _ensure_indexes(self):
        """Create performance-optimized indexes"""
        try:
            # Conversations indexes
            await self.conversations.create_index([
                ("user_id", 1), ("conversation_id", 1), ("timestamp", -1)
            ])
            await self.conversations.create_index([
                ("user_id", 1), ("timestamp", -1)
            ])
            await self.conversations.create_index([
                ("conversation_id", 1), ("timestamp", -1)
            ])
            
            # User profiles indexes
            await self.user_profiles.create_index([("user_id", 1)])
            await self.user_profiles.create_index([
                ("user_id", 1), ("updated_at", -1)
            ])
            
            # Context embeddings indexes for vector search
            await self.context_embeddings.create_index([("user_id", 1)])
            await self.context_embeddings.create_index([
                ("user_id", 1), ("similarity_score", -1)
            ])
            
            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    async def store_conversation(
        self, 
        user_id: str, 
        conversation_id: str, 
        interaction: dict
    ):
        """Store conversation with intelligent metadata extraction"""
        # Extract enhanced metadata
        metadata = await self._extract_interaction_metadata(interaction)
        
        document = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "timestamp": datetime.utcnow(),
            "message": interaction["message"],
            "response": interaction["response"],
            "intelligence": interaction.get("intelligence", {}),
            "context_used": interaction.get("context_used", 0),
            "processing_time_ms": interaction.get("processing_time_ms", 0),
            "thinking_steps": interaction.get("thinking_steps", []),
            "used_tools": interaction.get("used_tools", []),
            "sources": interaction.get("sources", []),
            "metadata": metadata,
            "performance": {
                "cache_hits": interaction.get("cache_hits", 0),
                "llm_calls": interaction.get("llm_calls", 1),
                "gpu_used": interaction.get("gpu_used", False)
            }
        }
        
        # Store with performance tracking
        start_time = time.time()
        result = await self.conversations.insert_one(document)
        storage_time = (time.time() - start_time) * 1000
        
        # Update user profile with interaction patterns
        await self._update_user_profile(user_id, interaction, storage_time)
        
        return result.inserted_id
```

## LangChain Integration

### Modern LangChain Architecture

#### BaseAgent with LangChain Integration
```python
class BaseAgent:
    """Unified base class with LangChain integration"""
    
    def __init__(
        self,
        agent_name: str,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ):
        """Initialize with configuration-driven LangChain model creation"""
        self.agent_name = agent_name
        self.config = get_config()
        self.agent_config = self.config.get_agent_config(agent_name)
        
        # Override parameters
        self.model_name = model_name
        self.provider = provider
        self.temperature = temperature
        self.kwargs = kwargs
        
        # Create LangChain chat model
        self.llm = self._create_llm()
    
    def _create_llm(self):
        """Create LangChain chat model from configuration"""
        try:
            return create_chat_model_from_config(
                agent_name=self.agent_name,
                provider=self.provider,
                model=self.model_name,
                temperature=self.temperature,
                **self.kwargs
            )
        except Exception as e:
            logger.error(f"Error creating LLM for {self.agent_name}: {str(e)}")
            raise
    
    def update_model(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ):
        """Dynamically update model configuration"""
        if model_name is not None:
            self.model_name = model_name
        if provider is not None:
            self.provider = provider
        
        self.kwargs.update(kwargs)
        self.llm = self._create_llm()
        logger.info(f"{self.agent_name} model updated to {self.model_name}")
        return self
```

#### Configuration-Driven Model Creation
```python
def create_chat_model_from_config(
    agent_name: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **overrides
):
    """Create LangChain chat model from unified configuration"""
    config = get_config()
    
    # Get configuration with overrides
    effective_provider = provider or config.get_default_provider()
    effective_model = model or config.get_default_model()
    
    # Provider-specific model creation
    if effective_provider == "ollama":
        from langchain_ollama import ChatOllama
        
        ollama_config = config.get_provider_config("ollama")
        return ChatOllama(
            model=effective_model,
            base_url=ollama_config.get("base_url", "http://localhost:11434"),
            temperature=overrides.get("temperature", config.get_default_temperature()),
            timeout=ollama_config.get("timeout", 30),
            **overrides
        )
    
    elif effective_provider == "openai":
        from langchain_openai import ChatOpenAI
        
        openai_config = config.get_provider_config("openai")
        return ChatOpenAI(
            model=effective_model,
            api_key=overrides.get("api_key") or os.getenv("OPENAI_API_KEY"),
            base_url=openai_config.get("base_url"),
            temperature=overrides.get("temperature", config.get_default_temperature()),
            **overrides
        )
    
    else:
        raise ValueError(f"Unsupported provider: {effective_provider}")
```

#### LangGraph Workflow Integration
```python
from langgraph import StateGraph, END

class ConversationWorkflow:
    """LangGraph-based conversation processing workflow"""
    
    def __init__(self):
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create optimized conversation workflow with state management"""
        workflow = StateGraph(ConversationState)
        
        # Add processing nodes
        workflow.add_node("validate_query", self.validate_query_node)
        workflow.add_node("extract_context", self.extract_context_node)
        workflow.add_node("classify_intent", self.classify_intent_node)
        workflow.add_node("process_with_supervisor", self.supervisor_processing_node)
        workflow.add_node("enhance_response", self.enhance_response_node)
        workflow.add_node("store_memory", self.store_memory_node)
        
        # Add conditional edges with intelligent routing
        workflow.add_edge("validate_query", "extract_context")
        workflow.add_edge("extract_context", "classify_intent")
        workflow.add_edge("classify_intent", "process_with_supervisor")
        workflow.add_edge("process_with_supervisor", "enhance_response")
        workflow.add_edge("enhance_response", "store_memory")
        workflow.add_edge("store_memory", END)
        
        # Set entry point
        workflow.set_entry_point("validate_query")
        
        return workflow.compile()
    
    async def validate_query_node(self, state: ConversationState) -> ConversationState:
        """Query validation with security checks"""
        validation = await self.query_validator.validate_query(state.message)
        state.validation_result = validation
        state.is_valid = validation.get('isValid', False)
        state.processed_steps.append("query_validated")
        
        if not state.is_valid:
            state.error_message = validation.get('description', 'Query validation failed')
        
        return state
    
    async def supervisor_processing_node(self, state: ConversationState) -> ConversationState:
        """SupervisorReAct agent processing with tool integration"""
        if not state.is_valid:
            return state
        
        context_prompt = self._prepare_context_prompt(state)
        
        result = await self.supervisor_agent.chat(
            user_message=state.message,
            user_id=state.user_id,
            context_prompt=context_prompt,
            return_thinking=True
        )
        
        state.response = result.get("response", "")
        state.thinking_steps = result.get("thinking_steps", [])
        state.used_tools = result.get("used_tools", [])
        state.sources = result.get("sources", [])
        state.processed_steps.append("supervisor_processed")
        
        return state
```

## Advanced Performance Features

### Cost Reduction and Optimization

#### Performance Tracking System
```python
class PerformanceTracker:
    """Advanced performance monitoring and cost optimization tracking"""
    
    def __init__(self):
        self.metrics = {
            "llm_calls_saved": 0,
            "cache_hits": {"L0": 0, "L1": 0, "L2": 0},
            "gpu_operations": 0,
            "processing_time_saved": 0,
            "memory_efficiency": 0,
            "cost_savings": 0
        }
        self.start_time = time.time()
    
    async def track_supervisor_efficiency(self, query_type: str, used_tools: List[str]):
        """Track SupervisorReAct agent efficiency"""
        # Traditional multi-agent approach: 3-5 LLM calls
        # SupervisorReAct approach: 1-2 LLM calls
        traditional_calls = 4 if query_type == "complex" else 3
        actual_calls = len(used_tools) + 1  # Tools + final response
        
        calls_saved = max(0, traditional_calls - actual_calls)
        self.metrics["llm_calls_saved"] += calls_saved
        
        # Estimate cost savings (assuming $0.001 per call)
        cost_saved = calls_saved * 0.001
        self.metrics["cost_savings"] += cost_saved
        
        logger.info(f"LLM calls saved: {calls_saved}, Total saved: {self.metrics['llm_calls_saved']}")
    
    async def track_cache_performance(self, cache_level: str, hit: bool, data_size: int = 0):
        """Track cache performance across memory levels"""
        if hit:
            self.metrics["cache_hits"][cache_level] += 1
            
            # Calculate time saved based on cache level
            time_saved = {
                "L0": 0.001,   # 1ms - RAM access
                "L1": 0.01,    # 10ms - SQLite access
                "L2": 0.1      # 100ms - MongoDB access
            }.get(cache_level, 0)
            
            self.metrics["processing_time_saved"] += time_saved
            
            # Track memory efficiency
            if data_size > 0:
                efficiency_gain = min(data_size / 1024, 10)  # Cap at 10KB
                self.metrics["memory_efficiency"] += efficiency_gain
    
    async def track_gpu_usage(self, operation_type: str, device_id: Optional[int] = None):
        """Track GPU usage and performance benefits"""
        self.metrics["gpu_operations"] += 1
        
        if device_id is not None:
            # GPU acceleration typically 10-100x faster for similarity calculations
            time_saved = 0.5  # Conservative estimate: 500ms saved per operation
            self.metrics["processing_time_saved"] += time_saved
            
            logger.info(f"GPU operation completed on device {device_id}")
    
    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary"""
        uptime = time.time() - self.start_time
        total_cache_hits = sum(self.metrics["cache_hits"].values())
        
        return {
            "uptime_seconds": round(uptime, 2),
            "llm_calls_saved": self.metrics["llm_calls_saved"],
            "total_cache_hits": total_cache_hits,
            "cache_breakdown": self.metrics["cache_hits"],
            "gpu_operations": self.metrics["gpu_operations"],
            "processing_time_saved_seconds": round(self.metrics["processing_time_saved"], 3),
            "estimated_cost_savings_usd": round(self.metrics["cost_savings"], 4),
            "memory_efficiency_score": round(self.metrics["memory_efficiency"], 2),
            "performance_improvement": self._calculate_performance_improvement()
        }
    
    def _calculate_performance_improvement(self) -> str:
        """Calculate overall performance improvement percentage"""
        baseline_operations = 100  # Baseline assumption
        optimized_operations = baseline_operations - self.metrics["llm_calls_saved"]
        
        if optimized_operations > 0:
            improvement = ((baseline_operations - optimized_operations) / baseline_operations) * 100
            return f"{improvement:.1f}%"
        return "0%"
```

#### Smart Caching Strategy
```python
class SmartCacheManager:
    """Intelligent multi-level caching with automatic promotion"""
    
    def __init__(self):
        self.l0_memory = L0Memory(max_size=1000)
        self.l1_memory = L1Memory()
        self.l2_memory = L2Memory()
        self.performance_tracker = PerformanceTracker()
    
    async def get_cached_response(
        self, 
        query_hash: str, 
        context_hash: str = None
    ) -> Optional[dict]:
        """Intelligent cache retrieval with automatic promotion"""
        
        # Try L0 (RAM) first - fastest access
        cache_key = f"{query_hash}:{context_hash}" if context_hash else query_hash
        
        response = await self.l0_memory.retrieve(cache_key)
        if response:
            await self.performance_tracker.track_cache_performance("L0", True)
            return response
        
        # Try L1 (SQLite) - medium speed
        response = await self.l1_memory.retrieve(cache_key)
        if response:
            # Promote to L0 for faster future access
            await self.l0_memory.store(cache_key, response, ttl=1800)
            await self.performance_tracker.track_cache_performance("L1", True)
            return response
        
        # Try L2 (MongoDB) - comprehensive but slower
        response = await self.l2_memory.retrieve_similar_interaction(cache_key)
        if response:
            # Promote to both L1 and L0
            await self.l1_memory.store(cache_key, response, ttl=7200)
            await self.l0_memory.store(cache_key, response, ttl=1800)
            await self.performance_tracker.track_cache_performance("L2", True)
            return response
        
        return None
    
    async def store_response(
        self, 
        query_hash: str, 
        response: dict, 
        importance: int = 1,
        context_hash: str = None
    ):
        """Store response across appropriate cache levels based on importance"""
        cache_key = f"{query_hash}:{context_hash}" if context_hash else query_hash
        
        # Always store in L2 for persistence and learning
        await self.l2_memory.store(cache_key, response)
        
        # Store in L1 based on importance (1-3 scale)
        if importance >= 2:
            await self.l1_memory.store(cache_key, response, ttl=7200)
        
        # Store in L0 for immediate reuse
        if importance >= 1:
            await self.l0_memory.store(cache_key, response, ttl=1800)
        
        logger.debug(f"Stored response in {importance} cache levels")
```

## Service Integration

### GraphRAG Integration

#### Enhanced GraphRAG Client
```python
class GraphRAGClient:
    """Enhanced GraphRAG service client with retry logic and optimization"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("GRAPHRAG_API_URL", "http://localhost:8003")
        self.timeout = aiohttp.ClientTimeout(total=60, connect=10)
        self.session = None
        self.retry_config = {
            "max_retries": 3,
            "backoff_factor": 0.3,
            "status_forcelist": [500, 502, 503, 504]
        }
        
    async def search(
        self,
        query: str,
        user_id: str,
        n_results: int = 5,
        mode: str = "hybrid"
    ) -> Dict[str, Any]:
        """Search knowledge base with enhanced error handling"""
        
        try:
            session = await self._get_session()
            
            payload = {
                "query": query,
                "user_id": user_id,
                "n_results": n_results,
                "mode": mode,
                "include_sources": True,
                "include_metadata": True
            }
            
            async with session.post(
                f"{self.base_url}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"GraphRAG search successful: {len(result.get('sources', []))} sources")
                    return result
                else:
                    error_text = await response.text()
                    logger.warning(f"GraphRAG search failed: HTTP {response.status} - {error_text}")
                    return {
                        "response": "No relevant information found in the knowledge base.",
                        "sources": [],
                        "error": True
                    }
                    
        except Exception as e:
            logger.error(f"GraphRAG service error: {str(e)}")
            return {
                "response": "Knowledge search service is currently unavailable.",
                "sources": [],
                "error": True
            }
    
    async def _get_session(self):
        """Get or create HTTP session with connection pooling"""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
        return self.session
```

#### GraphRAG Tool for SupervisorReAct Agent
```python
def create_graphrag_tool(graphrag_client: GraphRAGClient) -> Tool:
    """Create GraphRAG search tool for SupervisorReAct agent"""
    
    async def graphrag_search(query: str, user_id: str, n_results: int = 5) -> str:
        """Search knowledge base and return formatted results"""
        try:
            result = await graphrag_client.search(
                query=query,
                user_id=user_id,
                n_results=n_results
            )
            
            if result.get("error"):
                return result.get("response", "Search failed")
            
            response = result.get("response", "")
            sources = result.get("sources", [])
            
            # Store sources for extraction by agent
            graphrag_search.last_result = {
                "response": response,
                "sources": sources,
                "query": query
            }
            
            return response
            
        except Exception as e:
            logger.error(f"GraphRAG tool error: {str(e)}")
            return "Knowledge search is currently unavailable."
    
    # Add method to clear previous results
    graphrag_search.last_result = None
    graphrag_search.clear_last_result = lambda: setattr(graphrag_search, 'last_result', None)
    
    return Tool(
        name="graphrag_search",
        description="Search the knowledge base for specific information, documents, or expert knowledge. Use when the user asks about specific topics that might be in the knowledge base.",
        func=graphrag_search
    )
```

## Health Monitoring

### Comprehensive Health Check System

#### Service Health Monitoring
```python
class HealthMonitor:
    """Comprehensive health monitoring for Memory service and dependencies"""
    
    def __init__(self):
        self.start_time = time.time()
        self.health_cache = {}
        self.cache_ttl = 30  # 30 seconds cache
    
    async def comprehensive_health_check(self) -> dict:
        """Perform comprehensive health check with dependency validation"""
        start_time = time.time()
        
        health_status = {
            "status": "healthy",
            "service": "CogniVox Memory Service",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": int(time.time() - self.start_time),
            "dependencies": {},
            "performance": {},
            "gpu": {},
            "memory": {}
        }
        
        # Check MongoDB connectivity and performance
        mongo_health = await self._check_mongodb_health()
        health_status["dependencies"]["mongodb"] = mongo_health
        
        # Check Ollama LLM service
        ollama_health = await self._check_ollama_health()
        health_status["dependencies"]["ollama"] = ollama_health
        
        # Check GraphRAG service
        graphrag_health = await self._check_graphrag_health()
        health_status["dependencies"]["graphrag"] = graphrag_health
        
        # Check GPU status if enabled
        gpu_status = await self._check_gpu_status()
        health_status["gpu"] = gpu_status
        
        # Memory and performance metrics
        memory_status = await self._check_memory_status()
        health_status["memory"] = memory_status
        
        # Performance metrics
        performance = await self._get_performance_metrics()
        health_status["performance"] = performance
        
        # Overall status determination
        if any(dep.get("status") == "unhealthy" for dep in health_status["dependencies"].values()):
            health_status["status"] = "degraded"
        
        health_status["response_time_ms"] = int((time.time() - start_time) * 1000)
        
        return health_status
    
    async def _check_mongodb_health(self) -> dict:
        """Check MongoDB health with detailed metrics"""
        try:
            from src.memory.chat_memory import chat_memory
            
            start_time = time.time()
            
            # Test basic connectivity
            await chat_memory.client.admin.command('ping')
            
            # Get database statistics
            db_stats = await chat_memory.db.command('dbStats')
            
            # Get collection information
            collections = await chat_memory.db.list_collection_names()
            
            response_time = int((time.time() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "collections": len(collections),
                "database_size_mb": round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                "document_count": db_stats.get('objects', 0),
                "connection_status": "connected"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": 5000
            }
    
    async def _check_gpu_status(self) -> dict:
        """Check GPU availability and status"""
        try:
            from src.gpu_manager import GPUManager
            
            gpu_manager = GPUManager()
            
            if not gpu_manager.is_gpu_enabled():
                return {
                    "enabled": False,
                    "status": "disabled",
                    "message": "GPU acceleration is disabled"
                }
            
            gpu_status = {
                "enabled": True,
                "status": "healthy",
                "devices": []
            }
            
            # Get status for each GPU
            for device_id in range(gpu_manager._gpu_count):
                if device_id in gpu_manager._gpus:
                    gpu_resource = gpu_manager._gpus[device_id]
                    memory_stats = gpu_manager.get_gpu_memory_usage(device_id)
                    
                    device_status = {
                        "device_id": device_id,
                        "status": gpu_resource.status.name,
                        "owner": gpu_resource.owner,
                        "memory_mb": memory_stats,
                        "usage_count": gpu_resource.usage_count,
                        "total_usage_time": round(gpu_resource.total_usage_time, 2)
                    }
                    
                    gpu_status["devices"].append(device_status)
            
            return gpu_status
            
        except Exception as e:
            return {
                "enabled": False,
                "status": "error",
                "error": str(e)
            }
```

## Configuration Management

### Unified Configuration System

#### YAML-Based Configuration
```yaml
# config.yaml - Production-ready configuration
llm:
  default_provider: "ollama"
  default_model: "qwen3:4b"  # Optimized for performance
  default_temperature: 0.1   # Low for consistent responses
  default_timeout: 30
  
  ollama:
    base_url: "http://localhost:11434"
    models: ["qwen3:4b", "llama3.1", "mistral"]
    timeout: 30

agents:
  supervisor_react:
    provider: "ollama"
    model: "qwen3:4b"
    temperature: 0.1
    max_iterations: 3
    early_stopping: true
    thinking_timeout: 5
  
  context_relevance:
    provider: "ollama"
    model: "llama3.1"
    temperature: 0.2
    use_gpu_similarity: true
    max_relevant_items: 5

gpu:
  enable_gpu_acceleration: true
  device_ids: [0]
  fallback_to_cpu: true
  memory_limit_gb: 8
  cool_down_period: 1.0
  allocation_timeout: 30.0

memory:
  chat_memory:
    max_messages_per_chat: 1000
    cleanup_interval_hours: 24
    enable_compression: true
  
  cache:
    l0_max_size: 1000
    l0_default_ttl: 3600
    l1_default_ttl: 86400
    enable_l1_compression: true

performance:
  enable_monitoring: true
  track_cost_savings: true
  log_slow_queries: true
  slow_query_threshold: 10.0
```

---

## Conclusion

The CogniVox Agentic Memory Service represents a cutting-edge conversational AI engine that combines intelligent decision-making, GPU optimization, and sophisticated memory management. This technical documentation provides comprehensive coverage of the service's advanced capabilities, from UV-based setup to GPU acceleration and intelligent agent coordination.

### Key Technical Achievements
- **SupervisorReAct Agent**: Intelligent tool usage decisions reducing LLM calls by 40-60%
- **GPU Optimization Framework**: Singleton GPU manager with allocation tracking and CPU fallback
- **Multi-Level Memory System**: L0/L1/L2 hierarchy with smart caching and automatic promotion
- **UV Package Management**: Revolutionary setup speed with AI/ML dependency optimization
- **LangChain Integration**: Modern architecture with LangGraph workflows and unified configuration
- **Performance Monitoring**: Comprehensive tracking of cost savings, cache efficiency, and resource utilization

### Production Readiness Features
- **Health Monitoring**: Real-time dependency validation and performance metrics
- **Error Handling**: Comprehensive fallback mechanisms and graceful degradation
- **Configuration Management**: Unified YAML-based configuration with environment overrides
- **Resource Management**: Intelligent GPU allocation and memory optimization
- **Service Integration**: Robust GraphRAG integration with retry logic and optimization

### Future Enhancement Opportunities
- **Advanced Caching**: Machine learning-based cache eviction and promotion strategies
- **Multi-GPU Support**: Distributed GPU processing for large-scale deployments
- **Enhanced Analytics**: Advanced user behavior tracking and conversation pattern analysis
- **Real-time Learning**: Adaptive agent behavior based on user interaction patterns
- **Edge Deployment**: Optimization for edge computing environments with limited resources

For detailed information about other system components, refer to:
- [Complete System Documentation](./CogniVox_Complete_System_Documentation.md)
- [Backend Documentation](./CogniVox_Agentic_Backend_Technical_Documentation.md)
- [Frontend Documentation](./CogniVox_Agentic_Frontend_Technical_Documentation.md)
- [GraphRAG Documentation](./CogniVox_Agentic_GraphRAG_Technical_Documentation.md) 