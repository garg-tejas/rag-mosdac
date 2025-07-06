# src/run_pipeline.py
import asyncio
import argparse
import logging
import os
import shutil
from dotenv import load_dotenv

from src import config
from src.modules import crawler, kg_builder, vector_db_builder, qa_app

def setup_logging():
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                        handlers=[logging.FileHandler(config.LOG_FILE, mode='w', encoding='utf-8'), logging.StreamHandler()])

async def main():
    load_dotenv()
    setup_logging()

    parser = argparse.ArgumentParser(description="Run the MOSDAC RAG Pipeline.")
    parser.add_argument("--step", required=True, choices=['crawl', 'kg', 'vectordb', 'qa', 'all'],
                        help="The pipeline step to run.")
    parser.add_argument("--force", action='store_true', help="Force re-running a step even if output exists.")
    args = parser.parse_args()

    if args.step == 'crawl' or args.step == 'all':
        if args.force and config.MARKDOWN_DIR.exists():
            logging.info("Force flag set. Deleting existing markdown directory.")
            shutil.rmtree(config.MARKDOWN_DIR)
        if not config.MARKDOWN_DIR.exists() or not any(config.MARKDOWN_DIR.iterdir()):
            await crawler.run_crawl()
        else:
            logging.info("Markdown directory already exists. Skipping crawl. Use --force to re-run.")

    if args.step == 'kg' or args.step == 'all':
        if args.force and config.KG_FILE.exists():
            logging.info("Force flag set. Deleting existing knowledge graph file.")
            os.remove(config.KG_FILE)
        if not config.KG_FILE.exists():
            await kg_builder.build_knowledge_graph()
        else:
            logging.info("Knowledge graph already exists. Skipping build. Use --force to re-run.")

    if args.step == 'vectordb' or args.step == 'all':
        if args.force and os.path.exists(config.VECTOR_DB_PATH):
            logging.info("Force flag set. Deleting existing vector database.")
            shutil.rmtree(config.VECTOR_DB_PATH)
        if not os.path.exists(config.VECTOR_DB_PATH):
            vector_db_builder.build_vector_database()
        else:
            logging.info("Vector database already exists. Skipping build. Use --force to re-run.")

    if args.step == 'qa' or args.step == 'all':
        qa_app.start_qa_session()

if __name__ == "__main__":
    asyncio.run(main())