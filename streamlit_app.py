#!/usr/bin/env python3
"""
RAG-Crawl4AI Streamlit Interface
A beautiful web interface for the RAG pipeline with document viewing, 
knowledge graph visualization, and interactive Q&A.
"""

# Fix ChromaDB sqlite3 compatibility issue on Streamlit Cloud
import sys
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

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

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src import config
    from src.modules.qa_app import RAGPipeline
    from src.modules import crawler, kg_builder, vector_db_builder
    from src.modules.gpu_utils import check_gpu_setup, get_device
except ImportError as e:
    error_msg = str(e)
    if "sqlite3" in error_msg.lower() or "chroma" in error_msg.lower():
        st.error("""
        🚨 **ChromaDB SQLite Compatibility Issue**
        
        This appears to be a SQLite version compatibility issue. For Windows users:
        
        **Option 1 - Install Visual C++ Build Tools:**
        1. Download and install Microsoft C++ Build Tools from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        2. Run: `pip install pysqlite3`
        3. Restart the application
        
        **Option 2 - Use Alternative Database:**
        The application can be configured to use a different vector database if needed.
        
        **Option 3 - Use Docker:**
        Run the application in a Docker container for consistent dependencies.
        """)
    else:
        st.error(f"Import error: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="MOSDAC RAG System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
            "completed": config.KG_FILE.exists(),
            "path": config.KG_FILE,
            "description": "Knowledge graph extraction from content"
        },
        "vectordb": {
            "completed": os.path.exists(config.VECTOR_DB_PATH),
            "path": config.VECTOR_DB_PATH,
            "description": "Vector database creation for semantic search"
        }
    }
    return status

def show_pipeline_overview():
    """Display pipeline status and management."""
    st.header("📊 Pipeline Overview")
    
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
        st.markdown("### 🧠 Knowledge Graph")
        if status["kg"]["completed"]:
            st.markdown('<div class="status-card">✅ Completed</div>', unsafe_allow_html=True)
            if config.KG_FILE.exists():
                try:
                    kg_data = json.loads(config.KG_FILE.read_text())
                    st.metric("Entities", len(kg_data.get("entities", [])))
                    st.metric("Relationships", len(kg_data.get("relationships", [])))
                except:
                    st.error("Error reading KG file")
        else:
            st.markdown('<div class="status-card warning">⏳ Not Started</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("### 🔍 Vector Database")
        if status["vectordb"]["completed"]:
            st.markdown('<div class="status-card">✅ Completed</div>', unsafe_allow_html=True)
            try:
                import chromadb
                client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
                if config.VECTOR_DB_COLLECTION in [c.name for c in client.list_collections()]:
                    collection = client.get_collection(config.VECTOR_DB_COLLECTION)
                    st.metric("Documents", collection.count())
            except Exception as e:
                st.error(f"Error accessing vector DB: {e}")
        else:
            st.markdown('<div class="status-card warning">⏳ Not Started</div>', unsafe_allow_html=True)
    
    # GPU Status
    st.markdown("### 🖥️ System Status")
    device = get_device()
    if hasattr(device, 'type'):
        device_type = device.type
    else:
        device_type = str(device)
    
    if device_type == "cuda":
        st.success(f"🚀 GPU Acceleration Available: {device}")
    elif device_type == "mps":
        st.success(f"🍎 Apple Silicon MPS Available: {device}")
    else:
        st.info(f"💻 Using CPU: {device}")
    
    # Pipeline Control
    st.markdown("### ⚡ Pipeline Control")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🕷️ Run Crawl", type="secondary"):
            run_pipeline_step("crawl")
    
    with col2:
        if st.button("🧠 Build KG", type="secondary", disabled=not status["crawl"]["completed"]):
            run_pipeline_step("kg")
    
    with col3:
        if st.button("🔍 Build VectorDB", type="secondary", disabled=not status["crawl"]["completed"]):
            run_pipeline_step("vectordb")
    
    with col4:
        if st.button("🚀 Run All", type="primary"):
            run_pipeline_step("all")

def run_pipeline_step(step):
    """Run a pipeline step with progress indication."""
    with st.spinner(f"Running {step} step..."):
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "run_pipeline.py", "--step", step
            ], capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                st.success(f"✅ {step.title()} completed successfully!")
                st.code(result.stdout)
                st.rerun()
            else:
                st.error(f"❌ {step.title()} failed!")
                st.code(result.stderr)
        except Exception as e:
            st.error(f"Error running {step}: {e}")

def show_documents():
    """Display crawled documents with markdown preview."""
    st.header("📄 Document Browser")
    
    if not config.MARKDOWN_DIR.exists():
        st.warning("⚠️ No documents found. Run the crawl step first.")
        return
    
    md_files = list(config.MARKDOWN_DIR.rglob("*.md"))
    
    if not md_files:
        st.warning("⚠️ No markdown files found in the output directory.")
        return
    
    # File selector
    selected_file = st.selectbox(
        "📁 Select a document to view:",
        md_files,
        format_func=lambda x: str(x.relative_to(config.MARKDOWN_DIR))
    )
    
    if selected_file:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 📝 Raw Markdown")
            content = selected_file.read_text(encoding="utf-8")
            st.code(content, language="markdown")
        
        with col2:
            st.markdown("### 👁️ Rendered Preview")
            st.markdown('<div class="markdown-content">', unsafe_allow_html=True)
            st.markdown(content)
            st.markdown('</div>', unsafe_allow_html=True)
        
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

def show_knowledge_graph():
    """Display and visualize the knowledge graph."""
    st.header("🧠 Knowledge Graph Visualization")
    
    if not config.KG_FILE.exists():
        st.warning("⚠️ Knowledge graph not found. Run the KG building step first.")
        return
    
    try:
        kg_data = json.loads(config.KG_FILE.read_text())
        entities = kg_data.get("entities", [])
        relationships = kg_data.get("relationships", [])
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Total Entities", len(entities))
        with col2:
            st.metric("🔗 Total Relationships", len(relationships))
        with col3:
            entity_types = [e.get("type", "Unknown") for e in entities]
            st.metric("📋 Entity Types", len(set(entity_types)))
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["📊 Entity Analysis", "🔗 Relationship Network", "📋 Raw Data"])
        
        with tab1:
            # Entity type distribution
            entity_df = pd.DataFrame(entities)
            if not entity_df.empty:
                type_counts = entity_df['type'].value_counts()
                
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Entity Distribution by Type"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Entity table
                st.markdown("### 📋 All Entities")
                st.dataframe(entity_df, use_container_width=True)
        
        with tab2:
            # Network visualization (simplified)
            st.markdown("### 🔗 Relationship Network")
            
            if relationships:
                # Create a simple network representation
                rel_df = pd.DataFrame(relationships)
                st.dataframe(rel_df, use_container_width=True)
                
                # Relationship type distribution
                if 'relation' in rel_df.columns:
                    rel_counts = rel_df['relation'].value_counts().head(10)
                    fig = px.bar(
                        x=rel_counts.index,
                        y=rel_counts.values,
                        title="Top 10 Relationship Types"
                    )
                    fig.update_xaxis(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No relationships found in the knowledge graph.")
        
        with tab3:
            st.markdown("### 📄 Raw Knowledge Graph Data")
            st.json(kg_data)
    
    except Exception as e:
        st.error(f"Error loading knowledge graph: {e}")

def show_qa_interface():
    """Interactive Q&A interface."""
    st.header("💬 Interactive Q&A System")
    
    # Check if vector DB exists
    if not os.path.exists(config.VECTOR_DB_PATH):
        st.warning("⚠️ Vector database not found. Run the vector database building step first.")
        return
    
    # Initialize RAG system
    if "rag_system" not in st.session_state:
        try:
            with st.spinner("🔄 Initializing RAG system..."):
                st.session_state.rag_system = RAGPipeline()
            st.success("✅ RAG system ready!")
        except Exception as e:
            st.error(f"❌ Failed to initialize RAG system: {e}")
            return
    
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
                    result = st.session_state.rag_system.answer_question(question)
                    
                    # Handle both old string format and new dict format
                    if isinstance(result, dict):
                        answer = result["answer"]
                        sources = result.get("sources", [])
                        context_used = result.get("context_used", 0)
                    else:
                        answer = str(result)
                        sources = []
                        context_used = 0
                    
                    # Add to chat history
                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": answer,
                        "sources": sources,
                        "context_used": context_used,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
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
        
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()

def main():
    """Main Streamlit application."""
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
    
    # GPU status in sidebar
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
    
    # Project info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ About")
    st.sidebar.info(
        "RAG-Crawl4AI is a prototype demonstration of our approach to "
        "web content processing and knowledge extraction using modern RAG techniques."
    )
    
    # Run selected page
    pages[selected_page]()

if __name__ == "__main__":
    main() 