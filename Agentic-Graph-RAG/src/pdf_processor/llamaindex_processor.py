"""
LlamaIndex-based document processor for CogniVox.

This module provides document ingestion and processing using LlamaIndex,
replacing the custom processing pipeline with LlamaIndex's robust framework.
"""
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Handle async issues
try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    print("Note: nest_asyncio not available, async operations may have limitations")

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.core.node_parser import SimpleNodeParser, SentenceSplitter
from llama_index.core.extractors import TitleExtractor, QuestionsAnsweredExtractor
from llama_index.readers.file import PDFReader
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.core.schema import BaseNode, TextNode

from src.config import (
    CHUNK_SIZE, CHUNK_OVERLAP, OLLAMA_HOST, EMBEDDING_MODEL, 
    TEXT_GENERATION_MODEL
)
from src.pdf_processor.storage_adapter import DocumentStorageAdapter
from src.pdf_processor.llamaindex_embeddings import LlamaIndexEmbeddingsGenerator


class LlamaIndexProcessor:
    """
    Document processor using LlamaIndex for ingestion and processing.
    """
    
    def __init__(self, 
                 chunk_size: int = CHUNK_SIZE,
                 chunk_overlap: int = CHUNK_OVERLAP,
                 ollama_host: str = OLLAMA_HOST,
                 embedding_model: str = EMBEDDING_MODEL,
                 llm_model: str = TEXT_GENERATION_MODEL):
        """
        Initialize the LlamaIndex processor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            ollama_host: Ollama host URL
            embedding_model: Embedding model name
            llm_model: LLM model name for processing
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.ollama_host = ollama_host.rstrip("/")
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        
        # Initialize storage adapter
        self.storage_adapter = DocumentStorageAdapter()
        
        # Initialize embeddings generator
        self.embeddings_generator = LlamaIndexEmbeddingsGenerator(
            model_name=self.embedding_model,
            host=self.ollama_host
        )
        
        # Configure LlamaIndex settings
        self._configure_llamaindex()
        
        # Initialize PDF reader
        self.pdf_reader = PDFReader()
        
        # Initialize node parser with sentence splitter
        self.node_parser = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            paragraph_separator="\n\n",
            secondary_chunking_regex="[.!?]+\\s",
        )
        
        # Initialize extractors for enhanced metadata (optional due to memory constraints)
        self.extractors = []
        self.use_extractors = False  # Disable by default due to memory constraints
        
        # Only enable extractors if explicitly configured or sufficient memory is available
        try:
            if self.use_extractors:
                self.extractors = [
                    TitleExtractor(nodes=3, llm=self.llm),  # Reduced nodes for memory efficiency
                    QuestionsAnsweredExtractor(questions=2, llm=self.llm),  # Reduced questions
                ]
        except Exception as e:
            print(f"Warning: Could not initialize extractors: {e}")
            self.extractors = []
        
    def _configure_llamaindex(self):
        """Configure LlamaIndex global settings."""
        # Set up embedding model
        Settings.embed_model = OllamaEmbedding(
            model_name=self.embedding_model,
            base_url=self.ollama_host,
        )
        
        # Set up LLM
        self.llm = Ollama(
            model=self.llm_model,
            base_url=self.ollama_host,
            temperature=0.1,
        )
        Settings.llm = self.llm
        
        # Set chunk size
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap
        
    def process_pdf(self, pdf_path: str, extraction_method: str = "auto", user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a PDF document using LlamaIndex.
        
        Args:
            pdf_path: Path to the PDF file
            extraction_method: Method for text extraction (maintained for compatibility)
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Dictionary containing processed document data compatible with existing system
        """
        try:
            print(f"Processing PDF with LlamaIndex: {pdf_path}")
            if user_id:
                print(f"Storing document for user: {user_id}")
            
            # Load and store document with user_id
            stored_path, storage_file_hash = self._store_document(pdf_path, user_id)
            
            # Load document using LlamaIndex
            documents = self.pdf_reader.load_data(pdf_path)
            
            if not documents:
                raise ValueError("No documents loaded from PDF")
                
            # Process documents into nodes
            nodes = self._process_documents_to_nodes(documents, pdf_path)
            
            # Generate metadata - use storage_file_hash if available (SHA256), otherwise calculate SHA256
            # This ensures consistency with the filename used in storage
            metadata = self._generate_metadata(pdf_path, stored_path, documents[0], storage_file_hash)
            
            # Add user_id to metadata if provided
            if user_id:
                metadata["user_id"] = user_id
            
            # Convert nodes to chunks format compatible with existing system
            chunks = self._convert_nodes_to_chunks(nodes, metadata)
            
            # Generate embeddings for chunks
            if chunks:
                chunks = self.embeddings_generator.process_chunks(chunks)
            
            print(f"Generated {len(chunks)} chunks from {len(documents)} document pages")
            
            return {
                "metadata": metadata,
                "chunks": chunks
            }
            
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return {
                "metadata": {"file_path": pdf_path, "error": str(e)},
                "chunks": []
            }
    
    def _store_document(self, pdf_path: str, user_id: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """Store document using the storage adapter.
        
        Returns:
            Tuple of (stored_path, file_hash) where file_hash is the SHA256 hash used by storage
        """
        try:
            result = self.storage_adapter.save_document(pdf_path, user_id)
            if result.get("success", True):  # Default to True if success key not present
                # Return the stored path (storage_path or full_path) and file_hash
                stored_path = result.get("storage_path") or result.get("full_path", pdf_path)
                # Extract file_hash from result - it should be in the metadata or we can get it from storage_path
                file_hash = result.get("file_hash")
                if not file_hash and stored_path:
                    # Extract hash from storage path (e.g., "users/12/abc123.pdf" -> "abc123")
                    import os
                    filename = os.path.basename(stored_path)
                    if filename.endswith('.pdf'):
                        file_hash = filename[:-4]  # Remove .pdf extension
                return stored_path, file_hash
            return pdf_path, None
        except Exception as e:
            print(f"Warning: Failed to store document: {e}")
            return pdf_path, None
    
    def _process_documents_to_nodes(self, documents: List[Document], pdf_path: str) -> List[BaseNode]:
        """Process LlamaIndex documents into nodes."""
        all_nodes = []
        
        for doc_idx, document in enumerate(documents):
            # Parse document into nodes
            nodes = self.node_parser.get_nodes_from_documents([document])
            
            # Extract additional metadata using extractors (only if enabled and available)
            if self.extractors:
                try:
                    for extractor in self.extractors:
                        try:
                            nodes = extractor.extract(nodes)
                        except Exception as extractor_error:
                            print(f"Warning: Individual extractor failed: {extractor_error}")
                            continue  # Continue with other extractors
                except Exception as e:
                    print(f"Warning: All extractors failed: {e}")
                    # Continue without extracted metadata
            
            # Add document-level metadata to each node
            for node_idx, node in enumerate(nodes):
                # Ensure node has required metadata
                if not hasattr(node, 'metadata'):
                    node.metadata = {}
                    
                # Add page information (LlamaIndex PDF reader typically creates one doc per page)
                node.metadata.update({
                    "page_number": doc_idx + 1,
                    "chunk_index": node_idx,
                    "source_file": pdf_path,
                    "node_type": "text_chunk"
                })
                
                # Add document metadata if available
                if hasattr(document, 'metadata') and document.metadata:
                    node.metadata.update(document.metadata)
            
            all_nodes.extend(nodes)
        
        return all_nodes
    
    def _generate_metadata(self, pdf_path: str, stored_path: Optional[str], sample_doc: Document, storage_file_hash: Optional[str] = None) -> Dict[str, Any]:
        """Generate metadata for the document.
        
        Args:
            pdf_path: Path to the PDF file
            stored_path: Path where document is stored
            sample_doc: Sample document from LlamaIndex
            storage_file_hash: SHA256 hash from storage (if available). If provided, this will be used instead of calculating SHA256.
        """
        # Use storage_file_hash if available (SHA256 from storage), otherwise calculate SHA256
        # This ensures consistency with the filename used in storage
        if storage_file_hash:
            file_hash = storage_file_hash
        else:
            # Fallback to SHA256 if storage hash not available
            file_hash = self._calculate_file_hash(pdf_path)
        
        # Extract basic file information
        file_stats = os.stat(pdf_path)
        file_size = file_stats.st_size
        file_mod_time = file_stats.st_mtime
        
        # Extract title from document or filename
        title = Path(pdf_path).stem
        if hasattr(sample_doc, 'metadata') and sample_doc.metadata:
            title = sample_doc.metadata.get('title', title)
        
        # Count total pages (approximate from number of documents)
        page_count = len(self.pdf_reader.load_data(pdf_path))
        
        metadata = {
            "file_path": pdf_path,
            "file_hash": file_hash,
            "file_size": file_size,
            "file_mod_time": file_mod_time,
            "title": title,
            "page_count": page_count,
            "processor": "llamaindex",
            "processing_method": "llamaindex_pdf_reader"
        }
        
        # Add storage information
        if stored_path and stored_path != pdf_path:
            metadata["stored_path"] = stored_path
            metadata["document_path"] = stored_path
            metadata["is_local_stored"] = True
        else:
            metadata["document_path"] = pdf_path
            metadata["is_local_stored"] = False
        
        return metadata
    
    def _convert_nodes_to_chunks(self, nodes: List[BaseNode], doc_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert LlamaIndex nodes to chunks format compatible with existing system."""
        chunks = []
        
        for node in nodes:
            # Ensure we have text content
            if not hasattr(node, 'text') or not node.text:
                continue
                
            chunk = {
                "text": node.text,
                "metadata": {}
            }
            
            # Copy node metadata
            if hasattr(node, 'metadata') and node.metadata:
                chunk["metadata"].update(node.metadata)
            
            # Add document-level metadata
            chunk["metadata"].update({
                "file_hash": doc_metadata["file_hash"],
                "title": doc_metadata["title"],
                "document_path": doc_metadata["document_path"]
            })
            
            # Ensure required fields are present
            if "page_number" not in chunk["metadata"]:
                chunk["metadata"]["page_number"] = 1
            
            if "chunk_index" not in chunk["metadata"]:
                chunk["metadata"]["chunk_index"] = len(chunks)
            
            # Add LlamaIndex-specific metadata
            if hasattr(node, 'node_id'):
                chunk["metadata"]["node_id"] = node.node_id
                
            if hasattr(node, 'score'):
                chunk["metadata"]["relevance_score"] = node.score
            
            chunks.append(chunk)
        
        return chunks
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of the file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def create_index(self, documents: List[Document]) -> VectorStoreIndex:
        """Create a VectorStoreIndex from documents."""
        # Process documents into nodes
        nodes = []
        for document in documents:
            doc_nodes = self.node_parser.get_nodes_from_documents([document])
            nodes.extend(doc_nodes)
        
        # Create index from nodes
        index = VectorStoreIndex(nodes)
        return index
    
    def extract_enhanced_metadata(self, documents: List[Document]) -> Dict[str, Any]:
        """Extract enhanced metadata using LlamaIndex extractors."""
        if not documents:
            return {}
        
        try:
            # Process documents into nodes for extraction
            nodes = []
            for document in documents:
                doc_nodes = self.node_parser.get_nodes_from_documents([document])
                nodes.extend(doc_nodes)
            
            # Apply extractors
            enhanced_nodes = nodes
            for extractor in self.extractors:
                enhanced_nodes = extractor.extract(enhanced_nodes)
            
            # Aggregate extracted metadata
            extracted_metadata = {
                "titles": [],
                "questions_answered": [],
                "key_topics": []
            }
            
            for node in enhanced_nodes:
                if hasattr(node, 'metadata') and node.metadata:
                    # Collect titles
                    if 'document_title' in node.metadata:
                        extracted_metadata["titles"].append(node.metadata['document_title'])
                    
                    # Collect questions answered
                    if 'questions_this_excerpt_can_answer' in node.metadata:
                        questions = node.metadata['questions_this_excerpt_can_answer']
                        if isinstance(questions, list):
                            extracted_metadata["questions_answered"].extend(questions)
                        elif isinstance(questions, str):
                            extracted_metadata["questions_answered"].append(questions)
            
            # Remove duplicates and clean up
            extracted_metadata["titles"] = list(set(extracted_metadata["titles"]))
            extracted_metadata["questions_answered"] = list(set(extracted_metadata["questions_answered"]))
            
            return extracted_metadata
            
        except Exception as e:
            print(f"Warning: Enhanced metadata extraction failed: {e}")
            return {} 