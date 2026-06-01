import time
import functools
import logging
import json
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime

# Configure logger with a modern formatter
class ModernFormatter(logging.Formatter):
    """Modern log formatter with cleaner output and color support for console."""
    
    COLORS = {
        'HEADER': '\033[95m',
        'INFO': '\033[94m',
        'SUCCESS': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'RESET': '\033[0m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m'
    }
    
    def format(self, record):
        """Format log records with timestamp, level, and structured information."""
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        
        # Extract structured data if available
        structured_data = {}
        if hasattr(record, 'structured_data') and record.structured_data:
            structured_data = record.structured_data
            
        # Format the basic message
        formatted_message = f"{timestamp} | {self.COLORS['BOLD']}{record.levelname}{self.COLORS['RESET']} | {record.name}"
        
        # Add memory level information if available
        memory_level = structured_data.get('memory_level', '')
        operation = structured_data.get('operation', '')
        
        if memory_level:
            formatted_message += f" | {self.COLORS['INFO']}Memory:{self.COLORS['RESET']} {memory_level}"
            
        if operation:
            formatted_message += f" | {self.COLORS['INFO']}Op:{self.COLORS['RESET']} {operation}"
        
        # Add execution time if available
        if hasattr(record, 'execution_time'):
            color = self.COLORS['SUCCESS'] if record.execution_time < 1.0 else (
                self.COLORS['WARNING'] if record.execution_time < 5.0 else self.COLORS['ERROR']
            )
            formatted_message += f" | {color}Time:{self.COLORS['RESET']} {record.execution_time:.4f}s"
        
        # Add the main message
        formatted_message += f" | {record.getMessage()}"
        
        # Add optional structured data in JSON format for debugging/detailed logs
        if structured_data and record.levelno <= logging.DEBUG:
            formatted_message += f"\n  {json.dumps(structured_data, indent=2)}"
            
        return formatted_message

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('performance')

# Add console handler with the modern formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(ModernFormatter())
logger.addHandler(console_handler)

# Add file handler with JSON formatting for automated processing
file_handler = logging.FileHandler('performance.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Set the logger level
logger.setLevel(logging.INFO)

# Remove handlers from root logger to avoid duplicate messages
logger.propagate = False

def execution_timer(func_name: Optional[str] = None, log_level: int = logging.INFO, 
                   extra_data: Optional[Dict[str, Any]] = None) -> Callable:
    """
    A decorator that measures and logs the execution time of functions with modern formatting.
    
    Args:
        func_name: Optional custom name for the function in logs (defaults to function's name)
        log_level: The logging level to use (default: INFO)
        extra_data: Additional data to include in the log entry
        
    Returns:
        The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get function name (either provided or from the function itself)
            name = func_name if func_name else func.__name__
            
            # Extract memory level information if present in kwargs
            memory_level = kwargs.get('memory_level', None)
            if not memory_level and len(args) > 0 and hasattr(args[0], 'memory_level'):
                memory_level = args[0].memory_level
                
            # Record start time
            start_time = time.time()
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Build structured data
            structured_data = {
                'function': name,
                'execution_time': execution_time
            }
            
            # Add memory level information if available
            if memory_level:
                structured_data['memory_level'] = memory_level
                
            # Add operation type if we can determine it
            if 'operation' in kwargs:
                structured_data['operation'] = kwargs['operation']
                
            # Add any extra provided data
            if extra_data:
                structured_data.update(extra_data)
                
            # Extract memory level information from result if it's there
            if isinstance(result, tuple) and len(result) > 1:
                if isinstance(result[1], dict) and 'memory_levels' in result[1]:
                    memory_levels = result[1].get('memory_levels', [])
                    found_in = result[1].get('found_in', '')
                    structured_data['memory_levels'] = memory_levels
                    structured_data['found_in'] = found_in
                    memory_info = f"using {', '.join(memory_levels)}"
                    if found_in:
                        memory_info += f" (found in {found_in})"
                else:
                    memory_info = ""
            else:
                memory_info = ""
            
            # Create a log record with extra attributes
            log_record = logging.LogRecord(
                name=logger.name,
                level=log_level,
                pathname=func.__code__.co_filename,
                lineno=func.__code__.co_firstlineno,
                msg=f"{name}{' ' + memory_info if memory_info else ''}",
                args=(),
                exc_info=None
            )
            log_record.execution_time = execution_time
            log_record.structured_data = structured_data
            
            # Log using our custom formatter
            logger.handle(log_record)
            
            return result
        return wrapper
    
    # Handle case where decorator is used without arguments
    if callable(func_name):
        func = func_name
        func_name = None
        return decorator(func)
    
    return decorator

def timed_method(func=None, *, extra_data: Optional[Dict[str, Any]] = None):
    """
    A simplified decorator specifically designed for class methods.
    Automatically includes the class name in the log output and detects memory operations.
    
    Args:
        func: The function to decorate
        extra_data: Additional data to include in the log entry
        
    Returns:
        The decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> Any:
            # Get class and method name
            class_name = self.__class__.__name__
            method_name = func.__name__
            full_name = f"{class_name}.{method_name}"
            
            # Extract memory operation information
            operation_type = kwargs.get('operation', '')
            if not operation_type and 'operation' in func.__name__.lower():
                operation_parts = func.__name__.lower().split('_')
                for op in ['retrieve', 'store', 'update', 'delete']:
                    if op in operation_parts:
                        operation_type = op
                        break
            
            # Record start time
            start_time = time.time()
            
            # Execute the function
            result = func(self, *args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Build structured data
            structured_data = {
                'class': class_name,
                'method': method_name,
                'execution_time': execution_time
            }
            
            # Add memory manager information if available
            memory_level = None
            if hasattr(self, 'memory_manager'):
                # If this is a memory agent with levels
                if hasattr(self.memory_manager, '_l0') or hasattr(self.memory_manager, '_l2'):
                    structured_data['has_memory_manager'] = True
            
            # Add operation type if available
            if operation_type:
                structured_data['operation'] = operation_type
                
            # Add extra data if provided
            if extra_data:
                structured_data.update(extra_data)
                
            # Extract memory information from the result if it's there
            memory_info = ""
            if isinstance(result, tuple) and len(result) > 1:
                if isinstance(result[1], dict) and 'memory_levels' in result[1]:
                    memory_levels = result[1].get('memory_levels', [])
                    found_in = result[1].get('found_in', '')
                    structured_data['memory_levels'] = memory_levels
                    structured_data['found_in'] = found_in
                    memory_info = f"using {', '.join(memory_levels)}"
                    if found_in and found_in != "none":
                        memory_info += f" (found in {found_in})"
            
            # Create a log record with extra attributes
            log_record = logging.LogRecord(
                name=logger.name,
                level=logging.INFO,
                pathname=func.__code__.co_filename,
                lineno=func.__code__.co_firstlineno,
                msg=f"{full_name}{' ' + memory_info if memory_info else ''}",
                args=(),
                exc_info=None
            )
            log_record.execution_time = execution_time
            log_record.structured_data = structured_data
            
            # Log using our custom formatter
            logger.handle(log_record)
            
            return result
        return wrapper
    
    # Handle case where decorator is used without arguments
    if func is None:
        return decorator
    return decorator(func) 