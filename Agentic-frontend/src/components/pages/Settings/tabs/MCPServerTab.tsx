import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "../../../../contexts/ThemeContext";
import { toast } from "react-hot-toast";
import {
  FiServer,
  FiPlus,
  FiEdit3,
  FiTrash2,
  FiRefreshCw,
  FiCheck,
  FiX,
  FiAlertCircle,
  FiPlay,
  FiTool,
  FiDatabase,
  FiFileText,
  FiChevronRight,
  FiPower,
} from "react-icons/fi";
import {
  mcpApi,
  MCPServerConfig,
  MCPTool,
  MCPResource,
  MCPPrompt,
} from "../../../../services/mcpApi";

const MCPServerTab: React.FC = () => {
  const { isDarkMode } = useTheme();
  const [servers, setServers] = useState<MCPServerConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedServer, setSelectedServer] = useState<MCPServerConfig | null>(
    null
  );
  const [testingServer, setTestingServer] = useState<number | null>(null);
  const [syncingServer, setSyncingServer] = useState<number | null>(null);
  const [togglingServer, setTogglingServer] = useState<number | null>(null);
  const [expandedServer, setExpandedServer] = useState<number | null>(null);
  const [serverTools, setServerTools] = useState<Record<number, MCPTool[]>>({});
  const [serverResources, setServerResources] = useState<
    Record<number, MCPResource[]>
  >({});
  const [serverPrompts, setServerPrompts] = useState<
    Record<number, MCPPrompt[]>
  >({});
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [selectedResource, setSelectedResource] = useState<MCPResource | null>(
    null
  );
  const [selectedPrompt, setSelectedPrompt] = useState<MCPPrompt | null>(null);
  const [showToolModal, setShowToolModal] = useState(false);
  const [showResourceModal, setShowResourceModal] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);

  // Form state
  const [formData, setFormData] = useState<Partial<MCPServerConfig>>({
    name: "",
    description: "",
    server_type: "stdio",
    command: "",
    url: "",
    args: [],
    env_vars: {},
    is_active: true,
    auto_connect: true,
    require_approval: false,
    timeout: 30,
  });

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const data = await mcpApi.listServers();
      console.log("MCP Servers response:", data);
      setServers(data);
    } catch (error) {
      console.error("Failed to load MCP servers:", error);
      setServers([]);
      toast.error("Failed to load MCP servers");
    } finally {
      setLoading(false);
    }
  };

  const loadServerTools = async (serverId: number) => {
    try {
      const tools = await mcpApi.listTools(serverId, true);
      setServerTools((prev) => ({ ...prev, [serverId]: tools }));
    } catch (error) {
      console.error("Failed to load tools:", error);
      setServerTools((prev) => ({ ...prev, [serverId]: [] }));
    }
  };

  const loadServerResources = async (serverId: number) => {
    try {
      const resources = await mcpApi.listResources(serverId);
      setServerResources((prev) => ({ ...prev, [serverId]: resources }));
    } catch (error) {
      console.error("Failed to load resources:", error);
      setServerResources((prev) => ({ ...prev, [serverId]: [] }));
    }
  };

  const loadServerPrompts = async (serverId: number) => {
    try {
      const prompts = await mcpApi.listPrompts(serverId);
      setServerPrompts((prev) => ({ ...prev, [serverId]: prompts }));
    } catch (error) {
      console.error("Failed to load prompts:", error);
      setServerPrompts((prev) => ({ ...prev, [serverId]: [] }));
    }
  };

  const handleTestConnection = async (serverId: number) => {
    setTestingServer(serverId);
    try {
      const result = await mcpApi.testConnection(serverId);
      if (result.success) {
        toast.success(result.message);
        loadServers();
      } else {
        toast.error(result.error || "Connection test failed");
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to test connection");
    } finally {
      setTestingServer(null);
    }
  };

  const handleSyncServer = async (serverId: number) => {
    setSyncingServer(serverId);
    try {
      const result = await mcpApi.syncServer(serverId);
      if (result.success) {
        toast.success(
          `Synced ${result.tools_synced} tools, ${result.resources_synced} resources, ${result.prompts_synced} prompts`
        );
        loadServers();
        // Reload all data for this server
        loadServerTools(serverId);
        loadServerResources(serverId);
        loadServerPrompts(serverId);
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to sync server");
    } finally {
      setSyncingServer(null);
    }
  };

  const handleToggleActive = async (serverId: number) => {
    try {
      setTogglingServer(serverId);
      const result = await mcpApi.toggleServerActive(serverId);
      toast.success(result.message);
      await loadServers();
    } catch (error: any) {
      console.error("Failed to toggle server status:", error);
      toast.error(error.message || "Failed to toggle server status");
    } finally {
      setTogglingServer(null);
    }
  };

  const handleSaveServer = async () => {
    try {
      if (selectedServer) {
        await mcpApi.updateServer(selectedServer.id!, formData);
        toast.success("Server updated");
      } else {
        await mcpApi.createServer(formData);
        toast.success("Server created");
      }
      setShowAddModal(false);
      setSelectedServer(null);
      loadServers();
      resetForm();
    } catch (error: any) {
      toast.error(error.message || "Failed to save server");
    }
  };

  const handleDeleteServer = async (serverId: number) => {
    if (!confirm("Delete this server?")) return;

    try {
      await mcpApi.deleteServer(serverId);
      toast.success("Server deleted");
      loadServers();
    } catch (error: any) {
      toast.error(error.message || "Failed to delete");
    }
  };

  const handleEditServer = (server: MCPServerConfig) => {
    setSelectedServer(server);
    setFormData(server);
    setShowAddModal(true);
  };

  const resetForm = () => {
    setFormData({
      name: "",
      description: "",
      server_type: "stdio",
      command: "",
      url: "",
      args: [],
      env_vars: {},
      is_active: true,
      auto_connect: true,
      require_approval: false,
      timeout: 30,
    });
  };

  const toggleExpanded = (serverId: number) => {
    const newExpanded = expandedServer === serverId ? null : serverId;
    setExpandedServer(newExpanded);
    if (newExpanded) {
      if (!serverTools[serverId]) {
        loadServerTools(serverId);
      }
      if (!serverResources[serverId]) {
        loadServerResources(serverId);
      }
      if (!serverPrompts[serverId]) {
        loadServerPrompts(serverId);
      }
    }
  };

  const handleToolClick = (tool: MCPTool) => {
    setSelectedTool(tool);
    setShowToolModal(true);
  };

  const handleResourceClick = (resource: MCPResource) => {
    setSelectedResource(resource);
    setShowResourceModal(true);
  };

  const handlePromptClick = (prompt: MCPPrompt) => {
    setSelectedPrompt(prompt);
    setShowPromptModal(true);
  };

  // Helper to get dynamic counts
  const getToolCount = (serverId: number) => {
    return serverTools[serverId]?.length || 0;
  };

  const getResourceCount = (serverId: number) => {
    return serverResources[serverId]?.length || 0;
  };

  const getPromptCount = (serverId: number) => {
    return serverPrompts[serverId]?.length || 0;
  };

  // Calculate total counts across all servers
  const getTotalToolCount = () => {
    return Object.values(serverTools).reduce(
      (sum, tools) => sum + (tools?.length || 0),
      0
    );
  };

  const getTotalResourceCount = () => {
    return Object.values(serverResources).reduce(
      (sum, resources) => sum + (resources?.length || 0),
      0
    );
  };

  const getTotalPromptCount = () => {
    return Object.values(serverPrompts).reduce(
      (sum, prompts) => sum + (prompts?.length || 0),
      0
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "text-green-500";
      case "error":
        return "text-red-500";
      case "connecting":
        return "text-yellow-500";
      default:
        return isDarkMode ? "text-gray-500" : "text-gray-400";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <FiCheck className="w-3 h-3" />;
      case "error":
        return <FiX className="w-3 h-3" />;
      case "connecting":
        return <FiRefreshCw className="w-3 h-3 animate-spin" />;
      default:
        return <FiAlertCircle className="w-3 h-3" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      transition={{ duration: 0.2 }}
      className="space-y-4"
    >
      {/* Header */}
      <div
        className={`p-3 rounded-lg border ${
          isDarkMode
            ? "bg-gray-800/30 border-gray-700/30"
            : "bg-white border-gray-200"
        }`}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2.5">
            <div
              className={`p-1.5 rounded-lg ${
                isDarkMode ? "bg-purple-600/20" : "bg-purple-100"
              }`}
            >
              <FiServer
                className={`w-4 h-4 ${
                  isDarkMode ? "text-purple-400" : "text-purple-600"
                }`}
              />
            </div>
            <div>
              <h2
                className={`text-base font-semibold ${
                  isDarkMode ? "text-gray-100" : "text-gray-900"
                }`}
              >
                MCP Servers
              </h2>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => {
              setSelectedServer(null);
              resetForm();
              setShowAddModal(true);
            }}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors"
          >
            <FiPlus className="w-3 h-3" />
            Add Server
          </motion.button>
        </div>
        {/* Total Counts */}
        <div
          className={`flex items-center gap-4 pt-2 border-t ${
            isDarkMode ? "border-gray-700/30" : "border-gray-200"
          }`}
        >
          <div
            className={`flex items-center gap-1.5 text-xs ${
              isDarkMode ? "text-gray-400" : "text-gray-600"
            }`}
          >
            <FiTool className="w-3.5 h-3.5" />
            <span className="font-medium">{getTotalToolCount()}</span>
            <span>Tools</span>
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs ${
              isDarkMode ? "text-gray-400" : "text-gray-600"
            }`}
          >
            <FiDatabase className="w-3.5 h-3.5" />
            <span className="font-medium">{getTotalResourceCount()}</span>
            <span>Resources</span>
          </div>
          <div
            className={`flex items-center gap-1.5 text-xs ${
              isDarkMode ? "text-gray-400" : "text-gray-600"
            }`}
          >
            <FiFileText className="w-3.5 h-3.5" />
            <span className="font-medium">{getTotalPromptCount()}</span>
            <span>Prompts</span>
          </div>
        </div>
      </div>

      {/* Server List */}
      <div className="space-y-2">
        {loading ? (
          <div
            className={`p-8 rounded-lg border flex items-center justify-center ${
              isDarkMode
                ? "bg-gray-800/30 border-gray-700/30"
                : "bg-white border-gray-200"
            }`}
          >
            <FiRefreshCw
              className={`w-5 h-5 animate-spin ${
                isDarkMode ? "text-purple-400" : "text-purple-600"
              }`}
            />
          </div>
        ) : servers.length === 0 ? (
          <div
            className={`p-8 rounded-lg border text-center ${
              isDarkMode
                ? "bg-gray-800/30 border-gray-700/30 border-dashed"
                : "bg-white border-gray-300 border-dashed"
            }`}
          >
            <FiServer
              className={`w-8 h-8 mx-auto mb-2 ${
                isDarkMode ? "text-gray-600" : "text-gray-400"
              }`}
            />
            <p
              className={`text-sm font-medium ${
                isDarkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              No servers configured
            </p>
            <p
              className={`text-xs mt-1 ${
                isDarkMode ? "text-gray-500" : "text-gray-500"
              }`}
            >
              Add your first MCP server to get started
            </p>
          </div>
        ) : (
          servers.map((server) => (
            <motion.div
              key={server.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-lg border ${
                isDarkMode
                  ? "bg-gray-800/30 border-gray-700/30"
                  : "bg-white border-gray-200"
              }`}
            >
              {/* Server Header */}
              <div className="p-2">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <h3
                        className={`text-xs font-semibold truncate ${
                          isDarkMode ? "text-gray-100" : "text-gray-900"
                        }`}
                      >
                        {server.name}
                      </h3>
                      <span
                        className={`inline-flex items-center gap-0.5 px-1 py-0.5 rounded text-[10px] font-medium ${getStatusColor(
                          server.connection_status || "disconnected"
                        )} ${isDarkMode ? "bg-gray-700/50" : "bg-gray-100"}`}
                      >
                        {getStatusIcon(
                          server.connection_status || "disconnected"
                        )}
                        {server.connection_status || "off"}
                      </span>
                      <span
                        className={`px-1 py-0.5 rounded text-[10px] ${
                          isDarkMode
                            ? "bg-gray-700 text-gray-400"
                            : "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {server.server_type}
                      </span>
                    </div>
                    <div className="flex items-center gap-2.5 text-[10px]">
                      <div
                        className={`flex items-center gap-0.5 ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        }`}
                      >
                        <FiTool className="w-2.5 h-2.5" />
                        <span className="font-medium">
                          {getToolCount(server.id!) || server.tool_count || 0}
                        </span>
                      </div>
                      <div
                        className={`flex items-center gap-0.5 ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        }`}
                      >
                        <FiDatabase className="w-2.5 h-2.5" />
                        <span className="font-medium">
                          {getResourceCount(server.id!) ||
                            server.resource_count ||
                            0}
                        </span>
                      </div>
                      <div
                        className={`flex items-center gap-0.5 ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        }`}
                      >
                        <FiFileText className="w-2.5 h-2.5" />
                        <span className="font-medium">
                          {getPromptCount(server.id!) ||
                            server.prompt_count ||
                            0}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-0.5 ml-2">
                    {/* Toggle Active/Inactive */}
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleToggleActive(server.id!)}
                      disabled={togglingServer === server.id}
                      className={`p-1 rounded transition-colors ${
                        server.is_active
                          ? isDarkMode
                            ? "bg-green-900/30 text-green-400 hover:bg-green-900/50"
                            : "bg-green-100 text-green-600 hover:bg-green-200"
                          : isDarkMode
                          ? "bg-red-900/30 text-red-400 hover:bg-red-900/50"
                          : "bg-red-100 text-red-600 hover:bg-red-200"
                      }`}
                      title={
                        server.is_active ? "Disable Server" : "Enable Server"
                      }
                    >
                      {togglingServer === server.id ? (
                        <FiRefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <FiPower className="w-3 h-3" />
                      )}
                    </motion.button>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleTestConnection(server.id!)}
                      disabled={
                        testingServer === server.id || !server.is_active
                      }
                      className={`p-1 rounded transition-colors ${
                        !server.is_active
                          ? "opacity-40 cursor-not-allowed"
                          : isDarkMode
                          ? "hover:bg-gray-700 text-gray-400 hover:text-green-400"
                          : "hover:bg-gray-100 text-gray-600 hover:text-green-600"
                      }`}
                      title={
                        !server.is_active
                          ? "Server is disabled"
                          : "Test Connection"
                      }
                    >
                      {testingServer === server.id ? (
                        <FiRefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <FiPlay className="w-3 h-3" />
                      )}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleSyncServer(server.id!)}
                      disabled={
                        syncingServer === server.id || !server.is_active
                      }
                      className={`p-1 rounded transition-colors ${
                        !server.is_active
                          ? "opacity-40 cursor-not-allowed"
                          : isDarkMode
                          ? "hover:bg-gray-700 text-gray-400 hover:text-blue-400"
                          : "hover:bg-gray-100 text-gray-600 hover:text-blue-600"
                      }`}
                      title={
                        !server.is_active ? "Server is disabled" : "Sync Server"
                      }
                    >
                      {syncingServer === server.id ? (
                        <FiRefreshCw className="w-3 h-3 animate-spin" />
                      ) : (
                        <FiRefreshCw className="w-3 h-3" />
                      )}
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleEditServer(server)}
                      className={`p-1 rounded transition-colors ${
                        isDarkMode
                          ? "hover:bg-gray-700 text-gray-400 hover:text-purple-400"
                          : "hover:bg-gray-100 text-gray-600 hover:text-purple-600"
                      }`}
                      title="Edit"
                    >
                      <FiEdit3 className="w-3 h-3" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => handleDeleteServer(server.id!)}
                      className={`p-1 rounded transition-colors ${
                        isDarkMode
                          ? "hover:bg-gray-700 text-gray-400 hover:text-red-400"
                          : "hover:bg-gray-100 text-gray-600 hover:text-red-600"
                      }`}
                      title="Delete"
                    >
                      <FiTrash2 className="w-3 h-3" />
                    </motion.button>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => toggleExpanded(server.id!)}
                      className={`p-1 rounded transition-colors ${
                        isDarkMode
                          ? "hover:bg-gray-700 text-gray-400"
                          : "hover:bg-gray-100 text-gray-600"
                      }`}
                      title="Details"
                    >
                      <FiChevronRight
                        className={`w-3 h-3 transition-transform ${
                          expandedServer === server.id ? "rotate-90" : ""
                        }`}
                      />
                    </motion.button>
                  </div>
                </div>
              </div>

              {/* Expanded Tools View */}
              <AnimatePresence>
                {expandedServer === server.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div
                      className={`border-t px-2 py-1.5 ${
                        isDarkMode ? "border-gray-700/50" : "border-gray-200"
                      }`}
                    >
                      <h4
                        className={`text-[10px] font-semibold mb-1.5 flex items-center gap-1 ${
                          isDarkMode ? "text-gray-300" : "text-gray-700"
                        }`}
                      >
                        <FiTool
                          className={`w-3 h-3 ${
                            isDarkMode ? "text-purple-400" : "text-purple-600"
                          }`}
                        />
                        Tools ({getToolCount(server.id!)})
                      </h4>
                      {serverTools[server.id!] ? (
                        serverTools[server.id!].length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {serverTools[server.id!].map((tool) => (
                              <div
                                key={tool.id}
                                onClick={() => handleToolClick(tool)}
                                className={`px-1.5 py-1 rounded text-[10px] cursor-pointer transition-all border ${
                                  isDarkMode
                                    ? "bg-purple-900/20 border-purple-700/30 hover:bg-purple-900/30 text-purple-300"
                                    : "bg-purple-50 border-purple-200 hover:bg-purple-100 text-purple-700"
                                }`}
                              >
                                <div className="flex items-center gap-1">
                                  <span className="font-medium truncate max-w-[120px]">
                                    {tool.tool_name}
                                  </span>
                                  <div
                                    className={`w-1 h-1 rounded-full flex-shrink-0 ${
                                      tool.is_enabled
                                        ? "bg-green-500"
                                        : "bg-gray-400"
                                    }`}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p
                            className={`text-[10px] text-center py-1.5 ${
                              isDarkMode ? "text-gray-500" : "text-gray-500"
                            }`}
                          >
                            No tools found
                          </p>
                        )
                      ) : (
                        <div className="flex justify-center py-1.5">
                          <FiRefreshCw className="w-3 h-3 animate-spin text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Resources Section */}
                    <div
                      className={`border-t px-2 py-1.5 ${
                        isDarkMode ? "border-gray-700/50" : "border-gray-200"
                      }`}
                    >
                      <h4
                        className={`text-[10px] font-semibold mb-1.5 flex items-center gap-1 ${
                          isDarkMode ? "text-gray-300" : "text-gray-700"
                        }`}
                      >
                        <FiDatabase
                          className={`w-3 h-3 ${
                            isDarkMode ? "text-blue-400" : "text-blue-600"
                          }`}
                        />
                        Resources ({serverResources[server.id!]?.length || 0})
                      </h4>
                      {serverResources[server.id!] !== undefined ? (
                        serverResources[server.id!].length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {serverResources[server.id!].map((resource) => (
                              <div
                                key={resource.id}
                                onClick={() => handleResourceClick(resource)}
                                className={`px-1.5 py-1 rounded text-[10px] cursor-pointer transition-all border ${
                                  isDarkMode
                                    ? "bg-blue-900/20 border-blue-700/30 hover:bg-blue-900/30 text-blue-300"
                                    : "bg-blue-50 border-blue-200 hover:bg-blue-100 text-blue-700"
                                }`}
                              >
                                <div className="flex items-center gap-1">
                                  <span className="font-medium truncate max-w-[120px]">
                                    {resource.resource_name}
                                  </span>
                                  <div
                                    className={`w-1 h-1 rounded-full flex-shrink-0 ${
                                      resource.is_enabled
                                        ? "bg-green-500"
                                        : "bg-gray-400"
                                    }`}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p
                            className={`text-[10px] text-center py-1.5 ${
                              isDarkMode ? "text-gray-500" : "text-gray-500"
                            }`}
                          >
                            No resources found
                          </p>
                        )
                      ) : (
                        <div className="flex justify-center py-1.5">
                          <FiRefreshCw className="w-3 h-3 animate-spin text-gray-400" />
                        </div>
                      )}
                    </div>

                    {/* Prompts Section */}
                    <div
                      className={`border-t px-2 py-1.5 ${
                        isDarkMode ? "border-gray-700/50" : "border-gray-200"
                      }`}
                    >
                      <h4
                        className={`text-[10px] font-semibold mb-1.5 flex items-center gap-1 ${
                          isDarkMode ? "text-gray-300" : "text-gray-700"
                        }`}
                      >
                        <FiFileText
                          className={`w-3 h-3 ${
                            isDarkMode ? "text-purple-400" : "text-purple-600"
                          }`}
                        />
                        Prompts ({serverPrompts[server.id!]?.length || 0})
                      </h4>
                      {serverPrompts[server.id!] !== undefined ? (
                        serverPrompts[server.id!].length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {serverPrompts[server.id!].map((prompt) => (
                              <div
                                key={prompt.id}
                                onClick={() => handlePromptClick(prompt)}
                                className={`px-1.5 py-1 rounded text-[10px] cursor-pointer transition-all border ${
                                  isDarkMode
                                    ? "bg-purple-900/20 border-purple-700/30 hover:bg-purple-900/30 text-purple-300"
                                    : "bg-purple-50 border-purple-200 hover:bg-purple-100 text-purple-700"
                                }`}
                              >
                                <div className="flex items-center gap-1">
                                  <span className="font-medium truncate max-w-[120px]">
                                    {prompt.prompt_name}
                                  </span>
                                  <div
                                    className={`w-1 h-1 rounded-full flex-shrink-0 ${
                                      prompt.is_enabled
                                        ? "bg-green-500"
                                        : "bg-gray-400"
                                    }`}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <p
                            className={`text-[10px] text-center py-1.5 ${
                              isDarkMode ? "text-gray-500" : "text-gray-500"
                            }`}
                          >
                            No prompts found
                          </p>
                        )
                      ) : (
                        <div className="flex justify-center py-1.5">
                          <FiRefreshCw className="w-3 h-3 animate-spin text-gray-400" />
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>

      {/* Tool Details Modal */}
      <AnimatePresence>
        {showToolModal && selectedTool && (
          <ToolDetailsModal
            tool={selectedTool}
            onClose={() => {
              setShowToolModal(false);
              setSelectedTool(null);
            }}
            isDarkMode={isDarkMode}
          />
        )}
      </AnimatePresence>

      {/* Resource Details Modal */}
      <AnimatePresence>
        {showResourceModal && selectedResource && (
          <ResourceDetailsModal
            resource={selectedResource}
            onClose={() => {
              setShowResourceModal(false);
              setSelectedResource(null);
            }}
            isDarkMode={isDarkMode}
          />
        )}
      </AnimatePresence>

      {/* Prompt Details Modal */}
      <AnimatePresence>
        {showPromptModal && selectedPrompt && (
          <PromptDetailsModal
            prompt={selectedPrompt}
            onClose={() => {
              setShowPromptModal(false);
              setSelectedPrompt(null);
            }}
            isDarkMode={isDarkMode}
          />
        )}
      </AnimatePresence>

      {/* Add/Edit Modal */}
      <AnimatePresence>
        {showAddModal && (
          <ServerFormModal
            server={selectedServer}
            formData={formData}
            setFormData={setFormData}
            onSave={handleSaveServer}
            onCancel={() => {
              setShowAddModal(false);
              setSelectedServer(null);
              resetForm();
            }}
            isDarkMode={isDarkMode}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
};

// Tool Details Modal Component
const ToolDetailsModal: React.FC<{
  tool: MCPTool;
  onClose: () => void;
  isDarkMode: boolean;
}> = ({ tool, onClose, isDarkMode }) => {
  const renderSchema = (schema: any, level = 0): React.ReactNode => {
    if (!schema || typeof schema !== "object") {
      return (
        <span className="text-[10px] text-gray-500">{String(schema)}</span>
      );
    }

    if (schema.type === "object" && schema.properties) {
      const indentLevel = level * 8; // 8px per level
      return (
        <div className="space-y-0.5" style={{ marginLeft: `${indentLevel}px` }}>
          {Object.entries(schema.properties).map(
            ([key, value]: [string, any]) => (
              <div key={key} className="border-l border-gray-300 pl-1.5">
                <div className="flex items-start gap-1">
                  <span
                    className={`font-mono font-semibold text-[10px] ${
                      isDarkMode ? "text-purple-400" : "text-purple-600"
                    }`}
                  >
                    {key}
                  </span>
                  {schema.required?.includes(key) && (
                    <span className="text-[10px] text-red-400">*</span>
                  )}
                  {value.type && (
                    <span
                      className={`text-[10px] ${
                        isDarkMode ? "text-gray-400" : "text-gray-500"
                      }`}
                    >
                      ({value.type})
                    </span>
                  )}
                </div>
                {value.description && (
                  <p
                    className={`text-[10px] ${
                      isDarkMode ? "text-gray-400" : "text-gray-500"
                    } ml-3`}
                  >
                    {value.description}
                  </p>
                )}
                {value.type === "object" && renderSchema(value, level + 1)}
                {value.type === "array" && value.items && (
                  <div className="ml-3">
                    <span
                      className={`text-[10px] ${
                        isDarkMode ? "text-gray-400" : "text-gray-500"
                      }`}
                    >
                      Array of:
                    </span>
                    {renderSchema(value.items, level + 1)}
                  </div>
                )}
              </div>
            )
          )}
        </div>
      );
    }

    return (
      <pre
        className={`text-[10px] ${
          isDarkMode ? "text-gray-300" : "text-gray-800"
        }`}
      >
        {JSON.stringify(schema, null, 2)}
      </pre>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full max-w-xl max-h-[80vh] overflow-y-auto rounded-lg shadow-xl ${
          isDarkMode ? "bg-gray-800" : "bg-white"
        }`}
      >
        <div
          className={`sticky top-0 z-10 px-3 py-2 border-b flex items-center justify-between ${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <FiTool
              className={`w-4 h-4 ${
                isDarkMode ? "text-purple-400" : "text-purple-600"
              }`}
            />
            <h2
              className={`text-sm font-semibold ${
                isDarkMode ? "text-gray-100" : "text-gray-900"
              }`}
            >
              {tool.tool_name}
            </h2>
          </div>
          <button
            onClick={onClose}
            className={`p-0.5 rounded transition-colors ${
              isDarkMode
                ? "hover:bg-gray-700 text-gray-400"
                : "hover:bg-gray-200 text-gray-600"
            }`}
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3 space-y-2.5">
          {/* Description */}
          {tool.description && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Description
              </h3>
              <p
                className={`text-xs ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                {tool.description}
              </p>
            </div>
          )}

          {/* Input Schema */}
          {tool.input_schema && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1.5 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Input Parameters
              </h3>
              <div
                className={`p-2 rounded border text-[10px] font-mono overflow-x-auto ${
                  isDarkMode
                    ? "bg-gray-900/50 border-gray-700 text-gray-300"
                    : "bg-gray-50 border-gray-200 text-gray-800"
                }`}
              >
                {tool.input_schema.properties ? (
                  renderSchema(tool.input_schema)
                ) : (
                  <pre>{JSON.stringify(tool.input_schema, null, 2)}</pre>
                )}
              </div>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div
              className={`p-2 rounded border ${
                isDarkMode
                  ? "bg-gray-900/50 border-gray-700"
                  : "bg-gray-50 border-gray-200"
              }`}
            >
              <div
                className={`text-[10px] ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Usage Count
              </div>
              <div
                className={`text-sm font-semibold mt-0.5 ${
                  isDarkMode ? "text-gray-200" : "text-gray-800"
                }`}
              >
                {tool.usage_count}
              </div>
            </div>
            <div
              className={`p-2 rounded border ${
                isDarkMode
                  ? "bg-gray-900/50 border-gray-700"
                  : "bg-gray-50 border-gray-200"
              }`}
            >
              <div
                className={`text-[10px] ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Avg Execution Time
              </div>
              <div
                className={`text-sm font-semibold mt-0.5 ${
                  isDarkMode ? "text-gray-200" : "text-gray-800"
                }`}
              >
                {tool.average_execution_time > 0
                  ? `${tool.average_execution_time.toFixed(2)}s`
                  : "N/A"}
              </div>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-center gap-1.5">
            <span
              className={`text-xs ${
                isDarkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Status:
            </span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                tool.is_enabled
                  ? isDarkMode
                    ? "bg-green-900/30 text-green-400"
                    : "bg-green-100 text-green-700"
                  : isDarkMode
                  ? "bg-gray-700 text-gray-400"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              {tool.is_enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Resource Details Modal Component
const ResourceDetailsModal: React.FC<{
  resource: MCPResource;
  onClose: () => void;
  isDarkMode: boolean;
}> = ({ resource, onClose, isDarkMode }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full max-w-xl max-h-[80vh] overflow-y-auto rounded-lg shadow-xl ${
          isDarkMode ? "bg-gray-800" : "bg-white"
        }`}
      >
        <div
          className={`sticky top-0 z-10 px-3 py-2 border-b flex items-center justify-between ${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <FiDatabase
              className={`w-4 h-4 ${
                isDarkMode ? "text-blue-400" : "text-blue-600"
              }`}
            />
            <h2
              className={`text-sm font-semibold ${
                isDarkMode ? "text-gray-100" : "text-gray-900"
              }`}
            >
              {resource.resource_name}
            </h2>
          </div>
          <button
            onClick={onClose}
            className={`p-0.5 rounded transition-colors ${
              isDarkMode
                ? "hover:bg-gray-700 text-gray-400"
                : "hover:bg-gray-200 text-gray-600"
            }`}
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3 space-y-2.5">
          {/* Description */}
          {resource.description && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Description
              </h3>
              <p
                className={`text-xs ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                {resource.description}
              </p>
            </div>
          )}

          {/* Resource URI */}
          <div>
            <h3
              className={`text-xs font-semibold mb-1.5 ${
                isDarkMode ? "text-gray-300" : "text-gray-700"
              }`}
            >
              Resource URI
            </h3>
            <div
              className={`p-2 rounded border text-[10px] font-mono break-all ${
                isDarkMode
                  ? "bg-gray-900/50 border-gray-700 text-gray-300"
                  : "bg-gray-50 border-gray-200 text-gray-800"
              }`}
            >
              {resource.resource_uri}
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div
              className={`p-2 rounded border ${
                isDarkMode
                  ? "bg-gray-900/50 border-gray-700"
                  : "bg-gray-50 border-gray-200"
              }`}
            >
              <div
                className={`text-[10px] ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Access Count
              </div>
              <div
                className={`text-sm font-semibold mt-0.5 ${
                  isDarkMode ? "text-gray-200" : "text-gray-800"
                }`}
              >
                {resource.access_count}
              </div>
            </div>
            {resource.mime_type && (
              <div
                className={`p-2 rounded border ${
                  isDarkMode
                    ? "bg-gray-900/50 border-gray-700"
                    : "bg-gray-50 border-gray-200"
                }`}
              >
                <div
                  className={`text-[10px] ${
                    isDarkMode ? "text-gray-400" : "text-gray-600"
                  }`}
                >
                  MIME Type
                </div>
                <div
                  className={`text-sm font-semibold mt-0.5 ${
                    isDarkMode ? "text-gray-200" : "text-gray-800"
                  }`}
                >
                  {resource.mime_type}
                </div>
              </div>
            )}
          </div>

          {/* Status */}
          <div className="flex items-center gap-1.5">
            <span
              className={`text-xs ${
                isDarkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Status:
            </span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                resource.is_enabled
                  ? isDarkMode
                    ? "bg-green-900/30 text-green-400"
                    : "bg-green-100 text-green-700"
                  : isDarkMode
                  ? "bg-gray-700 text-gray-400"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              {resource.is_enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Prompt Details Modal Component
const PromptDetailsModal: React.FC<{
  prompt: MCPPrompt;
  onClose: () => void;
  isDarkMode: boolean;
}> = ({ prompt, onClose, isDarkMode }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.95, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full max-w-xl max-h-[80vh] overflow-y-auto rounded-lg shadow-xl ${
          isDarkMode ? "bg-gray-800" : "bg-white"
        }`}
      >
        <div
          className={`sticky top-0 z-10 px-3 py-2 border-b flex items-center justify-between ${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          <div className="flex items-center gap-1.5">
            <FiFileText
              className={`w-4 h-4 ${
                isDarkMode ? "text-purple-400" : "text-purple-600"
              }`}
            />
            <h2
              className={`text-sm font-semibold ${
                isDarkMode ? "text-gray-100" : "text-gray-900"
              }`}
            >
              {prompt.prompt_name}
            </h2>
          </div>
          <button
            onClick={onClose}
            className={`p-0.5 rounded transition-colors ${
              isDarkMode
                ? "hover:bg-gray-700 text-gray-400"
                : "hover:bg-gray-200 text-gray-600"
            }`}
          >
            <FiX className="w-4 h-4" />
          </button>
        </div>

        <div className="p-3 space-y-2.5">
          {/* Description */}
          {prompt.description && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Description
              </h3>
              <p
                className={`text-xs ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                {prompt.description}
              </p>
            </div>
          )}

          {/* Prompt Template */}
          {prompt.prompt_template && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1.5 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Template
              </h3>
              <div
                className={`p-2 rounded border text-[10px] font-mono whitespace-pre-wrap break-words max-h-32 overflow-y-auto ${
                  isDarkMode
                    ? "bg-gray-900/50 border-gray-700 text-gray-300"
                    : "bg-gray-50 border-gray-200 text-gray-800"
                }`}
              >
                {prompt.prompt_template}
              </div>
            </div>
          )}

          {/* Arguments */}
          {prompt.arguments && prompt.arguments.length > 0 && (
            <div>
              <h3
                className={`text-xs font-semibold mb-1.5 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Arguments ({prompt.arguments.length})
              </h3>
              <div className="space-y-1">
                {prompt.arguments.map((arg, index) => (
                  <div
                    key={index}
                    className={`p-1.5 rounded border ${
                      isDarkMode
                        ? "bg-gray-900/50 border-gray-700"
                        : "bg-gray-50 border-gray-200"
                    }`}
                  >
                    <div className="flex items-start gap-1">
                      <span
                        className={`font-mono font-semibold text-[10px] ${
                          isDarkMode ? "text-purple-400" : "text-purple-600"
                        }`}
                      >
                        {arg.name}
                      </span>
                      {arg.required && (
                        <span className="text-[10px] text-red-400">*</span>
                      )}
                    </div>
                    {arg.description && (
                      <p
                        className={`text-[10px] mt-0.5 ${
                          isDarkMode ? "text-gray-400" : "text-gray-600"
                        }`}
                      >
                        {arg.description}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div
              className={`p-2 rounded border ${
                isDarkMode
                  ? "bg-gray-900/50 border-gray-700"
                  : "bg-gray-50 border-gray-200"
              }`}
            >
              <div
                className={`text-[10px] ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Usage Count
              </div>
              <div
                className={`text-sm font-semibold mt-0.5 ${
                  isDarkMode ? "text-gray-200" : "text-gray-800"
                }`}
              >
                {prompt.usage_count}
              </div>
            </div>
            {prompt.last_used_at && (
              <div
                className={`p-2 rounded border ${
                  isDarkMode
                    ? "bg-gray-900/50 border-gray-700"
                    : "bg-gray-50 border-gray-200"
                }`}
              >
                <div
                  className={`text-[10px] ${
                    isDarkMode ? "text-gray-400" : "text-gray-600"
                  }`}
                >
                  Last Used
                </div>
                <div
                  className={`text-xs font-semibold mt-0.5 ${
                    isDarkMode ? "text-gray-200" : "text-gray-800"
                  }`}
                >
                  {new Date(prompt.last_used_at).toLocaleDateString()}
                </div>
              </div>
            )}
          </div>

          {/* Status */}
          <div className="flex items-center gap-1.5">
            <span
              className={`text-xs ${
                isDarkMode ? "text-gray-400" : "text-gray-600"
              }`}
            >
              Status:
            </span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                prompt.is_enabled
                  ? isDarkMode
                    ? "bg-green-900/30 text-green-400"
                    : "bg-green-100 text-green-700"
                  : isDarkMode
                  ? "bg-gray-700 text-gray-400"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              {prompt.is_enabled ? "Enabled" : "Disabled"}
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

// Compact Server Form Modal Component
const ServerFormModal: React.FC<{
  server: MCPServerConfig | null;
  formData: Partial<MCPServerConfig>;
  setFormData: React.Dispatch<React.SetStateAction<Partial<MCPServerConfig>>>;
  onSave: () => void;
  onCancel: () => void;
  isDarkMode: boolean;
}> = ({ server, formData, setFormData, onSave, onCancel, isDarkMode }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onCancel}
    >
      <motion.div
        initial={{ scale: 0.95, y: 10 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        onClick={(e) => e.stopPropagation()}
        className={`w-full max-w-md max-h-[85vh] overflow-y-auto rounded-xl shadow-2xl ${
          isDarkMode ? "bg-gray-800" : "bg-white"
        }`}
      >
        <div className="sticky top-0 z-10 px-4 py-3 border-b backdrop-blur-sm bg-opacity-90 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}">
          <h2
            className={`text-lg font-bold ${
              isDarkMode ? "text-gray-100" : "text-gray-900"
            }`}
          >
            {server ? "Edit Server" : "Add Server"}
          </h2>
        </div>

        <div className="p-4 space-y-3">
          {/* Name */}
          <div>
            <label
              className={`block text-xs font-medium mb-1 ${
                isDarkMode ? "text-gray-300" : "text-gray-700"
              }`}
            >
              Server Name *
            </label>
            <input
              type="text"
              value={formData.name || ""}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              className={`w-full px-3 py-1.5 text-sm rounded-lg border ${
                isDarkMode
                  ? "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500"
                  : "bg-white border-gray-300 text-gray-900 focus:border-purple-500"
              } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
              placeholder="My MCP Server"
            />
          </div>

          {/* Description */}
          <div>
            <label
              className={`block text-xs font-medium mb-1 ${
                isDarkMode ? "text-gray-300" : "text-gray-700"
              }`}
            >
              Description
            </label>
            <textarea
              value={formData.description || ""}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              rows={2}
              className={`w-full px-3 py-1.5 text-sm rounded-lg border ${
                isDarkMode
                  ? "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500"
                  : "bg-white border-gray-300 text-gray-900 focus:border-purple-500"
              } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
              placeholder="Optional description"
            />
          </div>

          {/* Type */}
          <div>
            <label
              className={`block text-xs font-medium mb-1 ${
                isDarkMode ? "text-gray-300" : "text-gray-700"
              }`}
            >
              Server Type *
            </label>
            <select
              value={formData.server_type || "stdio"}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  server_type: e.target.value as "stdio" | "sse" | "http",
                })
              }
              className={`w-full px-3 py-1.5 text-sm rounded-lg border ${
                isDarkMode
                  ? "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500"
                  : "bg-white border-gray-300 text-gray-900 focus:border-purple-500"
              } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
            >
              <option value="stdio">Standard I/O</option>
              <option value="sse">Server-Sent Events</option>
              <option value="http">HTTP/REST</option>
            </select>
          </div>

          {/* Command or URL */}
          {formData.server_type === "stdio" ? (
            <div>
              <label
                className={`block text-xs font-medium mb-1 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Command *
              </label>
              <input
                type="text"
                value={formData.command || ""}
                onChange={(e) =>
                  setFormData({ ...formData, command: e.target.value })
                }
                className={`w-full px-3 py-1.5 text-sm rounded-lg border font-mono ${
                  isDarkMode
                    ? "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500"
                    : "bg-white border-gray-300 text-gray-900 focus:border-purple-500"
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
                placeholder="node server.js"
              />
            </div>
          ) : (
            <div>
              <label
                className={`block text-xs font-medium mb-1 ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                URL *
              </label>
              <input
                type="url"
                value={formData.url || ""}
                onChange={(e) =>
                  setFormData({ ...formData, url: e.target.value })
                }
                className={`w-full px-3 py-1.5 text-sm rounded-lg border ${
                  isDarkMode
                    ? "bg-gray-700 border-gray-600 text-gray-100 focus:border-purple-500"
                    : "bg-white border-gray-300 text-gray-900 focus:border-purple-500"
                } focus:outline-none focus:ring-2 focus:ring-purple-500/20`}
                placeholder="https://api.example.com"
              />
            </div>
          )}

          {/* Options */}
          <div className="space-y-1.5 pt-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.is_active !== false}
                onChange={(e) =>
                  setFormData({ ...formData, is_active: e.target.checked })
                }
                className="w-3.5 h-3.5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span
                className={`text-xs ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Active
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.auto_connect !== false}
                onChange={(e) =>
                  setFormData({ ...formData, auto_connect: e.target.checked })
                }
                className="w-3.5 h-3.5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span
                className={`text-xs ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Auto-connect on startup
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.require_approval === true}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    require_approval: e.target.checked,
                  })
                }
                className="w-3.5 h-3.5 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <span
                className={`text-xs ${
                  isDarkMode ? "text-gray-300" : "text-gray-700"
                }`}
              >
                Require approval before executing
              </span>
            </label>
          </div>
        </div>

        {/* Actions */}
        <div
          className={`sticky bottom-0 flex items-center justify-end gap-2 px-4 py-3 border-t backdrop-blur-sm bg-opacity-90 ${
            isDarkMode
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onCancel}
            className={`px-3 py-1.5 text-sm rounded-lg font-medium ${
              isDarkMode
                ? "bg-gray-700 hover:bg-gray-600 text-gray-300"
                : "bg-gray-200 hover:bg-gray-300 text-gray-700"
            }`}
          >
            Cancel
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSave}
            className="px-3 py-1.5 text-sm rounded-lg font-medium bg-purple-600 hover:bg-purple-700 text-white"
          >
            {server ? "Update" : "Create"}
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default MCPServerTab;
