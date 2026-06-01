import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  FiSearch,
  FiPlus,
  FiFolder,
  FiStar,
  FiClock,
  FiMessageCircle,
  FiCalendar,
  FiRefreshCw,
  FiTrash2,
  FiGrid,
  FiList,
  FiX,
  FiFileText,
  FiUpload,
  FiToggleLeft,
  FiToggleRight,
} from "react-icons/fi";
import { useTheme } from "../../../contexts/ThemeContext";
import { useSidebar } from "../../../contexts/SidebarContext";
import { useAuth } from "../../../contexts/AuthContext";
import { useSpace } from "../../../contexts/SpaceContext";
import { motion, AnimatePresence } from "framer-motion";
import {
  chatApi,
  ChatThread,
  graphRagApi,
  Document,
} from "../../../services/api";
import { toast } from "react-hot-toast";
import DeleteConfirmModal from "../../DeleteConfirmModal/DeleteConfirmModal";
import FileUploadModal from "../../FileUploadModal/FileUploadModal";

interface ThreadWithMetadata extends ChatThread {
  category?: string;
}

const Library: React.FC = () => {
  const { isDarkMode } = useTheme();
  const { isOpen: sidebarOpen } = useSidebar();
  const { isAuthenticated } = useAuth();
  const {
    spaces,
    selectedSpace,
    setSelectedSpace,
    createSpace,
    deleteSpace: deleteSpaceFromContext,
    fetchSpaces,
  } = useSpace();
  const navigate = useNavigate();

  // Debug spaces
  useEffect(() => {
    console.log("Library - Spaces updated:", spaces.length, spaces);
    console.log("Library - Selected space:", selectedSpace);
  }, [spaces, selectedSpace]);

  // State management
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [threads, setThreads] = useState<ThreadWithMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Library view toggle (Chats vs Documents)
  const [libraryView, setLibraryView] = useState<"chats" | "documents">(
    "chats"
  );

  // Documents state
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(
    new Set()
  );
  const [showUploadModal, setShowUploadModal] = useState(false);

  // Space management state
  const [isCreatingSpace, setIsCreatingSpace] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState("");
  const [showSpaceSelector, setShowSpaceSelector] = useState(false);

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] =
    useState<ThreadWithMetadata | null>(null);
  const [documentToDelete, setDocumentToDelete] = useState<Document | null>(
    null
  );
  const [isDeleting, setIsDeleting] = useState(false);

  // Move to space state
  const [moveModalOpen, setMoveModalOpen] = useState(false);
  const [threadToMove, setThreadToMove] = useState<ThreadWithMetadata | null>(
    null
  );

  const tabs = [
    { id: "all", label: "All", icon: FiFolder },
    { id: "favorites", label: "Favorites", icon: FiStar },
    { id: "recent", label: "Recent", icon: FiClock },
  ];

  // Fetch threads on component mount and when selected space changes
  useEffect(() => {
    if (isAuthenticated && libraryView === "chats") {
      fetchThreads();
    }
  }, [isAuthenticated, selectedSpace, libraryView]);

  // Fetch documents when switching to documents view
  useEffect(() => {
    if (isAuthenticated && libraryView === "documents") {
      console.log("Library view changed to documents, fetching documents...");
      fetchDocuments();
    }
  }, [isAuthenticated, libraryView]);

  const fetchThreads = async () => {
    try {
      setLoading(true);
      // Pass selectedSpace?.id to filter by space (undefined means all threads)
      const spaceFilter = selectedSpace ? selectedSpace.id : undefined;
      const response = await chatApi.getThreads(true, spaceFilter);

      if (response.data && response.status === 200) {
        const threadsWithMetadata: ThreadWithMetadata[] = response.data.map(
          (thread: ChatThread) => ({
            ...thread,
            category: "recent",
          })
        );

        setThreads(threadsWithMetadata);
        console.log(
          `Loaded ${threadsWithMetadata.length} threads for space:`,
          selectedSpace?.name || "All"
        );
      } else {
        toast.error(response.error || "Failed to load threads");
        setThreads([]);
      }
    } catch (error) {
      console.error("Error fetching threads:", error);
      toast.error("Failed to load threads");
      setThreads([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchDocuments = async () => {
    try {
      setDocumentsLoading(true);
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;

      console.log("Fetching documents for user:", userId);
      const response = await graphRagApi.listDocuments(userId, 100);

      console.log("Documents API response:", response);

      if (response.data && response.status === 200) {
        const documentsList = response.data.documents || [];
        console.log("Documents list:", documentsList);

        // Set enabled to true by default if not provided (for backward compatibility)
        // Extract document_id from storage_path or use blob_name
        // If storage_path contains slashes (e.g., "users/12/filename.pdf"), extract just the filename
        const docsWithStatus = documentsList.map((doc: any) => {
          let docId = doc.document_id || doc.blob_name || doc.filename;

          // If storage_path exists and contains slashes, extract filename
          if (doc.storage_path && doc.storage_path.includes("/")) {
            const parts = doc.storage_path.split("/");
            docId = parts[parts.length - 1]; // Get last part (filename)
          }

          return {
            ...doc,
            enabled: doc.enabled !== undefined ? doc.enabled : true,
            document_id: docId,
          };
        });

        console.log("Processed documents:", docsWithStatus);
        setDocuments(docsWithStatus);
        console.log(`Loaded ${docsWithStatus.length} documents`);
      } else {
        console.error("Failed to load documents:", response.error);
        toast.error(response.error || "Failed to load documents");
        setDocuments([]);
      }
    } catch (error) {
      console.error("Error fetching documents:", error);
      toast.error("Failed to load documents");
      setDocuments([]);
    } finally {
      setDocumentsLoading(false);
    }
  };

  // Filter threads based on active tab and search query
  const filteredThreads = threads
    .filter((thread) => {
      // Get last message from sub_threads_data
      const lastMessage =
        thread.sub_threads_data && thread.sub_threads_data.length > 0
          ? thread.sub_threads_data[thread.sub_threads_data.length - 1].query
          : "";

      const matchesSearch =
        thread.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lastMessage.toLowerCase().includes(searchQuery.toLowerCase());

      let matchesTab = true;
      if (activeTab === "favorites") {
        matchesTab = thread.is_favorite === true;
      } else if (activeTab === "recent") {
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        matchesTab = new Date(thread.updated_at) > weekAgo;
      }

      return matchesSearch && matchesTab;
    })
    .sort((a, b) => {
      // Smart sort: Show most recently modified thread first, then rest in creation order (newest first)
      const aCreated = new Date(a.created_at).getTime();
      const bCreated = new Date(b.created_at).getTime();

      // Find the most recently updated thread
      const allThreads = threads.filter((t) => {
        const lastMessage =
          t.sub_threads_data && t.sub_threads_data.length > 0
            ? t.sub_threads_data[t.sub_threads_data.length - 1].query
            : "";
        const matchesSearch =
          t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          lastMessage.toLowerCase().includes(searchQuery.toLowerCase());
        let matchesTab = true;
        if (activeTab === "favorites") {
          matchesTab = t.is_favorite === true;
        } else if (activeTab === "recent") {
          const weekAgo = new Date();
          weekAgo.setDate(weekAgo.getDate() - 7);
          matchesTab = new Date(t.updated_at) > weekAgo;
        }
        return matchesSearch && matchesTab;
      });

      const mostRecentUpdated = allThreads.reduce((latest, current) => {
        return new Date(current.updated_at).getTime() >
          new Date(latest.updated_at).getTime()
          ? current
          : latest;
      }, allThreads[0]);

      // If one of them is the most recently updated, it goes first
      if (a.chat_id === mostRecentUpdated?.chat_id) return -1;
      if (b.chat_id === mostRecentUpdated?.chat_id) return 1;

      // For the rest, sort by creation date descending (newest first)
      return bCreated - aCreated;
    });

  const handleThreadClick = (chatId: string) => {
    navigate(`/chat?chatId=${chatId}`);
  };

  const toggleFavorite = async (
    thread: ThreadWithMetadata,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();

    try {
      // Call the API to toggle favorite
      const response = await chatApi.toggleFavorite(thread.chat_id);

      if (response.data && response.status === 200) {
        // Update local state with the returned data - use chat_id for comparison
        setThreads((prev) =>
          prev.map((t) =>
            t.chat_id === thread.chat_id // Use chat_id instead of _id for accurate matching
              ? { ...t, is_favorite: response.data!.is_favorite }
              : t
          )
        );

        // Add haptic feedback for mobile (if supported)
        if (navigator.vibrate) {
          navigator.vibrate(50);
        }

        // Show toast feedback
        toast.success(
          response.data.is_favorite
            ? "Added to favorites"
            : "Removed from favorites",
          { duration: 2000 }
        );
      } else {
        toast.error(response.error || "Failed to update favorite");
      }
    } catch (error) {
      console.error("Error toggling favorite:", error);
      toast.error("Failed to update favorite");
    }
  };

  const handleCreateSpace = async () => {
    if (!newSpaceName.trim()) return;

    try {
      const space = await createSpace({
        name: newSpaceName.trim(),
        color: "#6366f1",
      });
      if (space) {
        setIsCreatingSpace(false);
        setNewSpaceName("");
      }
    } catch (error) {
      console.error("Error creating space:", error);
    }
  };

  const handleDeleteSpace = async (spaceId: string) => {
    if (
      window.confirm(
        "Are you sure you want to delete this space? Threads will not be deleted."
      )
    ) {
      await deleteSpaceFromContext(spaceId);
    }
  };

  const handleDeleteClick = (
    thread: ThreadWithMetadata,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();
    setThreadToDelete(thread);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (libraryView === "chats" && threadToDelete) {
      try {
        setIsDeleting(true);
        console.log("Deleting thread with chat_id:", threadToDelete.chat_id);

        const response = await chatApi.deleteThread(threadToDelete.chat_id);

        if (response.status === 200 || response.status === 204) {
          toast.success("Chat deleted successfully");

          // Close modal and reset state
          setDeleteModalOpen(false);
          setThreadToDelete(null);

          // Refetch threads and spaces to ensure UI is in sync with backend and update counts
          await fetchThreads();
          await fetchSpaces();
        } else {
          console.error("Delete thread error response:", response);
          toast.error(response.error || "Failed to delete chat");
        }
      } catch (error) {
        console.error("Error deleting thread:", error);
        toast.error("Failed to delete chat");
      } finally {
        setIsDeleting(false);
      }
    } else if (libraryView === "documents" && documentToDelete) {
      await handleDocumentDeleteConfirm();
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setThreadToDelete(null);
    setDocumentToDelete(null);
  };

  const handleMoveClick = (
    thread: ThreadWithMetadata,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();
    setThreadToMove(thread);
    setMoveModalOpen(true);
  };

  const handleMoveToSpace = async (targetSpaceId: string | null) => {
    if (!threadToMove) return;

    try {
      const response = await chatApi.moveToSpace(
        threadToMove.chat_id,
        targetSpaceId
      );

      if (response.status === 200 && response.data) {
        toast.success(
          `Chat moved to ${
            targetSpaceId
              ? spaces.find((s) => s.id === targetSpaceId)?.name || "space"
              : "global"
          }`
        );
        setMoveModalOpen(false);
        setThreadToMove(null);
        // Refresh threads and spaces to reflect the change and update counts
        await fetchThreads();
        await fetchSpaces();
      } else {
        toast.error(response.error || "Failed to move chat");
      }
    } catch (error) {
      console.error("Error moving chat:", error);
      toast.error("Failed to move chat");
    }
  };

  // Document handlers
  const handleDocumentDeleteClick = (
    document: Document,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();
    setDocumentToDelete(document);
    setDeleteModalOpen(true);
  };

  const handleDocumentDeleteConfirm = async () => {
    if (!documentToDelete) return;

    try {
      setIsDeleting(true);
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;

      const documentId =
        documentToDelete.document_id || documentToDelete.blob_name;
      const response = await graphRagApi.deleteDocument(documentId, userId);

      if (response.status === 200 || response.status === 204) {
        toast.success("Document deleted successfully");
        setDeleteModalOpen(false);
        setDocumentToDelete(null);
        await fetchDocuments();
      } else {
        toast.error(response.error || "Failed to delete document");
      }
    } catch (error) {
      console.error("Error deleting document:", error);
      toast.error("Failed to delete document");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDocumentToggleEnable = async (
    document: Document,
    event: React.MouseEvent
  ) => {
    event.stopPropagation();

    try {
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;
      const documentId = document.document_id || document.blob_name;

      const response = document.enabled
        ? await graphRagApi.disableDocument(documentId, userId)
        : await graphRagApi.enableDocument(documentId, userId);

      if (response.status === 200) {
        setDocuments((prev) =>
          prev.map((doc) =>
            doc.document_id === documentId || doc.blob_name === documentId
              ? { ...doc, enabled: !doc.enabled }
              : doc
          )
        );
        toast.success(
          `Document ${document.enabled ? "disabled" : "enabled"} successfully`
        );
      } else {
        toast.error(
          response.error ||
            `Failed to ${document.enabled ? "disable" : "enable"} document`
        );
      }
    } catch (error) {
      console.error("Error toggling document status:", error);
      toast.error("Failed to update document status");
    }
  };

  const handleDocumentSelect = (
    documentId: string,
    event?: React.MouseEvent | React.ChangeEvent<HTMLInputElement>
  ) => {
    if (event) {
      event.stopPropagation();
    }
    setSelectedDocuments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(documentId)) {
        newSet.delete(documentId);
      } else {
        newSet.add(documentId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    const filteredDocs = filteredDocuments;
    if (selectedDocuments.size === filteredDocs.length) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(
        new Set(filteredDocs.map((doc) => doc.document_id || doc.blob_name))
      );
    }
  };

  const handleBatchEnable = async () => {
    if (selectedDocuments.size === 0) return;

    try {
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;
      const documentIds = Array.from(selectedDocuments);

      const response = await graphRagApi.batchEnableDocuments(
        documentIds,
        userId
      );

      if (response.status === 200) {
        setDocuments((prev) =>
          prev.map((doc) => {
            const docId = doc.document_id || doc.blob_name;
            return selectedDocuments.has(docId)
              ? { ...doc, enabled: true }
              : doc;
          })
        );
        setSelectedDocuments(new Set());
        toast.success(`Enabled ${documentIds.length} document(s) successfully`);
      } else {
        toast.error(response.error || "Failed to enable documents");
      }
    } catch (error) {
      console.error("Error enabling documents:", error);
      toast.error("Failed to enable documents");
    }
  };

  const handleBatchDisable = async () => {
    if (selectedDocuments.size === 0) return;

    try {
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;
      const documentIds = Array.from(selectedDocuments);

      const response = await graphRagApi.batchDisableDocuments(
        documentIds,
        userId
      );

      if (response.status === 200) {
        setDocuments((prev) =>
          prev.map((doc) => {
            const docId = doc.document_id || doc.blob_name;
            return selectedDocuments.has(docId)
              ? { ...doc, enabled: false }
              : doc;
          })
        );
        setSelectedDocuments(new Set());
        toast.success(
          `Disabled ${documentIds.length} document(s) successfully`
        );
      } else {
        toast.error(response.error || "Failed to disable documents");
      }
    } catch (error) {
      console.error("Error disabling documents:", error);
      toast.error("Failed to disable documents");
    }
  };

  const handleBatchDelete = async () => {
    if (selectedDocuments.size === 0) return;

    if (
      !window.confirm(
        `Are you sure you want to delete ${selectedDocuments.size} document(s)? This action cannot be undone.`
      )
    ) {
      return;
    }

    try {
      const userData = localStorage.getItem("user_data");
      const userId = userData ? JSON.parse(userData).id : undefined;
      const documentIds = Array.from(selectedDocuments);

      // Delete documents one by one
      const deletePromises = documentIds.map((id) =>
        graphRagApi.deleteDocument(id, userId)
      );

      await Promise.all(deletePromises);
      setSelectedDocuments(new Set());
      await fetchDocuments();
      toast.success(`Deleted ${documentIds.length} document(s) successfully`);
    } catch (error) {
      console.error("Error deleting documents:", error);
      toast.error("Failed to delete some documents");
    }
  };

  const handleUploadSuccess = () => {
    console.log("Upload success callback triggered");
    // Switch to documents view if not already there
    if (libraryView !== "documents") {
      setLibraryView("documents");
    }
    // Fetch documents after a short delay to ensure backend has processed them
    setTimeout(() => {
      fetchDocuments();
    }, 1000);
  };

  // Filter documents based on search query
  const filteredDocuments = documents
    .filter((doc) => {
      const matchesSearch =
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
        doc.blob_name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    })
    .sort((a, b) => {
      // Sort by creation date (newest first)
      return (
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    });

  const formatTimestamp = (timestamp: string) => {
    if (!timestamp) return "Unknown";

    // Parse the ISO string properly (handles timezone offset)
    const date = new Date(timestamp);
    const now = new Date();

    // Check if date is valid
    if (isNaN(date.getTime())) {
      return "Invalid date";
    }

    const diffInMilliseconds = now.getTime() - date.getTime();
    const diffInSeconds = Math.floor(diffInMilliseconds / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    // Handle future dates (in case of clock skew)
    if (diffInSeconds < 0) {
      return "just now";
    }

    if (diffInSeconds < 60) {
      return "just now";
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else if (diffInDays < 7) {
      return `${diffInDays}d ago`;
    } else {
      // For older dates, show abbreviated format
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
      });
    }
  };

  if (!isAuthenticated) {
    return (
      <motion.div
        className={`fixed inset-0 ${
          isDarkMode ? "bg-[#282a36]" : "bg-white"
        } overflow-y-auto`}
        animate={{
          marginLeft: sidebarOpen ? "16rem" : "4rem",
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
        style={{
          marginLeft:
            typeof window !== "undefined" && window.innerWidth < 768
              ? "0rem"
              : undefined,
        }}
      >
        <div className="flex items-center justify-center h-full px-4">
          <p
            className={`text-lg ${
              isDarkMode ? "text-gray-400" : "text-gray-600"
            }`}
          >
            Please sign in to view your library
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className={`fixed inset-0 ${
        isDarkMode ? "bg-[#282a36]" : "bg-white"
      } overflow-y-auto`}
      animate={{
        marginLeft: sidebarOpen ? "16rem" : "4rem",
      }}
      transition={{
        type: "spring",
        stiffness: 300,
        damping: 30,
      }}
      style={{
        marginLeft:
          typeof window !== "undefined" && window.innerWidth < 768
            ? "0rem"
            : undefined,
      }}
    >
      <div className="h-full flex flex-col">
        {/* Header - More compact */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className={`border-b ${
            isDarkMode ? "border-gray-700/50" : "border-gray-200"
          } px-4 py-4`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1
                className={`text-xl font-semibold ${
                  isDarkMode ? "text-gray-100" : "text-gray-900"
                }`}
              >
                {selectedSpace ? `${selectedSpace.name} Library` : "Library"}
              </h1>
              <span
                className={`px-2 py-1 rounded text-sm ${
                  isDarkMode
                    ? "bg-[#44475a] text-gray-400"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {libraryView === "chats"
                  ? filteredThreads.length
                  : filteredDocuments.length}
              </span>
            </div>

            {/* Library View Toggle Switch */}
            <div className="flex items-center gap-2 mr-2">
              <span
                className={`text-sm ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Chats
              </span>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setLibraryView(
                    libraryView === "chats" ? "documents" : "chats"
                  );
                  setSelectedDocuments(new Set()); // Clear selections when switching views
                }}
                className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${
                  libraryView === "documents"
                    ? isDarkMode
                      ? "bg-purple-600"
                      : "bg-purple-600"
                    : isDarkMode
                    ? "bg-[#44475a]"
                    : "bg-gray-300"
                }`}
              >
                <motion.div
                  className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-md`}
                  animate={{
                    x: libraryView === "documents" ? 24 : 0,
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30,
                  }}
                />
              </motion.button>
              <span
                className={`text-sm ${
                  isDarkMode ? "text-gray-400" : "text-gray-600"
                }`}
              >
                Documents
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Upload button for documents view */}
              {libraryView === "documents" && (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowUploadModal(true)}
                  className={`px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                    isDarkMode
                      ? "bg-purple-600 hover:bg-purple-700 text-white"
                      : "bg-purple-600 hover:bg-purple-700 text-white"
                  }`}
                >
                  <FiUpload className="w-4 h-4" />
                  <span className="hidden sm:inline">Upload</span>
                </motion.button>
              )}

              {/* View Mode Toggle */}
              <div
                className={`flex rounded-lg p-1 ${
                  isDarkMode ? "bg-[#44475a]" : "bg-gray-100"
                }`}
              >
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setViewMode("grid")}
                  className={`p-1.5 rounded transition-colors ${
                    viewMode === "grid"
                      ? isDarkMode
                        ? "bg-purple-600 text-white"
                        : "bg-purple-600 text-white"
                      : isDarkMode
                      ? "text-gray-400 hover:text-gray-300"
                      : "text-gray-500 hover:text-gray-600"
                  }`}
                  title="Grid view"
                >
                  <FiGrid className="w-4 h-4" />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setViewMode("list")}
                  className={`p-1.5 rounded transition-colors ${
                    viewMode === "list"
                      ? isDarkMode
                        ? "bg-purple-600 text-white"
                        : "bg-purple-600 text-white"
                      : isDarkMode
                      ? "text-gray-400 hover:text-gray-300"
                      : "text-gray-500 hover:text-gray-600"
                  }`}
                  title="List view"
                >
                  <FiList className="w-4 h-4" />
                </motion.button>
              </div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={
                  libraryView === "chats" ? fetchThreads : fetchDocuments
                }
                disabled={loading || documentsLoading}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode
                    ? "hover:bg-[#44475a] text-gray-400 hover:text-gray-300"
                    : "hover:bg-gray-100 text-gray-500 hover:text-gray-600"
                } ${
                  loading || documentsLoading
                    ? "opacity-50 cursor-not-allowed"
                    : ""
                }`}
              >
                <FiRefreshCw
                  className={`w-4 h-4 ${
                    loading || documentsLoading ? "animate-spin" : ""
                  }`}
                />
              </motion.button>

              {/* Space Selector - Only show for chats view */}
              {libraryView === "chats" && (
                <div className="relative">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowSpaceSelector(!showSpaceSelector)}
                    className={`px-3 py-2 rounded-lg flex items-center gap-2 transition-colors ${
                      isDarkMode
                        ? "bg-[#44475a] hover:bg-[#6272a4] text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-900"
                    }`}
                  >
                    <FiFolder className="w-4 h-4" />
                    <span className="hidden sm:inline">
                      {selectedSpace ? selectedSpace.name : "All Spaces"}
                    </span>
                  </motion.button>

                  {/* Space Dropdown */}
                  <AnimatePresence>
                    {showSpaceSelector && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={`absolute right-0 mt-2 w-64 rounded-lg shadow-lg z-50 ${
                          isDarkMode ? "bg-[#44475a]" : "bg-white"
                        }`}
                      >
                        <div className="p-2">
                          {/* All Spaces Option */}
                          <button
                            onClick={() => {
                              setSelectedSpace(null);
                              setShowSpaceSelector(false);
                            }}
                            className={`w-full text-left px-3 py-2 rounded transition-colors ${
                              !selectedSpace
                                ? isDarkMode
                                  ? "bg-purple-600 text-white"
                                  : "bg-purple-100 text-purple-900"
                                : isDarkMode
                                ? "hover:bg-[#6272a4] text-gray-200"
                                : "hover:bg-gray-100 text-gray-900"
                            }`}
                          >
                            All Spaces
                          </button>

                          {/* Space List */}
                          {spaces &&
                            Array.isArray(spaces) &&
                            spaces.map((space) => (
                              <div
                                key={space.id}
                                className="flex items-center gap-2"
                              >
                                <button
                                  onClick={() => {
                                    setSelectedSpace(space);
                                    setShowSpaceSelector(false);
                                  }}
                                  className={`flex-1 text-left px-3 py-2 rounded transition-colors ${
                                    selectedSpace?.id === space.id
                                      ? isDarkMode
                                        ? "bg-purple-600 text-white"
                                        : "bg-purple-100 text-purple-900"
                                      : isDarkMode
                                      ? "hover:bg-[#6272a4] text-gray-200"
                                      : "hover:bg-gray-100 text-gray-900"
                                  }`}
                                >
                                  <div className="flex items-center gap-2">
                                    <div
                                      className="w-3 h-3 rounded"
                                      style={{ backgroundColor: space.color }}
                                    />
                                    <span>{space.name}</span>
                                    <span
                                      className={`ml-auto text-xs ${
                                        isDarkMode
                                          ? "text-gray-400"
                                          : "text-gray-500"
                                      }`}
                                    >
                                      {space.thread_count}
                                    </span>
                                  </div>
                                </button>
                                <button
                                  onClick={() => handleDeleteSpace(space.id)}
                                  className={`p-2 rounded transition-colors ${
                                    isDarkMode
                                      ? "hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                                      : "hover:bg-red-100 text-gray-500 hover:text-red-600"
                                  }`}
                                >
                                  <FiTrash2 className="w-3 h-3" />
                                </button>
                              </div>
                            ))}

                          {/* Create New Space */}
                          {!isCreatingSpace ? (
                            <button
                              onClick={() => setIsCreatingSpace(true)}
                              className={`w-full text-left px-3 py-2 rounded mt-2 transition-colors ${
                                isDarkMode
                                  ? "hover:bg-[#6272a4] text-gray-400"
                                  : "hover:bg-gray-100 text-gray-600"
                              }`}
                            >
                              <FiPlus className="inline w-3 h-3 mr-2" />
                              New Space
                            </button>
                          ) : (
                            <div className="mt-2 flex gap-2">
                              <input
                                type="text"
                                placeholder="Space name..."
                                value={newSpaceName}
                                onChange={(e) =>
                                  setNewSpaceName(e.target.value)
                                }
                                onKeyDown={(e) => {
                                  if (e.key === "Enter") handleCreateSpace();
                                  if (e.key === "Escape") {
                                    setIsCreatingSpace(false);
                                    setNewSpaceName("");
                                  }
                                }}
                                className={`flex-1 px-2 py-1 text-sm rounded ${
                                  isDarkMode
                                    ? "bg-[#282a36] text-gray-100"
                                    : "bg-gray-100 text-gray-900"
                                }`}
                                autoFocus
                              />
                              <button
                                onClick={handleCreateSpace}
                                className="px-2 py-1 bg-purple-600 text-white rounded text-sm"
                              >
                                <FiPlus className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => {
                                  setIsCreatingSpace(false);
                                  setNewSpaceName("");
                                }}
                                className={`px-2 py-1 rounded text-sm ${
                                  isDarkMode
                                    ? "hover:bg-[#6272a4]"
                                    : "hover:bg-gray-200"
                                }`}
                              >
                                <FiX className="w-3 h-3" />
                              </button>
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}

              {/* Removed New Chat button - users now create chats from Home or within a selected space */}
            </div>
          </div>

          {/* Search and Tabs - More compact */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="flex flex-col sm:flex-row gap-3 mt-4"
          >
            {/* Search */}
            <div className="flex-1 relative">
              <input
                type="text"
                placeholder={
                  libraryView === "chats"
                    ? "Search threads..."
                    : "Search documents..."
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`w-full px-4 py-2 pl-10 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all ${
                  isDarkMode
                    ? "bg-[#44475a]/50 text-gray-100 placeholder-gray-400"
                    : "bg-gray-100/50 text-gray-900 placeholder-gray-500"
                }`}
              />
              <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
            </div>

            {/* Tabs - Only show for chats view */}
            {libraryView === "chats" && (
              <div className="flex gap-1">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;

                  // Calculate counts for each tab
                  const favoriteCount = threads.filter(
                    (t) => t.is_favorite
                  ).length;
                  const recentCount = threads.filter((t) => {
                    const weekAgo = new Date();
                    weekAgo.setDate(weekAgo.getDate() - 7);
                    return new Date(t.updated_at) > weekAgo;
                  }).length;

                  const tabCounts = {
                    all: threads.length,
                    recent: recentCount,
                    favorites: favoriteCount,
                  };

                  const count =
                    tabCounts[tab.id as keyof typeof tabCounts] || 0;

                  return (
                    <motion.button
                      key={tab.id}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setActiveTab(tab.id)}
                      className={`px-3 py-2 rounded-lg flex items-center gap-2 transition-all duration-200 relative ${
                        isActive
                          ? isDarkMode
                            ? "bg-[#44475a] text-purple-400 shadow-lg"
                            : "bg-purple-100 text-purple-700 shadow-lg"
                          : isDarkMode
                          ? "text-gray-400 hover:bg-[#44475a]/50 hover:text-gray-300"
                          : "text-gray-600 hover:bg-gray-100 hover:text-gray-700"
                      }`}
                    >
                      <motion.div
                        animate={
                          tab.id === "favorites" && favoriteCount > 0
                            ? {
                                rotate: [0, -10, 10, -5, 0],
                                scale: [1, 1.1, 1],
                              }
                            : {}
                        }
                        transition={{
                          duration: 0.8,
                          repeat: Infinity,
                          repeatDelay: 3,
                        }}
                      >
                        <Icon
                          className={`w-4 h-4 ${
                            tab.id === "favorites" && favoriteCount > 0
                              ? "text-yellow-400"
                              : ""
                          }`}
                        />
                      </motion.div>
                      <span className="hidden sm:inline">{tab.label}</span>

                      {/* Count badge */}
                      <AnimatePresence>
                        {count > 0 && (
                          <motion.span
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0, opacity: 0 }}
                            transition={{
                              type: "spring",
                              stiffness: 500,
                              damping: 25,
                            }}
                            className={`px-1.5 py-0.5 text-xs rounded-full font-medium ${
                              isActive
                                ? isDarkMode
                                  ? "bg-purple-500/30 text-purple-200"
                                  : "bg-purple-200 text-purple-800"
                                : isDarkMode
                                ? "bg-gray-600/50 text-gray-300"
                                : "bg-gray-200 text-gray-600"
                            }`}
                          >
                            {count}
                          </motion.span>
                        )}
                      </AnimatePresence>

                      {/* Active indicator */}
                      {isActive && (
                        <motion.div
                          layoutId="activeTabIndicator"
                          className={`absolute inset-0 rounded-lg -z-10 ${
                            isDarkMode ? "bg-[#44475a]" : "bg-purple-100"
                          }`}
                          transition={{
                            type: "spring",
                            stiffness: 500,
                            damping: 30,
                          }}
                        />
                      )}
                    </motion.button>
                  );
                })}
              </div>
            )}
          </motion.div>
        </motion.div>

        {/* Main Content Area */}
        <div className="flex-1 overflow-y-auto px-4 py-4">
          {/* Removed inline New Chat Creation - users create chats from Home page or within spaces */}

          {/* Loading State */}
          {(loading || documentsLoading) && libraryView === "chats" && (
            <div
              className={
                viewMode === "grid"
                  ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2"
                  : "space-y-2"
              }
            >
              {Array.from({ length: 12 }).map((_, index) => (
                <div
                  key={index}
                  className={`rounded-xl animate-pulse backdrop-blur-sm border ${
                    isDarkMode
                      ? "bg-gradient-to-br from-[#44475a]/60 to-[#6366f1]/5 border-gray-600/20 shadow-md shadow-black/10"
                      : "bg-gradient-to-br from-white/80 to-purple-50/20 border-gray-200/30 shadow-md shadow-gray-900/5"
                  } ${viewMode === "list" ? "flex gap-3 p-3" : "p-2"}`}
                >
                  {viewMode === "grid" ? (
                    <>
                      <div
                        className={`h-3 rounded mb-1 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-2 rounded mb-1 w-3/4 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-2 rounded w-1/2 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                    </>
                  ) : (
                    <>
                      <div className="flex-1 mr-3 sm:mr-4">
                        <div
                          className={`h-4 rounded mb-1 ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                        <div
                          className={`h-3 rounded w-2/3 ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                      <div className="w-32 sm:w-auto sm:min-w-32 flex-shrink-0">
                        <div
                          className={`h-3 rounded ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                      <div className="w-16 flex-shrink-0">
                        <div
                          className={`h-3 rounded ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Documents Loading State */}
          {documentsLoading && libraryView === "documents" && (
            <div
              className={
                viewMode === "grid"
                  ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2"
                  : "space-y-2"
              }
            >
              {Array.from({ length: 12 }).map((_, index) => (
                <div
                  key={index}
                  className={`rounded-xl animate-pulse backdrop-blur-sm border ${
                    isDarkMode
                      ? "bg-gradient-to-br from-[#44475a]/60 to-[#6366f1]/5 border-gray-600/20 shadow-md shadow-black/10"
                      : "bg-gradient-to-br from-white/80 to-purple-50/20 border-gray-200/30 shadow-md shadow-gray-900/5"
                  } ${viewMode === "list" ? "flex gap-3 p-3" : "p-2"}`}
                >
                  {viewMode === "grid" ? (
                    <>
                      <div
                        className={`h-3 rounded mb-1 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-2 rounded mb-1 w-3/4 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                      <div
                        className={`h-2 rounded w-1/2 ${
                          isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                        }`}
                      />
                    </>
                  ) : (
                    <>
                      <div className="flex-1 mr-3 sm:mr-4">
                        <div
                          className={`h-4 rounded mb-1 ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                        <div
                          className={`h-3 rounded w-2/3 ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                      <div className="w-32 sm:w-auto sm:min-w-32 flex-shrink-0">
                        <div
                          className={`h-3 rounded ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                      <div className="w-16 flex-shrink-0">
                        <div
                          className={`h-3 rounded ${
                            isDarkMode ? "bg-[#282a36]" : "bg-gray-200"
                          }`}
                        />
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Threads Display - Grid or List View */}
          {!loading && libraryView === "chats" && (
            <motion.div
              key="threads-container"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={
                viewMode === "grid"
                  ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-2"
                  : "space-y-2 overflow-hidden"
              }
            >
              {filteredThreads.length === 0 ? (
                <div className="col-span-full text-center py-8">
                  <FiMessageCircle
                    className={`w-10 h-10 mx-auto mb-3 ${
                      isDarkMode ? "text-gray-600" : "text-gray-400"
                    }`}
                  />
                  <p
                    className={`text-base font-medium mb-2 ${
                      isDarkMode ? "text-gray-400" : "text-gray-600"
                    }`}
                  >
                    {searchQuery ? "No threads found" : "No threads yet"}
                  </p>
                  <p
                    className={`text-sm ${
                      isDarkMode ? "text-gray-600" : "text-gray-500"
                    }`}
                  >
                    {searchQuery
                      ? "Try adjusting your search terms"
                      : "Start a new conversation to create your first thread"}
                  </p>
                </div>
              ) : (
                filteredThreads.map((thread) => {
                  // Compute last message and message count from sub_threads_data
                  const lastMessage =
                    thread.sub_threads_data &&
                    thread.sub_threads_data.length > 0
                      ? thread.sub_threads_data[
                          thread.sub_threads_data.length - 1
                        ].query
                      : "";
                  const messageCount = thread.sub_threads_data
                    ? thread.sub_threads_data.length * 2
                    : 0; // Query + Answer pairs

                  if (viewMode === "list") {
                    return (
                      <motion.div
                        key={thread._id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{
                          opacity: 1,
                          x: 0,
                          y: thread.is_favorite ? [0, -1, 0] : 0,
                        }}
                        transition={{
                          x: { duration: 0.3 },
                          opacity: { duration: 0.3 },
                          y: thread.is_favorite
                            ? {
                                duration: 3,
                                repeat: Infinity,
                                ease: "easeInOut",
                              }
                            : {},
                        }}
                        whileHover={{
                          boxShadow: thread.is_favorite
                            ? "0 8px 25px -5px rgba(251, 191, 36, 0.25)"
                            : "0 4px 20px -2px rgba(0, 0, 0, 0.1)",
                        }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => handleThreadClick(thread.chat_id)}
                        className={`group relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300 p-3 flex items-center gap-3 sm:gap-4 backdrop-blur-sm ${
                          thread.is_favorite
                            ? isDarkMode
                              ? "bg-gradient-to-r from-[#44475a]/95 via-[#44475a]/90 to-[#6366f1]/10 border border-yellow-400/30 shadow-lg shadow-yellow-400/20 hover:shadow-xl hover:shadow-yellow-400/25 hover:border-yellow-300/50"
                              : "bg-gradient-to-r from-white via-amber-50/30 to-yellow-100/40 border border-yellow-300/40 shadow-lg shadow-yellow-400/15 hover:shadow-xl hover:shadow-yellow-400/20 hover:border-yellow-200/60"
                            : isDarkMode
                            ? "bg-gradient-to-r from-[#44475a]/90 via-[#44475a]/85 to-[#6366f1]/5 border border-gray-600/30 hover:border-purple-400/40 shadow-md shadow-black/10 hover:shadow-lg hover:shadow-purple-500/10"
                            : "bg-gradient-to-r from-white via-slate-50/50 to-purple-50/30 border border-gray-200/60 hover:border-purple-300/50 shadow-md shadow-gray-900/5 hover:shadow-lg hover:shadow-purple-500/10"
                        }`}
                      >
                        {/* Subtle accent border */}
                        <div
                          className={`absolute left-0 top-0 bottom-0 w-1 rounded-l-xl ${
                            thread.is_favorite
                              ? "bg-gradient-to-b from-yellow-400 to-yellow-500"
                              : isDarkMode
                              ? "bg-gradient-to-b from-purple-500 to-purple-600 opacity-40"
                              : "bg-gradient-to-b from-purple-400 to-purple-500 opacity-30"
                          }`}
                        />

                        {/* List View Content */}
                        <div className="flex-1 min-w-0 mr-3 sm:mr-4">
                          <h3
                            className={`text-sm font-semibold line-clamp-1 mb-1 bg-gradient-to-r ${
                              isDarkMode
                                ? "from-gray-100 to-gray-200 bg-clip-text text-transparent"
                                : "from-gray-900 to-gray-700 bg-clip-text text-transparent"
                            }`}
                          >
                            {thread.title}
                          </h3>

                          {lastMessage && (
                            <p
                              className={`text-xs line-clamp-1 ${
                                isDarkMode ? "text-gray-400" : "text-gray-600"
                              }`}
                            >
                              {lastMessage}
                            </p>
                          )}
                        </div>

                        {/* Metadata - Fixed width for consistency */}
                        <div className="flex items-center gap-2 text-xs flex-shrink-0 w-32 sm:w-auto sm:min-w-32">
                          <div className="flex items-center gap-1">
                            <FiCalendar className="w-3 h-3 text-gray-500 flex-shrink-0" />
                            <span className="text-gray-500 truncate hidden sm:inline">
                              {formatTimestamp(thread.updated_at)}
                            </span>
                            <span className="text-gray-500 sm:hidden">
                              {formatTimestamp(thread.updated_at).split(" ")[0]}
                            </span>
                          </div>

                          {messageCount > 0 && (
                            <div className="flex items-center gap-1">
                              <FiMessageCircle className="w-3 h-3 text-gray-500 flex-shrink-0" />
                              <span className="text-gray-500">
                                {messageCount}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Actions - Fixed width for consistency */}
                        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex-shrink-0 w-24 justify-end">
                          <motion.button
                            onClick={(e) => toggleFavorite(thread, e)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className={`relative p-1.5 rounded-lg backdrop-blur-sm transition-all duration-300 ${
                              thread.is_favorite
                                ? "text-yellow-400 bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 shadow-lg shadow-yellow-500/30 border border-yellow-400/20"
                                : isDarkMode
                                ? "text-gray-400 hover:text-yellow-400 hover:bg-gradient-to-br hover:from-yellow-500/10 hover:to-yellow-600/5 hover:shadow-lg hover:shadow-yellow-500/20 hover:border hover:border-yellow-400/20"
                                : "text-gray-400 hover:text-yellow-500 hover:bg-gradient-to-br hover:from-yellow-500/10 hover:to-yellow-600/5 hover:shadow-lg hover:shadow-yellow-500/20 hover:border hover:border-yellow-400/20"
                            }`}
                            title={
                              thread.is_favorite
                                ? "Remove from favorites"
                                : "Add to favorites"
                            }
                          >
                            <motion.div
                              key={thread.is_favorite ? "filled" : "outline"}
                              initial={{ scale: 0.8, opacity: 0 }}
                              animate={{
                                scale: 1,
                                opacity: 1,
                                rotate: thread.is_favorite
                                  ? [0, -15, 15, -10, 0]
                                  : 0,
                              }}
                              transition={{
                                scale: {
                                  type: "spring",
                                  stiffness: 500,
                                  damping: 15,
                                },
                                opacity: { duration: 0.2 },
                                rotate: { duration: 0.6, ease: "easeInOut" },
                              }}
                              className="flex items-center justify-center w-3 h-3"
                            >
                              <FiStar
                                className={`w-3 h-3 ${
                                  thread.is_favorite ? "fill-current" : ""
                                }`}
                              />
                            </motion.div>

                            {/* Sparkle effect for favorites */}
                            <AnimatePresence>
                              {thread.is_favorite && (
                                <div
                                  key={`sparkles-${thread.chat_id}`}
                                  className="absolute inset-0 pointer-events-none"
                                >
                                  <motion.div
                                    className="absolute -top-1 -right-1 w-1 h-1 bg-yellow-400 rounded-full"
                                    initial={{ scale: 0, opacity: 0 }}
                                    animate={{
                                      scale: [0, 1, 0],
                                      opacity: [0, 1, 0],
                                    }}
                                    transition={{
                                      duration: 1,
                                      repeat: Infinity,
                                      delay: 0,
                                    }}
                                  />
                                  <motion.div
                                    className="absolute -top-0.5 -left-1 w-0.5 h-0.5 bg-yellow-300 rounded-full"
                                    initial={{ scale: 0, opacity: 0 }}
                                    animate={{
                                      scale: [0, 1, 0],
                                      opacity: [0, 1, 0],
                                    }}
                                    transition={{
                                      duration: 1,
                                      repeat: Infinity,
                                      delay: 0.3,
                                    }}
                                  />
                                  <motion.div
                                    className="absolute -bottom-1 -left-0.5 w-0.5 h-0.5 bg-yellow-200 rounded-full"
                                    initial={{ scale: 0, opacity: 0 }}
                                    animate={{
                                      scale: [0, 1, 0],
                                      opacity: [0, 1, 0],
                                    }}
                                    transition={{
                                      duration: 1,
                                      repeat: Infinity,
                                      delay: 0.6,
                                    }}
                                  />
                                </div>
                              )}
                            </AnimatePresence>
                          </motion.button>
                          <motion.button
                            onClick={(e) => handleMoveClick(thread, e)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className={`p-1.5 rounded-lg backdrop-blur-sm transition-all duration-300 ${
                              isDarkMode
                                ? "text-gray-400 hover:text-blue-400 hover:bg-gradient-to-br hover:from-blue-500/10 hover:to-blue-600/5 hover:shadow-lg hover:shadow-blue-500/20 hover:border hover:border-blue-400/20"
                                : "text-gray-400 hover:text-blue-500 hover:bg-gradient-to-br hover:from-blue-500/10 hover:to-blue-600/5 hover:shadow-lg hover:shadow-blue-500/20 hover:border hover:border-blue-400/20"
                            }`}
                            title="Move to space"
                          >
                            <motion.div
                              whileHover={{ scale: [1, 1.1, 1] }}
                              transition={{ duration: 0.3 }}
                            >
                              <FiFolder className="w-3 h-3" />
                            </motion.div>
                          </motion.button>
                          <motion.button
                            onClick={(e) => handleDeleteClick(thread, e)}
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            className={`p-1.5 rounded-lg backdrop-blur-sm transition-all duration-300 ${
                              isDarkMode
                                ? "text-gray-400 hover:text-red-400 hover:bg-gradient-to-br hover:from-red-500/10 hover:to-red-600/5 hover:shadow-lg hover:shadow-red-500/20 hover:border hover:border-red-400/20"
                                : "text-gray-400 hover:text-red-500 hover:bg-gradient-to-br hover:from-red-500/10 hover:to-red-600/5 hover:shadow-lg hover:shadow-red-500/20 hover:border hover:border-red-400/20"
                            }`}
                            title="Delete chat"
                          >
                            <motion.div
                              whileHover={{ rotate: [0, -5, 5, 0] }}
                              transition={{ duration: 0.3 }}
                            >
                              <FiTrash2 className="w-3 h-3" />
                            </motion.div>
                          </motion.button>
                        </div>
                      </motion.div>
                    );
                  }

                  // Grid View (existing implementation)
                  return (
                    <motion.div
                      key={thread._id}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{
                        opacity: 1,
                        scale: 1,
                        y: thread.is_favorite ? [0, -2, 0] : 0,
                      }}
                      transition={{
                        scale: { duration: 0.3 },
                        opacity: { duration: 0.3 },
                        y: thread.is_favorite
                          ? { duration: 3, repeat: Infinity, ease: "easeInOut" }
                          : {},
                      }}
                      whileHover={{
                        boxShadow: thread.is_favorite
                          ? "0 20px 40px -12px rgba(251, 191, 36, 0.25)"
                          : "0 10px 30px -4px rgba(0, 0, 0, 0.1)",
                      }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleThreadClick(thread.chat_id)}
                      className={`group relative overflow-hidden rounded-xl cursor-pointer transition-all duration-300 backdrop-blur-sm ${
                        thread.is_favorite
                          ? isDarkMode
                            ? "bg-gradient-to-br from-[#44475a]/95 via-[#44475a]/90 to-[#6366f1]/10 border border-yellow-400/30 shadow-lg shadow-yellow-400/20 hover:shadow-xl hover:shadow-yellow-400/25 hover:border-yellow-300/50"
                            : "bg-gradient-to-br from-white via-amber-50/40 to-yellow-100/50 border border-yellow-300/40 shadow-lg shadow-yellow-400/15 hover:shadow-xl hover:shadow-yellow-400/20 hover:border-yellow-200/60"
                          : isDarkMode
                          ? "bg-gradient-to-br from-[#44475a]/90 via-[#44475a]/85 to-[#6366f1]/5 border border-gray-600/30 hover:border-purple-400/40 shadow-md shadow-black/10 hover:shadow-lg hover:shadow-purple-500/10"
                          : "bg-gradient-to-br from-white via-slate-50/60 to-purple-50/40 border border-gray-200/60 hover:border-purple-300/50 shadow-md shadow-gray-900/5 hover:shadow-lg hover:shadow-purple-500/10"
                      }`}
                    >
                      {/* Subtle accent border */}
                      <div
                        className={`absolute top-0 left-0 right-0 h-1 rounded-t-xl ${
                          thread.is_favorite
                            ? "bg-gradient-to-r from-yellow-400 to-yellow-500"
                            : isDarkMode
                            ? "bg-gradient-to-r from-purple-500 to-purple-600 opacity-40"
                            : "bg-gradient-to-r from-purple-400 to-purple-500 opacity-30"
                        }`}
                      />

                      <div className="p-2">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-1">
                          <div className="flex-1 min-w-0">
                            <h3
                              className={`text-xs font-semibold mb-1 line-clamp-2 bg-gradient-to-r ${
                                isDarkMode
                                  ? "from-gray-100 to-gray-200 bg-clip-text text-transparent"
                                  : "from-gray-900 to-gray-700 bg-clip-text text-transparent"
                              }`}
                            >
                              {thread.title}
                            </h3>
                            <div className="flex items-center gap-1 text-xs">
                              <FiCalendar className="w-2.5 h-2.5 text-gray-500" />
                              <span className="text-gray-500 text-xs">
                                {formatTimestamp(thread.updated_at)}
                              </span>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <motion.button
                              onClick={(e) => toggleFavorite(thread, e)}
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              className={`relative p-1 rounded backdrop-blur-sm transition-all duration-300 ${
                                thread.is_favorite
                                  ? "text-yellow-400 bg-gradient-to-br from-yellow-500/20 to-yellow-600/10 shadow-lg shadow-yellow-500/30 border border-yellow-400/20"
                                  : isDarkMode
                                  ? "text-gray-400 hover:text-yellow-400 hover:bg-gradient-to-br hover:from-yellow-500/10 hover:to-yellow-600/5 hover:shadow-lg hover:shadow-yellow-500/20 hover:border hover:border-yellow-400/20"
                                  : "text-gray-400 hover:text-yellow-500 hover:bg-gradient-to-br hover:from-yellow-500/10 hover:to-yellow-600/5 hover:shadow-lg hover:shadow-yellow-500/20 hover:border hover:border-yellow-400/20"
                              }`}
                              title={
                                thread.is_favorite
                                  ? "Remove from favorites"
                                  : "Add to favorites"
                              }
                            >
                              {/* Star icon - maintains position */}
                              <motion.div
                                key={thread.is_favorite ? "filled" : "outline"}
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{
                                  scale: 1,
                                  opacity: 1,
                                  rotate: thread.is_favorite
                                    ? [0, -15, 15, -10, 0]
                                    : 0,
                                }}
                                transition={{
                                  scale: {
                                    type: "spring",
                                    stiffness: 500,
                                    damping: 15,
                                  },
                                  opacity: { duration: 0.2 },
                                  rotate: { duration: 0.6, ease: "easeInOut" },
                                }}
                                className="flex items-center justify-center w-3 h-3"
                              >
                                <FiStar
                                  className={`w-3 h-3 ${
                                    thread.is_favorite ? "fill-current" : ""
                                  }`}
                                />
                              </motion.div>

                              {/* Sparkle effect for favorites */}
                              <AnimatePresence>
                                {thread.is_favorite && (
                                  <div
                                    key={`sparkles-grid-${thread.chat_id}`}
                                    className="absolute inset-0 pointer-events-none"
                                  >
                                    <motion.div
                                      className="absolute -top-1 -right-1 w-1 h-1 bg-yellow-400 rounded-full"
                                      initial={{ scale: 0, opacity: 0 }}
                                      animate={{
                                        scale: [0, 1, 0],
                                        opacity: [0, 1, 0],
                                      }}
                                      transition={{
                                        duration: 1,
                                        repeat: Infinity,
                                        delay: 0,
                                      }}
                                    />
                                    <motion.div
                                      className="absolute -top-0.5 -left-1 w-0.5 h-0.5 bg-yellow-300 rounded-full"
                                      initial={{ scale: 0, opacity: 0 }}
                                      animate={{
                                        scale: [0, 1, 0],
                                        opacity: [0, 1, 0],
                                      }}
                                      transition={{
                                        duration: 1,
                                        repeat: Infinity,
                                        delay: 0.3,
                                      }}
                                    />
                                    <motion.div
                                      className="absolute -bottom-1 -left-0.5 w-0.5 h-0.5 bg-yellow-200 rounded-full"
                                      initial={{ scale: 0, opacity: 0 }}
                                      animate={{
                                        scale: [0, 1, 0],
                                        opacity: [0, 1, 0],
                                      }}
                                      transition={{
                                        duration: 1,
                                        repeat: Infinity,
                                        delay: 0.6,
                                      }}
                                    />
                                  </div>
                                )}
                              </AnimatePresence>
                            </motion.button>
                            <motion.button
                              onClick={(e) => handleMoveClick(thread, e)}
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              className={`p-1 rounded backdrop-blur-sm transition-all duration-300 ${
                                isDarkMode
                                  ? "text-gray-400 hover:text-blue-400 hover:bg-gradient-to-br hover:from-blue-500/10 hover:to-blue-600/5 hover:shadow-lg hover:shadow-blue-500/20 hover:border hover:border-blue-400/20"
                                  : "text-gray-400 hover:text-blue-500 hover:bg-gradient-to-br hover:from-blue-500/10 hover:to-blue-600/5 hover:shadow-lg hover:shadow-blue-500/20 hover:border hover:border-blue-400/20"
                              }`}
                              title="Move to space"
                            >
                              <motion.div
                                whileHover={{ scale: [1, 1.1, 1] }}
                                transition={{ duration: 0.3 }}
                              >
                                <FiFolder className="w-3 h-3" />
                              </motion.div>
                            </motion.button>
                            <motion.button
                              onClick={(e) => handleDeleteClick(thread, e)}
                              whileHover={{ scale: 1.05 }}
                              whileTap={{ scale: 0.95 }}
                              className={`p-1 rounded backdrop-blur-sm transition-all duration-300 ${
                                isDarkMode
                                  ? "text-gray-400 hover:text-red-400 hover:bg-gradient-to-br hover:from-red-500/10 hover:to-red-600/5 hover:shadow-lg hover:shadow-red-500/20 hover:border hover:border-red-400/20"
                                  : "text-gray-400 hover:text-red-500 hover:bg-gradient-to-br hover:from-red-500/10 hover:to-red-600/5 hover:shadow-lg hover:shadow-red-500/20 hover:border hover:border-red-400/20"
                              }`}
                              title="Delete chat"
                            >
                              <motion.div
                                whileHover={{ rotate: [0, -5, 5, 0] }}
                                transition={{ duration: 0.3 }}
                              >
                                <FiTrash2 className="w-3 h-3" />
                              </motion.div>
                            </motion.button>
                          </div>
                        </div>

                        {/* Content */}
                        {lastMessage && (
                          <p
                            className={`text-xs line-clamp-1 mt-1 ${
                              isDarkMode ? "text-gray-400" : "text-gray-600"
                            }`}
                          >
                            {lastMessage}
                          </p>
                        )}

                        {/* Message count */}
                        {messageCount > 0 && (
                          <div className="mt-1 pt-1 border-t border-gray-200/10">
                            <span
                              className={`text-xs ${
                                isDarkMode ? "text-gray-600" : "text-gray-400"
                              }`}
                            >
                              {messageCount} msg{messageCount !== 1 ? "s" : ""}
                            </span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })
              )}
            </motion.div>
          )}

          {/* Documents Display - Grid or List View */}
          {!documentsLoading && libraryView === "documents" && (
            <motion.div
              key="documents-container"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3 }}
              className="w-full"
            >
              {/* Selection Header Bar - Always visible when documents exist */}
              {filteredDocuments.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`sticky top-0 z-10 mb-3 px-1 py-2 rounded-lg backdrop-blur-sm border ${
                    selectedDocuments.size > 0
                      ? isDarkMode
                        ? "bg-purple-600/20 border-purple-500/30"
                        : "bg-purple-50 border-purple-200"
                      : isDarkMode
                      ? "bg-[#282a36]/50 border-gray-700/50"
                      : "bg-white/50 border-gray-200/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                          type="checkbox"
                          checked={
                            selectedDocuments.size ===
                              filteredDocuments.length &&
                            filteredDocuments.length > 0
                          }
                          onChange={handleSelectAll}
                          className="w-4 h-4 rounded cursor-pointer accent-purple-600"
                        />
                        <span
                          className={`text-sm font-medium transition-colors ${
                            isDarkMode
                              ? "text-gray-300 group-hover:text-gray-200"
                              : "text-gray-700 group-hover:text-gray-900"
                          }`}
                        >
                          {selectedDocuments.size > 0
                            ? `${selectedDocuments.size} selected`
                            : "Select all"}
                        </span>
                      </label>
                    </div>

                    {/* Compact Batch Actions */}
                    {selectedDocuments.size > 0 && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex items-center gap-1"
                      >
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={handleBatchEnable}
                          className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                            isDarkMode
                              ? "bg-green-600/20 text-green-400 hover:bg-green-600/30"
                              : "bg-green-50 text-green-700 hover:bg-green-100"
                          }`}
                        >
                          Enable
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={handleBatchDisable}
                          className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                            isDarkMode
                              ? "bg-yellow-600/20 text-yellow-400 hover:bg-yellow-600/30"
                              : "bg-yellow-50 text-yellow-700 hover:bg-yellow-100"
                          }`}
                        >
                          Disable
                        </motion.button>
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={handleBatchDelete}
                          className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-all ${
                            isDarkMode
                              ? "bg-red-600/20 text-red-400 hover:bg-red-600/30"
                              : "bg-red-50 text-red-700 hover:bg-red-100"
                          }`}
                        >
                          Delete
                        </motion.button>
                      </motion.div>
                    )}
                  </div>
                </motion.div>
              )}

              {/* Documents Grid/List Container */}
              <div
                className={
                  viewMode === "grid"
                    ? "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2"
                    : "space-y-1.5"
                }
              >
                {filteredDocuments.length === 0 ? (
                  <div className="col-span-full text-center py-12">
                    <div
                      className={`inline-flex p-4 rounded-2xl mb-4 ${
                        isDarkMode ? "bg-[#44475a]/30" : "bg-gray-100/50"
                      }`}
                    >
                      <FiFileText
                        className={`w-8 h-8 ${
                          isDarkMode ? "text-gray-500" : "text-gray-400"
                        }`}
                      />
                    </div>
                    <p
                      className={`text-sm font-medium mb-1 ${
                        isDarkMode ? "text-gray-300" : "text-gray-700"
                      }`}
                    >
                      {searchQuery ? "No documents found" : "No documents yet"}
                    </p>
                    <p
                      className={`text-xs mb-4 ${
                        isDarkMode ? "text-gray-500" : "text-gray-500"
                      }`}
                    >
                      {searchQuery
                        ? "Try adjusting your search terms"
                        : "Upload PDF documents to get started"}
                    </p>
                    {!searchQuery && (
                      <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => setShowUploadModal(true)}
                        className={`px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 mx-auto transition-colors ${
                          isDarkMode
                            ? "bg-purple-600 hover:bg-purple-700 text-white"
                            : "bg-purple-600 hover:bg-purple-700 text-white"
                        }`}
                      >
                        <FiUpload className="w-4 h-4" />
                        Upload Documents
                      </motion.button>
                    )}
                  </div>
                ) : (
                  filteredDocuments.map((document) => {
                    const documentId =
                      document.document_id || document.blob_name;
                    const isSelected = selectedDocuments.has(documentId);
                    const fileSizeMB = (
                      document.file_size /
                      1024 /
                      1024
                    ).toFixed(2);

                    if (viewMode === "list") {
                      return (
                        <motion.div
                          key={documentId}
                          initial={{ opacity: 0, y: 5 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.2 }}
                          whileHover={{ scale: 1.005 }}
                          className={`group relative rounded-lg transition-all duration-200 ${
                            isSelected
                              ? isDarkMode
                                ? "bg-purple-600/20 border border-purple-500/40"
                                : "bg-purple-50 border border-purple-200"
                              : document.enabled === false
                              ? isDarkMode
                                ? "bg-[#44475a]/40 border border-gray-700/30 opacity-60"
                                : "bg-gray-50 border border-gray-200 opacity-60"
                              : isDarkMode
                              ? "bg-[#44475a]/60 border border-gray-700/30 hover:border-purple-500/40 hover:bg-[#44475a]/70"
                              : "bg-white border border-gray-200 hover:border-purple-300 hover:shadow-sm"
                          }`}
                        >
                          <div className="flex items-center gap-3 p-2.5">
                            {/* Checkbox */}
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) =>
                                handleDocumentSelect(documentId, e)
                              }
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4 rounded cursor-pointer accent-purple-600 flex-shrink-0"
                            />

                            {/* Document Icon */}
                            <div
                              className={`flex-shrink-0 p-1.5 rounded ${
                                document.enabled === false
                                  ? isDarkMode
                                    ? "bg-gray-700/50"
                                    : "bg-gray-200"
                                  : isDarkMode
                                  ? "bg-purple-600/20"
                                  : "bg-purple-100"
                              }`}
                            >
                              <FiFileText
                                className={`w-4 h-4 ${
                                  document.enabled === false
                                    ? isDarkMode
                                      ? "text-gray-500"
                                      : "text-gray-400"
                                    : isDarkMode
                                    ? "text-purple-400"
                                    : "text-purple-600"
                                }`}
                              />
                            </div>

                            {/* Document Info */}
                            <div className="flex-1 min-w-0">
                              <h3
                                className={`text-sm font-medium truncate mb-0.5 ${
                                  isDarkMode ? "text-gray-200" : "text-gray-900"
                                }`}
                              >
                                {document.filename}
                              </h3>
                              <div className="flex items-center gap-1.5 text-xs">
                                <span
                                  className={
                                    isDarkMode
                                      ? "text-gray-500"
                                      : "text-gray-500"
                                  }
                                >
                                  {fileSizeMB} MB
                                </span>
                                <span
                                  className={
                                    isDarkMode
                                      ? "text-gray-600"
                                      : "text-gray-400"
                                  }
                                >
                                  •
                                </span>
                                <span
                                  className={
                                    isDarkMode
                                      ? "text-gray-500"
                                      : "text-gray-500"
                                  }
                                >
                                  {formatTimestamp(document.created_at)}
                                </span>
                              </div>
                            </div>

                            {/* Status Badge */}
                            <div
                              className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${
                                document.enabled === false
                                  ? isDarkMode
                                    ? "bg-gray-700/50 text-gray-400"
                                    : "bg-gray-200 text-gray-500"
                                  : isDarkMode
                                  ? "bg-green-600/20 text-green-400"
                                  : "bg-green-100 text-green-700"
                              }`}
                            >
                              {document.enabled === false
                                ? "Disabled"
                                : "Enabled"}
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                              <motion.button
                                onClick={(e) =>
                                  handleDocumentToggleEnable(document, e)
                                }
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                className={`p-1.5 rounded transition-colors ${
                                  document.enabled === false
                                    ? isDarkMode
                                      ? "text-green-400 hover:bg-green-600/20"
                                      : "text-green-600 hover:bg-green-100"
                                    : isDarkMode
                                    ? "text-yellow-400 hover:bg-yellow-600/20"
                                    : "text-yellow-600 hover:bg-yellow-100"
                                }`}
                                title={
                                  document.enabled === false
                                    ? "Enable document"
                                    : "Disable document"
                                }
                              >
                                {document.enabled === false ? (
                                  <FiToggleRight className="w-4 h-4" />
                                ) : (
                                  <FiToggleLeft className="w-4 h-4" />
                                )}
                              </motion.button>
                              <motion.button
                                onClick={(e) =>
                                  handleDocumentDeleteClick(document, e)
                                }
                                whileHover={{ scale: 1.1 }}
                                whileTap={{ scale: 0.9 }}
                                className={`p-1.5 rounded transition-colors ${
                                  isDarkMode
                                    ? "text-gray-400 hover:text-red-400 hover:bg-red-600/20"
                                    : "text-gray-400 hover:text-red-500 hover:bg-red-100"
                                }`}
                                title="Delete document"
                              >
                                <FiTrash2 className="w-4 h-4" />
                              </motion.button>
                            </div>
                          </div>
                        </motion.div>
                      );
                    }

                    // Grid View - Modern Minimal Card Design
                    return (
                      <motion.div
                        key={documentId}
                        initial={{ opacity: 0, scale: 0.96 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.2 }}
                        whileHover={{ y: -2 }}
                        className={`group relative rounded-xl overflow-hidden transition-all duration-200 ${
                          isSelected
                            ? isDarkMode
                              ? "bg-purple-600/10 border-2 border-purple-500/40 shadow-lg shadow-purple-500/10"
                              : "bg-purple-50/80 border-2 border-purple-300/60 shadow-md"
                            : document.enabled === false
                            ? isDarkMode
                              ? "bg-[#44475a]/20 border border-gray-700/20 opacity-50"
                              : "bg-gray-50/40 border border-gray-200/40 opacity-50"
                            : isDarkMode
                            ? "bg-[#44475a]/30 border border-gray-700/20 hover:bg-[#44475a]/40 hover:border-purple-500/30 hover:shadow-lg"
                            : "bg-white/80 border border-gray-200/50 hover:bg-white hover:border-purple-300/50 hover:shadow-md"
                        }`}
                      >
                        {/* Status Indicator - Top Edge */}
                        <div
                          className={`absolute top-0 left-0 right-0 h-0.5 ${
                            document.enabled === false
                              ? isDarkMode
                                ? "bg-gray-600"
                                : "bg-gray-400"
                              : isDarkMode
                              ? "bg-green-500"
                              : "bg-green-500"
                          }`}
                        />

                        {/* Checkbox - Top Right */}
                        <div className="absolute top-2 right-2 z-10">
                          <label className="cursor-pointer">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={(e) =>
                                handleDocumentSelect(documentId, e)
                              }
                              onClick={(e) => e.stopPropagation()}
                              className="w-4 h-4 rounded cursor-pointer accent-purple-600 bg-white/95 shadow-md border-0"
                            />
                          </label>
                        </div>

                        <div className="p-3 pt-4">
                          {/* Icon - Centered */}
                          <div className="flex justify-center mb-2">
                            <div
                              className={`p-2 rounded-lg transition-all ${
                                document.enabled === false
                                  ? isDarkMode
                                    ? "bg-gray-700/30"
                                    : "bg-gray-200/60"
                                  : isDarkMode
                                  ? "bg-purple-600/15 group-hover:bg-purple-600/25"
                                  : "bg-purple-100/70 group-hover:bg-purple-100"
                              }`}
                            >
                              <FiFileText
                                className={`w-5 h-5 ${
                                  document.enabled === false
                                    ? isDarkMode
                                      ? "text-gray-500"
                                      : "text-gray-400"
                                    : isDarkMode
                                    ? "text-purple-400"
                                    : "text-purple-600"
                                }`}
                              />
                            </div>
                          </div>

                          {/* Title */}
                          <h3
                            className={`text-xs font-semibold line-clamp-2 mb-1.5 text-center min-h-[2rem] leading-tight ${
                              isDarkMode ? "text-gray-100" : "text-gray-900"
                            }`}
                          >
                            {document.filename}
                          </h3>

                          {/* Metadata - Compact */}
                          <div className="flex items-center justify-center gap-1.5 mb-2.5 text-xs">
                            <span
                              className={
                                isDarkMode ? "text-gray-500" : "text-gray-500"
                              }
                            >
                              {fileSizeMB} MB
                            </span>
                          </div>

                          {/* Footer - Status and Actions */}
                          <div className="flex items-center justify-between pt-2 border-t border-gray-200/30 dark:border-gray-700/20">
                            {/* Status Dot */}
                            <div className="flex items-center gap-1">
                              <div
                                className={`w-1.5 h-1.5 rounded-full ${
                                  document.enabled === false
                                    ? isDarkMode
                                      ? "bg-gray-500"
                                      : "bg-gray-400"
                                    : isDarkMode
                                    ? "bg-green-500"
                                    : "bg-green-500"
                                }`}
                              />
                              <span
                                className={`text-xs ${
                                  isDarkMode ? "text-gray-400" : "text-gray-500"
                                }`}
                              >
                                {document.enabled === false ? "Off" : "On"}
                              </span>
                            </div>

                            {/* Actions */}
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <motion.button
                                onClick={(e) =>
                                  handleDocumentToggleEnable(document, e)
                                }
                                whileHover={{ scale: 1.15 }}
                                whileTap={{ scale: 0.9 }}
                                className={`p-2 rounded-lg transition-all ${
                                  document.enabled === false
                                    ? isDarkMode
                                      ? "text-green-400 hover:bg-green-600/20"
                                      : "text-green-600 hover:bg-green-100"
                                    : isDarkMode
                                    ? "text-yellow-400 hover:bg-yellow-600/20"
                                    : "text-yellow-600 hover:bg-yellow-100"
                                }`}
                                title={
                                  document.enabled === false
                                    ? "Enable"
                                    : "Disable"
                                }
                              >
                                {document.enabled === false ? (
                                  <FiToggleRight className="w-4 h-4" />
                                ) : (
                                  <FiToggleLeft className="w-4 h-4" />
                                )}
                              </motion.button>
                              <motion.button
                                onClick={(e) =>
                                  handleDocumentDeleteClick(document, e)
                                }
                                whileHover={{ scale: 1.15 }}
                                whileTap={{ scale: 0.9 }}
                                className={`p-2 rounded-lg transition-all ${
                                  isDarkMode
                                    ? "text-gray-400 hover:text-red-400 hover:bg-red-600/20"
                                    : "text-gray-400 hover:text-red-500 hover:bg-red-100"
                                }`}
                                title="Delete"
                              >
                                <FiTrash2 className="w-4 h-4" />
                              </motion.button>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* File Upload Modal */}
      <FileUploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title={
          libraryView === "chats"
            ? threadToDelete?.title || ""
            : documentToDelete?.filename || ""
        }
        isDeleting={isDeleting}
        description={
          libraryView === "chats"
            ? "This will permanently delete the chat and all its messages. This action cannot be undone."
            : "This will permanently delete the document from the knowledge base. This action cannot be undone."
        }
      />

      {/* Move to Space Modal - Compact Design */}
      <AnimatePresence>
        {moveModalOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => {
                setMoveModalOpen(false);
                setThreadToMove(null);
              }}
              className="fixed inset-0 bg-black/40 backdrop-blur-md z-50 flex items-center justify-center p-4"
            >
              {/* Modal */}
              <motion.div
                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                transition={{ type: "spring", duration: 0.3 }}
                onClick={(e) => e.stopPropagation()}
                className={`relative w-full max-w-sm mx-auto rounded-xl shadow-2xl overflow-hidden backdrop-blur-md ${
                  isDarkMode
                    ? "bg-gray-900/95 border border-gray-700/50"
                    : "bg-white/95 border border-gray-200/50"
                }`}
              >
                {/* Close button */}
                <button
                  onClick={() => {
                    setMoveModalOpen(false);
                    setThreadToMove(null);
                  }}
                  className={`absolute top-3 right-3 p-1.5 rounded-full transition-colors z-10 ${
                    isDarkMode
                      ? "hover:bg-gray-700/60 text-gray-400 hover:text-white"
                      : "hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                  }`}
                >
                  <FiX className="w-4 h-4" />
                </button>

                {/* Compact Header with Icon */}
                <div className="p-4 text-center">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.1, type: "spring" }}
                    className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                      isDarkMode ? "bg-blue-500/20" : "bg-blue-50"
                    }`}
                  >
                    <FiFolder className="w-6 h-6 text-blue-500" />
                  </motion.div>

                  <h3
                    className={`text-base font-semibold mb-2 ${
                      isDarkMode ? "text-white" : "text-gray-900"
                    }`}
                  >
                    Move to Space
                  </h3>

                  {/* Chat title preview */}
                  <div
                    className={`px-3 py-2 rounded-lg mb-3 ${
                      isDarkMode ? "bg-gray-800/60" : "bg-gray-50/80"
                    }`}
                  >
                    <p
                      className={`text-sm truncate ${
                        isDarkMode ? "text-gray-300" : "text-gray-700"
                      }`}
                    >
                      "{threadToMove?.title}"
                    </p>
                  </div>

                  <p
                    className={`text-xs mb-3 ${
                      isDarkMode ? "text-gray-400" : "text-gray-500"
                    }`}
                  >
                    Select a space to move this chat
                  </p>
                </div>

                {/* Compact Scrollable Space List */}
                <div
                  className={`mx-4 mb-4 rounded-lg max-h-48 overflow-y-auto ${
                    isDarkMode ? "bg-gray-800/40" : "bg-gray-50/60"
                  } p-1 space-y-1`}
                >
                  {/* Global/No Space Option */}
                  <motion.button
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={() => handleMoveToSpace(null)}
                    className={`w-full text-left px-3 py-2 rounded-md transition-all flex items-center gap-2 ${
                      !threadToMove?.space
                        ? isDarkMode
                          ? "bg-purple-600/30 text-purple-300"
                          : "bg-purple-100 text-purple-700"
                        : isDarkMode
                        ? "hover:bg-gray-700/60 text-gray-300"
                        : "hover:bg-gray-100 text-gray-700"
                    }`}
                  >
                    <FiFolder className="w-4 h-4 flex-shrink-0 text-gray-500" />
                    <span className="text-sm font-medium flex-1">Global</span>
                    {!threadToMove?.space && (
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded ${
                          isDarkMode ? "bg-purple-500/30" : "bg-purple-200"
                        }`}
                      >
                        ✓
                      </span>
                    )}
                  </motion.button>

                  {/* Space Options */}
                  {spaces &&
                    Array.isArray(spaces) &&
                    spaces.map((space) => (
                      <motion.button
                        key={space.id}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => handleMoveToSpace(space.id)}
                        className={`w-full text-left px-3 py-2 rounded-md transition-all flex items-center gap-2 ${
                          threadToMove?.space === space.id
                            ? isDarkMode
                              ? "bg-purple-600/30 text-purple-300"
                              : "bg-purple-100 text-purple-700"
                            : isDarkMode
                            ? "hover:bg-gray-700/60 text-gray-300"
                            : "hover:bg-gray-100 text-gray-700"
                        }`}
                      >
                        <FiFolder
                          className="w-4 h-4 flex-shrink-0"
                          style={{ color: space.color }}
                        />
                        <span className="text-sm font-medium flex-1 truncate">
                          {space.name}
                        </span>
                        {threadToMove?.space === space.id && (
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded ${
                              isDarkMode ? "bg-purple-500/30" : "bg-purple-200"
                            }`}
                          >
                            ✓
                          </span>
                        )}
                      </motion.button>
                    ))}
                </div>

                {/* Compact Cancel Button */}
                <div className="px-4 pb-4">
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => {
                      setMoveModalOpen(false);
                      setThreadToMove(null);
                    }}
                    className={`w-full px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${
                      isDarkMode
                        ? "bg-gray-700/60 hover:bg-gray-700 text-gray-300 hover:text-white"
                        : "bg-gray-100 hover:bg-gray-200 text-gray-700"
                    }`}
                  >
                    Cancel
                  </motion.button>
                </div>
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default Library;
