// API configuration and utility functions
// Only frontend is exposed to users - all backend services are internal
// Vite dev server proxies requests to localhost services (see vite.config.ts)
const API_BASE_URL =
  import.meta.env.VITE_API_URL || "/api";
const GRAPH_RAG_API_URL =
  import.meta.env.VITE_GRAPH_RAG_API_URL || "/graphrag";

// Log the API URLs for debugging
console.log("API Base URL:", API_BASE_URL);
console.log("Graph RAG API URL:", GRAPH_RAG_API_URL);

// Import the token expiration handler
import { triggerGlobalTokenExpiration } from "../contexts/AuthContext";
// Import timezone utilities
import { getCurrentDateTime } from "../lib/utils";

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login/`,
    REGISTER: `${API_BASE_URL}/auth/register/`,
    ME: `${API_BASE_URL}/auth/me/`,
  },
  CHAT: {
    THREADS: `${API_BASE_URL}/chat/threads`,
    MESSAGES: `${API_BASE_URL}/chat/messages`,
    CREATE_THREAD: `${API_BASE_URL}/chat/threads`,
    SPACES: `${API_BASE_URL}/chat/spaces`,
  },
  GRAPH_RAG: {
    INGEST: `${GRAPH_RAG_API_URL}/ingest`,
    DOCUMENTS_LIST: `${GRAPH_RAG_API_URL}/documents/list`,
    DOCUMENT_DELETE: (documentId: string) =>
      `${GRAPH_RAG_API_URL}/documents/${documentId}`,
    DOCUMENT_ENABLE: (documentId: string) =>
      `${GRAPH_RAG_API_URL}/documents/${documentId}/enable`,
    DOCUMENT_DISABLE: (documentId: string) =>
      `${GRAPH_RAG_API_URL}/documents/${documentId}/disable`,
    DOCUMENTS_BATCH_ENABLE: `${GRAPH_RAG_API_URL}/documents/batch/enable`,
    DOCUMENTS_BATCH_DISABLE: `${GRAPH_RAG_API_URL}/documents/batch/disable`,
  },
};

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

// Thread interface
export interface Thread {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  last_message?: string;
  message_count?: number;
}

// New interfaces for the API chat thread structure
export interface ChatSubThread {
  chat_id: string;
  model_name: string;
  query: string;
  answer: string;
  summary: string;
  sources: {
    document_title: string;
    content: string;
    relevance: number;
    file_path: string;
    download_url: string;
    page: number;
  }[];
  related_links: string[];
  n_results: number;
  execution_time?: number;
  created_at: string;
  updated_at: string;
}

export interface Space {
  id: string;
  user: string;
  name: string;
  description?: string;
  color: string;
  icon?: string;
  is_default: boolean;
  thread_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatThread {
  _id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  sub_threads: string[];
  chat_id: string;
  sub_threads_data: ChatSubThread[];
  is_favorite?: boolean;
  space?: string; // space ID
  space_details?: Space; // populated space details
}

// Interface for the new thread creation response
export interface NewThreadResponse {
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  sub_threads: any[];
  chat_id: string;
}

// Response interface for GraphRAG ingest
export interface GraphRAGIngestResponse {
  success: boolean;
  message: string;
  document_ids: string[];
  metadata: {
    file_count: number;
    source: string;
    user_id: string;
  };
}

// Utility function to make authenticated API calls
export const apiCall = async <T = any>(
  url: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> => {
  try {
    const token = localStorage.getItem("auth_token");

    const defaultHeaders: HeadersInit = {
      "Content-Type": "application/json",
    };

    if (token) {
      defaultHeaders.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    const isJson = response.headers
      .get("content-type")
      ?.includes("application/json");
    const data = isJson ? await response.json() : await response.text();

    if (!response.ok) {
      console.error("API request failed:", {
        url,
        status: response.status,
        statusText: response.statusText,
        data,
        requestOptions: options,
      });

      // Check for token expiration (401 Unauthorized)
      if (response.status === 401) {
        console.log("Token expired (401), triggering global logout...");
        triggerGlobalTokenExpiration();
        return {
          error: "Session expired. Please log in again.",
          status: response.status,
        };
      }

      // Handle different error response formats
      let errorMessage = "Request failed";

      if (data.detail) {
        // FastAPI error format
        if (Array.isArray(data.detail)) {
          // Validation errors - extract meaningful message
          errorMessage = data.detail
            .map((err: any) => {
              if (err.msg && err.loc) {
                return `${err.loc.join(".")}: ${err.msg}`;
              }
              return err.msg || "Validation error";
            })
            .join(", ");
        } else if (typeof data.detail === "string") {
          errorMessage = data.detail;
        }
      } else if (data.message) {
        errorMessage = data.message;
      }

      return {
        error: errorMessage,
        status: response.status,
      };
    }

    return {
      data,
      status: response.status,
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : "Network error",
      status: 0,
    };
  }
};

// Function to check if user is authenticated by verifying token
export const verifyAuthToken = async (): Promise<boolean> => {
  const token = localStorage.getItem("auth_token");
  if (!token) return false;

  try {
    const response = await apiCall(API_ENDPOINTS.AUTH.ME);
    return response.status === 200 && !!response.data;
  } catch {
    return false;
  }
};

// Space API functions
export const spaceApi = {
  // Get all spaces for the user
  getSpaces: async (): Promise<ApiResponse<Space[]>> => {
    return apiCall<Space[]>(API_ENDPOINTS.CHAT.SPACES);
  },

  // Create a new space
  createSpace: async (data: {
    name: string;
    description?: string;
    color?: string;
    icon?: string;
    is_default?: boolean;
  }): Promise<ApiResponse<Space>> => {
    return apiCall<Space>(API_ENDPOINTS.CHAT.SPACES, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  // Update a space
  updateSpace: async (
    spaceId: string,
    data: Partial<Space>
  ): Promise<ApiResponse<Space>> => {
    return apiCall<Space>(`${API_ENDPOINTS.CHAT.SPACES}/${spaceId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  // Delete a space
  deleteSpace: async (spaceId: string): Promise<ApiResponse<void>> => {
    return apiCall(`${API_ENDPOINTS.CHAT.SPACES}/${spaceId}`, {
      method: "DELETE",
    });
  },

  // Set a space as default
  setDefaultSpace: async (spaceId: string): Promise<ApiResponse<any>> => {
    return apiCall(`${API_ENDPOINTS.CHAT.SPACES}/${spaceId}/set_default`, {
      method: "POST",
    });
  },
};

// Chat API functions
export const chatApi = {
  // Fetch all threads with optional subthread parameter and space filter
  getThreads: async (
    includeSubthreads: boolean = true,
    spaceId?: string
  ): Promise<ApiResponse<ChatThread[]>> => {
    let url = `${API_ENDPOINTS.CHAT.THREADS}?subthread=${includeSubthreads}`;
    if (spaceId !== undefined) {
      url += `&space_id=${spaceId}`;
    }
    return apiCall<ChatThread[]>(url);
  },

  // Fetch a single thread by ID
  getThreadById: async (chatId: string): Promise<ApiResponse<ChatThread>> => {
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}`;
    return apiCall<ChatThread>(url);
  },

  // Fetch sub-threads for a specific chat_id
  getSubThreads: async (
    chatId: string
  ): Promise<ApiResponse<ChatSubThread[]>> => {
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}/sub_threads`;
    return apiCall<ChatSubThread[]>(url);
  },

  // Submit a chat query and get AI response
  submitChatQuery: async (
    threadId: string,
    query: string,
    nResults: number = 5,
    responseMode: string = "general"
  ): Promise<ApiResponse<ChatSubThread>> => {
    console.log("Submitting chat query:", {
      threadId,
      query,
      nResults,
      responseMode,
    });

    // Only send required fields - backend will populate answer, summary, sources, etc.
    const requestBody = {
      query: query.trim(),
      response_mode: responseMode,
      n_results: nResults,
    };

    console.log("Chat query request body:", JSON.stringify(requestBody));

    const url = `${API_ENDPOINTS.CHAT.THREADS}/${threadId}/sub_threads`;
    return apiCall<ChatSubThread>(url, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  },

  // Create a new thread using the correct API format
  createNewThread: async (
    title: string,
    userId: string,
    spaceId?: string
  ): Promise<ApiResponse<NewThreadResponse>> => {
    console.log(
      "Creating new thread with title:",
      title,
      "for user:",
      userId,
      "in space:",
      spaceId
    );

    const requestBody: any = {
      title: title.trim(),
    };

    // Add space_id if provided
    if (spaceId) {
      requestBody.space = spaceId;
    }

    console.log("New thread request body:", JSON.stringify(requestBody));
    console.log("API endpoint:", API_ENDPOINTS.CHAT.CREATE_THREAD);

    return apiCall<NewThreadResponse>(API_ENDPOINTS.CHAT.CREATE_THREAD, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });
  },

  // Legacy create thread method (kept for backward compatibility)
  createThread: async (title: string): Promise<ApiResponse<Thread>> => {
    console.log("Creating thread with title (legacy):", title);

    // Try simple format first
    let requestBody: any = { title: title.trim() };

    console.log("Request body (simple):", JSON.stringify(requestBody));
    console.log("API endpoint:", API_ENDPOINTS.CHAT.CREATE_THREAD);

    let response = await apiCall<Thread>(API_ENDPOINTS.CHAT.CREATE_THREAD, {
      method: "POST",
      body: JSON.stringify(requestBody),
    });

    // If simple format fails with 422, try with additional fields
    if (response.status === 422) {
      console.log("Simple format failed, trying with additional fields...");
      const currentTime = getCurrentDateTime(); // Use proper timezone-aware datetime
      requestBody = {
        title: title.trim(),
        user_id: null, // Will be handled by backend from auth token
        created_at: currentTime,
        updated_at: currentTime,
      };

      console.log("Request body (extended):", JSON.stringify(requestBody));

      response = await apiCall<Thread>(API_ENDPOINTS.CHAT.CREATE_THREAD, {
        method: "POST",
        body: JSON.stringify(requestBody),
      });
    }

    return response;
  },

  // Get messages for a specific thread
  getMessages: async (threadId: string): Promise<ApiResponse<any[]>> => {
    const url = `${API_ENDPOINTS.CHAT.MESSAGES}?thread_id=${threadId}`;
    return apiCall<any[]>(url);
  },

  // Delete a thread by chat_id
  deleteThread: async (chatId: string): Promise<ApiResponse<any>> => {
    console.log("Deleting thread with chat_id:", chatId);
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}`;

    return apiCall(url, {
      method: "DELETE",
    });
  },

  // Toggle favorite status
  toggleFavorite: async (chatId: string): Promise<ApiResponse<ChatThread>> => {
    console.log("Toggling favorite for thread:", chatId);
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}/toggle_favorite`;

    return apiCall<ChatThread>(url, {
      method: "POST",
    });
  },

  // Update favorite status
  updateFavorite: async (
    chatId: string,
    isFavorite: boolean
  ): Promise<ApiResponse<ChatThread>> => {
    console.log(
      "Updating favorite status for thread:",
      chatId,
      "to",
      isFavorite
    );
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}/update_favorite`;

    return apiCall<ChatThread>(url, {
      method: "PATCH",
      body: JSON.stringify({ is_favorite: isFavorite }),
    });
  },

  // Move thread to a different space
  moveToSpace: async (
    chatId: string,
    spaceId: string | null
  ): Promise<ApiResponse<ChatThread>> => {
    console.log("Moving thread", chatId, "to space:", spaceId);
    const url = `${API_ENDPOINTS.CHAT.THREADS}/${chatId}/move_to_space`;

    return apiCall<ChatThread>(url, {
      method: "PATCH",
      body: JSON.stringify({ space_id: spaceId }),
    });
  },
};

// Document interface
export interface Document {
  filename: string;
  blob_name: string;
  file_size: number;
  created_at: string;
  download_url?: string;
  storage_path: string;
  enabled?: boolean; // Optional enabled status
  document_id?: string; // Optional document ID (can use blob_name as fallback)
}

export interface DocumentsListResponse {
  documents: Document[];
  count: number;
  user_id?: string;
  storage_type: string;
}

// GraphRAG API functions
export const graphRagApi = {
  // Upload files to GraphRAG ingest endpoint
  uploadFiles: async (
    files: File[],
    userId: string,
    options: {
      force?: boolean;
      extractionMethod?: string;
      maxWorkers?: number;
      useLlamaindex?: boolean;
    } = {}
  ): Promise<ApiResponse<GraphRAGIngestResponse>> => {
    try {
      const {
        force = true,
        extractionMethod = "auto",
        maxWorkers = 4,
        useLlamaindex = true,
      } = options;

      // Create FormData for multipart/form-data request
      const formData = new FormData();

      // Add all files with the key 'files'
      files.forEach((file) => {
        formData.append("files", file);
      });

      // Build query parameters
      const queryParams = new URLSearchParams({
        force: force.toString(),
        extraction_method: extractionMethod,
        max_workers: maxWorkers.toString(),
        user_id: userId,
        use_llamaindex: useLlamaindex.toString(),
      });

      const url = `${API_ENDPOINTS.GRAPH_RAG.INGEST}?${queryParams}`;

      console.log("Uploading files to GraphRAG:", {
        url,
        fileCount: files.length,
        fileNames: files.map((f) => f.name),
        userId,
        options,
      });

      // Get auth token for the request
      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: formData,
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        console.error("GraphRAG file upload failed:", {
          url,
          status: response.status,
          statusText: response.statusText,
          data,
        });

        // Handle different error response formats
        let errorMessage = "File upload failed";

        if (data.detail) {
          if (Array.isArray(data.detail)) {
            errorMessage = data.detail
              .map((err: any) => err.msg || "Upload error")
              .join(", ");
          } else if (typeof data.detail === "string") {
            errorMessage = data.detail;
          }
        } else if (data.message) {
          errorMessage = data.message;
        }

        return {
          error: errorMessage,
          status: response.status,
        };
      }

      console.log("GraphRAG file upload successful:", data);

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      console.error("GraphRAG file upload error:", error);
      return {
        error:
          error instanceof Error
            ? error.message
            : "Network error during file upload",
        status: 0,
      };
    }
  },

  // List documents
  listDocuments: async (
    userId?: string,
    limit: number = 50
  ): Promise<ApiResponse<DocumentsListResponse>> => {
    try {
      const queryParams = new URLSearchParams({ limit: limit.toString() });
      if (userId) {
        queryParams.append("user_id", userId);
      }

      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENTS_LIST}?${queryParams}`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "GET",
        headers,
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      console.log("List documents API response:", {
        status: response.status,
        ok: response.ok,
        data: data,
        contentType: response.headers.get("content-type"),
        dataType: typeof data,
        dataKeys: typeof data === "object" ? Object.keys(data) : "N/A",
        documentsCount:
          typeof data === "object" && data.documents
            ? data.documents.length
            : "N/A",
        documentsArray:
          typeof data === "object" && data.documents ? data.documents : "N/A",
      });

      if (!response.ok) {
        let errorMessage = "Failed to list documents";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },

  // Delete a document
  deleteDocument: async (
    documentId: string,
    userId?: string
  ): Promise<ApiResponse<any>> => {
    try {
      const queryParams = new URLSearchParams();
      if (userId) {
        queryParams.append("user_id", userId);
      }

      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENT_DELETE(documentId)}${
        queryParams.toString() ? `?${queryParams}` : ""
      }`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "DELETE",
        headers,
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to delete document";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data: data || { success: true },
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },

  // Enable a document
  enableDocument: async (
    documentId: string,
    userId?: string
  ): Promise<ApiResponse<any>> => {
    try {
      const queryParams = new URLSearchParams();
      if (userId) {
        queryParams.append("user_id", userId);
      }

      // URL encode the document ID to handle special characters like .pdf
      const encodedDocumentId = encodeURIComponent(documentId);
      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENT_ENABLE(
        encodedDocumentId
      )}${queryParams.toString() ? `?${queryParams}` : ""}`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
        "Content-Type": "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to enable document";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data: data || { success: true },
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },

  // Disable a document
  disableDocument: async (
    documentId: string,
    userId?: string
  ): Promise<ApiResponse<any>> => {
    try {
      const queryParams = new URLSearchParams();
      if (userId) {
        queryParams.append("user_id", userId);
      }

      // URL encode the document ID to handle special characters like .pdf
      const encodedDocumentId = encodeURIComponent(documentId);
      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENT_DISABLE(
        encodedDocumentId
      )}${queryParams.toString() ? `?${queryParams}` : ""}`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
        "Content-Type": "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to disable document";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data: data || { success: true },
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },

  // Batch enable documents
  batchEnableDocuments: async (
    documentIds: string[],
    userId?: string
  ): Promise<ApiResponse<any>> => {
    try {
      const queryParams = new URLSearchParams();
      if (userId) {
        queryParams.append("user_id", userId);
      }

      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENTS_BATCH_ENABLE}${
        queryParams.toString() ? `?${queryParams}` : ""
      }`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
        "Content-Type": "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify({ document_ids: documentIds }),
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to enable documents";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data: data || { success: true },
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },

  // Batch disable documents
  batchDisableDocuments: async (
    documentIds: string[],
    userId?: string
  ): Promise<ApiResponse<any>> => {
    try {
      const queryParams = new URLSearchParams();
      if (userId) {
        queryParams.append("user_id", userId);
      }

      const url = `${API_ENDPOINTS.GRAPH_RAG.DOCUMENTS_BATCH_DISABLE}${
        queryParams.toString() ? `?${queryParams}` : ""
      }`;

      const token = localStorage.getItem("auth_token");
      const headers: HeadersInit = {
        accept: "application/json",
        "Content-Type": "application/json",
      };

      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      const response = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify({ document_ids: documentIds }),
      });

      const isJson = response.headers
        .get("content-type")
        ?.includes("application/json");
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMessage = "Failed to disable documents";
        if (data.detail) {
          errorMessage =
            typeof data.detail === "string"
              ? data.detail
              : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
        return {
          error: errorMessage,
          status: response.status,
        };
      }

      return {
        data: data || { success: true },
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Network error",
        status: 0,
      };
    }
  },
};

// Update default export to include graphRagApi
export default {
  API_ENDPOINTS,
  apiCall,
  verifyAuthToken,
  chatApi,
  graphRagApi,
};
