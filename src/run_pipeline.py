# src/run_pipeline.py
import asyncio
import argparse
import logging
import os
import shutil
from dotenv import load_dotenv

from src import config
from src.modules import crawler, kg_builder, vector_db_builder, qa_app
from src.modules.kg_builder import get_neo4j_session

def setup_logging():
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
                        handlers=[logging.FileHandler(config.LOG_FILE, mode='w', encoding='utf-8'), logging.StreamHandler()])

def check_neo4j_has_entities():
    """Check if Neo4j has any entities."""
    try:
        session = get_neo4j_session()
        if session:
            result = session.run("MATCH (n:Entity) RETURN count(n) as count").single()
            session.close()
            return result["count"] > 0
    except:
        return False

def clear_neo4j_graph():
    """Clear all entities and relationships from Neo4j."""
    try:
        session = get_neo4j_session()
        if session:
            session.run("MATCH (n) DETACH DELETE n")
            session.close()
            logging.info("Cleared existing Neo4j knowledge graph.")
    except Exception as e:
        logging.error(f"Error clearing Neo4j graph: {e}")

def check_pinecone_has_vectors():
    """Check if Pinecone index exists and has vectors."""
    try:
        if not os.getenv("PINECONE_API_KEY"):
            return False
        from src.modules.vector_db_builder import get_pinecone_index
        from src import config
        index = get_pinecone_index()
        stats = index.describe_index_stats()
        
        # Check the specific namespace
        namespace_stats = stats.get('namespaces', {}).get(config.PINECONE_NAMESPACE, {})
        vector_count = namespace_stats.get('vector_count', 0)
        return vector_count > 0
    except:
        return False

def clear_pinecone_index():
    """Clear all vectors from Pinecone index."""
    try:
        from src.modules.vector_db_builder import get_pinecone_index
        index = get_pinecone_index()
        # Delete all vectors (Pinecone doesn't have a clear all, so we'd need to rebuild)
        logging.info("Pinecone will be rebuilt with new vectors.")
    except Exception as e:
        logging.error(f"Error accessing Pinecone index: {e}")

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
        if args.force and check_neo4j_has_entities():
            logging.info("Force flag set. Clearing existing Neo4j knowledge graph.")
            clear_neo4j_graph()
        if not check_neo4j_has_entities():
            await kg_builder.build_knowledge_graph()
        else:
            logging.info("Neo4j knowledge graph already exists. Skipping build. Use --force to re-run.")

    if args.step == 'vectordb' or args.step == 'all':
        if args.force and check_pinecone_has_vectors():
            logging.info("Force flag set. Will rebuild Pinecone index.")
            clear_pinecone_index()
        if not check_pinecone_has_vectors():
            vector_db_builder.build_vector_database()
        else:
            logging.info("Pinecone vector database already exists. Skipping build. Use --force to re-run.")

    if args.step == 'qa' or args.step == 'all':
        qa_app.start_qa_session()

if __name__ == "__main__":
    asyncio.run(main())