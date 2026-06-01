import React, { useCallback, useState } from "react";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import CloseIcon from "@mui/icons-material/Close";
import { useDropzone, FileRejection } from "react-dropzone";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import ClearAllIcon from "@mui/icons-material/ClearAll";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CircularProgress from "@mui/material/CircularProgress";
import toast from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";
import { graphRagApi } from "../../services/api";

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess?: (response: any) => void;
  maxFiles?: number;
}

const MAX_FILES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB per file

const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
  maxFiles = MAX_FILES,
}) => {
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  // Get user ID from localStorage (you might want to get this from auth context instead)
  const getUserId = (): string => {
    // Try to get from auth token or user data in localStorage
    const userData = localStorage.getItem('user_data');
    if (userData) {
      try {
        const parsed = JSON.parse(userData);
        return parsed.id || parsed.user_id || "1"; // fallback to "1" if no ID found
      } catch {
        return "1"; // fallback
      }
    }
    return "1"; // fallback user ID
  };

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      // Handle rejected files
      if (rejectedFiles.length > 0) {
        const reasons = rejectedFiles.map(fileRejection => {
          if (fileRejection.errors.some((error) => error.code === 'file-invalid-type')) {
            return 'Only PDF files are allowed';
          }
          if (fileRejection.errors.some((error) => error.code === 'file-too-large')) {
            return 'File size must be less than 10MB';
          }
          return 'Invalid file';
        });
        toast.error(reasons[0], {
          style: {
            borderRadius: "10px",
            background: "#ef4444",
            color: "#fff",
          },
        });
      }

      const remainingSlots = maxFiles - uploadedFiles.length;
      const filesToAdd = acceptedFiles.slice(0, remainingSlots);

      if (uploadedFiles.length + acceptedFiles.length > maxFiles) {
        toast.error(`You can only upload up to ${maxFiles} PDF files`, {
          style: {
            borderRadius: "10px",
            background: "#f59e0b",
            color: "#fff",
          },
        });
      }

      if (filesToAdd.length > 0) {
        setUploadedFiles((prevFiles) => [...prevFiles, ...filesToAdd]);
        toast.success(`Added ${filesToAdd.length} PDF file${filesToAdd.length > 1 ? 's' : ''}`, {
          style: {
            borderRadius: "10px",
            background: "#10b981",
            color: "#fff",
          },
        });
      }
    },
    [uploadedFiles, maxFiles]
  );

  const removeFile = (indexToRemove: number, event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setUploadedFiles((prevFiles) =>
      prevFiles.filter((_, index) => index !== indexToRemove)
    );
    toast.success("File removed", {
      style: {
        borderRadius: "10px",
        background: "#10b981",
        color: "#fff",
      },
    });
  };

  const clearAllFiles = (event: React.MouseEvent) => {
    event.preventDefault();
    event.stopPropagation();
    setUploadedFiles([]);
    toast.success("All files cleared", {
      style: {
        borderRadius: "10px",
        background: "#10b981",
        color: "#fff",
      },
    });
  };

  const handleUpload = async () => {
    if (uploadedFiles.length > 0) {
      setIsUploading(true);
      const userId = getUserId();

      try {
        console.log('Uploading files to GraphRAG:', {
          fileCount: uploadedFiles.length,
          fileNames: uploadedFiles.map(f => f.name),
          userId
        });

        const response = await graphRagApi.uploadFiles(uploadedFiles, userId, {
          force: true,
          extractionMethod: 'auto',
          maxWorkers: 4,
          useLlamaindex: true
        });

        if (response.error) {
          toast.error(response.error, {
            style: {
              borderRadius: "10px",
              background: "#ef4444",
              color: "#fff",
            },
          });
          return;
        }

        // Success
        if (response.data) {
          console.log('Upload successful:', response.data);
          toast.success(`${response.data.metadata.file_count} PDF file${response.data.metadata.file_count > 1 ? 's' : ''} uploaded successfully! ${response.data.message}`, {
            style: {
              borderRadius: "10px",
              background: "#10b981",
              color: "#fff",
            },
            duration: 4000,
          });
          
          if (onUploadSuccess) {
            onUploadSuccess(response.data);
          }
        }

        setUploadedFiles([]);
        onClose();
      } catch (error) {
        console.error('Upload error:', error);
        toast.error("Failed to upload files", {
          style: {
            borderRadius: "10px",
            background: "#ef4444",
            color: "#fff",
          },
        });
      } finally {
        setIsUploading(false);
      }
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: uploadedFiles.length >= maxFiles,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxSize: MAX_FILE_SIZE,
    multiple: true
  });

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={(e) => {
          // Only close if clicking the backdrop, not the modal content
          if (e.target === e.currentTarget) {
            onClose();
          }
        }}
      >
        <motion.div 
          className="relative bg-[#1a1a1a] rounded-xl shadow-2xl w-full max-w-sm border border-white/10"
          initial={{ scale: 0.95, y: 10 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.95, y: 10 }}
          transition={{ type: "spring", stiffness: 400, damping: 25 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Minimal Header */}
          <div className="flex justify-between items-center p-4 pb-2">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-red-500 rounded-full"></div>
              <h2 className="text-sm font-medium text-white">Upload PDFs</h2>
              <span className="text-xs text-gray-500">
                {uploadedFiles.length}/{maxFiles}
              </span>
            </div>
            <div className="flex items-center gap-1">
              {uploadedFiles.length > 0 && (
                <button
                  onClick={clearAllFiles}
                  className="text-xs text-gray-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-white/10"
                >
                  Clear
                </button>
              )}
              <IconButton
                onClick={onClose}
                size="small"
                sx={{ 
                  color: "#9ca3af",
                  "&:hover": {
                    color: "#fff",
                    backgroundColor: "rgba(255, 255, 255, 0.1)",
                  }
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </div>
          </div>

          {/* Compact Content */}
          <div className="px-4 pb-4">
            <div
              {...getRootProps()}
              className={`border border-dashed rounded-lg p-4 text-center cursor-pointer transition-all duration-200
                ${
                  uploadedFiles.length >= maxFiles
                    ? "border-gray-700 bg-gray-800/20 cursor-not-allowed"
                    : isDragActive
                    ? "border-red-500 bg-red-500/5"
                    : "border-gray-600 hover:border-gray-500 hover:bg-white/5"
                }`}
            >
              <input {...getInputProps()} />
              {uploadedFiles.length > 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <div className="space-y-2 mb-3">
                    {uploadedFiles.map((file, index) => (
                      <motion.div
                        key={index}
                        className="flex items-center justify-between p-2 rounded bg-white/5 hover:bg-white/10 transition-colors group"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                      >
                        <div className="flex items-center gap-2">
                          <InsertDriveFileIcon
                            sx={{ fontSize: 14, color: "#ef4444" }}
                          />
                          <div className="text-left">
                            <span className="text-gray-200 text-xs font-medium block truncate max-w-32">
                              {file.name}
                            </span>
                            <span className="text-gray-500 text-xs">
                              {(file.size / 1024 / 1024).toFixed(1)} MB
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={(e: React.MouseEvent) => removeFile(index, e)}
                          className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-red-400 p-1"
                        >
                          <DeleteOutlineIcon fontSize="small" />
                        </button>
                      </motion.div>
                    ))}
                  </div>
                  {uploadedFiles.length < maxFiles && (
                    <div className="text-center py-2 border-t border-white/10">
                      <p className="text-xs text-gray-400">
                        Drop more or click to browse
                      </p>
                    </div>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <CloudUploadIcon sx={{ fontSize: 32, color: "#9ca3af" }} />
                  <p className="mt-2 text-sm text-gray-300 font-medium">
                    {isDragActive
                      ? "Drop PDFs here"
                      : "Upload PDFs"}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    Max {maxFiles} files • 10MB each
                  </p>
                </motion.div>
              )}
            </div>

            {/* Compact Upload Button */}
            {uploadedFiles.length > 0 && (
              <motion.div
                className="mt-3 flex justify-end"
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: 0.1 }}
              >
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className={`text-white text-xs px-3 py-1.5 rounded-lg transition-colors font-medium flex items-center gap-1.5 ${
                    isUploading 
                      ? 'bg-gray-600 cursor-not-allowed' 
                      : 'bg-red-500 hover:bg-red-600'
                  }`}
                >
                  {isUploading ? (
                    <>
                      <CircularProgress size={14} sx={{ color: 'white' }} />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <UploadFileIcon sx={{ fontSize: 14 }} />
                      Upload {uploadedFiles.length}
                    </>
                  )}
                </button>
              </motion.div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default FileUploadModal;
