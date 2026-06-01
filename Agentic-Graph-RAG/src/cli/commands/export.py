"""
Command module for exporting the knowledge graph.
"""
import os
from src.graph_db.knowledge_graph import KnowledgeGraphManager


def export_command(args):
    """
    Export the knowledge graph.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    export_format = args.format
    output_path = args.output_path
    
    # Initialize knowledge graph manager
    kg_manager = KnowledgeGraphManager()
    
    # Set default output path if not provided
    if not output_path:
        if export_format == "json":
            output_path = "knowledge_graph.json"
        elif export_format == "graphml":
            output_path = "knowledge_graph.graphml"
        elif export_format == "rdf":
            output_path = "knowledge_graph.rdf"
    
    # Check if output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created directory: {output_dir}")
        except OSError as e:
            print(f"Error creating directory {output_dir}: {e}")
            return False
    
    # Export the graph
    print(f"Exporting knowledge graph as {export_format}...")
    result_path = kg_manager.export_knowledge_graph(export_format, output_path)
    
    if result_path:
        print(f"Knowledge graph exported to: {os.path.abspath(result_path)}")
        return True
    else:
        print("Failed to export knowledge graph")
        return False 