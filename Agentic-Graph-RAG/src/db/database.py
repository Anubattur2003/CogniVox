"""
Database management module.
"""
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.graph_db.neo4j_adapter import Neo4jAdapter
from src.graph_db.vector_store import get_vector_store


class DatabaseManager:
    """
    Database manager for basic database operations.
    """
    
    def __init__(self, db_type="neo4j"):
        """
        Initialize database manager.
        
        Args:
            db_type: Type of the database.
        """
        self.db_type = db_type
        self.db_adapter = None
        
        if db_type == "neo4j":
            self.db_adapter = Neo4jAdapter()
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        # Initialize vector store
        self.vector_store = get_vector_store() 