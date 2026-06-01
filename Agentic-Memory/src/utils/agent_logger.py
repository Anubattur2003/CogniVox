"""
Colored logging utility for multi-agent system.

Provides color-coded logging for different agents to improve log readability
without affecting performance or accuracy.
"""
import logging
import sys
from typing import Optional


class AgentColorFormatter(logging.Formatter):
    """
    Custom formatter that adds colors to agent logs.
    Uses ANSI escape codes - lightweight and doesn't require external dependencies.
    """
    
    # ANSI color codes
    COLORS = {
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        
        # Agent-specific colors
        'QUERY_ANALYZER': '\033[36m',      # Cyan
        'GRAPHRAG': '\033[34m',             # Blue
        'MCP_COORDINATOR': '\033[33m',      # Yellow
        'RESPONSE_SYNTHESIZER': '\033[35m', # Magenta
        'VALIDATOR': '\033[32m',            # Green
        'ORCHESTRATOR': '\033[31m',         # Red (for coordination)
        
        # Log level colors
        'DEBUG': '\033[90m',    # Dark gray
        'INFO': '\033[94m',     # Light blue
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
    }
    
    # Agent name mappings
    AGENT_COLORS = {
        'query_analyzer': 'QUERY_ANALYZER',
        'query analysis': 'QUERY_ANALYZER',
        'graphrag': 'GRAPHRAG',
        'graphrag_agent': 'GRAPHRAG',
        'mcp_coordinator': 'MCP_COORDINATOR',
        'mcp coordinator': 'MCP_COORDINATOR',
        'response_synthesizer': 'RESPONSE_SYNTHESIZER',
        'response synthesis': 'RESPONSE_SYNTHESIZER',
        'validator': 'VALIDATOR',
        'validation': 'VALIDATOR',
        'orchestrator': 'ORCHESTRATOR',
        'multi-agent': 'ORCHESTRATOR',
    }
    
    def __init__(self, use_colors: bool = True):
        """
        Initialize the formatter.
        
        Args:
            use_colors: Whether to use colors (False for file output)
        """
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()  # Only color if terminal
    
    def _get_agent_color(self, record: logging.LogRecord) -> str:
        """Determine agent color from log record."""
        # Check message for agent keywords
        message_lower = record.getMessage().lower()
        logger_name_lower = record.name.lower()
        
        for keyword, color_key in self.AGENT_COLORS.items():
            if keyword in message_lower or keyword in logger_name_lower:
                return self.COLORS.get(color_key, '')
        
        return ''
    
    def _get_level_color(self, levelname: str) -> str:
        """Get color for log level."""
        return self.COLORS.get(levelname, '')
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        if not self.use_colors:
            # Return standard format without colors
            return super().format(record)
        
        # Get colors
        agent_color = self._get_agent_color(record)
        level_color = self._get_level_color(record.levelname)
        reset = self.COLORS['RESET']
        bold = self.COLORS['BOLD']
        
        # Format timestamp
        timestamp = self.formatTime(record, self.datefmt)
        
        # Extract agent name
        agent_name = self._extract_agent_name(record)
        
        # Build colored message
        # Format: TIMESTAMP | [AGENT] LEVEL | logger | message
        agent_prefix = ''
        if agent_color and agent_name:
            agent_prefix = f"{agent_color}{bold}[{agent_name}]{reset} "
        
        level_prefix = f"{level_color}{bold}{record.levelname:8s}{reset}"
        
        # Build formatted message
        parts = [timestamp]
        if agent_prefix:
            parts.append(agent_prefix.rstrip())
        parts.append(level_prefix)
        parts.append(f"{record.name}")
        parts.append(record.getMessage())
        
        formatted = " | ".join(parts)
        
        # Add exception info if present
        if record.exc_info:
            formatted += '\n' + self.formatException(record.exc_info)
        
        return formatted
    
    def _extract_agent_name(self, record: logging.LogRecord) -> Optional[str]:
        """Extract agent name from log record."""
        message_lower = record.getMessage().lower()
        logger_name_lower = record.name.lower()
        
        # Priority: Check logger name first (more reliable)
        # Logger names are like "cogniVox.query_analyzer" or "cogniVox.mcp_coordinator"
        if 'query_analyzer' in logger_name_lower or 'query.analyzer' in logger_name_lower:
            return 'QueryAnalyzer'
        elif 'graphrag' in logger_name_lower:
            return 'GraphRAG'
        elif 'mcp_coordinator' in logger_name_lower or 'mcp.coordinator' in logger_name_lower:
            return 'MCPCoordinator'
        elif 'response_synthesizer' in logger_name_lower or 'response.synthesizer' in logger_name_lower:
            return 'ResponseSynthesizer'
        elif 'validator' in logger_name_lower and 'orchestrator' not in logger_name_lower:
            return 'Validator'
        elif 'orchestrator' in logger_name_lower:
            return 'Orchestrator'
        
        # Fallback: Check message content for agent mentions
        if 'query analysis agent' in message_lower or 'query analyzer' in message_lower:
            return 'QueryAnalyzer'
        elif 'graphrag agent' in message_lower or ('graphrag' in message_lower and 'search' in message_lower):
            return 'GraphRAG'
        elif 'mcp coordinator' in message_lower or ('mcp' in message_lower and 'coordinator' in message_lower):
            return 'MCPCoordinator'
        elif 'response synthesis agent' in message_lower or 'response synthesizer' in message_lower:
            return 'ResponseSynthesizer'
        elif 'validation agent' in message_lower or ('validator' in message_lower and 'validating' in message_lower):
            return 'Validator'
        elif 'multi-agent' in message_lower or 'orchestrator' in message_lower:
            return 'Orchestrator'
        
        return None


def setup_agent_logger(logger_name: str = "cogniVox", use_colors: bool = True) -> logging.Logger:
    """
    Setup logger with agent color formatting.
    
    Args:
        logger_name: Name of the logger
        use_colors: Whether to use colors
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(AgentColorFormatter(use_colors=use_colors))
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    
    # Set logger level
    logger.setLevel(logging.INFO)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_agent_logger(agent_name: str, use_colors: bool = True) -> logging.Logger:
    """
    Get a logger for a specific agent with appropriate coloring.
    
    Args:
        agent_name: Name of the agent (e.g., 'query_analyzer', 'mcp_coordinator')
        use_colors: Whether to use colors
        
    Returns:
        Configured logger
    """
    # Use consistent logger name format
    logger = logging.getLogger(f"cogniVox.{agent_name}")
    
    # Only setup if not already configured
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(AgentColorFormatter(use_colors=use_colors))
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    
    return logger

