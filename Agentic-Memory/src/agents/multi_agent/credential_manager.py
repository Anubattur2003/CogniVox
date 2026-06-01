"""
Credential Manager for MCP Servers

Dynamically loads and manages credentials for MCP servers from Django backend.
"""
import logging
import os
import requests
from typing import Dict, Any, Optional
from functools import lru_cache

logger = logging.getLogger("cogniVox")


class CredentialManager:
    """
    Manages MCP server credentials dynamically.
    
    Credentials are stored in Django MCPServerConfig model's env_vars field
    and loaded on-demand for security.
    """
    
    def __init__(self, django_api_url: Optional[str] = None):
        """
        Initialize the credential manager.
        
        Args:
            django_api_url: Django API base URL (defaults to env var)
        """
        self.django_api_url = django_api_url or os.getenv(
            "DJANGO_API_URL",
            "http://localhost:8000"
        )
        # Cache key format: "{user_id}_{server_id}" for user-scoped credentials
        self.credentials_cache: Dict[str, Dict[str, Any]] = {}
    
    def get_server_credentials(
        self,
        server_id: int,
        auth_token: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get credentials for a specific MCP server (RBAC enforced).
        
        Only returns credentials for servers owned by the authenticated user.
        Django backend validates ownership via auth_token.
        
        Args:
            server_id: MCP server configuration ID
            auth_token: JWT authentication token (required for RBAC)
            user_id: Optional user identifier for logging
            
        Returns:
            Dictionary with credentials (env vars, API keys, etc.) - user-scoped
        """
        # Check cache first (credentials are user-scoped via Django RBAC)
        cache_key = f"{user_id}_{server_id}" if user_id else str(server_id)
        if cache_key in self.credentials_cache:
            logger.debug(f"Using cached credentials for server {server_id} (user: {user_id})")
            return self.credentials_cache[cache_key]
        
        try:
            if not auth_token:
                logger.warning(f"Credential Manager: No auth token provided for server {server_id} - RBAC violation prevented")
                return {}
            
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            # Django backend validates user owns this server via auth_token
            response = requests.get(
                f"{self.django_api_url}/api/mcp/servers/{server_id}/",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            server_config = response.json()
            
            # Extract credentials from env_vars field (already filtered by user ownership)
            credentials = server_config.get("env_vars", {})
            
            # Cache credentials with user context
            self.credentials_cache[cache_key] = credentials
            
            logger.info(f"Loaded credentials for MCP server {server_id} (user: {user_id or 'unknown'}) - RBAC enforced")
            return credentials
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning(f"Credential Manager: Access denied to server {server_id} (user: {user_id}) - RBAC violation")
            elif e.response.status_code == 404:
                logger.warning(f"Credential Manager: Server {server_id} not found or not owned by user {user_id}")
            else:
                logger.error(f"Failed to load credentials for server {server_id}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load credentials for server {server_id} (user: {user_id}): {str(e)}")
            return {}
    
    def get_all_user_credentials(
        self,
        user_id: str,
        auth_token: str
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get credentials for all active MCP servers for a user.
        
        Args:
            user_id: User identifier
            auth_token: JWT authentication token
            
        Returns:
            Dictionary mapping server_id to credentials
        """
        try:
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.django_api_url}/api/mcp/servers/",
                headers=headers,
                params={"is_active": "true"},
                timeout=10
            )
            response.raise_for_status()
            
            servers = response.json()
            all_credentials = {}
            
            for server in servers:
                server_id = server.get("id")
                if server_id:
                    credentials = server.get("env_vars", {})
                    all_credentials[server_id] = credentials
                    # Update cache
                    self.credentials_cache[server_id] = credentials
            
            logger.info(f"Loaded credentials for {len(all_credentials)} MCP servers")
            return all_credentials
            
        except Exception as e:
            logger.error(f"Failed to load user credentials: {str(e)}")
            return {}
    
    def clear_cache(self, server_id: Optional[int] = None):
        """
        Clear credentials cache.
        
        Args:
            server_id: Optional server ID to clear. If None, clears all.
        """
        if server_id:
            self.credentials_cache.pop(server_id, None)
            logger.info(f"Cleared credentials cache for server {server_id}")
        else:
            self.credentials_cache.clear()
            logger.info("Cleared all credentials cache")
    
    def inject_credentials(
        self,
        server_config: Dict[str, Any],
        auth_token: str
    ) -> Dict[str, Any]:
        """
        Inject credentials into server configuration.
        
        Args:
            server_config: Server configuration dictionary
            auth_token: JWT authentication token
            
        Returns:
            Server configuration with credentials injected
        """
        server_id = server_config.get("id")
        if not server_id:
            return server_config
        
        # Get credentials
        credentials = self.get_server_credentials(server_id, auth_token)
        
        # Inject into env_vars if not already present
        if credentials and "env_vars" not in server_config:
            server_config["env_vars"] = credentials
        elif credentials:
            # Merge credentials
            existing_env = server_config.get("env_vars", {})
            existing_env.update(credentials)
            server_config["env_vars"] = existing_env
        
        return server_config

