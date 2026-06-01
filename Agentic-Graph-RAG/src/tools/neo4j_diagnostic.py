#!/usr/bin/env python
"""
Neo4j Diagnostic Tool

This script helps diagnose issues with the Neo4j database by inspecting
node content and testing search functionality.
"""

import argparse
import json
from pprint import pprint

from src.graph_db import KnowledgeGraphManager, Neo4jAdapter


def main():
    parser = argparse.ArgumentParser(description="Neo4j Diagnostic Tool")
    parser.add_argument("--action", choices=["inspect", "search", "both"], default="both",
                        help="Action to perform: inspect database, search, or both")
    parser.add_argument("--keyword", type=str, default="constitution",
                        help="Keyword to search for (for search action)")
    parser.add_argument("--output", type=str, help="Output file for results (JSON format)")
    args = parser.parse_args()
    
    # Create a Neo4j adapter
    neo4j = Neo4jAdapter()
    
    # Initialize knowledge graph manager
    kg = KnowledgeGraphManager()
    
    results = {}
    
    # Inspect database
    if args.action in ["inspect", "both"]:
        print("Inspecting Neo4j database...")
        inspection = neo4j.inspect_database()
        results["inspection"] = inspection
        
        print("\nDatabase statistics:")
        print(f"Node counts: {inspection.get('node_counts', [])}")
        print(f"Relationship counts: {inspection.get('relationship_counts', [])}")
        
        print("\nSample documents:")
        for doc in inspection.get("document_samples", []):
            print(f"- {doc.get('title')} ({doc.get('file_path')}): {doc.get('page_count')} pages")
        
        print("\nSample chunks:")
        for chunk in inspection.get("chunk_samples", []):
            text = chunk.get("text", "")
            print(f"- {text[:100]}... (vector_id: {chunk.get('vector_id')})")
        
        print(f"\nConstitution test: {inspection.get('constitution_test', 0)} chunks contain 'constitution'")
    
    # Search test
    if args.action in ["search", "both"]:
        keyword = args.keyword
        print(f"\nTesting search for '{keyword}'...")
        
        # Test Neo4j adapter direct search
        print("\nNeo4j adapter search test:")
        search_test = neo4j.search_test(keyword)
        results["neo4j_search"] = search_test
        
        print(f"Exact match count: {search_test.get('exact_match_count', 0)}")
        print(f"Case-insensitive match count: {search_test.get('case_insensitive_match_count', 0)}")
        
        print("\nSample matches:")
        for sample in search_test.get("sample_matches", []):
            print(f"- {sample}")
        
        # Test KnowledgeGraphManager keyword search
        print("\nKnowledgeGraphManager keyword search test:")
        kg_results = kg.keyword_search(keyword, limit=10)
        results["kg_search"] = {
            "count": len(kg_results),
            "results": [{
                "text": result.get("text", "")[:100] + "...",
                "document_title": result.get("document_title", ""),
                "page_number": result.get("page_number", 0),
                "score": result.get("score", 0)
            } for result in kg_results]
        }
        
        print(f"Found {len(kg_results)} results")
        for result in kg_results:
            print(f"- {result.get('document_title')} (page {result.get('page_number')}): "
                  f"{result.get('text', '')[:100]}...")
    
    # Save results to file if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main() 