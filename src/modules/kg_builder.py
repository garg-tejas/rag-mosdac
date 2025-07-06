# src/modules/kg_builder.py

import asyncio
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from urllib.parse import urlparse

# Crawl4AI for crawling and markdown generation
from crawl4ai import (
    AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# LiteLLM for making a direct, controlled API call
from litellm import acompletion
import litellm

from src import config

# --- PYDANTIC MODELS ---
class Entity(BaseModel):
    name: str = Field(description="A specific and unique name for the entity.")
    type: str = Field(description="The category of the entity (e.g., 'Satellite', 'Mission').")

class Relationship(BaseModel):
    source: str = Field(description="The name of the source entity.")
    target: str = Field(description="The name of the target entity.")
    relation: str = Field(description="A descriptive verb phrase for the relationship.")

class KnowledgeGraph(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

# --- HELPER FUNCTIONS ---
def save_markdown_content(result):
    """Saves the markdown content of a crawl result to a file."""
    try:
        # Create a file path that mirrors the URL structure
        parsed_url = urlparse(result.url)
        path_str = parsed_url.path.strip("/")
        
        # Handle root URL and pages ending with a slash
        if not path_str or result.url.endswith('/'):
            # If path is empty or just folders, create index.md inside
            page_dir = config.MARKDOWN_DIR.joinpath(path_str)
            file_name = "index.md"
        else:
            # For specific files like /about-us
            parts = path_str.split('/')
            page_dir = config.MARKDOWN_DIR.joinpath(*parts[:-1])
            file_name = f"{parts[-1]}.md"

        page_dir.mkdir(parents=True, exist_ok=True)
        
        md_path = page_dir / file_name
        md_path.write_text(result.markdown.raw_markdown, encoding="utf-8")
        logging.info(f"  -> Saved markdown to: {md_path}")
    except Exception as e:
        logging.error(f"  -> Error saving markdown for {result.url}: {e}")

async def extract_kg_directly(markdown_content: str) -> KnowledgeGraph:
    if not markdown_content or not markdown_content.strip():
        return KnowledgeGraph()
    
    prompt = f"""You are an expert knowledge graph extractor. Analyze the provided markdown text from the MOSDAC website and extract key information as a knowledge graph.

CRITICAL INSTRUCTIONS:
1. Your response must be ONLY a valid JSON object - no additional text, explanations, or formatting
2. Focus on substantive content: satellites, missions, instruments, data products, organizations
3. Extract clear entity-relationship pairs
4. Use descriptive but concise entity names and relationship types

REQUIRED JSON STRUCTURE:
{{
  "entities": [
    {{"name": "Entity Name", "type": "Entity Type"}},
    ...
  ],
  "relationships": [
    {{"source": "Source Entity", "target": "Target Entity", "relation": "relationship description"}},
    ...
  ]
}}

EXAMPLE OUTPUT:
{{
  "entities": [
    {{"name": "INSAT-3D", "type": "Satellite"}},
    {{"name": "MOSDAC", "type": "Organization"}}
  ],
  "relationships": [
    {{"source": "MOSDAC", "target": "INSAT-3D", "relation": "operates"}}
  ]
}}

MARKDOWN CONTENT TO ANALYZE:
---
{markdown_content}
---

Return only the JSON object:"""
    
    try:
        llm_api_key = os.getenv("GEMINI_API_KEY")
        if not llm_api_key:
            logging.error("GEMINI_API_KEY not found in environment variables.")
            return KnowledgeGraph()
            
        response = await acompletion(
            model="gemini/gemini-2.0-flash", 
            messages=[{"role": "user", "content": prompt}], 
            api_key=llm_api_key,
            temperature=0.1, 
            max_tokens=16384, 
            response_format={"type": "json_object"}
        )
        
        json_content = response.choices[0].message.content
        if not json_content or not json_content.strip(): 
            logging.warning("Empty response from LLM")
            return KnowledgeGraph()
        
        # Clean up the JSON content
        json_content = json_content.strip()
        
        # Try to parse JSON with better error handling
        try:
            parsed_data = json.loads(json_content)
            return KnowledgeGraph.model_validate(parsed_data)
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing failed at line {e.lineno}, column {e.colno}: {e.msg}")
            logging.error(f"Problematic JSON content (first 500 chars): {json_content[:500]}")
            
            # Try to fix common JSON issues
            try:
                # Remove any text before the first { or after the last }
                start_idx = json_content.find('{')
                end_idx = json_content.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    cleaned_json = json_content[start_idx:end_idx+1]
                    parsed_data = json.loads(cleaned_json)
                    logging.info("Successfully recovered from JSON parsing error")
                    return KnowledgeGraph.model_validate(parsed_data)
                else:
                    logging.error("Could not find valid JSON boundaries")
                    return KnowledgeGraph()
            except Exception as recovery_error:
                logging.error(f"JSON recovery attempt failed: {recovery_error}")
                return KnowledgeGraph()
        
    except Exception as e:
        logging.error(f"LLM call failed: {e}", exc_info=True)
        return KnowledgeGraph()

# --- MAIN KG BUILDER FUNCTION ---
async def build_knowledge_graph():
    """Builds a knowledge graph by crawling URLs and extracting entities and relationships."""
    logging.info("Starting knowledge graph construction.")
    
    llm_api_key = os.getenv("GEMINI_API_KEY")
    if not llm_api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        return

    # Define URLs to crawl (using config if available, otherwise default)
    urls_to_crawl = getattr(config, 'URLS_TO_CRAWL', [
        "https://mosdac.gov.in/", "https://mosdac.gov.in/insat-3dr", "https://mosdac.gov.in/insat-3d",
        "https://mosdac.gov.in/kalpana-1", "https://mosdac.gov.in/oceansat-2", "https://mosdac.gov.in/soil-moisture-0",
        "https://mosdac.gov.in/global-ocean-surface-current", "https://mosdac.gov.in/data-access-policy",
        "https://mosdac.gov.in/about-us", "https://mosdac.gov.in/faq-page",
    ])

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        markdown_generator=DefaultMarkdownGenerator(options={"ignore_links": True})
    )

    final_kg = KnowledgeGraph()
    logging.info(f"Starting crawl and KG extraction from {len(urls_to_crawl)} pages.")
    
    try:
        litellm.set_verbose = False
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            for i, url in enumerate(urls_to_crawl):
                logging.info(f"Processing URL ({i+1}/{len(urls_to_crawl)}): {url}")
                
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success and result.markdown and result.markdown.raw_markdown:
                    logging.info(f"  -> Crawl successful. Markdown length: {len(result.markdown.raw_markdown)}")
                    
                    # Save the markdown content
                    save_markdown_content(result)

                    kg_part = await extract_kg_directly(result.markdown.raw_markdown)
                    
                    if kg_part.entities or kg_part.relationships:
                        existing_entity_names = {e.name for e in final_kg.entities}
                        new_entities_count = 0
                        for entity in kg_part.entities:
                            if entity.name not in existing_entity_names:
                                final_kg.entities.append(entity)
                                existing_entity_names.add(entity.name)
                                new_entities_count += 1
                        
                        final_kg.relationships.extend(kg_part.relationships)
                        logging.info(f"  -> Extracted {new_entities_count} new entities and {len(kg_part.relationships)} relationships.")
                    else:
                        logging.warning("  -> No KG data extracted from this page's content.")
                else:
                    logging.error(f"  -> Failed to crawl or get markdown for {url}: {result.error_message}")

                if i < len(urls_to_crawl) - 1:
                    logging.info("Waiting 6 seconds to respect API rate limit...")
                    await asyncio.sleep(6)

        config.KG_FILE.write_text(final_kg.model_dump_json(indent=2), encoding="utf-8")
        logging.info("-" * 50)
        logging.info("Knowledge graph construction complete!")
        logging.info(f"Total unique entities: {len(final_kg.entities)}")
        logging.info(f"Total relationships: {len(final_kg.relationships)}")
        logging.info(f"Knowledge Graph saved to: {config.KG_FILE}")
        logging.info(f"Markdown files saved in: {config.MARKDOWN_DIR}")

    except Exception as e:
        logging.critical(f"A critical error occurred during KG building: {e}", exc_info=True)
    finally:
        logging.info("Shutting down background tasks...")
        try:
            litellm.shutdown()
        except:
            pass  # Ignore shutdown errors