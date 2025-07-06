#!/usr/bin/env python3
"""
Entry point script for the MOSDAC RAG Pipeline.
This script allows running the pipeline from the root directory.
"""
import sys
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Now import and run the main pipeline
from src.run_pipeline import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
