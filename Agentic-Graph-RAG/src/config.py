import os
import yaml
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Load YAML configuration if available
config_path = os.getenv("CONFIG_PATH", "config.yaml")
yaml_config = {}
try:
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
except Exception as e:
    print(f"Warning: Could not load config from {config_path}: {e}")
    yaml_config = {}

# Project paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
PDF_DIR = Path(os.getenv("PDF_STORAGE_PATH", DATA_DIR / "pdfs"))
VECTOR_STORE_PATH = Path(os.getenv("VECTOR_STORE_PATH", DATA_DIR / "db" / "vectors"))

# Document storage configuration
storage_config = yaml_config.get("storage", {})
BUCKET_PATH = Path(os.getenv("BUCKET_PATH", storage_config.get("bucket_path", "Bucket")))

# Ensure directories exist
PDF_DIR.mkdir(parents=True, exist_ok=True)
BUCKET_PATH.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)

# Database Configuration
GRAPH_DB_TYPE = os.getenv("GRAPH_DB_TYPE", "neo4j")

# Neo4j Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ArangoDB Configuration
ARANGO_HOST = os.getenv("ARANGO_HOST", "localhost")
ARANGO_PORT = int(os.getenv("ARANGO_PORT", 8529))
ARANGO_USER = os.getenv("ARANGO_USER", "root")
ARANGO_PASSWORD = os.getenv("ARANGO_PASSWORD", "password")
ARANGO_DB = os.getenv("ARANGO_DB", "knowledge_graph")

# Vector Store Configuration
VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "chroma")

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434/nomic-embed-text")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
TEXT_GENERATION_MODEL = os.getenv("TEXT_GENERATION_MODEL", "qwen3:4b")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Document Processing Configuration
pdf_config = yaml_config.get("pdf", {})
USE_LLAMAINDEX = os.getenv("USE_LLAMAINDEX", str(pdf_config.get("use_llamaindex", True))).lower() == "true"

# GPU Settings
USE_CUDA = os.getenv("USE_CUDA", "true").lower() == "true"
CUDA_VISIBLE_DEVICES = os.getenv("CUDA_VISIBLE_DEVICES", "0")

if USE_CUDA:
    os.environ["CUDA_VISIBLE_DEVICES"] = CUDA_VISIBLE_DEVICES 