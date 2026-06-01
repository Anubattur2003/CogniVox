#!/usr/bin/env python3
"""
Test script for LlamaIndex integration in CogniVox.

This script tests the basic functionality of the LlamaIndex processor
to ensure it can process PDFs and generate chunks correctly.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pdf_processor.llamaindex_processor import LlamaIndexProcessor
from src.config import USE_LLAMAINDEX


def test_llamaindex_processor():
    """Test the LlamaIndex processor."""
    print("Testing LlamaIndex Processor...")
    print(f"USE_LLAMAINDEX config: {USE_LLAMAINDEX}")
    
    try:
        # Initialize the processor
        processor = LlamaIndexProcessor()
        print("✓ LlamaIndex processor initialized successfully")
        
        # Check if we have a test PDF
        test_pdf_path = "data/test.pdf"
        if not os.path.exists(test_pdf_path):
            print(f"⚠ Test PDF not found at {test_pdf_path}")
            print("Please add a test PDF file to data/test.pdf to test document processing")
            return True
        
        # Test processing a PDF
        print(f"Testing PDF processing with: {test_pdf_path}")
        result = processor.process_pdf(test_pdf_path)
        
        if "error" in result.get("metadata", {}):
            print(f"✗ Error processing PDF: {result['metadata']['error']}")
            return False
        
        chunks = result.get("chunks", [])
        metadata = result.get("metadata", {})
        
        print(f"✓ PDF processed successfully")
        print(f"  - Generated {len(chunks)} chunks")
        print(f"  - Document title: {metadata.get('title', 'N/A')}")
        print(f"  - Page count: {metadata.get('page_count', 'N/A')}")
        print(f"  - Processor: {metadata.get('processor', 'N/A')}")
        
        # Check if chunks have embeddings
        if chunks:
            first_chunk = chunks[0]
            if "embedding" in first_chunk:
                embedding_dim = len(first_chunk["embedding"])
                print(f"  - Embedding dimension: {embedding_dim}")
            else:
                print("  - No embeddings found in chunks")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing LlamaIndex processor: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embeddings_generator():
    """Test the LlamaIndex embeddings generator."""
    print("\nTesting LlamaIndex Embeddings Generator...")
    
    try:
        from src.pdf_processor.llamaindex_embeddings import LlamaIndexEmbeddingsGenerator
        
        # Initialize the embeddings generator
        embeddings_gen = LlamaIndexEmbeddingsGenerator()
        print("✓ LlamaIndex embeddings generator initialized successfully")
        
        # Test single embedding generation
        test_text = "This is a test sentence for embedding generation."
        embedding = embeddings_gen.generate_embedding(test_text)
        
        if embedding:
            print(f"✓ Single embedding generated successfully (dimension: {len(embedding)})")
        else:
            print("✗ Failed to generate single embedding")
            return False
        
        # Test batch embedding generation
        test_texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        embeddings = embeddings_gen.generate_embeddings(test_texts)
        
        if len(embeddings) == len(test_texts) and all(embeddings):
            print(f"✓ Batch embeddings generated successfully ({len(embeddings)} embeddings)")
        else:
            print("✗ Failed to generate batch embeddings")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing embeddings generator: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("CogniVox LlamaIndex Integration Test")
    print("=" * 50)
    
    # Test the processor
    processor_success = test_llamaindex_processor()
    
    # Test the embeddings generator
    embeddings_success = test_embeddings_generator()
    
    print("\n" + "=" * 50)
    if processor_success and embeddings_success:
        print("✓ All LlamaIndex integration tests passed!")
        return 0
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 