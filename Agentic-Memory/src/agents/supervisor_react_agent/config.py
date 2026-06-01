"""
Performance configuration for the Supervisor ReAct Agent.
"""
from typing import Dict, Any

# Performance-optimized configuration for the Supervisor ReAct Agent
SUPERVISOR_REACT_CONFIG = {
    # Model configuration for optimal performance
    "model": {
        "name": "qwen3:4b",  # Fast, capable model
        "temperature": 0.1,   # Low temperature for more consistent, faster responses
        "max_tokens": 1000,   # Reasonable limit to prevent overly long responses
        "timeout": 30         # 30 second timeout for tool calls
    },
    
    # Agent execution configuration - OPTIMIZED for speed
    "agent": {
        "max_iterations": 2,           # Reduced from 3 to 2 to prevent long chains
        "early_stopping": True,        # Stop early when possible
        "verbose": False,              # Disable verbose logging in production
        "handle_parsing_errors": True, # Gracefully handle parsing errors
        "max_context_length": 2000,    # Reduced from 4000 for faster processing
        "thinking_timeout": 3,         # Reduced from 5s to 3s for faster decisions
        "total_timeout": 150,          # Increased to accommodate full GraphRAG processing pipeline
        "tool_timeout": 120            # Increased to match GraphRAG timeout needs
    },
    
    # Tool configuration - OPTIMIZED for faster responses
    "tools": {
        "graphrag_timeout": 120,       # Increased to handle full GraphRAG processing pipeline
        "max_graphrag_results": 20,     # Increased to 20 for better context coverage
        "enable_tool_caching": True,   # Cache tool results when possible
        "max_tool_retries": 2,         # Balanced retries for Qwen3:4b
        "fail_fast": True              # Fail fast instead of long retries
    },
    
    # Context management
    "context": {
        "max_history_length": 10,      # Limit conversation history
        "max_context_tokens": 2000,    # Limit total context tokens
        "prioritize_recent": True,     # Prioritize recent messages
        "compress_history": True       # Compress older history
    },
    
    # Performance monitoring
    "monitoring": {
        "enable_timing": True,         # Track timing metrics
        "log_slow_queries": True,      # Log queries that take too long
        "slow_query_threshold": 10.0   # Threshold for slow queries (seconds)
    }
}

def get_performance_config() -> Dict[str, Any]:
    """Get the performance configuration for the Supervisor ReAct Agent."""
    return SUPERVISOR_REACT_CONFIG.copy()

def update_performance_config(updates: Dict[str, Any]):
    """Update the performance configuration with new values."""
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    deep_update(SUPERVISOR_REACT_CONFIG, updates)

# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    "agent": {
        "verbose": True,
        "max_iterations": 5
    },
    "monitoring": {
        "enable_timing": True,
        "log_slow_queries": True,
        "slow_query_threshold": 5.0
    }
}

PRODUCTION_CONFIG = {
    "agent": {
        "verbose": False,
        "max_iterations": 3
    },
    "model": {
        "timeout": 20
    },
    "monitoring": {
        "enable_timing": False,
        "log_slow_queries": True,
        "slow_query_threshold": 15.0
    }
} 
