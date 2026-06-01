from typing import Dict, List, Optional, Any, Union
import json
import os
from pathlib import Path

import networkx as nx
from pyvis.network import Network
# Remove direct matplotlib import - will be imported lazily when needed
# import matplotlib.pyplot as plt
import plotly.graph_objects as go

from src.graph_db.neo4j_adapter import Neo4jAdapter


class GraphVisualizer:
    """
    Visualize the knowledge graph.
    """
    
    def __init__(self, graph_db=None):
        """
        Initialize the graph visualizer.
        
        Args:
            graph_db: Graph database adapter. If None, a new Neo4j adapter will be created.
        """
        self.graph_db = graph_db if graph_db else Neo4jAdapter()
        
    def _get_graph_data(self, limit: int = 100, show_all: bool = False) -> dict:
        """
        Get graph data from the database.
        
        Args:
            limit: Maximum number of nodes to retrieve.
            show_all: If True, ignore limit and retrieve all nodes.
            
        Returns:
            Dictionary with nodes and edges.
        """
        if isinstance(self.graph_db, Neo4jAdapter):
            try:
                # Query to get documents, pages, and chunks with relationships
                query = """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[r1:CONTAINS]->(p:Page)
                OPTIONAL MATCH (p)-[r2:CONTAINS]->(c:Chunk)
                RETURN d, r1, p, r2, c
                """
                
                # Only add LIMIT if not showing all
                if not show_all:
                    query += " LIMIT $limit"
                    result = self.graph_db.graph.run(query, limit=limit).data()
                else:
                    result = self.graph_db.graph.run(query).data()
                
                # Extract nodes and edges
                nodes = []
                edges = []
                node_ids = set()
                edge_keys = set()  # To avoid duplicate edges
                
                for record in result:
                    # Add document node
                    if record["d"] and record["d"]["id"] not in node_ids:
                        nodes.append({
                            "id": record["d"]["id"],
                            "label": record["d"]["title"] if record["d"]["title"] else "Document",
                            "group": "document",
                            "title": f"Document: {record['d']['title']}",
                            "data": dict(record["d"])
                        })
                        node_ids.add(record["d"]["id"])
                    
                    # Add page node
                    if record["p"] and record["p"]["id"] not in node_ids:
                        nodes.append({
                            "id": record["p"]["id"],
                            "label": f"Page {record['p']['page_number']}",
                            "group": "page",
                            "title": f"Page {record['p']['page_number']}",
                            "data": dict(record["p"])
                        })
                        node_ids.add(record["p"]["id"])
                    
                    # Add chunk node
                    if record["c"] and record["c"]["id"] not in node_ids:
                        # Truncate text for display
                        text = record["c"]["text"]
                        if len(text) > 30:
                            text = text[:30] + "..."
                            
                        nodes.append({
                            "id": record["c"]["id"],
                            "label": text,
                            "group": "chunk",
                            "title": record["c"]["text"],
                            "data": dict(record["c"])
                        })
                        node_ids.add(record["c"]["id"])
                    
                    # Add document-page edge
                    if record["d"] and record["p"] and record["r1"]:
                        edge_key = f"{record['d']['id']}-{record['p']['id']}"
                        if edge_key not in edge_keys:
                            edges.append({
                                "from": record["d"]["id"],
                                "to": record["p"]["id"],
                                "label": "CONTAINS",
                                "arrows": "to"
                            })
                            edge_keys.add(edge_key)
                    
                    # Add page-chunk edge
                    if record["p"] and record["c"] and record["r2"]:
                        edge_key = f"{record['p']['id']}-{record['c']['id']}"
                        if edge_key not in edge_keys:
                            edges.append({
                                "from": record["p"]["id"],
                                "to": record["c"]["id"],
                                "label": "CONTAINS",
                                "arrows": "to"
                            })
                            edge_keys.add(edge_key)
                
                # Now let's look for any additional relationships between chunks
                # This query finds any relationships between chunks that aren't the standard page-chunk ones
                extra_query = """
                MATCH (c1:Chunk)-[r]-(c2)
                WHERE NOT type(r) = 'CONTAINS'
                RETURN c1, r, c2
                """
                
                if not show_all:
                    extra_result = self.graph_db.graph.run(extra_query).data()
                    
                    for record in extra_result:
                        # Get the source and target nodes
                        source = record["c1"]
                        target = record["c2"]
                        relationship = record["r"]
                        
                        # Skip if we don't have both nodes in our graph
                        if source["id"] not in node_ids or target["id"] not in node_ids:
                            continue
                            
                        # Add the edge in the correct direction
                        if relationship.start_node.id == source.id:
                            from_node = source["id"]
                            to_node = target["id"]
                        else:
                            from_node = target["id"]
                            to_node = source["id"]
                            
                        edge_type = type(relationship).__name__
                        edge_key = f"{from_node}-{to_node}"
                        
                        if edge_key not in edge_keys:
                            edges.append({
                                "from": from_node,
                                "to": to_node,
                                "label": edge_type,
                                "arrows": "to"
                            })
                            edge_keys.add(edge_key)
                
                return {"nodes": nodes, "edges": edges}
                
            except Exception as e:
                print(f"Error getting graph data: {e}")
                return {"nodes": [], "edges": []}
        else:
            print("Visualization not implemented for this graph database type")
            return {"nodes": [], "edges": []}
    
    def visualize_with_pyvis(self, output_path: str = "knowledge_graph.html", height: str = "800px", width: str = "100%", node_limit: int = 100, show_all: bool = False) -> str:
        """
        Create an interactive visualization using pyvis.
        
        Args:
            output_path: Path to save the HTML file.
            height: Height of the visualization.
            width: Width of the visualization.
            node_limit: Maximum number of nodes to display if show_all is False.
            show_all: If True, display all nodes and edges without limit.
            
        Returns:
            Path to the generated HTML file.
        """
        # Get graph data
        graph_data = self._get_graph_data(limit=node_limit, show_all=show_all)
        
        # Create network
        net = Network(height=height, width=width, notebook=False, directed=True)
        
        # Add nodes
        for node in graph_data["nodes"]:
            net.add_node(
                node["id"], 
                label=node["label"], 
                title=node["title"],
                group=node["group"]
            )
        
        # Add edges
        for edge in graph_data["edges"]:
            net.add_edge(
                edge["from"], 
                edge["to"], 
                title=edge["label"],
                arrows=edge.get("arrows", "to")
            )
        
        # Set options - use different physics for large graphs
        if len(graph_data["nodes"]) > 50 or show_all:
            # Better physics for large graphs
            net.set_options("""
            {
              "physics": {
                "barnesHut": {
                  "gravitationalConstant": -2000,
                  "centralGravity": 0.3,
                  "springLength": 95,
                  "springConstant": 0.04,
                  "damping": 0.09
                },
                "solver": "barnesHut",
                "stabilization": {
                  "iterations": 1000
                }
              },
              "layout": {
                "improvedLayout": true
              },
              "interaction": {
                "navigationButtons": true,
                "keyboard": true
              },
              "edges": {
                "color": {
                  "inherit": true
                },
                "smooth": {
                  "type": "continuous",
                  "forceDirection": "none"
                }
              }
            }
            """)
        else:
            # Default physics for smaller graphs
            net.set_options("""
            {
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 200,
                  "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based",
                "timestep": 0.5
              },
              "layout": {
                "hierarchical": {
                  "enabled": false
                }
              },
              "interaction": {
                "navigationButtons": true,
                "keyboard": true
              },
              "edges": {
                "smooth": {
                  "type": "continuous",
                  "forceDirection": "none"
                }
              }
            }
            """)
        
        # Generate the visualization
        try:
            net.save_graph(output_path)
            print(f"Interactive visualization saved to {output_path} with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges")
            return output_path
        except Exception as e:
            print(f"Error saving visualization: {e}")
            return ""
    
    def visualize_with_networkx(self, output_path: str = "knowledge_graph.png") -> str:
        """
        Create a static visualization using networkx and matplotlib.
        
        Args:
            output_path: Path to save the PNG file.
            
        Returns:
            Path to the generated PNG file.
        """
        try:
            # Lazy import matplotlib to avoid startup issues
            import matplotlib.pyplot as plt
        except ImportError:
            print("Error: matplotlib is required for static visualization. Please install it with 'pip install matplotlib'")
            return ""
        
        # Get graph data
        graph_data = self._get_graph_data()
        
        # Create graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph_data["nodes"]:
            G.add_node(node["id"], label=node["label"], group=node["group"])
        
        # Add edges
        for edge in graph_data["edges"]:
            G.add_edge(edge["from"], edge["to"], label=edge["label"])
        
        # Set up the plot
        plt.figure(figsize=(12, 10))
        
        # Define node colors by group
        node_colors = []
        for node in G.nodes():
            group = G.nodes[node]["group"]
            if group == "document":
                node_colors.append("skyblue")
            elif group == "page":
                node_colors.append("lightgreen")
            else:
                node_colors.append("lightcoral")
        
        # Define layout
        layout = nx.spring_layout(G, k=0.5, iterations=50)
        
        # Draw graph
        nx.draw(
            G, 
            pos=layout, 
            with_labels=True, 
            node_color=node_colors, 
            node_size=800, 
            alpha=0.8, 
            font_size=8,
            arrows=True
        )
        
        # Save the visualization
        try:
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close()
            print(f"Static visualization saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving visualization: {e}")
            return ""
    
    def create_opencv_visualizable_graph(self, output_path: str = "opencv_graph.json") -> str:
        """
        Create a JSON file that can be used with OpenCV for further visualization and manipulation.
        
        Args:
            output_path: Path to save the JSON file.
            
        Returns:
            Path to the generated JSON file.
        """
        # Get graph data
        graph_data = self._get_graph_data()
        
        # Extract positions for nodes - make this compatible with OpenCV
        # by normalizing coordinates to 0-1 range
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Create a networkx graph to calculate positions
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node["id"])
        for edge in edges:
            G.add_edge(edge["from"], edge["to"])
        
        # Calculate layout
        layout = nx.spring_layout(G)
        
        # Normalize positions to 0-1 range
        pos_x = [pos[0] for pos in layout.values()]
        pos_y = [pos[1] for pos in layout.values()]
        
        if pos_x and pos_y:  # Avoid empty lists
            min_x, max_x = min(pos_x), max(pos_x)
            min_y, max_y = min(pos_y), max(pos_y)
            
            range_x = max_x - min_x if max_x != min_x else 1
            range_y = max_y - min_y if max_y != min_y else 1
            
            # Add normalized positions to nodes
            for node in nodes:
                node_id = node["id"]
                if node_id in layout:
                    node["x"] = (layout[node_id][0] - min_x) / range_x
                    node["y"] = (layout[node_id][1] - min_y) / range_y
        
        # Prepare OpenCV-friendly format
        opencv_data = {
            "nodes": [
                {
                    "id": node["id"],
                    "label": node["label"],
                    "group": node["group"],
                    "x": node.get("x", 0.5),  # Default to center if missing
                    "y": node.get("y", 0.5),
                    "data": node.get("data", {})
                }
                for node in nodes
            ],
            "edges": [
                {
                    "source": edge["from"],
                    "target": edge["to"],
                    "label": edge["label"]
                }
                for edge in edges
            ]
        }
        
        # Save to file
        try:
            with open(output_path, 'w') as f:
                json.dump(opencv_data, f, indent=2)
            print(f"OpenCV-compatible graph data saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error saving OpenCV graph data: {e}")
            return ""
