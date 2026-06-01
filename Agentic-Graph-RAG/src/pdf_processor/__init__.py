from typing import Optional
from src.pdf_processor.pdf_extractor import PDFExtractor
from src.pdf_processor.text_processor import TextProcessor
from src.pdf_processor.embeddings_generator import OllamaEmbeddingsGenerator
from src.pdf_processor.storage_adapter import DocumentStorageAdapter
from src.pdf_processor.llamaindex_processor import LlamaIndexProcessor
from src.config import CHUNK_SIZE, CHUNK_OVERLAP


class PDFProcessor:
    """
    Main interface for processing PDF documents.
    """
    
    def __init__(self, 
                 save_pdf: bool = True, 
                 chunk_size: int = CHUNK_SIZE, 
                 chunk_overlap: int = CHUNK_OVERLAP,
                 use_llamaindex: bool = True):
        """
        Initialize the PDF processor.
        
        Args:
            save_pdf: Whether to save a copy of the processed PDFs.
            chunk_size: Size of text chunks.
            chunk_overlap: Overlap between consecutive chunks.
            use_llamaindex: Whether to use LlamaIndex for processing (default: True).
        """
        self.use_llamaindex = use_llamaindex
        
        if use_llamaindex:
            # Use LlamaIndex processor
            self.llamaindex_processor = LlamaIndexProcessor(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            # Use legacy processors
            self.pdf_extractor = PDFExtractor(save_pdf=save_pdf)
            self.text_processor = TextProcessor(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            self.embeddings_generator = OllamaEmbeddingsGenerator()
            self.storage_adapter = DocumentStorageAdapter()
        
    def process_pdf(self, pdf_path: str, generate_embeddings: bool = True, extraction_method: str = "auto", user_id: Optional[str] = None) -> dict:
        """
        Process a PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
            generate_embeddings: Whether to generate embeddings for the chunks.
            extraction_method: Method for extracting text ("auto", "pdfminer", "pypdf2", or "ocr")
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Dictionary containing the processed PDF data.
        """
        if self.use_llamaindex:
            return self._process_pdf_with_llamaindex(pdf_path, extraction_method, user_id)
        else:
            return self._process_pdf_legacy(pdf_path, generate_embeddings, extraction_method, user_id)
    
    def _process_pdf_with_llamaindex(self, pdf_path: str, extraction_method: str = "auto", user_id: Optional[str] = None) -> dict:
        """
        Process PDF using LlamaIndex.
        
        Args:
            pdf_path: Path to the PDF file.
            extraction_method: Method for extracting text (maintained for compatibility).
            user_id: Optional user ID for user-specific storage
            
        Returns:
            Dictionary containing the processed PDF data.
        """
        try:
            print(f"Processing PDF with LlamaIndex: {pdf_path}")
            print(f"Using local storage for document storage")
            
            # Process with LlamaIndex, passing user_id
            result = self.llamaindex_processor.process_pdf(pdf_path, extraction_method, user_id)
            
            # Remove info/success logs for embedding generation
            # if result.get("chunks"):
            #     print(f"Generated {len(result['chunks'])} chunks with LlamaIndex")
            #     print(f"Embeddings generated automatically by LlamaIndex")
            
            return result
            
        except Exception as e:
            print(f"Error processing PDF with LlamaIndex {pdf_path}: {e}")
            return {
                "metadata": {"file_path": pdf_path, "error": str(e)},
                "chunks": []
            }
    
    def _process_pdf_legacy(self, pdf_path: str, generate_embeddings: bool = True, extraction_method: str = "auto", user_id: Optional[str] = None) -> dict:
        """
        Process PDF using legacy processors.
        
        Args:
            pdf_path: Path to the PDF file.
            generate_embeddings: Whether to generate embeddings for the chunks.
            extraction_method: Method for extracting text ("auto", "pdfminer", "pypdf2", or "ocr")
            
        Returns:
            Dictionary containing the processed PDF data.
        """
        try:
            print(f"Processing PDF with legacy processors: {pdf_path}")
            print(f"Using extraction method: {extraction_method}")
            print(f"Using local storage for document storage")
            
            # Extract text from the PDF
            pdf_data = self.pdf_extractor.extract_text(pdf_path, method=extraction_method)
            
            # Verify PDF data has the expected structure
            if not pdf_data or not isinstance(pdf_data, dict):
                raise ValueError(f"Invalid PDF data structure: {type(pdf_data)}")
                
            if "metadata" not in pdf_data:
                raise ValueError("PDF data missing metadata")
                
            if "pages" not in pdf_data or not pdf_data["pages"]:
                raise ValueError("PDF data missing pages or has empty pages")
            
            # Set document_path in metadata BEFORE processing chunks
            # This ensures chunks get the correct storage path in their metadata
            if "stored_path" in pdf_data["metadata"]:
                pdf_data["metadata"]["document_path"] = pdf_data["metadata"]["stored_path"]
            elif "file_path" in pdf_data["metadata"]:
                pdf_data["metadata"]["document_path"] = pdf_data["metadata"]["file_path"]
            
            # Process the extracted text into chunks
            chunks = self.text_processor.process_pdf_text(pdf_data)
            
            # Check if chunks were generated successfully
            if not chunks:
                # Try OCR if auto extraction failed to produce chunks
                if extraction_method == "auto" and hasattr(self.pdf_extractor, 'try_ocr_extraction'):
                    print(f"No chunks generated with automatic extraction. Trying OCR for {pdf_path}")
                    try:
                        # Use EasyOCR
                        try:
                            import easyocr
                            print("Using EasyOCR extraction...")
                            ocr_pages = self.pdf_extractor.try_ocr_extraction(pdf_path)
                        except ImportError:
                            print("EasyOCR not available. Please install with: pip install easyocr pdf2image")
                            raise
                        
                        if ocr_pages:
                            pdf_data["pages"] = ocr_pages
                            # Try again with OCR results
                            chunks = self.text_processor.process_pdf_text(pdf_data)
                            if chunks:
                                print(f"OCR extraction succeeded and generated {len(chunks)} chunks")
                    except Exception as ocr_error:
                        print(f"OCR fallback failed: {ocr_error}")
                
                if not chunks:
                    print(f"Warning: No text chunks were generated from {pdf_path}")
            else:
                print(f"Generated {len(chunks)} text chunks from {pdf_path}")
            
            # Generate embeddings if requested
            if generate_embeddings and chunks:
                try:
                    chunks = self.embeddings_generator.process_chunks(chunks)
                    print(f"Generated embeddings for {len(chunks)} chunks")
                except Exception as e:
                    print(f"Error generating embeddings: {e}")
                    # Continue processing even if embeddings fail
            
            # Update metadata with storage information
            pdf_data["metadata"]["is_local_stored"] = True
            if "stored_path" in pdf_data["metadata"]:
                pdf_data["metadata"]["physical_path"] = pdf_data["metadata"]["stored_path"]
                # Set document_path to the stored path (GCP URI) for chunk metadata
                pdf_data["metadata"]["document_path"] = pdf_data["metadata"]["stored_path"]
            elif "file_path" in pdf_data["metadata"]:
                # Fallback to original file_path if no stored_path
                pdf_data["metadata"]["document_path"] = pdf_data["metadata"]["file_path"]
            
            # Add user_id to metadata if provided
            if user_id:
                pdf_data["metadata"]["user_id"] = user_id
            else:
                pdf_data["metadata"]["user_type"] = "global"
            
            return {
                "metadata": pdf_data["metadata"],
                "chunks": chunks
            }
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            # Return a minimal valid structure so the calling code can handle the error
            return {
                "metadata": {"file_path": pdf_path, "error": str(e)},
                "chunks": []
            }
