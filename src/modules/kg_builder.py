# src/modules/kg_builder.py

import asyncio
import os
import logging
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List

# LiteLLM for making a direct, controlled API call
from litellm import acompletion
import litellm

# Neo4j for knowledge graph storage
from neo4j import GraphDatabase

from src import config

# --- NORMALIZATION FUNCTIONS ---
def normalize_name(text: str) -> str:
    """Normalize entity/relationship names to consistent snake_case format."""
    if not text or not isinstance(text, str):
        return ""
    
    # Trim whitespace
    text = text.strip()
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces, hyphens, and other separators with underscores
    text = re.sub(r'[-\s\.\/\\]+', '_', text)
    
    # Remove special characters except underscores and alphanumeric
    text = re.sub(r'[^a-z0-9_]', '', text)
    
    # Remove multiple consecutive underscores
    text = re.sub(r'_+', '_', text)
    
    # Remove leading/trailing underscores
    text = text.strip('_')
    
    return text

def normalize_type(text: str) -> str:
    """Normalize entity types to consistent format."""
    if not text or not isinstance(text, str):
        return "unknown"
    
    # Trim and convert to lowercase
    text = text.strip().lower()
    
    # Common type mappings for consistency
    type_mappings = {
        'organization': 'organization',
        'org': 'organization',
        'company': 'organization',
        'institution': 'organization',
        'satellite': 'satellite',
        'sat': 'satellite',
        'spacecraft': 'satellite',
        'instrument': 'instrument',
        'sensor': 'instrument',
        'data_product': 'data_product',
        'product': 'data_product',
        'dataset': 'data_product',
        'parameter': 'parameter',
        'param': 'parameter',
        'measurement': 'parameter',
        'mission': 'mission',
        'program': 'mission',
        'service': 'service',
        'application': 'application',
        'app': 'application',
        'technology': 'technology',
        'tech': 'technology'
    }
    
    return type_mappings.get(text, text)

def normalize_relation(text: str) -> str:
    """Normalize relationship names to consistent format."""
    if not text or not isinstance(text, str):
        return "relates_to"
    
    # Trim and convert to lowercase
    text = text.strip().lower()
    
    # Common relation mappings for consistency
    relation_mappings = {
        'operates': 'operates',
        'runs': 'operates',
        'manages': 'operates',
        'launches': 'launches',
        'deployed': 'launches',
        'carries': 'carries',
        'hosts': 'carries',
        'contains': 'carries',
        'measures': 'measures',
        'observes': 'measures',
        'detects': 'measures',
        'monitors': 'measures',
        'provides': 'provides',
        'supplies': 'provides',
        'offers': 'provides',
        'processes': 'processes',
        'analyzes': 'processes',
        'handles': 'processes',
        'archives': 'archives',
        'stores': 'archives',
        'maintains': 'archives',
        'distributes': 'distributes',
        'disseminates': 'distributes',
        'shares': 'distributes',
        'supports': 'supports',
        'enables': 'supports',
        'facilitates': 'supports',
        'develops': 'develops',
        'creates': 'develops',
        'builds': 'develops',
        'collects': 'collects',
        'gathers': 'collects',
        'acquires': 'collects',
        'transmits': 'transmits',
        'sends': 'transmits',
        'broadcasts': 'transmits',
        'generates': 'generates',
        'produces': 'generates',
        'creates': 'generates',
        'validates': 'validates',
        'verifies': 'validates',
        'calibrates': 'calibrates'
    }
    
    # Replace spaces and hyphens with underscores
    text = re.sub(r'[-\s]+', '_', text)
    
    return relation_mappings.get(text, text)

# --- PYDANTIC MODELS ---
class Entity(BaseModel):
    name: str = Field(description="A specific and unique name for the entity.")
    type: str = Field(description="The category of the entity (e.g., 'Satellite', 'Mission').")
    
    def __init__(self, **data):
        # Normalize name and type before validation
        if 'name' in data:
            data['name'] = normalize_name(data['name'])
        if 'type' in data:
            data['type'] = normalize_type(data['type'])
        super().__init__(**data)

class Relationship(BaseModel):
    source: str = Field(description="The name of the source entity.")
    target: str = Field(description="The name of the target entity.")
    relation: str = Field(description="A descriptive verb phrase for the relationship.")
    
    def __init__(self, **data):
        # Normalize source, target, and relation before validation
        if 'source' in data:
            data['source'] = normalize_name(data['source'])
        if 'target' in data:
            data['target'] = normalize_name(data['target'])
        if 'relation' in data:
            data['relation'] = normalize_relation(data['relation'])
        super().__init__(**data)

class KnowledgeGraph(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)

# --- NEO4J INTEGRATION ---
class Neo4jKnowledgeGraph:
    def __init__(self):
        self.driver = None
        self.connect()
    
    def connect(self):
        """Connect to Neo4j Aura instance."""
        try:
            neo4j_uri = os.getenv("NEO4J_URI", config.NEO4J_URI)
            neo4j_username = os.getenv("NEO4J_USERNAME", config.NEO4J_USERNAME)
            neo4j_password = os.getenv("NEO4J_PASSWORD", config.NEO4J_PASSWORD)
            
            self.driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(neo4j_username, neo4j_password)
            )
            
            # Test the connection
            with self.driver.session(database=config.NEO4J_DATABASE) as session:
                session.run("RETURN 1")
            
            logging.info("Successfully connected to Neo4j Aura")
            
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
    
    def clear_graph(self):
        """Clear all nodes and relationships from the knowledge graph."""
        if not self.driver:
            return
        
        try:
            with self.driver.session(database=config.NEO4J_DATABASE) as session:
                session.run("MATCH (n) DETACH DELETE n")
            logging.info("Cleared existing knowledge graph in Neo4j")
        except Exception as e:
            logging.error(f"Error clearing Neo4j graph: {e}")
    
    def add_entities_and_relationships(self, kg: KnowledgeGraph):
        """Add entities and relationships to Neo4j with duplicate prevention."""
        if not self.driver:
            logging.warning("No Neo4j connection available")
            return
        
        try:
            with self.driver.session(database=config.NEO4J_DATABASE) as session:
                # Add entities with merge to prevent duplicates
                entities_added = 0
                for entity in kg.entities:
                    # Skip empty names
                    if not entity.name or entity.name.strip() == "":
                        continue
                    
                    result = session.run(
                        """
                        MERGE (e:Entity {name: $name})
                        ON CREATE SET e.type = $type, e.created = timestamp()
                        ON MATCH SET e.type = $type, e.updated = timestamp()
                        RETURN e.name as name, labels(e) as labels
                        """,
                        name=entity.name,
                        type=entity.type
                    )
                    
                    if result.single():
                        entities_added += 1
                
                # Add relationships with merge to prevent duplicates
                relationships_added = 0
                for rel in kg.relationships:
                    # Skip relationships with empty names
                    if not rel.source or not rel.target or rel.source.strip() == "" or rel.target.strip() == "":
                        continue
                    
                    # Skip self-relationships
                    if rel.source == rel.target:
                        continue
                    
                    result = session.run(
                        """
                        MATCH (source:Entity {name: $source_name})
                        MATCH (target:Entity {name: $target_name})
                        MERGE (source)-[r:RELATES {relation: $relation}]->(target)
                        ON CREATE SET r.created = timestamp()
                        ON MATCH SET r.updated = timestamp()
                        RETURN r.relation as relation
                        """,
                        source_name=rel.source,
                        target_name=rel.target,
                        relation=rel.relation
                    )
                    
                    if result.single():
                        relationships_added += 1
                
                logging.info(f"Added/updated {entities_added} entities and {relationships_added} relationships to Neo4j")
                
        except Exception as e:
            logging.error(f"Error adding data to Neo4j: {e}")
    
    def get_graph_stats(self):
        """Get statistics about the knowledge graph."""
        if not self.driver:
            return {"entities": 0, "relationships": 0}
        
        try:
            with self.driver.session(database=config.NEO4J_DATABASE) as session:
                entity_count = session.run("MATCH (n:Entity) RETURN count(n) as count").single()["count"]
                rel_count = session.run("MATCH ()-[r:RELATES]->() RETURN count(r) as count").single()["count"]
                return {"entities": entity_count, "relationships": rel_count}
        except Exception as e:
            logging.error(f"Error getting Neo4j stats: {e}")
            return {"entities": 0, "relationships": 0}

# --- HELPER FUNCTIONS ---
async def extract_kg_directly(markdown_content: str) -> KnowledgeGraph:
    if not markdown_content or not markdown_content.strip():
        return KnowledgeGraph()
    
    prompt = f"""You are an expert knowledge graph extractor specialized in meteorological and oceanographic satellite systems. Analyze the provided MOSDAC website content and extract a technical knowledge graph.

CONTEXT: MOSDAC (Meteorological and Oceanographic Satellite Data Archival Center) is a data center under ISRO's Space Applications Centre that handles satellite data reception, processing, analysis, and dissemination for earth observation.

CRITICAL INSTRUCTIONS:
1. Your response must be ONLY a valid JSON object - no additional text, explanations, or formatting
2. Focus on technical entities: satellites, instruments, data products, parameters, missions, organizations, applications
3. Use SPECIFIC technical relationships - avoid generic terms like "relates to", "associated with", "connected to"
4. Extract measurable parameters, data types, and technical specifications when available

ENTITY TYPES TO FOCUS ON:
- Satellite, Instrument, DataProduct, Parameter, Organization, Mission, Application, Service, Technology

PREFERRED RELATIONSHIP TYPES (use these when applicable):
- operates, launches, carries, measures, provides, processes, archives, disseminates, supports
- hosts, manages, develops, maintains, monitors, generates, distributes, analyzes
- observes, detects, collects, stores, transmits, calibrates, validates

REQUIRED JSON STRUCTURE:
{{
  "entities": [
    {{"name": "Entity Name", "type": "Entity Type"}},
    ...
  ],
  "relationships": [
    {{"source": "Source Entity", "target": "Target Entity", "relation": "specific_technical_relation"}},
    ...
  ]
}}

EXAMPLE OUTPUT:
{{
  "entities": [
    {{"name": "INSAT-3D", "type": "Satellite"}},
    {{"name": "MOSDAC", "type": "Organization"}},
    {{"name": "Sea Surface Temperature", "type": "Parameter"}},
    {{"name": "IMAGER", "type": "Instrument"}}
  ],
  "relationships": [
    {{"source": "MOSDAC", "target": "INSAT-3D", "relation": "operates"}},
    {{"source": "INSAT-3D", "target": "IMAGER", "relation": "carries"}},
    {{"source": "IMAGER", "target": "Sea Surface Temperature", "relation": "measures"}},
    {{"source": "MOSDAC", "target": "Sea Surface Temperature", "relation": "processes"}}
  ]
}}

MARKDOWN CONTENT TO ANALYZE:
---
{markdown_content}
---

Return only the JSON object with specific technical relationships:"""
    
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
    """Builds a knowledge graph from saved markdown files and stores in Neo4j."""
    logging.info("Starting knowledge graph construction from saved markdown files.")
    
    llm_api_key = os.getenv("GEMINI_API_KEY")
    if not llm_api_key:
        logging.error("GEMINI_API_KEY not found in environment variables.")
        return

    # Initialize Neo4j connection
    neo4j_kg = Neo4jKnowledgeGraph()
    
    if not neo4j_kg.driver:
        logging.error("Failed to connect to Neo4j. Cannot proceed with knowledge graph building.")
        return

    # Check if markdown files exist
    if not config.MARKDOWN_DIR.exists():
        logging.error("Markdown directory not found. Please run the crawl step first.")
        return
    
    # Get all saved markdown files
    md_files = list(config.MARKDOWN_DIR.rglob("*.md"))
    if not md_files:
        logging.error("No markdown files found. Please run the crawl step first.")
        return

    final_kg = KnowledgeGraph()
    logging.info(f"Processing {len(md_files)} markdown files for KG extraction.")
    
    try:
        litellm.set_verbose = False
        
        # Clear existing graph in Neo4j
        neo4j_kg.clear_graph()
        
        for i, md_file in enumerate(md_files):
            logging.info(f"Processing file ({i+1}/{len(md_files)}): {md_file.relative_to(config.MARKDOWN_DIR)}")
            
            try:
                # Read markdown content from saved file
                markdown_content = md_file.read_text(encoding="utf-8")
                
                if markdown_content and markdown_content.strip():
                    logging.info(f"  -> Processing markdown content. Length: {len(markdown_content)}")
                    
                    kg_part = await extract_kg_directly(markdown_content)
                    
                    if kg_part.entities or kg_part.relationships:
                        # Use normalized names for duplicate checking
                        existing_entity_names = {e.name for e in final_kg.entities}
                        new_entities_count = 0
                        for entity in kg_part.entities:
                            # Entity names are already normalized in the Entity.__init__ method
                            if entity.name and entity.name not in existing_entity_names:
                                final_kg.entities.append(entity)
                                existing_entity_names.add(entity.name)
                                new_entities_count += 1
                        
                        # Remove duplicate relationships using normalized names
                        existing_relationships = {(r.source, r.target, r.relation) for r in final_kg.relationships}
                        new_relationships_count = 0
                        for rel in kg_part.relationships:
                            # Relationship names are already normalized in the Relationship.__init__ method
                            rel_tuple = (rel.source, rel.target, rel.relation)
                            if rel.source and rel.target and rel_tuple not in existing_relationships:
                                final_kg.relationships.append(rel)
                                existing_relationships.add(rel_tuple)
                                new_relationships_count += 1
                        
                        logging.info(f"  -> Extracted {new_entities_count} new entities and {new_relationships_count} new relationships.")
                    else:
                        logging.warning("  -> No KG data extracted from this file's content.")
                else:
                    logging.warning(f"  -> Empty or invalid markdown content in {md_file}")
                    
            except Exception as e:
                logging.error(f"  -> Error processing {md_file}: {e}")
                continue

            # Add small delay to avoid overwhelming the LLM API
            if i < len(md_files) - 1:
                logging.info("Waiting 6 seconds before next file...")
                await asyncio.sleep(6)

        # Save to Neo4j only
        neo4j_kg.add_entities_and_relationships(final_kg)
        stats = neo4j_kg.get_graph_stats()
        
        logging.info("-" * 50)
        logging.info("Knowledge graph construction complete!")
        logging.info(f"Processed {len(md_files)} markdown files")
        logging.info(f"Total unique entities: {len(final_kg.entities)}")
        logging.info(f"Total relationships: {len(final_kg.relationships)}")
        logging.info(f"Neo4j Knowledge Graph: {stats['entities']} entities, {stats['relationships']} relationships")

    except Exception as e:
        logging.critical(f"A critical error occurred during KG building: {e}", exc_info=True)
    finally:
        logging.info("Shutting down background tasks...")
        try:
            litellm.shutdown()
        except:
            pass  # Ignore shutdown errors
        
        # Close Neo4j connection
        if neo4j_kg:
            neo4j_kg.close()

def get_neo4j_session():
    """Get a Neo4j session for querying the knowledge graph."""
    try:
        neo4j_uri = os.getenv("NEO4J_URI", config.NEO4J_URI)
        neo4j_username = os.getenv("NEO4J_USERNAME", config.NEO4J_USERNAME)
        neo4j_password = os.getenv("NEO4J_PASSWORD", config.NEO4J_PASSWORD)
        
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_username, neo4j_password)
        )
        
        return driver.session(database=config.NEO4J_DATABASE)
    except Exception as e:
        logging.error(f"Failed to create Neo4j session: {e}")
        return None