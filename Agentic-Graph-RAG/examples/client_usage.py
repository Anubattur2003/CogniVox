"""
Example usage of the CogniVox GraphRAG client.
"""
from src.client.cognivox_client import CogniVoxClient

def main():
    # Create a client
    client = CogniVoxClient("http://localhost:8000")
    
    # Check service health
    health = client.health_check()
    print("Service health:", health)
    

    
    # Ingest a document
    ingest_result = client.ingest("data/pdfs/sample.pdf", force=True)
    print("Document ingestion:", ingest_result)
    
    # Query the knowledge graph
    query_result = client.query("What is the main topic of the document?", mode="hybrid", n_results=3)
    print("Query result:", query_result)
    
    # Generate a visualization
    viz_result = client.visualize(output_format="html")
    print("Visualization:", viz_result)
    
    # Export the knowledge graph
    export_result = client.export(format="json")
    print("Export:", export_result)
    
if __name__ == "__main__":
    main() 