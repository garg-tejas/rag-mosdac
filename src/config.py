# src/config.py
from pathlib import Path

# --- Project Paths ---
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
MARKDOWN_DIR = OUTPUT_DIR / "markdown" / "mosdac.gov.in"
KG_FILE = OUTPUT_DIR / "knowledge_graph.json"
VECTOR_DB_PATH = str(OUTPUT_DIR / "vector_db")
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

# --- Vector DB Configuration ---
VECTOR_DB_COLLECTION = "mosdac_collection"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"