from typing import Dict, List, Optional, Any, Union
import uuid
import time

from py2neo import Graph, Node, Relationship
from py2neo.matching import NodeMatcher
from tqdm import tqdm

from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD


def sanitize_metadata(value):
    """
    Convert all values to standard Python types that Neo4j can handle.
    
    Args:
        value: The value to sanitize (can be a dictionary, list, or other type)
        
    Returns:
        A sanitized version of the value
    """
    # Handle None values
    if value is None:
        return None
        
    # Handle PyPDF2 TextStringObject and other special PyPDF2 types
    if hasattr(value, 'original_bytes') or hasattr(value, 'indirect_reference'):
        return str(value)
    
    # More comprehensive check for PyPDF2 types
    type_str = str(type(value))
    if 'PyPDF2' in type_str or 'pdf' in type_str.lower():
        return str(value)
    
    # Handle dictionaries
    elif isinstance(value, (dict, Dict)):
        sanitized = {}
        for key, val in value.items():
            sanitized[key] = sanitize_metadata(val)
        return sanitized
    
    # Handle lists
    elif isinstance(value, (list, List)):
        return [sanitize_metadata(item) for item in value]
    
    # Return values Neo4j can handle directly
    elif isinstance(value, (bool, int, float, str)):
        return value
    
    # Convert any other types to string
    else:
        return str(value)


class Neo4jAdapter:
    """
    Adapter for Neo4j graph database operations.
    """
    
    def __init__(self, uri: str = NEO4J_URI, username: str = NEO4J_USER, password: str = NEO4J_PASSWORD):
        """
        Initialize the Neo4j adapter.
        
        Args:
            uri: Neo4j connection URI.
            username: Neo4j username.
            password: Neo4j password.
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.graph = Graph(uri, auth=(username, password))
        self.node_matcher = NodeMatcher(self.graph)
    
    


    def create_document_node(self, metadata: Dict) -> Node:
        """
        Create a document node in the graph.
        
        Args:
            metadata: Document metadata.
            
        Returns:
            Created document node.
        """
        # Sanitize metadata to ensure it contains only standard Python types
        clean_metadata = sanitize_metadata(metadata)
        
        # Create document node
        document_node = Node(
            "Document",
            id=str(uuid.uuid4()),
            title=clean_metadata.get("title", ""),
            author=clean_metadata.get("author", "Unknown"),
            subject=clean_metadata.get("subject", ""),
            file_hash=clean_metadata.get("file_hash", ""),
            file_path=clean_metadata.get("file_path", ""),
            page_count=clean_metadata.get("page_count", 0),
            file_size=clean_metadata.get("file_size", 0),
            last_modified=clean_metadata.get("last_modified", 0)
        )
        
        # Create the node in the database
        self.graph.create(document_node)
        
        return document_node
    
    def create_page_node(self, document_node: Node, page_number: int) -> Node:
        """
        Create a page node in the graph.
        
        Args:
            document_node: Parent document node.
            page_number: Page number.
            
        Returns:
            Created page node.
        """
        # Create page node
        page_node = Node(
            "Page",
            id=str(uuid.uuid4()),
            page_number=page_number,
            document_id=document_node["id"]
        )
        
        # Create the node in the database
        self.graph.create(page_node)
        
        # Create relationship between document and page
        contains_rel = Relationship(document_node, "CONTAINS", page_node)
        self.graph.create(contains_rel)
        
        return page_node
    
    def create_chunk_node(self, page_node: Node, chunk_data: Dict) -> Node:
        """
        Create a chunk node in the graph.
        
        Args:
            page_node: Parent page node.
            chunk_data: Chunk data dictionary.
            
        Returns:
            Created chunk node.
        """
        # Sanitize chunk data to ensure it contains only standard Python types
        clean_chunk_data = sanitize_metadata(chunk_data)
        
        # Get document ID from page node
        document_id = page_node["document_id"]
        
        # Create chunk node with a more unique identifier for chunk_id
        # This ensures we don't violate the unique constraint
        unique_chunk_id = f"{document_id}_{page_node['page_number']}_{clean_chunk_data['metadata']['chunk_id']}"
        
        # Ensure text is a string
        chunk_text = str(clean_chunk_data.get("text", ""))
        if not chunk_text:
            print(f"Warning: Empty text for chunk {unique_chunk_id}")
        
        # Log vector_id presence for debugging
        vector_id = clean_chunk_data.get("vector_id", "")
        if not vector_id:
            print(f"Warning: Missing vector_id for chunk {unique_chunk_id}")
        
        chunk_node = Node(
            "Chunk",
            id=str(uuid.uuid4()),
            text=chunk_text,
            chunk_id=clean_chunk_data["metadata"]["chunk_id"],
            unique_chunk_id=unique_chunk_id,
            chunk_size=clean_chunk_data["metadata"]["chunk_size"],
            vector_id=vector_id,
            page_id=page_node["id"],
            document_id=document_id
        )
        
        # Create the node in the database
        try:
            self.graph.create(chunk_node)
            print(f"Successfully created chunk node with vector_id: {vector_id} and text length: {len(chunk_text)}")
        except Exception as e:
            # If there's a constraint error, regenerate with a timestamp to ensure uniqueness
            if "already exists with label" in str(e) and "chunk_id" in str(e):
                ts = int(time.time() * 1000)  # Millisecond timestamp
                # Update the chunk_id to ensure uniqueness
                chunk_node["unique_chunk_id"] = f"{unique_chunk_id}_{ts}"
                self.graph.create(chunk_node)
                print(f"Created chunk node with timestamp-modified ID and vector_id: {vector_id}")
            else:
                # If it's a different error, re-raise it
                print(f"Error creating chunk node: {e}")
                raise
        
        # Create relationship between page and chunk
        contains_rel = Relationship(page_node, "CONTAINS", chunk_node)
        self.graph.create(contains_rel)
        
        return chunk_node
    
    def find_document_by_hash(self, file_hash: str, user_id: Optional[str] = None) -> Optional[Node]:
        """
        Find a document node by its file hash.
        
        Args:
            file_hash: The hash of the document to find.
            user_id: Optional user ID. If provided, only find documents
                     associated with this user. If not, only find global documents.
            
        Returns:
            The document node if found, None otherwise.
        """
        try:
            # Ensure user_id is None if empty string
            user_id = user_id if user_id and user_id.strip() else None
            
            if user_id:
                # First try finding user-specific document
                query = """
                MATCH (d:Document)
                WHERE d.file_hash = $file_hash AND d.user_id = $user_id
                RETURN d
                LIMIT 1
                """
                result = self.graph.run(query, file_hash=file_hash, user_id=user_id).data()
                if result:
                    return result[0]["d"]
                
                # If no user-specific document found, check if there's a global version
                # that this user can access
                query = """
                MATCH (d:Document)
                WHERE d.file_hash = $file_hash AND d.user_type = 'global'
                RETURN d
                LIMIT 1
                """
                result = self.graph.run(query, file_hash=file_hash).data()
                if result:
                    return result[0]["d"]
                    
                # As a last resort, check for documents with no user attribution (legacy)
                query = """
                MATCH (d:Document)
                WHERE d.file_hash = $file_hash AND d.user_id IS NULL AND d.user_type IS NULL
                RETURN d
                LIMIT 1
                """
                result = self.graph.run(query, file_hash=file_hash).data()
                if result:
                    return result[0]["d"]
            else:
                # When no user_id provided, only look for global documents
                query = """
                MATCH (d:Document)
                WHERE d.file_hash = $file_hash AND 
                      (d.user_type = 'global' OR (d.user_id IS NULL AND d.user_type IS NULL))
                RETURN d
                LIMIT 1
                """
                result = self.graph.run(query, file_hash=file_hash).data()
                if result:
                    return result[0]["d"]
            
            # Document not found or not accessible to this user
            return None
        except Exception as e:
            print(f"Error finding document by hash: {e}")
            return None

    def delete_document(self, file_hash: str, user_id: Optional[str] = None) -> bool:
        """
        Delete a document and all its pages and chunks from the graph database.
        
        Args:
            file_hash: Hash of the document to delete.
            user_id: Optional user ID. If provided, only delete document for this specific user.
                     If not provided, only delete global document.
            
        Returns:
            True if document was deleted, False otherwise.
        """
        try:
            # Ensure user_id is None if empty string
            user_id = user_id if user_id and user_id.strip() else None
            
            document_node = self.find_document_by_hash(file_hash, user_id)
            
            if not document_node:
                print(f"Document with hash {file_hash} not found or not accessible to user {user_id}.")
                return False
            
            # Verify user permissions
            doc_user_id = document_node.get("user_id")
            doc_user_type = document_node.get("user_type")
            
            if user_id:
                # When user_id is provided, ensure we can only delete:
                # 1. Documents with matching user_id
                # 2. Global documents if no specific user version exists
                if doc_user_id and doc_user_id != user_id:
                    print(f"Cannot delete document - belongs to different user: {doc_user_id}")
                    return False
            else:
                # When no user_id is provided, we can only delete:
                # 1. Documents marked as global
                # 2. Legacy documents with no user attribution
                if doc_user_id:
                    print(f"Cannot delete user-specific document without user_id")
                    return False
                if doc_user_type != "global" and doc_user_type is not None:
                    print(f"Cannot delete non-global document without user_id")
                    return False
            
            # Delete all chunks and pages associated with this document
            if user_id:
                query = """
                MATCH (d:Document {file_hash: $file_hash})
                WHERE d.user_id = $user_id OR d.user_type = 'global' OR (d.user_id IS NULL AND d.user_type IS NULL)
                OPTIONAL MATCH (d)-[:CONTAINS]->(p:Page)
                OPTIONAL MATCH (p)-[:CONTAINS]->(c:Chunk)
                DETACH DELETE c, p, d
                RETURN count(d) as deleted_count
                """
                params = {"file_hash": file_hash, "user_id": user_id}
            else:
                query = """
                MATCH (d:Document {file_hash: $file_hash})
                WHERE d.user_type = 'global' OR (d.user_id IS NULL AND d.user_type IS NULL)
                OPTIONAL MATCH (d)-[:CONTAINS]->(p:Page)
                OPTIONAL MATCH (p)-[:CONTAINS]->(c:Chunk)
                DETACH DELETE c, p, d
                RETURN count(d) as deleted_count
                """
                params = {"file_hash": file_hash}
            
            result = self.graph.run(query, **params).data()
            deleted_count = result[0]["deleted_count"] if result else 0
            
            if deleted_count > 0:
                print(f"Deleted document with hash {file_hash}")
                return True
            else:
                print(f"Document with hash {file_hash} was not deleted - possible permission error")
                return False
        except Exception as e:
            print(f"Error deleting document with hash {file_hash}: {e}")
            return False
    
    def update_document_enabled_status(self, file_hash: str, enabled: bool, user_id: Optional[str] = None) -> bool:
        """
        Update the enabled status of a document.
        
        Args:
            file_hash: Hash of the document to update.
            enabled: True to enable, False to disable.
            user_id: Optional user ID. If provided, only update document for this specific user.
            
        Returns:
            True if document was updated, False otherwise.
        """
        try:
            user_id = user_id if user_id and user_id.strip() else None
            
            # First, try to find the document to check what exists
            # Check all possible documents with this hash
            check_query = """
            MATCH (d:Document {file_hash: $file_hash})
            RETURN d, d.user_id AS doc_user_id, d.user_type AS doc_user_type
            LIMIT 10
            """
            check_result = self.graph.run(check_query, file_hash=file_hash).data()
            
            if not check_result:
                print(f"No document found with hash {file_hash} in Neo4j")
                # Document exists in storage but not in Neo4j - create a minimal node
                # This can happen if document was ingested before Neo4j storage was implemented
                # or if Neo4j storage failed during ingestion
                print(f"Attempting to create minimal document node for hash {file_hash}")
                return self._create_minimal_document_node(file_hash, enabled, user_id)
            
            print(f"Found {len(check_result)} document(s) with hash {file_hash}")
            for doc_data in check_result:
                doc = doc_data.get("d")
                doc_user_id = doc_data.get("doc_user_id")
                doc_user_type = doc_data.get("doc_user_type")
                print(f"  - Document user_id: {doc_user_id}, user_type: {doc_user_type}")
            
            # Try to update with user_id matching
            if user_id:
                # Convert user_id to string for comparison (Neo4j might store as string or int)
                user_id_str = str(user_id)
                query = """
                MATCH (d:Document {file_hash: $file_hash})
                WHERE (d.user_id = $user_id OR toString(d.user_id) = $user_id_str) 
                   OR d.user_type = 'global' 
                   OR (d.user_id IS NULL AND d.user_type IS NULL)
                SET d.enabled = $enabled
                RETURN d, d.user_id AS updated_user_id
                """
                params = {"file_hash": file_hash, "user_id": user_id, "user_id_str": user_id_str, "enabled": enabled}
            else:
                query = """
                MATCH (d:Document {file_hash: $file_hash})
                WHERE d.user_type = 'global' OR (d.user_id IS NULL AND d.user_type IS NULL)
                SET d.enabled = $enabled
                RETURN d
                """
                params = {"file_hash": file_hash, "enabled": enabled}
            
            result = self.graph.run(query, **params).data()
            
            if result:
                print(f"Successfully updated document enabled status: {file_hash} -> {enabled}")
                if user_id and result[0].get("updated_user_id"):
                    print(f"Updated document for user_id: {result[0].get('updated_user_id')}")
                return True
            else:
                print(f"Document with hash {file_hash} was not updated - no matching document found")
                return False
        except Exception as e:
            print(f"Error updating document enabled status with hash {file_hash}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_minimal_document_node(self, file_hash: str, enabled: bool, user_id: Optional[str] = None) -> bool:
        """
        Create a minimal document node in Neo4j for a document that exists in storage
        but not in the knowledge graph. This allows enabling/disabling documents that
        weren't fully ingested into Neo4j.
        
        Args:
            file_hash: Hash of the document
            enabled: Initial enabled status
            user_id: Optional user ID
            
        Returns:
            True if created successfully, False otherwise
        """
        try:
            user_id = user_id if user_id and user_id.strip() else None
            
            # Create minimal document properties
            document_properties = {
                "id": str(uuid.uuid4()),
                "file_hash": file_hash,
                "title": "",  # Unknown - document not fully ingested
                "author": "Unknown",
                "subject": "",
                "file_path": "",  # Unknown
                "page_count": 0,
                "file_size": 0,
                "last_modified": 0,
                "enabled": enabled
            }
            
            # Add user_id or user_type
            if user_id:
                document_properties["user_id"] = user_id
            else:
                document_properties["user_type"] = "global"
            
            # Create and sanitize document properties
            document_node = Node("Document", **sanitize_metadata(document_properties))
            
            # Create the document node
            self.graph.create(document_node)
            
            print(f"Created minimal document node for hash {file_hash} with enabled={enabled}")
            return True
            
        except Exception as e:
            print(f"Error creating minimal document node: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def store_document_knowledge_graph(self, processed_pdf: Dict, vector_store_ids: List[str]) -> Union[bool, Dict]:
        """
        Store a processed PDF document as a knowledge graph.
        
        This creates nodes for the document, pages, and chunks, and establishes
        relationships between them.
        
        Args:
            processed_pdf: Processed PDF data.
            vector_store_ids: IDs of the vectors stored in the vector store.
            
        Returns:
            True if successful, or a dictionary with status if document already exists.
        """
        try:
            # Extract metadata and sanitize it
            metadata = sanitize_metadata(processed_pdf.get("metadata", {}))
            file_hash = metadata.get("file_hash", "")
            
            # Get user_id from metadata if present, ensure it's None if empty string
            user_id = metadata.get("user_id")
            user_id = user_id if user_id and str(user_id).strip() else None
            metadata["user_id"] = user_id  # Update metadata with normalized user_id
            
            # Get user_type from metadata
            user_type = metadata.get("user_type")
            
            # Log the document details
            if user_id:
                print(f"Storing document for user: {user_id}")
            elif user_type == "global":
                print("Storing global document (accessible to all users)")
            
            # Check if document already exists
            existing_doc = self.find_document_by_hash(file_hash, user_id)
            if existing_doc:
                return {
                    "status": "already_exists",
                    "file_hash": file_hash,
                    "user_id": user_id
                }
            
            # Create document node with sanitized properties
            # Use stored path if available (for GCP), otherwise use original file_path
            document_path = (metadata.get("stored_path") or 
                           metadata.get("physical_path") or 
                           metadata.get("file_path", ""))
            
            document_properties = {
                "id": str(uuid.uuid4()),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", "Unknown"),
                "subject": metadata.get("subject", ""),
                "file_hash": metadata.get("file_hash", ""),
                "file_path": document_path,  # This will be the storage path (GCP URI or local)
                "original_file_path": metadata.get("file_path", ""),  # Keep original for reference
                "page_count": metadata.get("page_count", 0),
                "file_size": metadata.get("file_size", 0),
                "last_modified": metadata.get("last_modified", 0),
                "enabled": True  # Documents are enabled by default
            }
            
            # Add user_id to document node if provided, or user_type if document is global
            if user_id:
                document_properties["user_id"] = user_id
            elif user_type == "global":
                document_properties["user_type"] = "global"
                
            # Create and sanitize all document properties
            document_node = Node("Document", **sanitize_metadata(document_properties))
            
            # Create the document node in the database
            self.graph.create(document_node)
            
            # Process pages and chunks
            chunks = processed_pdf.get("chunks", [])
            pages = {}
            
            # Group chunks by page
            for i, chunk in enumerate(chunks):
                chunk_metadata = sanitize_metadata(chunk.get("metadata", {}))
                page_num = chunk_metadata.get("page_number", 0)
                
                # Create page node if it doesn't exist yet
                if page_num not in pages:
                    page_properties = {
                        "id": str(uuid.uuid4()),
                        "page_number": page_num,
                        "document_id": document_node["id"]
                    }
                    
                    # Add user_id to page node if provided, or user_type if global
                    if user_id:
                        page_properties["user_id"] = user_id
                    elif user_type == "global":
                        page_properties["user_type"] = "global"
                    
                    # Create and sanitize all page properties
                    page_node = Node("Page", **sanitize_metadata(page_properties))
                    
                    # Create the page node
                    self.graph.create(page_node)
                    
                    # Create relationship between document and page
                    contains_rel = Relationship(document_node, "CONTAINS", page_node)
                    self.graph.create(contains_rel)
                    
                    # Store page node
                    pages[page_num] = page_node
                
                # Get the page node
                page_node = pages[page_num]
                
                # Sanitize text and create chunk node
                chunk_text = sanitize_metadata(chunk.get("text", ""))
                chunk_id = f"{file_hash}_{page_num}_{i}"
                
                chunk_properties = {
                    "id": str(uuid.uuid4()),
                    "unique_chunk_id": chunk_id,
                    "text": chunk_text,
                    "page_number": page_num,
                    "index": i,
                    "vector_id": vector_store_ids[i] if i < len(vector_store_ids) else None
                }
                
                # Add user_id to chunk node if provided, or user_type if global
                if user_id:
                    chunk_properties["user_id"] = user_id
                elif user_type == "global":
                    chunk_properties["user_type"] = "global"
                
                # Copy relevant metadata to chunk properties
                for key, value in chunk_metadata.items():
                    if key not in ["text", "page_number", "index", "user_id", "user_type"] and value is not None:
                        chunk_properties[key] = value
                
                # Create and sanitize all chunk properties
                chunk_node = Node("Chunk", **sanitize_metadata(chunk_properties))
                
                # Create the chunk node
                self.graph.create(chunk_node)
                
                # Create relationship between page and chunk
                contains_rel = Relationship(page_node, "CONTAINS", chunk_node)
                self.graph.create(contains_rel)
            
            return True
        except Exception as e:
            print(f"Error storing document in knowledge graph: {e}")
            return False
            
    def _repair_document_relationships(self, document_id: str) -> bool:
        """
        Attempt to repair missing relationships in the document structure.
        
        Args:
            document_id: ID of the document to repair
            
        Returns:
            True if repairs were made, False otherwise
        """
        try:
            # Ensure pages are connected to document
            fix_page_relations_query = """
            MATCH (d:Document {id: $document_id})
            MATCH (p:Page {document_id: $document_id})
            WHERE NOT (d)-[:CONTAINS]->(p)
            WITH d, p
            CREATE (d)-[:CONTAINS]->(p)
            RETURN count(*) as fixed_page_relations
            """
            page_result = self.graph.run(fix_page_relations_query, document_id=document_id).data()
            fixed_pages = page_result[0]["fixed_page_relations"] if page_result else 0
            
            # Ensure chunks are connected to pages
            fix_chunk_relations_query = """
            MATCH (p:Page)
            MATCH (c:Chunk {page_id: p.id})
            WHERE NOT (p)-[:CONTAINS]->(c)
            WITH p, c
            CREATE (p)-[:CONTAINS]->(c)
            RETURN count(*) as fixed_chunk_relations
            """
            chunk_result = self.graph.run(fix_chunk_relations_query).data()
            fixed_chunks = chunk_result[0]["fixed_chunk_relations"] if chunk_result else 0
            
            print(f"Relationship repair: Fixed {fixed_pages} page relations and {fixed_chunks} chunk relations")
            return fixed_pages > 0 or fixed_chunks > 0
            
        except Exception as e:
            print(f"Error repairing document relationships: {e}")
            return False

    def inspect_database(self) -> Dict:
        """
        Inspect the Neo4j database to get information about nodes and relationships.
        This is useful for diagnostics.
        
        Returns:
            Dictionary with database statistics and sample data.
        """
        try:
            # Get count of nodes by label
            node_count_query = """
            MATCH (n)
            RETURN labels(n) as label, count(n) as count
            """
            node_counts = self.graph.run(node_count_query).data()
            
            # Get count of relationships by type
            rel_count_query = """
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            """
            rel_counts = self.graph.run(rel_count_query).data()
            
            # Get sample of document nodes
            doc_sample_query = """
            MATCH (d:Document)
            RETURN d.title as title, d.file_path as file_path, d.page_count as page_count
            LIMIT 5
            """
            doc_samples = self.graph.run(doc_sample_query).data()
            
            # Get sample of chunk nodes
            chunk_sample_query = """
            MATCH (c:Chunk)
            RETURN c.text as text, c.vector_id as vector_id, c.chunk_id as chunk_id
            LIMIT 5
            """
            chunk_samples = self.graph.run(chunk_sample_query).data()
            
            # Try a case-insensitive search for "constitution" as a test
            search_test_query = """
            MATCH (c:Chunk)
            WHERE toLower(c.text) CONTAINS 'constitution'
            RETURN count(c) as match_count
            """
            search_test = self.graph.run(search_test_query).data()
            constitution_count = search_test[0]["match_count"] if search_test else 0
            
            return {
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "document_samples": doc_samples,
                "chunk_samples": chunk_samples,
                "constitution_test": constitution_count
            }
            
        except Exception as e:
            print(f"Error inspecting database: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
            
    def search_test(self, keyword: str) -> Dict:
        """
        Test search functionality with the given keyword.
        
        Args:
            keyword: Keyword to search for.
            
        Returns:
            Dictionary with search statistics.
        """
        try:
            # Test exact case match
            exact_query = """
            MATCH (c:Chunk)
            WHERE c.text CONTAINS $keyword
            RETURN count(c) as count
            """
            exact_count = self.graph.run(exact_query, keyword=keyword).data()[0]["count"]
            
            # Test case-insensitive match
            case_insensitive_query = """
            MATCH (c:Chunk)
            WHERE toLower(c.text) CONTAINS toLower($keyword)
            RETURN count(c) as count
            """
            case_insensitive_count = self.graph.run(case_insensitive_query, keyword=keyword).data()[0]["count"]
            
            # Get sample matches
            sample_query = """
            MATCH (c:Chunk)
            WHERE toLower(c.text) CONTAINS toLower($keyword)
            RETURN left(c.text, 100) as text_sample
            LIMIT 3
            """
            samples = self.graph.run(sample_query, keyword=keyword).data()
            
            return {
                "keyword": keyword,
                "exact_match_count": exact_count,
                "case_insensitive_match_count": case_insensitive_count,
                "sample_matches": [s["text_sample"] for s in samples]
            }
            
        except Exception as e:
            print(f"Error in search test: {e}")
            return {"error": str(e)}

    def retrieve_document_from_knowledge_graph(self, document_hash: str, user_id: Optional[str] = None) -> Dict:
        """
        Retrieve a document and all its related pages and chunks from the knowledge graph.
        
        Args:
            document_hash: The hash of the document to retrieve.
            user_id: Optional user ID to filter documents for a specific user.
                    If provided, only user-specific documents will be returned.
                    If None, only global documents will be returned.
        
        Returns:
            A dictionary containing document details and its chunks.
        """
        try:
            # Build the query based on whether user_id is provided
            if user_id:
                query = """
                MATCH (d:Document {file_hash: $hash, user_id: $user_id})
                MATCH (d)-[:CONTAINS]->(p:Page)
                MATCH (p)-[:CONTAINS]->(c:Chunk)
                RETURN d, collect(distinct p) as pages, collect(c) as chunks
                """
                params = {"hash": document_hash, "user_id": user_id}
                print(f"Retrieving document {document_hash} for user {user_id}")
            else:
                query = """
                MATCH (d:Document {file_hash: $hash})
                WHERE d.user_type = 'global' OR d.user_id IS NULL
                MATCH (d)-[:CONTAINS]->(p:Page)
                MATCH (p)-[:CONTAINS]->(c:Chunk)
                RETURN d, collect(distinct p) as pages, collect(c) as chunks
                """
                params = {"hash": document_hash}
                print(f"Retrieving global document {document_hash}")
            
            result = self.graph.run(query, **params).data()
            
            if not result:
                print(f"Document with hash {document_hash} not found")
                return {}
                
            # Extract document properties
            document = result[0]['d']
            pages = result[0]['pages']
            chunks = result[0]['chunks']
            
            # Create a structured response
            document_data = {
                "document": dict(document),
                "pages": [dict(page) for page in pages],
                "chunks": [dict(chunk) for chunk in chunks]
            }
            
            # Add user source information
            if user_id:
                document_data["user_source"] = user_id
            elif document.get("user_type") == "global":
                document_data["user_source"] = "global"
            else:
                document_data["user_source"] = "legacy"
                
            return document_data
            
        except Exception as e:
            print(f"Error retrieving document: {e}")
            import traceback
            traceback.print_exc()
            return {}
