/**
 * MCP Panel Component
 *
 * A minimal, compact panel that displays MCP tool execution results
 * alongside chat messages in a separate column.
 */
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "../../contexts/ThemeContext";
import {
  FiTool,
  FiCheck,
  FiX,
  FiLoader,
  FiChevronDown,
  FiClock,
  FiServer,
  FiAlertCircle,
} from "react-icons/fi";
import { mcpApi, MCPExecutionLog } from "../../services/mcpApi";

interface MCPPanelProps {
  chatThreadId?: string;
  isOpen?: boolean;
  onToggle?: () => void;
}

const MCPPanel: React.FC<MCPPanelProps> = ({
  chatThreadId,
  isOpen = true,
  onToggle,
}) => {
  const { isDarkMode } = useTheme();
  const [executions, setExecutions] = useState<MCPExecutionLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedExecution, setExpandedExecution] = useState<number | null>(
    null
  );

  useEffect(() => {
    if (isOpen && chatThreadId) {
      loadExecutions();
      // Poll for updates every 5 seconds
      const interval = setInterval(loadExecutions, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen, chatThreadId]);

  const loadExecutions = async () => {
    if (!chatThreadId) return;

    try {
      setLoading(true);
      const logs = await mcpApi.listExecutionLogs({
        chat_thread_id: chatThreadId,
      });
      setExecutions(logs);
    } catch (error) {
      console.error("Failed to load MCP executions:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <FiCheck className="w-4 h-4 text-green-500" />;
      case "error":
        return <FiX className="w-4 h-4 text-red-500" />;
      case "running":
        return <FiLoader className="w-4 h-4 text-blue-500 animate-spin" />;
      case "pending":
        return <FiClock className="w-4 h-4 text-yellow-500" />;
      default:
        return <FiAlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "success":
        return isDarkMode
          ? "bg-green-900/20 border-green-500/30"
          : "bg-green-50 border-green-200";
      case "error":
        return isDarkMode
          ? "bg-red-900/20 border-red-500/30"
          : "bg-red-50 border-red-200";
      case "running":
        return isDarkMode
          ? "bg-blue-900/20 border-blue-500/30"
          : "bg-blue-50 border-blue-200";
      default:
        return isDarkMode
          ? "bg-gray-800/50 border-gray-700"
          : "bg-gray-50 border-gray-200";
    }
  };

  const formatExecutionTime = (time: number) => {
    if (time < 1) return `${(time * 1000).toFixed(0)}ms`;
    return `${time.toFixed(2)}s`;
  };

  if (!isOpen) return null;

  return (
    <div
      className={`h-full flex flex-col border-l ${
        isDarkMode
          ? "border-gray-700 bg-gray-800/50"
          : "border-gray-200 bg-gray-50/50"
      }`}
    >
      {/* Panel Header */}
      <div
        className={`flex items-center justify-between p-4 border-b ${
          isDarkMode ? "border-gray-700" : "border-gray-200"
        }`}
      >
        <div className="flex items-center gap-2">
          <FiTool
            className={`w-5 h-5 ${
              isDarkMode ? "text-purple-400" : "text-purple-600"
            }`}
          />
          <h3
            className={`text-sm font-semibold ${
              isDarkMode ? "text-gray-200" : "text-gray-800"
            }`}
          >
            MCP Tools
          </h3>
          {executions.length > 0 && (
            <span
              className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                isDarkMode
                  ? "bg-purple-900/30 text-purple-300"
                  : "bg-purple-100 text-purple-700"
              }`}
            >
              {executions.length}
            </span>
          )}
        </div>
        {onToggle && (
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onToggle}
            className={`p-1 rounded transition-colors ${
              isDarkMode
                ? "hover:bg-gray-700 text-gray-400"
                : "hover:bg-gray-200 text-gray-600"
            }`}
          >
            <FiX className="w-4 h-4" />
          </motion.button>
        )}
      </div>

      {/* Execution List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {loading && executions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <FiLoader
              className={`w-6 h-6 animate-spin ${
                isDarkMode ? "text-purple-400" : "text-purple-600"
              }`}
            />
          </div>
        ) : executions.length === 0 ? (
          <div className="text-center py-8">
            <FiTool
              className={`w-12 h-12 mx-auto mb-3 opacity-30 ${
                isDarkMode ? "text-gray-600" : "text-gray-400"
              }`}
            />
            <p
              className={`text-sm ${
                isDarkMode ? "text-gray-500" : "text-gray-600"
              }`}
            >
              No MCP tool executions yet
            </p>
          </div>
        ) : (
          <AnimatePresence>
            {executions.map((execution) => (
              <motion.div
                key={execution.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`rounded-lg border transition-all ${getStatusColor(
                  execution.status
                )}`}
              >
                {/* Execution Header */}
                <button
                  onClick={() =>
                    setExpandedExecution(
                      expandedExecution === execution.id ? null : execution.id
                    )
                  }
                  className="w-full p-3 text-left hover:opacity-80 transition-opacity"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {getStatusIcon(execution.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4
                          className={`text-sm font-medium truncate ${
                            isDarkMode ? "text-gray-200" : "text-gray-800"
                          }`}
                        >
                          {execution.tool_name}
                        </h4>
                        {execution.execution_time > 0 && (
                          <span
                            className={`text-xs ${
                              isDarkMode ? "text-gray-500" : "text-gray-600"
                            }`}
                          >
                            {formatExecutionTime(execution.execution_time)}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs">
                        <div className="flex items-center gap-1">
                          <FiServer className="w-3 h-3" />
                          <span
                            className={
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }
                          >
                            {execution.server_name}
                          </span>
                        </div>
                        <span
                          className={
                            isDarkMode ? "text-gray-600" : "text-gray-400"
                          }
                        >
                          •
                        </span>
                        <span
                          className={
                            isDarkMode ? "text-gray-500" : "text-gray-600"
                          }
                        >
                          {new Date(execution.started_at).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    <motion.div
                      animate={{
                        rotate: expandedExecution === execution.id ? 180 : 0,
                      }}
                      transition={{ duration: 0.2 }}
                    >
                      <FiChevronDown
                        className={`w-4 h-4 ${
                          isDarkMode ? "text-gray-500" : "text-gray-600"
                        }`}
                      />
                    </motion.div>
                  </div>
                </button>

                {/* Expanded Content */}
                <AnimatePresence>
                  {expandedExecution === execution.id && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <div
                        className={`px-3 pb-3 space-y-2 border-t ${
                          isDarkMode
                            ? "border-gray-700/50"
                            : "border-gray-200/50"
                        }`}
                      >
                        {/* Input Parameters */}
                        {execution.input_params &&
                          Object.keys(execution.input_params).length > 0 && (
                            <div>
                              <h5
                                className={`text-xs font-semibold mb-1 mt-2 ${
                                  isDarkMode ? "text-gray-400" : "text-gray-600"
                                }`}
                              >
                                Input:
                              </h5>
                              <pre
                                className={`text-xs p-2 rounded overflow-x-auto ${
                                  isDarkMode
                                    ? "bg-gray-900/50 text-gray-300"
                                    : "bg-white text-gray-700"
                                }`}
                              >
                                {JSON.stringify(
                                  execution.input_params,
                                  null,
                                  2
                                )}
                              </pre>
                            </div>
                          )}

                        {/* Output Result */}
                        {execution.status === "success" &&
                          execution.output_result && (
                            <div>
                              <h5
                                className={`text-xs font-semibold mb-1 ${
                                  isDarkMode ? "text-gray-400" : "text-gray-600"
                                }`}
                              >
                                Result:
                              </h5>
                              <pre
                                className={`text-xs p-2 rounded overflow-x-auto ${
                                  isDarkMode
                                    ? "bg-gray-900/50 text-gray-300"
                                    : "bg-white text-gray-700"
                                }`}
                              >
                                {JSON.stringify(
                                  execution.output_result,
                                  null,
                                  2
                                )}
                              </pre>
                            </div>
                          )}

                        {/* Error Message */}
                        {execution.status === "error" &&
                          execution.error_message && (
                            <div>
                              <h5
                                className={`text-xs font-semibold mb-1 ${
                                  isDarkMode ? "text-red-400" : "text-red-600"
                                }`}
                              >
                                Error:
                              </h5>
                              <p
                                className={`text-xs p-2 rounded ${
                                  isDarkMode
                                    ? "bg-red-900/20 text-red-300"
                                    : "bg-red-50 text-red-700"
                                }`}
                              >
                                {execution.error_message}
                              </p>
                            </div>
                          )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
};

export default MCPPanel;
