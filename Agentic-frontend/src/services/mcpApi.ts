/**
 * MCP API Service
 *
 * Handles all communication with the Django MCP API endpoints.
 */

// Only frontend is exposed - backend services are internal via proxy
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";
const MCP_ENDPOINT = `${API_BASE_URL}/mcp`;

export interface MCPServerConfig {
  id?: number;
  name: string;
  description?: string;
  server_type: "stdio" | "sse" | "http";
  command?: string;
  url?: string;
  args?: string[];
  env_vars?: Record<string, string>;
  is_active?: boolean;
  auto_connect?: boolean;
  require_approval?: boolean;
  timeout?: number;
  connection_status?: "connected" | "disconnected" | "error" | "connecting";
  error_message?: string;
  last_connected_at?: string;
  last_sync_at?: string;
  tool_count?: number;
  resource_count?: number;
  prompt_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface MCPTool {
  id: number;
  server_id: number;
  server_name: string;
  tool_name: string;
  description?: string;
  input_schema: Record<string, any>;
  is_enabled: boolean;
  usage_count: number;
  last_used_at?: string;
  average_execution_time: number;
}

export interface MCPResource {
  id: number;
  server_id: number;
  server_name: string;
  resource_uri: string;
  resource_name: string;
  description?: string;
  resource_type?: string;
  mime_type?: string;
  is_enabled: boolean;
  access_count: number;
  last_accessed_at?: string;
}

export interface MCPPrompt {
  id: number;
  server_id: number;
  server_name: string;
  prompt_name: string;
  description?: string;
  prompt_template?: string;
  arguments?: Array<{
    name: string;
    description?: string;
    required?: boolean;
  }>;
  is_enabled: boolean;
  usage_count: number;
  last_used_at?: string;
}

export interface MCPExecutionLog {
  id: number;
  user_username: string;
  tool_name: string;
  server_name: string;
  status: "pending" | "running" | "success" | "error" | "cancelled";
  input_params: Record<string, any>;
  output_result?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  execution_time: number;
  chat_thread_id?: string;
}

class MCPApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem("auth_token");
    return {
      "Content-Type": "application/json",
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  // Server Management
  async listServers(): Promise<MCPServerConfig[]> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch servers");
    const data = await response.json();
    // Handle paginated response
    if (data && typeof data === "object" && Array.isArray(data.results)) {
      return data.results;
    }
    // Handle direct array response
    return Array.isArray(data) ? data : [];
  }

  async getServer(id: number): Promise<MCPServerConfig> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/${id}/`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch server");
    return response.json();
  }

  async createServer(
    config: Partial<MCPServerConfig>
  ): Promise<MCPServerConfig> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(config),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to create server");
    }
    return response.json();
  }

  async updateServer(
    id: number,
    config: Partial<MCPServerConfig>
  ): Promise<MCPServerConfig> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/${id}/`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error("Failed to update server");
    return response.json();
  }

  async deleteServer(id: number): Promise<void> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/${id}/`, {
      method: "DELETE",
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to delete server");
  }

  async testConnection(id: number): Promise<{
    success: boolean;
    message: string;
    server_info?: any;
    error?: string;
  }> {
    const response = await fetch(
      `${MCP_ENDPOINT}/servers/${id}/test_connection/`,
      {
        method: "POST",
        headers: this.getAuthHeaders(),
      }
    );
    if (!response.ok) throw new Error("Failed to test connection");
    return response.json();
  }

  async syncServer(id: number): Promise<{
    success: boolean;
    message: string;
    tools_synced: number;
    resources_synced: number;
    prompts_synced: number;
  }> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/${id}/sync/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to sync server");
    return response.json();
  }

  async disconnectServer(
    id: number
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${MCP_ENDPOINT}/servers/${id}/disconnect/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to disconnect server");
    return response.json();
  }

  async toggleServerActive(id: number): Promise<{
    success: boolean;
    message: string;
    server: MCPServerConfig;
  }> {
    const response = await fetch(
      `${MCP_ENDPOINT}/servers/${id}/toggle_active/`,
      {
        method: "POST",
        headers: this.getAuthHeaders(),
      }
    );
    if (!response.ok) throw new Error("Failed to toggle server status");
    return response.json();
  }

  // Tool Management
  async listTools(serverId?: number, isEnabled?: boolean): Promise<MCPTool[]> {
    const params = new URLSearchParams();
    if (serverId !== undefined) params.append("server_id", serverId.toString());
    if (isEnabled !== undefined)
      params.append("is_enabled", isEnabled.toString());

    const response = await fetch(`${MCP_ENDPOINT}/tools/?${params}`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch tools");
    const data = await response.json();
    // Handle paginated response
    if (data && typeof data === "object" && Array.isArray(data.results)) {
      return data.results;
    }
    // Handle direct array response
    return Array.isArray(data) ? data : [];
  }

  async getTool(id: number): Promise<MCPTool> {
    const response = await fetch(`${MCP_ENDPOINT}/tools/${id}/`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch tool");
    return response.json();
  }

  async executeTool(
    id: number,
    arguments_: Record<string, any>,
    chatThreadId?: string
  ): Promise<{
    success: boolean;
    result?: any;
    error?: string;
    execution_time: number;
    execution_id: number;
  }> {
    const response = await fetch(`${MCP_ENDPOINT}/tools/${id}/execute/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({
        tool_id: id,
        arguments: arguments_,
        chat_thread_id: chatThreadId,
      }),
    });
    if (!response.ok) throw new Error("Failed to execute tool");
    return response.json();
  }

  async toggleTool(
    id: number
  ): Promise<{ success: boolean; is_enabled: boolean }> {
    const response = await fetch(`${MCP_ENDPOINT}/tools/${id}/toggle/`, {
      method: "PATCH",
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to toggle tool");
    return response.json();
  }

  // Resource Management
  async listResources(serverId?: number): Promise<MCPResource[]> {
    const params = new URLSearchParams();
    if (serverId !== undefined) params.append("server_id", serverId.toString());

    const response = await fetch(`${MCP_ENDPOINT}/resources/?${params}`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch resources");
    const data = await response.json();
    // Handle paginated response
    if (data && typeof data === "object" && Array.isArray(data.results)) {
      return data.results;
    }
    // Handle direct array response
    return Array.isArray(data) ? data : [];
  }

  async readResource(id: number): Promise<{
    success: boolean;
    content: any;
    resource_uri: string;
    mime_type?: string;
  }> {
    const response = await fetch(`${MCP_ENDPOINT}/resources/${id}/read/`, {
      method: "GET",
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to read resource");
    return response.json();
  }

  // Prompt Management
  async listPrompts(serverId?: number): Promise<MCPPrompt[]> {
    const params = new URLSearchParams();
    if (serverId !== undefined) params.append("server_id", serverId.toString());

    const response = await fetch(`${MCP_ENDPOINT}/prompts/?${params}`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch prompts");
    const data = await response.json();
    // Handle paginated response
    if (data && typeof data === "object" && Array.isArray(data.results)) {
      return data.results;
    }
    // Handle direct array response
    return Array.isArray(data) ? data : [];
  }

  async renderPrompt(
    id: number,
    arguments_: Record<string, any>
  ): Promise<{
    success: boolean;
    rendered_prompt: string;
  }> {
    const response = await fetch(`${MCP_ENDPOINT}/prompts/${id}/render/`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ arguments: arguments_ }),
    });
    if (!response.ok) throw new Error("Failed to render prompt");
    return response.json();
  }

  // Execution Logs
  async listExecutionLogs(filters?: {
    status?: string;
    tool_id?: number;
    chat_thread_id?: string;
  }): Promise<MCPExecutionLog[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append("status", filters.status);
    if (filters?.tool_id) params.append("tool_id", filters.tool_id.toString());
    if (filters?.chat_thread_id)
      params.append("chat_thread_id", filters.chat_thread_id);

    const response = await fetch(`${MCP_ENDPOINT}/logs/?${params}`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch execution logs");
    const data = await response.json();
    // Handle paginated response
    if (data && typeof data === "object" && Array.isArray(data.results)) {
      return data.results;
    }
    // Handle direct array response
    return Array.isArray(data) ? data : [];
  }

  async getExecutionLog(id: number): Promise<MCPExecutionLog> {
    const response = await fetch(`${MCP_ENDPOINT}/logs/${id}/`, {
      headers: this.getAuthHeaders(),
    });
    if (!response.ok) throw new Error("Failed to fetch execution log");
    return response.json();
  }
}

export const mcpApi = new MCPApiService();
