"""
Command module for visualizing the knowledge graph.
"""
import os
from src.visualization import GraphVisualizer


def visualize_command(args):
    """
    Visualize the knowledge graph.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    output_format = args.output_format
    output_path = args.output_path
    node_limit = args.node_limit
    all_nodes = args.all
    
    # Initialize graph visualizer
    graph_visualizer = GraphVisualizer()
    
    # Determine node limit
    if all_nodes:
        node_limit = None
        print("Visualizing all nodes in the graph (this may be slow for large graphs)")
    elif node_limit <= 0:
        print("Error: node_limit must be a positive integer")
        return False
    else:
        print(f"Visualizing with node limit: {node_limit}")
    
    # Check output path exists
    if output_path:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"Created directory: {output_dir}")
            except OSError as e:
                print(f"Error creating directory {output_dir}: {e}")
                return False
    
    # Generate visualization
    if output_format == "html":
        if not output_path:
            output_path = "knowledge_graph.html"
        
        print(f"Generating {output_format} visualization...")
        result = graph_visualizer.visualize_with_pyvis(output_path, node_limit=node_limit, show_all=all_nodes)
        
        if result:
            print(f"Visualization saved to: {os.path.abspath(output_path)}")
            return True
        else:
            print("Failed to generate visualization")
            return False
            
    elif output_format == "png":
        if not output_path:
            output_path = "knowledge_graph.png"
            
        print(f"Generating {output_format} visualization...")
        result = graph_visualizer.visualize_with_networkx(output_path)
        
        if result:
            print(f"Visualization saved to: {os.path.abspath(output_path)}")
            return True
        else:
            print("Failed to generate visualization")
            return False
            
    elif output_format == "json":
        if not output_path:
            output_path = "knowledge_graph.json"
            
        print(f"Generating {output_format} export...")
        result = graph_visualizer.export_as_json(output_path, node_limit)
        
        if result:
            print(f"Graph data exported to: {os.path.abspath(output_path)}")
            return True
        else:
            print("Failed to export graph data")
            return False
    
    else:
        print(f"Error: Unsupported output format: {output_format}")
        print("Supported formats: html, png, json")
        return False 