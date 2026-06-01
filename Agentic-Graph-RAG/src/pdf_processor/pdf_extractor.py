import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import PyPDF2
from pdfminer.high_level import extract_text
from tqdm import tqdm
import numpy as np

from src.config import PDF_DIR
from src.pdf_processor.storage_adapter import DocumentStorageAdapter


class PDFExtractor:
    """
    A class for extracting text from PDF documents.
    """
    
    def __init__(self, save_pdf: bool = True):
        """
        Initialize the PDFExtractor.
        
        Args:
            save_pdf: Whether to save a copy of the PDF in storage.
        """
        self.save_pdf = save_pdf
        self.pdf_dir = PDF_DIR
        self.storage_adapter = DocumentStorageAdapter()
        
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute the SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            The SHA-256 hash of the file.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def save_pdf_copy(self, file_path: str) -> str:
        """
        Save a copy of the PDF in storage (either locally or in GCP bucket).
        
        Args:
            file_path: Path to the original PDF file.
            
        Returns:
            Path to the saved PDF file.
        """
        result = self.storage_adapter.save_document(file_path)
        return result["file_path"]
    
    def get_pdf_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Dictionary containing the PDF metadata.
        """
        with open(file_path, "rb") as file:
            try:
                reader = PyPDF2.PdfReader(file)
                info = reader.metadata
                
                # Set default title from filename if not available
                title = Path(file_path).stem
                if info and hasattr(info, 'title') and info.title:
                    title = info.title
                
                # Compute file hash
                file_hash = self.compute_file_hash(file_path)
                
                # Convert PyPDF2 metadata to a regular dict
                metadata = {
                    "title": title,
                    "author": info.author if info and hasattr(info, 'author') and info.author else "Unknown",
                    "subject": info.subject if info and hasattr(info, 'subject') and info.subject else "",
                    "creator": info.creator if info and hasattr(info, 'creator') and info.creator else "",
                    "producer": info.producer if info and hasattr(info, 'producer') and info.producer else "",
                    "page_count": len(reader.pages),
                    "file_hash": file_hash,
                    "file_path": str(file_path),
                    "is_local_stored": True
                }
                
                return metadata
            except Exception as e:
                print(f"Error extracting PDF metadata: {e}")
                
                # Computing file hash even if metadata extraction fails
                try:
                    file_hash = self.compute_file_hash(file_path)
                except Exception:
                    file_hash = "unknown"
                
                return {
                    "title": Path(file_path).stem,
                    "author": "Unknown",
                    "subject": "",
                    "creator": "",
                    "producer": "",
                    "page_count": 0,  # Will be updated later if possible
                    "file_hash": file_hash,
                    "file_path": str(file_path),
                    "error": str(e),
                    "is_local_stored": True
                }
    
    def extract_text_with_pdfminer(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file using pdfminer.six.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of page dictionaries with text content.
        """
        try:
            # First count pages with PyPDF2
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
            
            result = []
            for page_num in tqdm(range(page_count), desc="Extracting pages"):
                try:
                    page_text = extract_text(file_path, page_numbers=[page_num])
                    # Store as dictionary for consistent format
                    result.append({
                        "page_number": page_num + 1,
                        "text": page_text if page_text else "",
                        "extraction_method": "pdfminer"
                    })
                except Exception as e:
                    print(f"Error extracting page {page_num+1}: {e}")
                    # Include empty page with error info
                    result.append({
                        "page_number": page_num + 1,
                        "text": "",
                        "extraction_method": "pdfminer",
                        "error": str(e)
                    })
                
            return result
        except Exception as e:
            print(f"Error in pdfminer extraction: {e}")
            return []
    
    def extract_text_with_pypdf2(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from a PDF file using PyPDF2.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of page dictionaries with text content.
        """
        result = []
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(tqdm(reader.pages, desc="Extracting pages")):
                    try:
                        text = page.extract_text()
                        # Store as dictionary for consistent format
                        result.append({
                            "page_number": i + 1,
                            "text": text if text else "",
                            "extraction_method": "pypdf2"
                        })
                    except Exception as e:
                        print(f"Error extracting page {i+1}: {e}")
                        # Include empty page with error info
                        result.append({
                            "page_number": i + 1,
                            "text": "",
                            "extraction_method": "pypdf2",
                            "error": str(e)
                        })
        except Exception as e:
            print(f"Error in PyPDF2 extraction: {e}")
        
        return result
    
    def try_ocr_extraction(self, file_path: str, ocr_engine: str = "easyocr") -> List[Dict[str, Any]]:
        """
        Extract text using OCR.
        
        Args:
            file_path: Path to the PDF file.
            ocr_engine: OCR engine to use (only "easyocr" is supported).
            
        Returns:
            List of page dictionaries with text content.
        """
        # Always use EasyOCR regardless of the parameter
        return self._extract_with_easyocr(file_path)
    
    def _extract_with_easyocr(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Extract text using EasyOCR.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            List of page dictionaries with text content.
        """
        try:
            # Try to import optional dependencies
            import easyocr
            from pdf2image import convert_from_path
            
            # Initialize EasyOCR reader with English language
            reader = easyocr.Reader(['en'])
            
            # Convert PDF pages to images
            pages = convert_from_path(file_path, 300)  # DPI 300
            result = []
            
            for i, page in enumerate(tqdm(pages, desc="EasyOCR processing pages")):
                try:
                    # Perform OCR using EasyOCR
                    ocr_result = reader.readtext(np.array(page))
                    
                    # Combine text from all detected regions
                    text = ' '.join([item[1] for item in ocr_result])
                    
                    result.append({
                        "page_number": i + 1,
                        "text": text if text else "",
                        "extraction_method": "ocr_easyocr"
                    })
                except Exception as e:
                    print(f"EasyOCR error on page {i+1}: {e}")
                    result.append({
                        "page_number": i + 1,
                        "text": "",
                        "extraction_method": "ocr_easyocr",
                        "error": str(e)
                    })
            
            return result
                    
        except ImportError:
            print("EasyOCR extraction requires easyocr and pdf2image. Install with: pip install easyocr pdf2image")
            return []
        except Exception as e:
            print(f"Error in EasyOCR extraction: {e}")
            return []
    
    def extract_text(self, file_path: str, method: str = "auto") -> Dict:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file.
            method: Text extraction method ('auto', 'pdfminer', 'pypdf2', or 'ocr').
            
        Returns:
            Dictionary containing metadata and extracted pages.
        """
        # Save a copy if requested
        dest_path = file_path
        if self.save_pdf:
            dest_path = self.save_pdf_copy(file_path)
        
        # Extract metadata
        metadata = self.get_pdf_metadata(file_path)
        
        # Update file path in metadata to the stored path
        metadata["stored_path"] = dest_path
        
        # Extract text using the specified method
        pages = []
        
        if method == 'auto':
            # First try PyPDF2 (faster but less accurate)
            pages = self.extract_text_with_pypdf2(file_path)
            
            # Check if extraction was successful
            if not pages or not any(page["text"] for page in pages):
                print(f"PyPDF2 extraction failed or returned empty text. Trying PDFMiner for {file_path}")
                pages = self.extract_text_with_pdfminer(file_path)
                
            # If still no text, try OCR extraction
            if not pages or not any(page["text"] for page in pages):
                print(f"PDFMiner extraction failed or returned empty text. Trying OCR for {file_path}")
                try:
                    pages = self.try_ocr_extraction(file_path)
                except Exception as e:
                    print(f"OCR extraction failed: {e}")
        
        elif method == 'pdfminer':
            pages = self.extract_text_with_pdfminer(file_path)
            
        elif method == 'pypdf2':
            pages = self.extract_text_with_pypdf2(file_path)
            
        elif method == 'ocr':
            try:
                pages = self.try_ocr_extraction(file_path)
            except Exception as e:
                print(f"OCR extraction failed: {e}")
                # Fallback to pdfminer if OCR fails
                print("Falling back to PDFMiner extraction")
                pages = self.extract_text_with_pdfminer(file_path)
        
        else:
            raise ValueError(f"Unknown extraction method: {method}")
        
        # If we have pages but metadata doesn't have page count
        if pages and metadata["page_count"] == 0:
            metadata["page_count"] = len(pages)
        
        return {
            "metadata": metadata,
            "pages": pages
        } 