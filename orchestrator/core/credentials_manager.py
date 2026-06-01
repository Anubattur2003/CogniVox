"""
Credentials Management
=====================
Handles credential setup, loading, environment configuration, and export functionality.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Fallback console for systems without Rich
    class Console:
        def print(self, *args, **kwargs):
            print(*args)
        def rule(self, *args, **kwargs):
            print("=" * 60)

logger = logging.getLogger("orchestrator.credentials")


class CredentialsManager:
    """Manages system credentials, environment files, and configuration"""
    
    def __init__(self, console: Console, project_root: Path):
        self.console = console
        self.project_root = project_root
        self.credentials_file = project_root / "credentials.json"
        self.env_file = project_root / ".env"
        self.default_credentials = {}
        self._setup_default_credentials()
    
    def _setup_default_credentials(self):
        """Setup default credentials and service URLs"""
        self.default_credentials = {
            "database": {
                "postgres": {
                    "host": "127.0.0.1",
                    "port": 5432,
                    "database": "cognivox",
                    "username": "cognivox",
                    "password": "cognivox",
                    "url": "postgresql://cognivox:cognivox@127.0.0.1:5432/cognivox"
                },
                "mongodb": {
                    "host": "127.0.0.1",
                    "port": 27017,
                    "database": "cognivox",
                    "username": "cognivox",
                    "password": "cognivox",
                    "admin_username": "cognivox",
                    "admin_password": "cognivox",
                    "url": "mongodb://cognivox:cognivox@127.0.0.1:27017/cognivox?authSource=cognivox",
                    "admin_url": "mongodb://cognivox:cognivox@127.0.0.1:27017"
                },
                "neo4j": {
                    "host": "127.0.0.1",
                    "port": 7474,
                    "bolt_port": 7687,
                    "username": "neo4j",
                    "password": "password",
                    "url": "bolt://neo4j:password@127.0.0.1:7687",
                    "browser_url": "http://127.0.0.1:7474/browser/"
                }
            },
            "llm_services": {
                "ollama": {
                    "host": "127.0.0.1",
                    "port": 11434,
                    "url": "http://127.0.0.1:11434",
                    "api_url": "http://127.0.0.1:11434/api",
                    "models": ["llama3.2:1b", "nomic-embed-text"]
                }
            },
            "application_services": {
                "backend": {
                    "host": "127.0.0.1",
                    "port": 8000,
                    "url": "http://127.0.0.1:8000",
                    "api_url": "http://127.0.0.1:8000/api",
                    "docs_url": "http://127.0.0.1:8000/docs",
                    "health_url": "http://127.0.0.1:8000/health"
                },
                "memory": {
                    "host": "127.0.0.1",
                    "port": 8002,
                    "url": "http://127.0.0.1:8002",
                    "api_url": "http://127.0.0.1:8002/api",
                    "health_url": "http://127.0.0.1:8002/api/health"
                },
                "graphrag": {
                    "host": "127.0.0.1",
                    "port": 8003,
                    "url": "http://127.0.0.1:8003",
                    "api_url": "http://127.0.0.1:8003/api",
                    "health_url": "http://127.0.0.1:8003/health"
                },
                "frontend": {
                    "host": "127.0.0.1",
                    "port": 3000,
                    "url": "http://127.0.0.1:3000"
                }
            },
            "admin_interfaces": {
                "pgadmin": {
                    "host": "127.0.0.1",
                    "port": 5050,
                    "url": "http://127.0.0.1:5050",
                    "email": "admin@admin.com",
                    "password": "admin"
                },
                "neo4j_browser": {
                    "url": "http://127.0.0.1:7474/browser/",
                    "username": "neo4j",
                    "password": "password"
                }
            },
            "api_keys": {
                "openai": {
                    "api_key": "your_openai_api_key_here",
                    "model": "gpt-4"
                },
                "anthropic": {
                    "api_key": "your_anthropic_api_key_here",
                    "model": "claude-3-sonnet-20240229"
                }
            },
            "security": {
                "jwt_secret": "your_jwt_secret_here_change_in_production",
                "session_secret": "your_session_secret_here_change_in_production"
            }
        }

    def get_default_credentials(self) -> Dict[str, Any]:
        """Get the default credentials configuration"""
        return self.default_credentials

    def create_credentials_file(self) -> bool:
        """Create credentials.json file with default values"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(self.default_credentials, f, indent=4)
            self.console.print(f"✅ Created credentials file: {self.credentials_file}", style="green")
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to create credentials file: {e}", style="red")
            return False

    def load_credentials(self) -> bool:
        """Load and merge credentials from file"""
        if not self.credentials_file.exists():
            self.console.print("⚠️  Credentials file not found, creating default...", style="yellow")
            return self.create_credentials_file()
        
        try:
            with open(self.credentials_file, 'r') as f:
                loaded_credentials = json.load(f)
            
            # Merge with defaults to ensure all required keys exist
            self.merge_credentials(self.default_credentials, loaded_credentials)
            self.console.print(f"✅ Loaded credentials from {self.credentials_file}", style="green")
            return True
        except Exception as e:
            self.console.print(f"❌ Failed to load credentials: {e}", style="red")
            return False

    def merge_credentials(self, default: dict, loaded: dict):
        """Recursively merge loaded credentials with defaults"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self.merge_credentials(default[key], value)
            else:
                default[key] = value

    def get_service_urls(self) -> Dict[str, str]:
        """Get all service URLs from credentials"""
        urls = {}
        
        # Application services
        for service_name, config in self.default_credentials.get("application_services", {}).items():
            if "url" in config:
                urls[service_name] = config["url"]
        
        # Database admin interfaces
        for service_name, config in self.default_credentials.get("admin_interfaces", {}).items():
            if "url" in config:
                urls[f"{service_name}_admin"] = config["url"]
        
        # LLM services
        for service_name, config in self.default_credentials.get("llm_services", {}).items():
            if "url" in config:
                urls[service_name] = config["url"]
        
        return urls

    def create_env_file(self) -> bool:
        """Create .env file from credentials"""
        try:
            env_content = []
            env_content.append("# CogniVox Agentic Platform Environment Configuration")
            env_content.append("# Generated automatically from credentials.json")
            env_content.append("")
            
            # Database configurations
            db_config = self.default_credentials.get("database", {})
            
            # PostgreSQL
            postgres = db_config.get("postgres", {})
            env_content.extend([
                "# PostgreSQL Database",
                f"POSTGRES_HOST={postgres.get('host', '127.0.0.1')}",
                f"POSTGRES_PORT={postgres.get('port', 5432)}",
                f"POSTGRES_DB={postgres.get('database', 'cognivox')}",
                f"POSTGRES_USER={postgres.get('username', 'cognivox')}",
                f"POSTGRES_PASSWORD={postgres.get('password', 'cognivox')}",
                f"DATABASE_URL={postgres.get('url', '')}",
                ""
            ])
            
            # MongoDB
            mongodb = db_config.get("mongodb", {})
            env_content.extend([
                "# MongoDB Database",
                f"MONGO_HOST={mongodb.get('host', '127.0.0.1')}",
                f"MONGO_PORT={mongodb.get('port', 27017)}",
                f"MONGO_DATABASE={mongodb.get('database', 'cognivox')}",
                f"MONGO_USERNAME={mongodb.get('username', 'cognivox')}",
                f"MONGO_PASSWORD={mongodb.get('password', 'cognivox')}",
                f"MONGO_URL={mongodb.get('url', '')}",
                ""
            ])
            
            # Neo4j
            neo4j = db_config.get("neo4j", {})
            env_content.extend([
                "# Neo4j Graph Database",
                f"NEO4J_HOST={neo4j.get('host', '127.0.0.1')}",
                f"NEO4J_PORT={neo4j.get('port', 7474)}",
                f"NEO4J_BOLT_PORT={neo4j.get('bolt_port', 7687)}",
                f"NEO4J_USERNAME={neo4j.get('username', 'neo4j')}",
                f"NEO4J_PASSWORD={neo4j.get('password', 'password')}",
                f"NEO4J_URL={neo4j.get('url', '')}",
                ""
            ])
            
            # LLM Services
            llm_config = self.default_credentials.get("llm_services", {})
            ollama = llm_config.get("ollama", {})
            env_content.extend([
                "# Ollama LLM Service",
                f"OLLAMA_HOST={ollama.get('url', 'http://127.0.0.1:11434')}",  # Use full URL instead of just host
                f"OLLAMA_PORT={ollama.get('port', 11434)}",
                f"OLLAMA_URL={ollama.get('url', '')}",
                f"OLLAMA_API_URL={ollama.get('api_url', '')}",
                ""
            ])
            
            # Application Services
            app_config = self.default_credentials.get("application_services", {})
            for service_name, config in app_config.items():
                service_upper = service_name.upper()
                env_content.extend([
                    f"# {service_name.title()} Service",
                    f"{service_upper}_HOST={config.get('host', '127.0.0.1')}",
                    f"{service_upper}_PORT={config.get('port', '')}",
                    f"{service_upper}_URL={config.get('url', '')}",
                    ""
                ])
            
            # API Keys
            api_keys = self.default_credentials.get("api_keys", {})
            env_content.extend([
                "# API Keys (Replace with your actual keys)",
                f"OPENAI_API_KEY={api_keys.get('openai', {}).get('api_key', '')}",
                f"ANTHROPIC_API_KEY={api_keys.get('anthropic', {}).get('api_key', '')}",
                ""
            ])
            
            # Security
            security = self.default_credentials.get("security", {})
            env_content.extend([
                "# Security Configuration",
                f"JWT_SECRET={security.get('jwt_secret', '')}",
                f"SESSION_SECRET={security.get('session_secret', '')}",
                ""
            ])
            
            # Write to file
            with open(self.env_file, 'w') as f:
                f.write('\n'.join(env_content))
            
            self.console.print(f"✅ Created environment file: {self.env_file}", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Failed to create .env file: {e}", style="red")
            return False

    def show_all_credentials(self):
        """Display all credentials in a structured format"""
        if not RICH_AVAILABLE:
            self.console.print("\n=== All Credentials ===")
            self.console.print(json.dumps(self.default_credentials, indent=2))
            return

        # Create a tree structure for better visualization
        tree = Tree("🔐 CogniVox Agentic Platform Credentials")
        
        # Database section
        db_tree = tree.add("🗄️  Database Services")
        for db_name, db_config in self.default_credentials.get("database", {}).items():
            db_node = db_tree.add(f"📊 {db_name.upper()}")
            for key, value in db_config.items():
                if "password" in key.lower() or "secret" in key.lower():
                    db_node.add(f"{key}: {'*' * len(str(value))}")
                else:
                    db_node.add(f"{key}: {value}")
        
        # LLM Services section
        llm_tree = tree.add("🤖 LLM Services")
        for llm_name, llm_config in self.default_credentials.get("llm_services", {}).items():
            llm_node = llm_tree.add(f"🧠 {llm_name.upper()}")
            for key, value in llm_config.items():
                llm_node.add(f"{key}: {value}")
        
        # Application Services section
        app_tree = tree.add("🚀 Application Services")
        for app_name, app_config in self.default_credentials.get("application_services", {}).items():
            app_node = app_tree.add(f"⚙️  {app_name.upper()}")
            for key, value in app_config.items():
                app_node.add(f"{key}: {value}")
        
        # Admin Interfaces section
        admin_tree = tree.add("🔧 Admin Interfaces")
        for admin_name, admin_config in self.default_credentials.get("admin_interfaces", {}).items():
            admin_node = admin_tree.add(f"🌐 {admin_name.upper()}")
            for key, value in admin_config.items():
                if "password" in key.lower():
                    admin_node.add(f"{key}: {'*' * len(str(value))}")
                else:
                    admin_node.add(f"{key}: {value}")
        
        # API Keys section
        api_tree = tree.add("🔑 API Keys")
        for api_name, api_config in self.default_credentials.get("api_keys", {}).items():
            api_node = api_tree.add(f"🌍 {api_name.upper()}")
            for key, value in api_config.items():
                if "key" in key.lower():
                    api_node.add(f"{key}: {'*' * 10}...{str(value)[-4:] if len(str(value)) > 4 else '****'}")
                else:
                    api_node.add(f"{key}: {value}")
        
        panel = Panel(tree, title="System Credentials", border_style="blue")
        self.console.print(panel)

    def show_urls_only(self):
        """Display only service URLs in a clean table"""
        if not RICH_AVAILABLE:
            self.console.print("\n=== Service URLs ===")
            urls = self.get_service_urls()
            for service, url in urls.items():
                self.console.print(f"{service}: {url}")
            return

        table = Table(title="🌐 Service URLs", show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan", no_wrap=True)
        table.add_column("URL", style="blue")
        table.add_column("Status", style="green")

        urls = self.get_service_urls()
        for service_name, url in urls.items():
            # You could add health check status here if needed
            status = "🔗 Available"
            table.add_row(service_name.title(), url, status)

        self.console.print(table)

    def export_credentials(self, format_type: str, filename: str = None) -> bool:
        """Export credentials in different formats"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"cognivox_credentials_{timestamp}.{format_type}"
        
        try:
            if format_type.lower() == "json":
                with open(filename, 'w') as f:
                    json.dump(self.default_credentials, f, indent=4)
            elif format_type.lower() == "env":
                # Flatten credentials to environment variables
                def flatten_dict(d, parent_key='', sep='_'):
                    items = []
                    for k, v in d.items():
                        new_key = f"{parent_key}{sep}{k}".upper() if parent_key else k.upper()
                        if isinstance(v, dict):
                            items.extend(flatten_dict(v, new_key, sep=sep).items())
                        else:
                            items.append((new_key, v))
                    return dict(items)
                
                flat_credentials = flatten_dict(self.default_credentials)
                with open(filename, 'w') as f:
                    f.write("# CogniVox Agentic Platform Credentials Export\n")
                    f.write(f"# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    for key, value in flat_credentials.items():
                        f.write(f"{key}={value}\n")
            else:
                self.console.print(f"❌ Unsupported format: {format_type}", style="red")
                return False
            
            self.console.print(f"✅ Credentials exported to: {filename}", style="green")
            return True
            
        except Exception as e:
            self.console.print(f"❌ Failed to export credentials: {e}", style="red")
            return False

    def validate_configuration(self) -> bool:
        """Validate the current configuration"""
        issues = []
        
        # Check if files exist
        if not self.credentials_file.exists():
            issues.append("❌ credentials.json file missing")
        
        if not self.env_file.exists():
            issues.append("❌ .env file missing")
        
        # Check for placeholder values
        api_keys = self.default_credentials.get("api_keys", {})
        for service, config in api_keys.items():
            api_key = config.get("api_key", "")
            if "your_" in api_key.lower() or "here" in api_key.lower():
                issues.append(f"⚠️  {service} API key appears to be a placeholder")
        
        # Check security settings
        security = self.default_credentials.get("security", {})
        for key, value in security.items():
            if "your_" in str(value).lower() or "here" in str(value).lower():
                issues.append(f"⚠️  {key} appears to be a placeholder")
        
        if issues:
            self.console.print("🔍 Configuration Issues Found:", style="yellow")
            for issue in issues:
                self.console.print(f"  {issue}")
            return False
        else:
            self.console.print("✅ Configuration validation passed", style="green")
            return True 