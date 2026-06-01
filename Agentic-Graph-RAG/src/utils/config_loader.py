"""
Configuration loader utility.
"""
import os
import json
from pathlib import Path
import yaml


class ConfigLoader:
    """
    Configuration loader for loading settings from various sources.
    Priority order:
    1. Environment variables
    2. Configuration file (yaml or json)
    3. Default values
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the configuration loader.
        
        Args:
            config_file: Path to the configuration file.
        """
        self.config = {}
        self.config_file = config_file
        
        # Load default configuration
        self._load_defaults()
        
        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)
            
        # Load from environment variables
        self._load_from_env()
    
    def _load_defaults(self):
        """Load default configuration values."""
        self.config = {
            "db": {
                "type": "neo4j",
                "host": "localhost",
                "port": 7687,
                "user": "neo4j",
                "password": "password",
                "database": "neo4j"
            },
            "vector_store": {
                "type": "chromadb",
                "path": "data/db/chroma"
            },
            "pdf": {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "extraction_method": "auto"
            },
            "storage": {
                "bucket_path": "Bucket"
            },
            "query": {
                "default_mode": "hybrid",
                "default_results": 5
            },
            "visualization": {
                "default_format": "html",
                "node_limit": 100
            },
            "export": {
                "default_format": "json"
            }
        }
    
    def _load_from_file(self, config_file):
        """Load configuration from a file."""
        if not os.path.exists(config_file):
            print(f"Warning: Config file not found: {config_file}")
            return
        
        try:
            file_ext = os.path.splitext(config_file)[1].lower()
            
            if file_ext == '.json':
                with open(config_file, 'r') as f:
                    file_config = json.load(f)
            elif file_ext in ['.yaml', '.yml']:
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
            else:
                print(f"Warning: Unsupported config file format: {file_ext}")
                return
                
            # Update config with file values
            self._update_nested_dict(self.config, file_config)
            
        except Exception as e:
            print(f"Error loading config from file: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # Map of environment variable names to config keys
        env_mapping = {
            "COGNIVOX_DB_TYPE": ["db", "type"],
            "COGNIVOX_DB_HOST": ["db", "host"],
            "COGNIVOX_DB_PORT": ["db", "port"],
            "COGNIVOX_DB_USER": ["db", "user"],
            "COGNIVOX_DB_PASSWORD": ["db", "password"],
            "COGNIVOX_DB_DATABASE": ["db", "database"],
            "COGNIVOX_VECTOR_STORE_TYPE": ["vector_store", "type"],
            "COGNIVOX_VECTOR_STORE_PATH": ["vector_store", "path"],
            "COGNIVOX_PDF_CHUNK_SIZE": ["pdf", "chunk_size"],
            "COGNIVOX_PDF_CHUNK_OVERLAP": ["pdf", "chunk_overlap"],
            "COGNIVOX_PDF_EXTRACTION_METHOD": ["pdf", "extraction_method"],
            "COGNIVOX_QUERY_DEFAULT_MODE": ["query", "default_mode"],
            "COGNIVOX_QUERY_DEFAULT_RESULTS": ["query", "default_results"],
            "COGNIVOX_VISUALIZATION_DEFAULT_FORMAT": ["visualization", "default_format"],
            "COGNIVOX_VISUALIZATION_NODE_LIMIT": ["visualization", "node_limit"],
            "COGNIVOX_EXPORT_DEFAULT_FORMAT": ["export", "default_format"]
        }
        
        # Update config with environment variables
        for env_var, config_path in env_mapping.items():
            if env_var in os.environ:
                self._set_nested_value(self.config, config_path, os.environ[env_var])
    
    def _update_nested_dict(self, d, u):
        """Recursively update a nested dictionary."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._update_nested_dict(d[k], v)
            else:
                d[k] = v
    
    def _set_nested_value(self, d, path, value):
        """Set a value in a nested dictionary using a path."""
        for key in path[:-1]:
            d = d.setdefault(key, {})
        
        # Convert value to the appropriate type
        key = path[-1]
        if key in d:
            if isinstance(d[key], int):
                value = int(value)
            elif isinstance(d[key], float):
                value = float(value)
            elif isinstance(d[key], bool):
                value = value.lower() in ['true', 'yes', '1', 'y']
        
        d[key] = value
    
    def get(self, *keys, default=None):
        """Get a configuration value using a list of keys."""
        value = self.config
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_all(self):
        """Get the entire configuration dictionary."""
        return self.config 