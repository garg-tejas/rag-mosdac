# src/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Project Paths ---
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
MARKDOWN_DIR = OUTPUT_DIR / "markdown" / "mosdac.gov.in"
LOG_FILE = OUTPUT_DIR / "pipeline.log"

# --- Crawl Configuration ---
URLS_TO_CRAWL = [
    "https://mosdac.gov.in/", "https://mosdac.gov.in/insat-3dr", "https://mosdac.gov.in/insat-3d",
    "https://mosdac.gov.in/kalpana-1", "https://mosdac.gov.in/oceansat-2", "https://mosdac.gov.in/soil-moisture-0",
    "https://mosdac.gov.in/global-ocean-surface-current", "https://mosdac.gov.in/data-access-policy",
    "https://mosdac.gov.in/about-us", "https://mosdac.gov.in/faq-page",
]

# --- LLM Configuration ---
LLM_PROVIDER = "gemini/gemini-2.0-flash"

# --- Vector DB Configuration (Pinecone) ---
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
PINECONE_INDEX_NAME = "mosdac-rag"
PINECONE_DIMENSION = 1024  # Dimension for BAAI/bge-large-en-v1.5
PINECONE_METRIC = "cosine"
PINECONE_NAMESPACE = "mosdac"  # Namespace for organizing vectors

# --- Knowledge Graph Configuration (Neo4j Aura) ---
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password")
NEO4J_DATABASE = "neo4j"