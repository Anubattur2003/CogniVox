"""
Command module for querying the knowledge graph.
"""
import json
import time
from src.query_engine import QueryProcessor


def query_command(args):
    """
    Query the knowledge graph.
    
    Args:
        args: Command line arguments.
        
    Returns:
        True if successful, False otherwise.
    """
    # Start timing
    start_time = time.time()
    
    query_text = args.query
    mode = args.mode
    n_results = args.n_results
    json_format = args.json
    markdown_format = args.markdown
    user_id = getattr(args, 'user_id', None)  # Get user_id if provided, None otherwise
    
    # Verify only one output format is specified
    if json_format and markdown_format:
        print("Error: Please specify only one output format (--json OR --markdown)")
        return False
    
    # Initialize query processor
    query_processor = QueryProcessor()
    
    # Process the query
    if not (json_format or markdown_format):
        print(f"Querying with mode: {mode}")
        print(f"Query: {query_text}")
        if user_id:
            print(f"User ID: {user_id}")
    
    # Analyze the query
    analysis = query_processor.analyze_query(query_text)
    if not (json_format or markdown_format):
        print(f"Query analysis: {analysis}")
    
    # Run the query
    if mode == "auto" and "mode" in analysis:
        mode = analysis["mode"]
        if not (json_format or markdown_format):
            print(f"Auto-detected search mode: {mode}")
    
    result = query_processor.query(query_text, mode, n_results, user_id=user_id)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Generate concise summary if there is an LLM response
    summary = None
    if result["llm_response"]:
        summary_prompt = f"Summarize this in under 30 words: {result['llm_response']}"
        summary = query_processor.generate_quick_summary(summary_prompt)
    
    # Format as JSON if requested
    if json_format:
        # Create a clean JSON structure with the requested order
        json_result = {
            "query": query_text,
            "concise_summary": summary if summary else None,
            "generated_response": result["llm_response"] if result["llm_response"] else None,
            "mode": mode,
            "execution_time": round(execution_time, 3),  # Add execution time
            "results": []
        }
        
        # Add user_id if provided
        if user_id:
            json_result["user_id"] = user_id
        
        # Format each result
        if result["results"]:
            for r in result["results"]:
                doc_path = r.get("metadata", {}).get("document_path") or r.get("metadata", {}).get("file_path", "Unknown")
                
                # Generate download URL if it's a GCP URI
                download_url = None
                if doc_path.startswith("documents/") or doc_path.startswith("file://"):
                    try:
                        from src.pdf_processor.storage_adapter import DocumentStorageAdapter
                        storage_adapter = DocumentStorageAdapter()
                        download_url = storage_adapter.get_download_url(doc_path, expiration_minutes=60)
                    except Exception as e:
                        print(f"Warning: Failed to generate download URL for {doc_path}: {e}")
                
                result_entry = {
                    "document_title": r.get("metadata", {}).get("title", "Unknown"),
                    "document_path": doc_path,
                    "download_url": download_url,
                    "page": r.get("metadata", {}).get("page_number", "Unknown"),
                    "text": r.get("text", ""),
                    "relevance_score": 1.0 - r.get("distance", 0) if "distance" in r else None
                }
                
                # Add user_source if present
                if "user_source" in r:
                    result_entry["user_source"] = r["user_source"]
                    
                json_result["results"].append(result_entry)
        
        # Pretty print the JSON
        print(json.dumps(json_result, indent=2))
        return True
    
    # Format as Markdown if requested
    elif markdown_format:
        # Header with query info in the requested order
        md_output = f"# Query: \"{query_text}\"\n\n"
        
        # User info if provided
        if user_id:
            md_output += f"*User ID: {user_id}*\n\n"
        
        # Concise summary
        if summary:
            md_output += "## Concise Summary\n\n"
            md_output += "*" + summary + "*\n\n"
        
        # Generated response section
        if result["llm_response"]:
            md_output += "## Generated Response\n\n"
            md_output += result["llm_response"] + "\n\n"
        
        # Search mode and execution time
        md_output += f"## Search Mode: {mode}\n\n"
        md_output += f"*Execution time: {execution_time:.3f} seconds*\n\n"
        
        # Results section
        if not result["results"]:
            md_output += "## Results\n\nNo results found.\n\n"
        else:
            md_output += "## Results\n\n"
            for i, r in enumerate(result["results"]):
                md_output += f"### Result {i+1}\n\n"
                
                if "metadata" in r:
                    md_output += f"**Document**: {r['metadata'].get('title', 'Unknown')}  \n"
                    doc_path = r['metadata'].get('document_path') or r['metadata'].get('file_path', 'Unknown')
                    md_output += f"**Source**: `{doc_path}`  \n"
                    
                    # Add download URL if available
                    if doc_path.startswith("documents/") or doc_path.startswith("file://"):
                        try:
                            from src.pdf_processor.storage_adapter import DocumentStorageAdapter
                            storage_adapter = DocumentStorageAdapter()
                            download_url = storage_adapter.get_download_url(doc_path, expiration_minutes=60)
                            md_output += f"**Download**: [Click to download]({download_url})  \n"
                        except Exception:
                            pass  # Skip if download URL generation fails
                    
                    md_output += f"**Page**: {r['metadata'].get('page_number', 'Unknown')}  \n"
                
                if "distance" in r:
                    relevance = 1.0 - r.get("distance", 0)
                    md_output += f"**Relevance**: {relevance:.2f}  \n"
                
                if "user_source" in r:
                    md_output += f"**User Source**: {r['user_source']}  \n"
                    
                md_output += "\n**Content**:\n\n```\n"
                md_output += r.get("text", "")
                md_output += "\n```\n\n"
        
        # Print the markdown
        print(md_output)
        return True
    
    # Print results in text format
    print(f"\nQuery: {query_text}")
    
    # Print user info if provided
    if user_id:
        print(f"User ID: {user_id}")
    
    # Print concise summary if available
    if summary:
        print("\nConcise Summary:")
        print(summary)
    
    # Print LLM response if available
    if result["llm_response"]:
        print("\nGenerated response:")
        print(result["llm_response"])
    
    # Print search mode and execution time
    print(f"\nSearch Mode: {mode}")
    print(f"Execution time: {execution_time:.3f} seconds")
    
    # Print results
    print("\nResults:")
    if not result["results"]:
        print("No results found.")
    else:
        for i, r in enumerate(result["results"]):
            print(f"\nResult {i+1}:")
            if "metadata" in r:
                print(f"Document: {r['metadata'].get('title', 'Unknown')}")
                doc_path = r['metadata'].get('document_path') or r['metadata'].get('file_path', 'Unknown')
                print(f"Source: {doc_path}")
                
                # Add download URL if available
                if doc_path.startswith("documents/") or doc_path.startswith("file://"):
                    try:
                        from src.pdf_processor.storage_adapter import DocumentStorageAdapter
                        storage_adapter = DocumentStorageAdapter()
                        download_url = storage_adapter.get_download_url(doc_path, expiration_minutes=60)
                        print(f"Download URL: {download_url}")
                    except Exception:
                        pass  # Skip if download URL generation fails
                
                print(f"Page: {r['metadata'].get('page_number', 'Unknown')}")
            if "user_source" in r:
                print(f"User Source: {r['user_source']}")
            print(f"Text: {r.get('text', '')[:200]}...")
    
    return True 