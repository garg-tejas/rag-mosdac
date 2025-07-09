#!/usr/bin/env python3
"""
RAG-Crawl4AI Streamlit Interface
A beautiful web interface for the RAG pipeline with document viewing, 
knowledge graph visualization, and interactive Q&A.
"""

import streamlit as st
import os
import sys
import json
import asyncio
import logging
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import time
from datetime import datetime
import networkx as nx
from pyvis.network import Network
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src import config
    from src.modules.qa_app import RAGPipeline
    from src.modules import crawler, kg_builder, vector_db_builder
    from src.modules.gpu_utils import check_gpu_setup, get_device
    from src.modules.kg_builder import get_neo4j_session
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="MOSDAC RAG System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for connection status
def init_connection_state():
    """Initialize connection status in session state."""
    if 'connection_status' not in st.session_state:
        st.session_state.connection_status = {
            'pinecone': {'checked': False, 'connected': False, 'last_check': None, 'error': None},
            'neo4j': {'checked': False, 'connected': False, 'last_check': None, 'error': None},
            'rag_system': {'initialized': False, 'instance': None, 'error': None}
        }

def check_pinecone_connection_cached():
    """Check Pinecone connection with caching."""
    conn_state = st.session_state.connection_status['pinecone']
    
    # Return cached result if already checked
    if conn_state['checked'] and conn_state['last_check']:
        time_since_check = time.time() - conn_state['last_check']
        if time_since_check < 300:  # Cache for 5 minutes
            return conn_state['connected']
    
    # Perform actual check
    try:
        if not os.getenv("PINECONE_API_KEY"):
            conn_state.update({
                'checked': True, 'connected': False, 
                'last_check': time.time(), 'error': 'API key not found'
            })
            return False
            
        from src.modules.vector_db_builder import get_pinecone_index
        index = get_pinecone_index()
        stats = index.describe_index_stats()
        
        # Check the specific namespace
        namespace_stats = stats.get('namespaces', {}).get(config.PINECONE_NAMESPACE, {})
        vector_count = namespace_stats.get('vector_count', 0)
        is_connected = vector_count > 0
        
        conn_state.update({
            'checked': True, 'connected': is_connected,
            'last_check': time.time(), 'error': None
        })
        return is_connected
        
    except Exception as e:
        conn_state.update({
            'checked': True, 'connected': False,
            'last_check': time.time(), 'error': str(e)
        })
        return False

def check_neo4j_connection_cached():
    """Check Neo4j connection with caching."""
    conn_state = st.session_state.connection_status['neo4j']
    
    # Return cached result if already checked
    if conn_state['checked'] and conn_state['last_check']:
        time_since_check = time.time() - conn_state['last_check']
        if time_since_check < 300:  # Cache for 5 minutes
            return conn_state['connected']
    
    # Perform actual check
    try:
        session = get_neo4j_session()
        if session:
            result = session.run("MATCH (n:Entity) RETURN count(n) as count").single()
            session.close()
            is_connected = result["count"] > 0
            
            conn_state.update({
                'checked': True, 'connected': is_connected,
                'last_check': time.time(), 'error': None
            })
            return is_connected
        else:
            conn_state.update({
                'checked': True, 'connected': False,
                'last_check': time.time(), 'error': 'Failed to create session'
            })
            return False
            
    except Exception as e:
        conn_state.update({
            'checked': True, 'connected': False,
            'last_check': time.time(), 'error': str(e)
        })
        return False

def get_rag_system_cached():
    """Get RAG system instance with caching."""
    rag_state = st.session_state.connection_status['rag_system']
    
    # Return cached instance if available
    if rag_state['initialized'] and rag_state['instance']:
        return rag_state['instance']
    
    # Initialize RAG system
    try:
        rag_system = RAGPipeline()
        rag_state.update({
            'initialized': True, 'instance': rag_system, 'error': None
        })
        return rag_system
        
    except Exception as e:
        rag_state.update({
            'initialized': False, 'instance': None, 'error': str(e)
        })
        return None

def refresh_connection_status():
    """Force refresh of all connection statuses."""
    st.session_state.connection_status = {
        'pinecone': {'checked': False, 'connected': False, 'last_check': None, 'error': None},
        'neo4j': {'checked': False, 'connected': False, 'last_check': None, 'error': None},
        'rag_system': {'initialized': False, 'instance': None, 'error': None}
    }
    # Force recheck
    check_pinecone_connection_cached()
    check_neo4j_connection_cached()

def get_neo4j_stats_cached():
    """Get Neo4j knowledge graph statistics with caching."""
    # Only get stats if connection is already established
    if not check_neo4j_connection_cached():
        return {"entities": 0, "relationships": 0}
    
    try:
        session = get_neo4j_session()
        if session:
            entity_count = session.run("MATCH (n:Entity) RETURN count(n) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r:RELATES]->() RETURN count(r) as count").single()["count"]
            session.close()
            return {"entities": entity_count, "relationships": rel_count}
    except Exception as e:
        st.error(f"Error getting Neo4j stats: {e}")
    return {"entities": 0, "relationships": 0}

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .prototype-banner {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ff6b6b;
        margin-bottom: 1rem;
    }
    
    .status-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    
    .status-card.warning {
        border-left-color: #ffc107;
        background: #fff3cd;
    }
    
    .status-card.error {
        border-left-color: #dc3545;
        background: #f8d7da;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    .stTabs > div > div > div > div {
        padding-top: 1rem;
    }
    
    .markdown-content {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 3px solid #007bff;
    }
</style>
""", unsafe_allow_html=True)

def display_header():
    """Display the main header with hackathon banner."""
    st.markdown("""
    <div class="prototype-banner">
        <h3>🛰️ ISRO BAH HACKATHON SUBMISSION</h3>
        <p>This is an innovative idea demonstration showcasing our RAG approach for intelligent 
        processing and querying of MOSDAC satellite data and documentation.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🚀 MOSDAC Knowledge-Powered RAG System</h1>
        <p>Intelligent Satellite Data Processing & Knowledge Management</p>
    </div>
    """, unsafe_allow_html=True)

def get_pipeline_status():
    """Check the status of each pipeline step."""
    status = {
        "crawl": {
            "completed": config.MARKDOWN_DIR.exists() and any(config.MARKDOWN_DIR.rglob("*.md")),
            "path": config.MARKDOWN_DIR,
            "description": "Web content crawling and markdown extraction"
        },
        "kg": {
            "completed": check_neo4j_connection_cached(),
            "path": "Neo4j Aura",
            "description": "Knowledge graph extraction and storage in Neo4j"
        },
        "vectordb": {
            "completed": check_pinecone_connection_cached(),
            "path": "Pinecone Cloud",
            "description": "Vector database creation in Pinecone for semantic search"
        }
    }
    return status

def show_pipeline_overview():
    """Display pipeline status and management."""
    st.header("📊 Pipeline Overview")
    
    # Connection refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Connections", help="Force refresh database connection status"):
            refresh_connection_status()
            st.rerun()
    
    status = get_pipeline_status()
    
    # Status cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🕷️ Web Crawling")
        if status["crawl"]["completed"]:
            st.markdown('<div class="status-card">✅ Completed</div>', unsafe_allow_html=True)
            if config.MARKDOWN_DIR.exists():
                md_files = list(config.MARKDOWN_DIR.rglob("*.md"))
                st.metric("Markdown Files", len(md_files))
        else:
            st.markdown('<div class="status-card warning">⏳ Not Started</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🧠 Knowledge Graph (Neo4j)")
        conn_state = st.session_state.connection_status['neo4j']
        
        if status["kg"]["completed"]:
            st.markdown('<div class="status-card">✅ Completed</div>', unsafe_allow_html=True)
            neo4j_stats = get_neo4j_stats_cached()
            st.metric("Entities", neo4j_stats["entities"])
            st.metric("Relationships", neo4j_stats["relationships"])
        else:
            if conn_state['error']:
                st.markdown('<div class="status-card error">❌ Connection Error</div>', unsafe_allow_html=True)
                st.caption(f"Error: {conn_state['error'][:50]}...")
            else:
                st.markdown('<div class="status-card warning">⏳ Not Started</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 🔍 Vector Database (Pinecone)")
        conn_state = st.session_state.connection_status['pinecone']
        
        if status["vectordb"]["completed"]:
            st.markdown('<div class="status-card">✅ Completed</div>', unsafe_allow_html=True)
            try:
                from src.modules.vector_db_builder import get_pinecone_index
                index = get_pinecone_index()
                stats = index.describe_index_stats()
                namespace_stats = stats.get('namespaces', {}).get(config.PINECONE_NAMESPACE, {})
                vector_count = namespace_stats.get('vector_count', 0)
                st.metric("Vectors", vector_count)
            except:
                st.metric("Status", "Connected")
        else:
            if conn_state['error']:
                st.markdown('<div class="status-card error">❌ Connection Error</div>', unsafe_allow_html=True)
                st.caption(f"Error: {conn_state['error'][:50]}...")
            else:
                st.markdown('<div class="status-card warning">⏳ Not Started</div>', unsafe_allow_html=True)
    
    # Show last check times if available
    with st.expander("🔍 Connection Details", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            neo4j_state = st.session_state.connection_status['neo4j']
            if neo4j_state['last_check']:
                last_check = datetime.fromtimestamp(neo4j_state['last_check'])
                st.caption(f"Last checked: {last_check.strftime('%H:%M:%S')}")
            
        with col2:
            pinecone_state = st.session_state.connection_status['pinecone']
            if pinecone_state['last_check']:
                last_check = datetime.fromtimestamp(pinecone_state['last_check'])
                st.caption(f"Last checked: {last_check.strftime('%H:%M:%S')}")
        
        with col3:
            rag_state = st.session_state.connection_status['rag_system']
            if rag_state['initialized']:
                st.caption("RAG System: ✅ Initialized")
            elif rag_state['error']:
                st.caption(f"RAG System: ❌ {rag_state['error'][:30]}...")
    
    # Pipeline execution
    st.markdown("### 🚀 Pipeline Execution")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🕷️ Run Crawling", type="secondary"):
            run_pipeline_step("crawl")
    
    with col2:
        if st.button("🧠 Build Knowledge Graph", type="secondary", 
                   help="Extract entities and relationships with improved normalization to prevent duplicates"):
            run_pipeline_step("kg")
    
    with col3:
        if st.button("🔍 Build Vector Database", type="secondary"):
            run_pipeline_step("vectordb")
    
    # Full pipeline run
    st.markdown("---")
    if st.button("🚀 Run Full Pipeline", type="primary"):
        run_pipeline_step("all")

def run_pipeline_step(step):
    """Run a specific pipeline step."""
    if step == "crawl":
        with st.spinner("🕷️ Crawling websites and extracting content..."):
            try:
                asyncio.run(crawler.build_knowledge_graph())
                st.success("✅ Crawling completed!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Crawling failed: {e}")
    
    elif step == "kg":
        with st.spinner("🧠 Building knowledge graph..."):
            try:
                asyncio.run(kg_builder.build_knowledge_graph())
                st.success("✅ Knowledge graph built!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Knowledge graph building failed: {e}")
    
    elif step == "vectordb":
        with st.spinner("🔍 Building vector database..."):
            try:
                vector_db_builder.build_vector_database()
                st.success("✅ Vector database built!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Vector database building failed: {e}")
    
    elif step == "all":
        with st.spinner("🚀 Running full pipeline..."):
            try:
                # Run all steps in sequence
                asyncio.run(kg_builder.build_knowledge_graph())
                vector_db_builder.build_vector_database()
                st.success("✅ Full pipeline completed!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Pipeline failed: {e}")

def show_documents():
    """Display document browser and content viewer."""
    st.header("📄 Document Browser")
    
    if not config.MARKDOWN_DIR.exists():
        st.warning("⚠️ No documents found. Run the crawling step first.")
        return
    
    # Get all markdown files
    md_files = list(config.MARKDOWN_DIR.rglob("*.md"))
    
    if not md_files:
        st.warning("⚠️ No markdown files found in the output directory.")
        return
    
    # File selector
    file_names = [f.relative_to(config.MARKDOWN_DIR) for f in md_files]
    selected_file_name = st.selectbox("📁 Select a document:", file_names)
    
    if selected_file_name:
        selected_file = config.MARKDOWN_DIR / selected_file_name
        
        # Display file content
        st.markdown(f"### 📄 {selected_file_name}")
        
        try:
            content = selected_file.read_text(encoding="utf-8")
            
            # Content display with styling
            st.markdown('<div class="markdown-content">', unsafe_allow_html=True)
            st.markdown(content)
            st.markdown('</div>', unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return
        
        # Document stats
        st.markdown("### 📊 Document Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Characters", len(content))
        with col2:
            st.metric("Lines", content.count('\n') + 1)
        with col3:
            st.metric("Words", len(content.split()))
        with col4:
            st.metric("File Size", f"{selected_file.stat().st_size / 1024:.1f} KB")

def create_network_graph(entities, relationships, original_matches=None):
    """Create an interactive network graph using pyvis with highlighting for original matches."""
    
    try:
        # Create pyvis network
        net = Network(height="400px", width="100%", bgcolor="#222222", font_color="white")
        
        # Configure physics
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "barnesHut": {
              "gravitationalConstant": -30000,
              "centralGravity": 0.3,
              "springLength": 95,
              "springConstant": 0.04,
              "damping": 0.09,
              "avoidOverlap": 0.1
            },
            "maxVelocity": 26,
            "minVelocity": 0.1,
            "timestep": 0.35,
            "stabilization": {"iterations": 150}
          }
        }
        """)
        
        # Color scheme for different entity types
        type_colors = {
            "satellite": "#FF6B6B",      # Red
            "organization": "#4ECDC4",   # Teal  
            "instrument": "#45B7D1",     # Blue
            "data_product": "#96CEB4",   # Green
            "parameter": "#FECA57",      # Yellow
            "mission": "#FF9FF3",        # Pink
            "service": "#54A0FF",        # Light Blue
            "application": "#5F27CD",    # Purple
            "technology": "#00D2D3"      # Cyan
        }
        
        # Set to track original matches for highlighting
        original_match_set = set(original_matches) if original_matches else set()
        
        # Add nodes with different styling for original matches
        for entity in entities:
            entity_name = entity['name']
            entity_type = entity.get('type', 'unknown')
            
            # Determine color and size based on whether it's an original match
            is_original = entity_name in original_match_set
            base_color = type_colors.get(entity_type, "#95A5A6")
            
            if is_original:
                # Original matches: larger, brighter, with border
                color = base_color
                size = 25
                borderWidth = 4
                borderColor = "#FFD700"  # Gold border for original matches
                title = f"🎯 ORIGINAL MATCH\nName: {entity_name}\nType: {entity_type}"
            else:
                # Expanded nodes: smaller, slightly transparent
                color = base_color + "CC"  # Add transparency
                size = 15
                borderWidth = 1
                borderColor = "#FFFFFF"
                title = f"🔗 Connected Node\nName: {entity_name}\nType: {entity_type}"
            
            net.add_node(
                entity_name, 
                label=entity_name.replace('_', ' ').title(),
                color=color,
                size=size,
                title=title,
                borderWidth=borderWidth,
                shapeProperties={"borderDashes": False if is_original else [5, 5]}
            )
        
        # Add edges with different styles for connections to original matches
        for rel in relationships:
            source_is_original = rel['source'] in original_match_set
            target_is_original = rel['target'] in original_match_set
            
            # Style edge based on connection to original matches
            if source_is_original or target_is_original:
                # Connection involves an original match - make it prominent
                color = "#FFD700"  # Gold
                width = 3
            else:
                # Connection between expanded nodes - make it subtle
                color = "#95A5A6"  # Gray
                width = 1
            
            net.add_edge(
                rel['source'], 
                rel['target'],
                label=rel['relation'].replace('_', ' ').title(),
                color=color,
                width=width,
                title=f"Relationship: {rel['relation']}"
            )
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
        net.save_graph(temp_file.name)
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        st.error(f"Error creating network graph: {e}")
        return None

def show_knowledge_graph():
    """Display and visualize the knowledge graph."""
    st.header("🧠 Knowledge Graph Visualization")
    
    # Check Neo4j connection
    if not check_neo4j_connection_cached():
        st.warning("⚠️ Neo4j knowledge graph not found. Run the KG building step first.")
        return
    
    try:
        entities = []
        relationships = []
        
        # Load from Neo4j
        session = get_neo4j_session()
        if session:
            # Get entities
            entity_result = session.run("MATCH (n:Entity) RETURN n.name as name, n.type as type")
            entities = [{"name": record["name"], "type": record["type"]} for record in entity_result]
            
            # Get relationships
            rel_result = session.run("""
                MATCH (source:Entity)-[r:RELATES]->(target:Entity) 
                RETURN source.name as source, target.name as target, r.relation as relation
            """)
            relationships = [{"source": record["source"], "target": record["target"], "relation": record["relation"]} for record in rel_result]
            
            session.close()
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Total Entities", len(entities))
        with col2:
            st.metric("🔗 Total Relationships", len(relationships))
        with col3:
            entity_types = [e.get("type", "Unknown") for e in entities]
            st.metric("📋 Entity Types", len(set(entity_types)))
        
        # Interactive controls
        st.markdown("### 🎮 Interactive Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Entity type filter
            all_types = sorted(set(entity_types))
            selected_types = st.multiselect(
                "🏷️ Filter by Entity Type:",
                all_types,
                default=all_types
            )
        
        with col2:
            # Entity search
            search_term = st.text_input(
                "🔍 Search Entities:", 
                placeholder="e.g., INSAT-3D, MOSDAC, satellite, ocean, temperature",
                help="Search supports various formats: 'INSAT-3D', 'INSAT 3D', 'insat_3d' all work the same"
            )
            
            # Add search suggestions if no search term is entered
            if not search_term:
                st.caption("💡 Try searching: INSAT-3D, MOSDAC, Oceansat-2, Kalpana-1, temperature, satellite")
            else:
                # Show what we're searching for
                st.caption(f"🔍 Searching for entities containing: '{search_term}'")
        
        # BFS Expansion Controls (only show when searching)
        if search_term:
            with st.expander("🔗 BFS Expansion Settings", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    max_depth = st.slider(
                        "Maximum BFS Depth", 
                        min_value=1, 
                        max_value=5, 
                        value=3,
                        help="How many hops away from matching entities to include"
                    )
                with col2:
                    show_original_highlights = st.checkbox(
                        "Highlight Original Matches",
                        value=True,
                        help="Visually distinguish original search matches from expanded nodes"
                    )
                st.info("🌐 BFS will find all entities connected to your search matches within the specified depth")
        
        # Filter entities and relationships based on selection
        filtered_entities = []
        
        # First, find entities that match the search term
        matching_entities = []
        for entity in entities:
            # Apply type filter
            if entity['type'] not in selected_types:
                continue
            # Apply smart search filter
            if search_term:
                if smart_entity_search(entity['name'], search_term):
                    matching_entities.append(entity)
            else:
                filtered_entities.append(entity)
        
        # If search term is provided, expand to include all connected nodes
        if search_term and matching_entities:
            # Use BFS to find all connected entities
            max_depth = locals().get('max_depth', 3)  # Default to 3 if not set
            subgraph_result = find_connected_subgraph(matching_entities, entities, relationships, max_depth)
            filtered_entities = subgraph_result["entities"]
            
            # Apply type filter to the expanded results
            filtered_entities = [e for e in filtered_entities if e['type'] in selected_types]
            
            # Filter relationships to only include filtered entities
            filtered_entity_names = {e['name'] for e in filtered_entities}
            filtered_relationships = [
                rel for rel in relationships 
                if rel['source'] in filtered_entity_names and rel['target'] in filtered_entity_names
            ]
            
            # Show expansion information with depth details
            original_matches = subgraph_result["original_matches"]
            expanded_count = subgraph_result["expanded_count"]
            max_depth_used = subgraph_result["max_depth_used"]
            
            if expanded_count > 0:
                st.success(f"🎯 Found {len(original_matches)} direct matches → Expanded to {len(filtered_entities)} connected entities (+{expanded_count} nodes, max depth: {max_depth_used})")
                
                # Show depth distribution
                depths = subgraph_result["depths"]
                depth_counts = {}
                for entity_name, depth in depths.items():
                    if any(e['name'] == entity_name and e['type'] in selected_types for e in entities):
                        depth_counts[depth] = depth_counts.get(depth, 0) + 1
                
                depth_info = " | ".join([f"Depth {d}: {count}" for d, count in sorted(depth_counts.items())])
                st.caption(f"📊 Distribution: {depth_info}")
            else:
                st.info(f"🎯 Found {len(original_matches)} matching entities (no additional connections within depth {max_depth})")
                
        else:
            # No search term - filter relationships normally
            filtered_entity_names = {e['name'] for e in filtered_entities}
            filtered_relationships = [
                rel for rel in relationships 
                if rel['source'] in filtered_entity_names and rel['target'] in filtered_entity_names
            ]
        
        st.info(f"Showing {len(filtered_entities)} entities and {len(filtered_relationships)} relationships")
        
        # Add debug information if search term is used
        if search_term and len(filtered_entities) == 0 and len(entities) > 0:
            with st.expander("🔧 Search Debug Information", expanded=True):
                st.warning(f"No entities found for search term: '{search_term}'")
                
                # Test the search function with some sample entities
                sample_entities = entities[:5]
                st.markdown("**Testing search with sample entities:**")
                for entity in sample_entities:
                    match_result = smart_entity_search(entity['name'], search_term)
                    icon = "✅" if match_result else "❌"
                    st.markdown(f"{icon} `{entity['name']}` ({entity['type']})")
                
                st.markdown("**💡 Suggestions:**")
                st.markdown("- Try shorter search terms (e.g., 'insat', 'ocean', 'temp')")
                st.markdown("- Use common words from entity names")
                st.markdown("- Clear the search box to see all entities")
                
                if st.button("🔄 Clear Search", key="clear_search"):
                    st.rerun()
        
        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🌐 Interactive Network", "📊 Entity Analysis", "🔗 Relationships", "🔍 Neo4j Query", "📋 Raw Data"])
        
        with tab1:
            st.markdown("### 🌐 Interactive Knowledge Graph")
            
            if filtered_entities and filtered_relationships:
                # Create interactive network graph
                original_matches_list = []
                if search_term and 'subgraph_result' in locals():
                    original_matches_list = subgraph_result.get("original_matches", [])
                
                graph_file = create_network_graph(filtered_entities, filtered_relationships, original_matches_list)
                if graph_file:
                    # Display the graph
                    with open(graph_file, 'r', encoding='utf-8') as f:
                        graph_html = f.read()
                    st.components.v1.html(graph_html, height=500)
                    
                    # Clean up temp file
                    os.unlink(graph_file)
                
                # Add legend for the visualization
                if search_term and original_matches_list:
                    with st.expander("🎨 Visualization Legend", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Node Types:**")
                            st.markdown("🎯 **Gold Border**: Original search matches")
                            st.markdown("🔗 **White Border**: Connected nodes found via BFS")
                            st.markdown("**Size**: Original matches are larger")
                        with col2:
                            st.markdown("**Edge Types:**")
                            st.markdown("🟡 **Gold Edges**: Connect to original matches")
                            st.markdown("⚪ **Gray Edges**: Connect expanded nodes")
                            st.markdown("**Width**: Connections to matches are thicker")
                
                # Graph statistics
                st.markdown("### 📈 Network Statistics")
                col1, col2, col3, col4 = st.columns(4)
                
                # Calculate some basic network metrics
                entity_names = [e['name'] for e in filtered_entities]
                source_counts = {}
                target_counts = {}
                
                for rel in filtered_relationships:
                    source_counts[rel['source']] = source_counts.get(rel['source'], 0) + 1
                    target_counts[rel['target']] = target_counts.get(rel['target'], 0) + 1
                
                with col1:
                    if source_counts:
                        most_connected = max(source_counts.items(), key=lambda x: x[1])
                        st.metric("Most Connected Entity", most_connected[0], most_connected[1])
                
                with col2:
                    relation_types = [r['relation'] for r in filtered_relationships]
                    st.metric("Unique Relations", len(set(relation_types)))
                
                with col3:
                    avg_connections = len(filtered_relationships) / len(filtered_entities) if filtered_entities else 0
                    st.metric("Avg Connections", f"{avg_connections:.1f}")
                
                with col4:
                    density = len(filtered_relationships) / (len(filtered_entities) * (len(filtered_entities) - 1) / 2) if len(filtered_entities) > 1 else 0
                    st.metric("Graph Density", f"{density:.3f}")
            
            else:
                st.info("No entities or relationships found to visualize with current filters.")
                
                # Provide helpful debugging information
                if search_term:
                    st.markdown("**🔍 Search Tips:**")
                    st.markdown(f"- You searched for: `{search_term}`")
                    st.markdown("- Try different variations like:")
                    st.markdown(f"  - `{search_term.upper()}`")
                    st.markdown(f"  - `{search_term.lower()}`")
                    st.markdown(f"  - Individual words from your search")
                    st.markdown("- Check if you've filtered out the entity type you're looking for")
                    st.markdown("- Try removing search terms to see all entities first")
                    
                    # Show what entities are available (first few)
                    if entities:
                        st.markdown("**📋 Available entities (sample):**")
                        sample_entities = entities[:10]
                        for entity in sample_entities:
                            st.markdown(f"- `{entity['name']}` ({entity['type']})")
                        if len(entities) > 10:
                            st.markdown(f"... and {len(entities) - 10} more entities")
                else:
                    st.markdown("**💡 Tip:** Try selecting different entity types or add a search term to filter entities.")
        
        with tab2:
            # Entity type distribution
            if filtered_entities:
                entity_df = pd.DataFrame(filtered_entities)
                type_counts = entity_df['type'].value_counts()
                
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Entity Distribution by Type (Filtered)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Entity table with search
                st.markdown("### 📋 Filtered Entities")
                st.dataframe(entity_df, use_container_width=True)
                
                # Entity details
                st.markdown("### 🔍 Entity Details")
                selected_entity = st.selectbox("Select an entity to see its connections:", 
                                               [e['name'] for e in filtered_entities])
                
                if selected_entity:
                    # Find all relationships for this entity
                    entity_rels = [r for r in relationships if r['source'] == selected_entity or r['target'] == selected_entity]
                    
                    st.write(f"**{selected_entity}** has {len(entity_rels)} connections:")
                    for rel in entity_rels:
                        if rel['source'] == selected_entity:
                            st.write(f"→ {rel['relation']} → **{rel['target']}**")
                        else:
                            st.write(f"← {rel['relation']} ← **{rel['source']}**")
            else:
                st.info("No entities found with current filters.")
        
        with tab3:
            # Relationship analysis
            st.markdown("### 🔗 Relationship Analysis")
            
            if filtered_relationships:
                # Create a simple network representation
                rel_df = pd.DataFrame(filtered_relationships)
                st.dataframe(rel_df, use_container_width=True)
                
                # Relationship type distribution
                if 'relation' in rel_df.columns:
                    rel_counts = rel_df['relation'].value_counts().head(10)
                    fig = px.bar(
                        x=rel_counts.index,
                        y=rel_counts.values,
                        title="Top 10 Relationship Types (Filtered)"
                    )
                    fig.update_layout(xaxis_tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Relationship search
                st.markdown("### 🔍 Find Paths")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_entity = st.selectbox("Start Entity:", [e['name'] for e in filtered_entities])
                with col2:
                    end_entity = st.selectbox("End Entity:", [e['name'] for e in filtered_entities])
                
                if st.button("🔍 Find Path") and start_entity and end_entity:
                    # Simple path finding (direct connections only)
                    paths = []
                    for rel in filtered_relationships:
                        if rel['source'] == start_entity and rel['target'] == end_entity:
                            paths.append(f"{start_entity} → {rel['relation']} → {end_entity}")
                        elif rel['source'] == end_entity and rel['target'] == start_entity:
                            paths.append(f"{start_entity} ← {rel['relation']} ← {end_entity}")
                    
                    if paths:
                        st.success("Direct connections found:")
                        for path in paths:
                            st.write(f"• {path}")
                    else:
                        st.info("No direct connections found between these entities.")
            
            else:
                st.info("No relationships found with current filters.")
        
        with tab4:
            # Neo4j query interface
            st.markdown("### 🔍 Custom Neo4j Queries")
            st.info("Execute custom Cypher queries against the knowledge graph")
            
            # Predefined queries
            st.markdown("#### 📚 Example Queries")
            
            example_queries = {
                "All Satellites": "MATCH (n:Entity) WHERE toLower(n.type) = 'satellite' RETURN n.name as satellite ORDER BY satellite",
                "MOSDAC Connections": "MATCH (mosdac:Entity) WHERE toLower(mosdac.name) CONTAINS 'mosdac' WITH mosdac MATCH (mosdac)-[r:RELATES]-(connected) RETURN mosdac.name, r.relation, connected.name, connected.type LIMIT 20",
                "Most Connected Entities": "MATCH (n:Entity)-[r:RELATES]-() WITH n, count(r) as connections RETURN n.name, n.type, connections ORDER BY connections DESC LIMIT 10",
                "Instrument Relationships": "MATCH (i:Entity) WHERE toLower(i.type) = 'instrument' MATCH (i)-[r:RELATES]-(other) RETURN i.name as instrument, r.relation, other.name, other.type LIMIT 20",
                "INSAT Satellites": "MATCH (n:Entity) WHERE toLower(n.name) CONTAINS 'insat' RETURN n.name as satellite, n.type ORDER BY satellite",
                "Data Products": "MATCH (n:Entity) WHERE toLower(n.type) CONTAINS 'data' OR toLower(n.type) CONTAINS 'parameter' RETURN n.name as product, n.type ORDER BY product"
            }
            
            selected_example = st.selectbox("Choose an example query:", list(example_queries.keys()))
            
            if selected_example:
                query_text = example_queries[selected_example]
                st.code(query_text, language="cypher")
                
                if st.button("🚀 Run Example Query"):
                    try:
                        session = get_neo4j_session()
                        if session:
                            result = session.run(query_text)
                            records = [record.data() for record in result]
                            session.close()
                            
                            if records:
                                df = pd.DataFrame(records)
                                st.dataframe(df, use_container_width=True)
                                st.success(f"Query returned {len(records)} results")
                            else:
                                st.info("Query returned no results")
                    except Exception as e:
                        st.error(f"Query failed: {e}")
            
            # Custom query
            st.markdown("#### ✏️ Custom Query")
            custom_query = st.text_area(
                "Enter your Cypher query:",
                placeholder="MATCH (n:Entity) RETURN n.name, n.type LIMIT 10",
                height=100
            )
            
            if st.button("🚀 Execute Custom Query") and custom_query:
                try:
                    session = get_neo4j_session()
                    if session:
                        result = session.run(custom_query)
                        records = [record.data() for record in result]
                        session.close()
                        
                        if records:
                            df = pd.DataFrame(records)
                            st.dataframe(df, use_container_width=True)
                            st.success(f"Query returned {len(records)} results")
                        else:
                            st.info("Query returned no results")
                except Exception as e:
                    st.error(f"Query failed: {e}")
        
        with tab5:
            st.markdown("### 📄 Raw Knowledge Graph Data")
            kg_display_data = {
                "entities": filtered_entities,
                "relationships": filtered_relationships,
                "source": "Neo4j Database"
            }
            st.json(kg_display_data)
    
    except Exception as e:
        st.error(f"Error loading knowledge graph: {e}")

def show_qa_interface():
    """Interactive Q&A interface."""
    st.header("💬 Interactive Q&A System")
    
    # Check if Pinecone is configured
    if not check_pinecone_connection_cached():
        st.warning("⚠️ Pinecone vector database not configured or empty. Please check your PINECONE_API_KEY and run the vector database building step first.")
        return
    
    # Get cached RAG system
    rag_system = get_rag_system_cached()
    if not rag_system:
        rag_state = st.session_state.connection_status['rag_system']
        st.error(f"❌ Failed to initialize RAG system: {rag_state.get('error', 'Unknown error')}")
        if st.button("🔄 Retry RAG Initialization"):
            st.session_state.connection_status['rag_system'] = {'initialized': False, 'instance': None, 'error': None}
            st.rerun()
        return
    
    # Show RAG system status
    st.success("✅ RAG system ready!")
    
    # Chat interface
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Suggested questions
    st.markdown("### 💡 Suggested Questions")
    suggested_questions = [
        "What are the main objectives of the INSAT-3DR mission?",
        "What kind of data does the 'Soil Moisture' product provide?",
        "What is MOSDAC's data access policy?",
        "Tell me about the Oceansat-2 satellite.",
        "What instruments are available on INSAT-3D?"
    ]
    
    cols = st.columns(3)
    for i, question in enumerate(suggested_questions):
        col = cols[i % 3]
        if col.button(f"❓ {question[:50]}...", key=f"q_{i}"):
            st.session_state.current_question = question
    
    # Question input
    question = st.text_input(
        "🤔 Ask a question about MOSDAC:",
        value=st.session_state.get("current_question", ""),
        placeholder="e.g., What are the main features of INSAT-3D?"
    )
    
    if st.button("🚀 Get Answer", type="primary", disabled=not question):
        if question:
            with st.spinner("🔍 Searching knowledge base..."):
                try:
                    result = rag_system.answer_question(question)
                    
                    # Handle both old string format and new dict format
                    if isinstance(result, dict):
                        answer = result["answer"]
                        sources = result.get("sources", [])
                        context_used = result.get("context_used", 0)
                        confidence_scores = result.get("confidence_scores", [])
                    else:
                        answer = str(result)
                        sources = []
                        context_used = 0
                        confidence_scores = []
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": answer,
                        "sources": sources,
                        "context_used": context_used,
                        "confidence_scores": confidence_scores,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    # Show the answer immediately
                    st.markdown("### 🤖 Answer")
                    st.markdown(answer)
                    
                    # Show metadata
                    if sources or context_used or confidence_scores:
                        st.markdown("### 📊 Answer Details")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if sources:
                                st.markdown(f"**📄 Sources:** {', '.join(sources[:3])}")
                        with col2:
                            if context_used:
                                st.markdown(f"**📈 Documents:** {context_used}")
                        with col3:
                            if confidence_scores:
                                avg_confidence = sum(confidence_scores) / len(confidence_scores)
                                st.markdown(f"**🎯 Confidence:** {avg_confidence:.3f}")
                    
                    # Show related knowledge graph if Neo4j is available
                    if check_neo4j_connection_cached():
                        st.markdown("### 🧠 Related Knowledge Graph")
                        
                        # Extract potential entity names from question and answer
                        search_text = f"{question} {answer}"
                        
                        # Get related subgraph
                        subgraph = get_related_subgraph([question, answer])
                        
                        if subgraph["entities"]:
                            st.info(f"Found {len(subgraph['entities'])} related entities and {len(subgraph['relationships'])} relationships")
                            
                            # Create tabs for different views
                            kg_tab1, kg_tab2 = st.tabs(["🌐 Visualization", "📊 Data"])
                            
                            with kg_tab1:
                                # Create interactive network graph
                                if subgraph["entities"] and subgraph["relationships"]:
                                    graph_file = create_network_graph(subgraph["entities"], subgraph["relationships"])
                                    if graph_file:
                                        with open(graph_file, 'r', encoding='utf-8') as f:
                                            graph_html = f.read()
                                        st.components.v1.html(graph_html, height=400)
                                        os.unlink(graph_file)
                                elif subgraph["entities"]:
                                    st.info("Found entities but no relationships to visualize")
                                    for entity in subgraph["entities"][:5]:
                                        st.write(f"• **{entity['name']}** ({entity['type']})")
                            
                            with kg_tab2:
                                if subgraph["entities"]:
                                    st.markdown("**Entities:**")
                                    entity_df = pd.DataFrame(subgraph["entities"])
                                    st.dataframe(entity_df, use_container_width=True)
                                
                                if subgraph["relationships"]:
                                    st.markdown("**Relationships:**")
                                    rel_df = pd.DataFrame(subgraph["relationships"])
                                    st.dataframe(rel_df, use_container_width=True)
                        else:
                            st.info("No related entities found in the knowledge graph for this query.")
                    
                    # Clear current question
                    if "current_question" in st.session_state:
                        del st.session_state.current_question
                    
                except Exception as e:
                    st.error(f"❌ Error getting answer: {e}")
    
    # Display chat history
    if st.session_state.chat_history:
        st.markdown("### 💬 Chat History")
        
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            with st.expander(f"Q: {chat['question'][:100]}... [{chat['timestamp']}]", expanded=i==0):
                st.markdown(f"**Question:** {chat['question']}")
                st.markdown(f"**Answer:** {chat['answer']}")
                
                # Show additional metadata if available
                if chat.get("sources"):
                    st.markdown(f"**📊 Sources:** {', '.join(chat['sources'][:3])}")
                if chat.get("context_used"):
                    st.markdown(f"**📈 Documents used:** {chat['context_used']}")
                if chat.get("confidence_scores"):
                    avg_confidence = sum(chat['confidence_scores']) / len(chat['confidence_scores'])
                    st.markdown(f"**🎯 Confidence:** {avg_confidence:.3f}")
        
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()

def extract_entities_from_text(text: str, all_entities: list) -> list:
    """Extract relevant entities from text based on entity names."""
    if not text or not all_entities:
        return []
    
    text_lower = text.lower()
    relevant_entities = []
    
    for entity in all_entities:
        entity_name = entity['name'].lower()
        # Check if entity name (or parts of it) appear in the text
        if entity_name in text_lower or any(word in text_lower for word in entity_name.split('_')):
            relevant_entities.append(entity)
    
    return relevant_entities

def smart_entity_search(entity_name: str, search_term: str) -> bool:
    """Smart search function that handles normalized entity names and various search formats."""
    if not search_term or not entity_name:
        return True
    
    # Import normalization function
    from src.modules.kg_builder import normalize_name
    
    # Normalize both the search term and entity name for comparison
    normalized_search = normalize_name(search_term)
    normalized_entity = entity_name.lower()
    
    # Direct match with normalized search
    if normalized_search in normalized_entity:
        return True
    
    # Check if any word from the search term appears in entity name
    search_words = search_term.lower().replace('-', ' ').replace('_', ' ').split()
    entity_words = normalized_entity.replace('_', ' ').split()
    
    # Check for word overlap
    for search_word in search_words:
        if len(search_word) > 2:  # Only check meaningful words
            for entity_word in entity_words:
                if search_word in entity_word or entity_word in search_word:
                    return True
    
    # Check for partial matches with original search term
    search_lower = search_term.lower()
    if search_lower in normalized_entity or any(word in normalized_entity for word in search_lower.split() if len(word) > 2):
        return True
    
    return False

def find_connected_subgraph(matching_entities: list, all_entities: list, all_relationships: list, max_depth: int = 3) -> dict:
    """
    Use BFS to find all entities connected to the matching entities up to max_depth.
    Returns a dictionary with expanded entities, relationships, and depth information.
    """
    if not matching_entities:
        return {"entities": [], "relationships": [], "depths": {}, "original_matches": [], "expanded_count": 0}
    
    # Create adjacency list for efficient graph traversal
    adjacency = {}
    for entity in all_entities:
        adjacency[entity['name']] = []
    
    # Build adjacency list from relationships
    for rel in all_relationships:
        if rel['source'] in adjacency and rel['target'] in adjacency:
            adjacency[rel['source']].append(rel['target'])
            adjacency[rel['target']].append(rel['source'])  # Undirected graph
    
    # BFS to find all connected nodes with depth tracking
    visited = set()
    depths = {}  # Track depth of each node
    queue = []
    original_matches = set()
    
    # Start BFS from all matching entities (depth 0)
    for entity in matching_entities:
        entity_name = entity['name']
        if entity_name not in visited:
            queue.append((entity_name, 0))  # (node, depth)
            visited.add(entity_name)
            depths[entity_name] = 0
            original_matches.add(entity_name)
    
    # Perform BFS with depth limiting
    while queue:
        current_entity, current_depth = queue.pop(0)
        
        # Don't expand beyond max_depth
        if current_depth >= max_depth:
            continue
        
        # Add all neighbors to queue if not visited
        for neighbor in adjacency.get(current_entity, []):
            if neighbor not in visited:
                visited.add(neighbor)
                new_depth = current_depth + 1
                depths[neighbor] = new_depth
                queue.append((neighbor, new_depth))
    
    # Collect all entities in the connected component
    connected_entities = []
    for entity in all_entities:
        if entity['name'] in visited:
            connected_entities.append(entity)
    
    # Collect all relationships within the connected component
    connected_relationships = []
    for rel in all_relationships:
        if rel['source'] in visited and rel['target'] in visited:
            connected_relationships.append(rel)
    
    return {
        "entities": connected_entities,
        "relationships": connected_relationships,
        "depths": depths,
        "original_matches": list(original_matches),
        "expanded_count": len(connected_entities) - len(matching_entities),
        "max_depth_used": max(depths.values()) if depths else 0
    }

def get_related_subgraph(search_texts: list) -> dict:
    """Get entities and relationships related to the given search texts."""
    if not search_texts:
        return {"entities": [], "relationships": []}
    
    try:
        session = get_neo4j_session()
        if not session:
            return {"entities": [], "relationships": []}
        
        # Extract potential entity names from search texts
        from src.modules.kg_builder import normalize_name
        
        # Combine all search texts
        combined_text = " ".join(search_texts).lower()
        
        # Get all entities from the database first
        all_entities_query = "MATCH (n:Entity) RETURN n.name as name, n.type as type"
        all_entities_result = session.run(all_entities_query)
        all_entities = [{"name": record["name"], "type": record["type"]} for record in all_entities_result]
        
        # Find entities that match search text
        relevant_entities = []
        search_words = set(combined_text.split())
        
        for entity in all_entities:
            entity_name = entity["name"]
            entity_words = set(entity_name.split("_"))
            
            # Check for exact name match or significant word overlap
            if (entity_name in combined_text or 
                any(word in combined_text for word in entity_words if len(word) > 2) or
                len(entity_words.intersection(search_words)) > 0):
                relevant_entities.append(entity)
        
        if not relevant_entities:
            # If no entities found by text matching, try a broader search
            # Look for entities containing key terms
            key_terms = ["insat", "mosdac", "satellite", "oceansat", "kalpana", "3d", "3dr"]
            for term in key_terms:
                if term in combined_text:
                    term_query = "MATCH (n:Entity) WHERE toLower(n.name) CONTAINS $term RETURN n.name as name, n.type as type"
                    term_result = session.run(term_query, term=term)
                    for record in term_result:
                        entity_data = {"name": record["name"], "type": record["type"]}
                        if entity_data not in relevant_entities:
                            relevant_entities.append(entity_data)
        
        if not relevant_entities:
            session.close()
            return {"entities": [], "relationships": []}
        
        # Get relationships between these entities and their immediate neighbors
        found_entity_names = [e["name"] for e in relevant_entities]
        
        rel_query = """
        MATCH (source:Entity)-[r:RELATES]->(target:Entity)
        WHERE source.name IN $entity_names OR target.name IN $entity_names
        RETURN DISTINCT source.name as source, target.name as target, r.relation as relation
        LIMIT 50
        """
        
        rel_result = session.run(rel_query, entity_names=found_entity_names)
        relationships = [{"source": record["source"], "target": record["target"], "relation": record["relation"]} for record in rel_result]
        
        # Add any additional entities that appear in relationships
        additional_entities = set()
        for rel in relationships:
            additional_entities.add(rel["source"])
            additional_entities.add(rel["target"])
        
        # Get entity types for additional entities not already in relevant_entities
        existing_names = {e["name"] for e in relevant_entities}
        for entity_name in additional_entities:
            if entity_name not in existing_names:
                entity_query_single = "MATCH (n:Entity {name: $name}) RETURN n.name as name, n.type as type"
                single_result = session.run(entity_query_single, name=entity_name)
                single_record = single_result.single()
                if single_record:
                    relevant_entities.append({"name": single_record["name"], "type": single_record["type"]})
        
        session.close()
        return {"entities": relevant_entities, "relationships": relationships}
        
    except Exception as e:
        st.error(f"Error getting related subgraph: {e}")
        return {"entities": [], "relationships": []}

def main():
    """Main Streamlit application."""
    init_connection_state() # Initialize connection status on startup
    display_header()
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    
    pages = {
        "📊 Pipeline Overview": show_pipeline_overview,
        "📄 Document Browser": show_documents,
        "🧠 Knowledge Graph": show_knowledge_graph,
        "💬 Q&A Interface": show_qa_interface
    }
    
    selected_page = st.sidebar.radio("Select a page:", list(pages.keys()))
    
    # System status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🖥️ System Status")
    device = get_device()
    if hasattr(device, 'type'):
        device_type = device.type
    else:
        device_type = str(device)
    
    if device_type == "cuda":
        st.sidebar.success("🚀 GPU Ready")
    elif device_type == "mps":
        st.sidebar.success("🍎 MPS Ready")
    else:
        st.sidebar.info("💻 CPU Mode")
    
    # Database status
    st.sidebar.markdown("### 🗄️ Database Status")
    if check_pinecone_connection_cached():
        st.sidebar.success("📌 Pinecone Connected")
    else:
        st.sidebar.warning("📌 Pinecone Not Connected")
    
    if check_neo4j_connection_cached():
        st.sidebar.success("🧠 Neo4j Connected")
    else:
        st.sidebar.warning("🧠 Neo4j Not Connected")
    
    # Project info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info(
        "RAG-Crawl4AI is a prototype demonstration of our approach to "
        "web content processing and knowledge extraction using modern RAG techniques with Pinecone and Neo4j."
    )
    
    # Run selected page
    pages[selected_page]()

if __name__ == "__main__":
    main() 