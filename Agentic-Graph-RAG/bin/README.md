# CogniVox CLI Executables

This directory contains the executable scripts for the CogniVox application.

## Main Executable

- **cognivox**: Main entry point script for CogniVox
- **cognivox.bat**: Windows batch file for easy execution on Windows

## Usage

```bash
cognivox [command] [options]
```

## Available Commands

### Document Management

- **ingest**: Ingest a PDF document into the knowledge graph
  ```bash
  cognivox ingest --pdf_path <path_to_pdf> [--force] [--extraction-method auto|pdfminer|pypdf2|ocr]
  ```

- **remove**: Remove a document from the knowledge graph
  ```bash
  cognivox remove --pdf_path <path_to_pdf> | --file_hash <hash> [--force]
  ```

### Query and Visualization

- **query**: Query the knowledge graph
  ```bash
  cognivox query --query "your query" [--mode semantic|keyword|hybrid] [--n_results N] [--json|--markdown]
  ```

- **visualize**: Generate visualizations of the knowledge graph
  ```bash
  cognivox visualize [--output_format html|png|opencv] [--output_path <path>] [--node_limit N] [--all]
  ```



### Export

- **export**: Export the knowledge graph in various formats
  ```bash
  cognivox export [--format json|graphml|rdf] [--output_path <path>]
  ```

## Installation

The executables will be available in your PATH after installing the package:

```bash
pip install -e .
``` 