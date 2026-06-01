```mermaid
graph TD
    Start([User Query]) --> API[FastAPI Endpoint<br/>/api/chat]
    
    API --> Auth[Extract Auth Token<br/>User ID: 10]
    Auth --> Mode{Response Mode?}
    
    Mode -->|agentic| StartThinking[Start Thinking Process<br/>agentic_processing]
    
    StartThinking --> Context[Fetch Context<br/>SQLite Cache]
    Context --> Cache{Cache Hit?}
    Cache -->|Yes| MemHit[Memory Cache Hit<br/>~0ms]
    Cache -->|No| MemFetch[Fetch from MongoDB<br/>threads & sub_threads]
    
    MemHit --> Router[Response Mode Router]
    MemFetch --> Router
    
    Router --> Orchestrator[Multi-Agent Orchestrator<br/>Workflow Start]
    
    Orchestrator --> QueryAnalyzer[Query Analysis Agent<br/>Model: qwen2.5:7b<br/>Temp: 0.1]
    
    QueryAnalyzer --> MCPFetch[Fetch MCP Capabilities<br/>4 tools, 2 resources, 1 prompt]
    
    MCPFetch --> Analysis{Query Analysis Result}
    
    Analysis -->|GraphRAG=True| GraphRAGAgent[GraphRAG Agent<br/>Execute KB Search]
    Analysis -->|MCP=True| MCPAgent[MCP Agent<br/>Execute Tool Calls]
    
    GraphRAGAgent --> GraphRAGService[GraphRAG Service<br/>http://localhost:8003/query]
    
    GraphRAGService --> StorageInit[Initialize Storage Manager<br/>Local: Bucket/users/10]
    
    StorageInit --> VectorDB[ChromaDB Client<br/>Collection: documents]
    
    VectorDB --> HybridSearch[Hybrid Search<br/>Semantic: 0.6<br/>Keyword: 0.4]
    
    HybridSearch --> UserFilter[User-Specific Filter<br/>user_id: 10]
    
    UserFilter --> SemanticSearch[Semantic Search<br/>Vector Embeddings<br/>Top 10 Results]
    
    SemanticSearch --> KeywordSearch[Keyword Search<br/>Optimized Parallel<br/>Multiple Keywords]
    
    KeywordSearch --> Combine[Combine & Rank Results<br/>Weighted Scoring]
    
    Combine --> Results[Return 2-4 Sources<br/>With Metadata]
    
    Results --> ResponseSynthesis[Response Synthesis Agent<br/>Model: gemma2:2b<br/>Temp: 0.7]
    
    MCPAgent --> ResponseSynthesis
    
    ResponseSynthesis --> Validator{Validator<br/>Enabled?}
    
    Validator -->|Disabled| FinalResponse[Final Response<br/>~48-60 seconds]
    Validator -->|Enabled| ValidateAgent[Validation Agent<br/>gemma2:2b]
    
    ValidateAgent --> FinalResponse
    
    FinalResponse --> FormatSources[Format Source Documents<br/>document_title, content,<br/>page, relevance, file_path]
    
    FormatSources --> StoreMemory[Store Interaction<br/>SQLite + MongoDB<br/>~15ms]
    
    StoreMemory --> UpdateCache[Update Memory Cache<br/>L0 ChatMemory]
    
    UpdateCache --> ThinkingComplete[Finish Thinking Process<br/>Status: success]
    
    ThinkingComplete --> Response[Send Response to Frontend<br/>source_found: True<br/>sources: 2-4<br/>tools_used: graphrag_search]
    
    Response --> End([User Receives Response])
    
    ```