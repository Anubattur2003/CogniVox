"""
Main CLI entry point for CogniVox.
"""
import argparse
import sys

from src.cli.commands.ingest import ingest_command
from src.cli.commands.query import query_command
from src.cli.commands.visualize import visualize_command
from src.cli.commands.export import export_command
from src.cli.commands.remove import remove_command
from src.cli.commands.cleanup import cleanup_command


def parse_args():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="CogniVox Knowledge Graph")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a PDF document")
    ingest_parser.add_argument("--pdf_path", required=True, help="Path to the PDF file")
    ingest_parser.add_argument("--db_type", default="neo4j", help="Graph database type (default: neo4j)")
    ingest_parser.add_argument("--force", action="store_true", help="Force re-ingestion even if document already exists")
    ingest_parser.add_argument("--chunk_size", type=int, help="Size of text chunks")
    ingest_parser.add_argument("--chunk_overlap", type=int, help="Overlap between consecutive chunks")
    ingest_parser.add_argument("--extraction_method", default="auto", 
                             choices=["auto", "pdfminer", "pypdf2", "ocr"], 
                             help="Method for extracting text from PDF (default: auto)")
    ingest_parser.add_argument("--use_llamaindex", action="store_true", 
                             help="Use LlamaIndex for document processing (overrides config)")
    ingest_parser.add_argument("--use_legacy", action="store_true", 
                             help="Use legacy processors instead of LlamaIndex")
    ingest_parser.add_argument("--user_id", help="Optional user ID to associate with the document")
    
    # Query command
    query_parser = subparsers.add_parser("query", help="Query the knowledge graph")
    query_parser.add_argument("--query", required=True, help="Query to run")
    query_parser.add_argument("--mode", default="hybrid", choices=["semantic", "keyword", "hybrid"], 
                              help="Search mode")
    query_parser.add_argument("--n_results", type=int, default=5, help="Number of results to return")
    query_parser.add_argument("--json", action="store_true", help="Return results in JSON format")
    query_parser.add_argument("--markdown", action="store_true", help="Return results in Markdown format")
    query_parser.add_argument("--user_id", help="Optional user ID to search for specific user documents")
    
    # Visualize command
    visualize_parser = subparsers.add_parser("visualize", help="Visualize the knowledge graph")
    visualize_parser.add_argument("--output_format", default="html", choices=["html", "png", "opencv"],
                                 help="Output format")
    visualize_parser.add_argument("--output_path", help="Output path")
    visualize_parser.add_argument("--node_limit", type=int, default=100, 
                                 help="Maximum number of nodes to display")
    visualize_parser.add_argument("--all", action="store_true", 
                                 help="Show all nodes and edges without limit")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export the knowledge graph")
    export_parser.add_argument("--format", default="json", choices=["json", "graphml", "rdf"],
                              help="Export format")
    export_parser.add_argument("--output_path", help="Output path")
    

    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a document from the knowledge graph")
    remove_group = remove_parser.add_mutually_exclusive_group(required=True)
    remove_group.add_argument("--pdf_path", help="Path to the PDF file to remove")
    remove_group.add_argument("--file_hash", help="Hash of the file to remove")
    remove_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    remove_parser.add_argument("--db_type", default="neo4j", help="Graph database type (default: neo4j)")
    remove_parser.add_argument("--user_id", help="Optional user ID to remove specific user document")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up all database components")
    cleanup_parser.add_argument("--confirm", action="store_true", 
                               help="Confirm cleanup operation (required for safety)")
    cleanup_parser.add_argument("--include-local-data", action="store_true", default=True,
                               help="Include local document storage cleanup")
    cleanup_parser.add_argument("--include-gcp-data", action="store_true", default=True,
                               help="Include GCP bucket data cleanup")
    cleanup_parser.add_argument("--include-temp-files", action="store_true", default=True,
                               help="Include temporary files cleanup")
    cleanup_parser.add_argument("--skip-local-data", action="store_true",
                               help="Skip local document storage cleanup")
    cleanup_parser.add_argument("--skip-gcp-data", action="store_true",
                               help="Skip GCP bucket data cleanup")
    cleanup_parser.add_argument("--skip-temp-files", action="store_true",
                               help="Skip temporary files cleanup")
    
    return parser.parse_args()


def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    if args.command == "ingest":
        success = ingest_command(args)
    elif args.command == "query":
        success = query_command(args)
    elif args.command == "visualize":
        success = visualize_command(args)
    elif args.command == "export":
        success = export_command(args)
    elif args.command == "remove":
        success = remove_command(args)
    elif args.command == "cleanup":
        # Handle skip flags by setting the corresponding include flags to False
        if hasattr(args, 'skip_local_data') and args.skip_local_data:
            args.include_local_data = False
        if hasattr(args, 'skip_gcp_data') and args.skip_gcp_data:
            args.include_gcp_data = False
        if hasattr(args, 'skip_temp_files') and args.skip_temp_files:
            args.include_temp_files = False
        
        success = cleanup_command(args)
    else:
        print("Error: No command specified. Use --help for usage information.")
        success = False
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 