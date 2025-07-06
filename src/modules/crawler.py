# src/modules/crawler.py
import asyncio
import logging
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from src import config

def save_markdown_content(result):
    """Saves the markdown content of a crawl result to a file."""
    try:
        parsed_url = urlparse(result.url)
        path_str = parsed_url.path.strip("/")
        if not path_str or result.url.endswith('/'):
            page_dir = config.MARKDOWN_DIR / path_str
            file_name = "index.md"
        else:
            parts = path_str.split('/')
            page_dir = config.MARKDOWN_DIR / Path(*parts[:-1])
            file_name = f"{parts[-1]}.md"
        page_dir.mkdir(parents=True, exist_ok=True)
        md_path = page_dir / file_name
        md_path.write_text(result.markdown.raw_markdown, encoding="utf-8")
        logging.info(f"  -> Saved markdown to: {md_path}")
    except Exception as e:
        logging.error(f"  -> Error saving markdown for {result.url}: {e}")

async def run_crawl():
    """Crawls the predefined list of URLs and saves their markdown content."""
    logging.info(f"Starting crawl for {len(config.URLS_TO_CRAWL)} pages.")
    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in config.URLS_TO_CRAWL:
            logging.info(f"Crawling: {url}")
            result = await crawler.arun(url=url, config=run_config)
            if result.success and result.markdown and result.markdown.raw_markdown:
                save_markdown_content(result)
            else:
                logging.error(f"Failed to crawl or get markdown for {url}: {result.error_message}")
    logging.info("Crawl finished.")