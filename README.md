# 🚀 MOSDAC Knowledge-Powered RAG System

<!-- Crawl4AI Attribution Badge -->
<div align="center">
  <a href="https://github.com/unclecode/crawl4ai">
    <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/>
  </a>
</div>

> ## 🛰️ **ISRO BAH HACKATHON IDEA SUBMISSION**
>
> **This is an innovative proof-of-concept demonstrating our RAG approach for intelligent satellite data processing.**
>
> 🎯 **Objective**: Novel RAG-based approach for intelligent MOSDAC satellite data processing & querying  
> 🛰️ **Focus Area**: Space Technology & Applications - Data Processing & Knowledge Management  
> 🧪 **Innovation**: LLM-powered knowledge extraction from unstructured space/satellite documentation  
> 📊 **Value**: Transform complex satellite data into intelligent, queryable knowledge systems
>
> ## 🌐 **🚀 LIVE DEMO**
>
> **Try Our System Now**: [spacey-mosdac.streamlit.app](https://spacey-mosdac.streamlit.app/)
>
> _No setup required - Interactive proof-of-concept ready_
>
> ---

## 🌟 **Innovation Statement**

This proof-of-concept addresses a critical challenge in space data management: **making complex satellite and meteorological data more accessible and queryable**. Our system demonstrates how modern RAG technology can transform static MOSDAC documentation into an intelligent knowledge assistant.

**Key Innovation**: Beyond simple document search, our system **understands relationships** between satellites, missions, instruments, and data products, enabling sophisticated queries like _"What instruments on INSAT-3D help with monsoon prediction?"_

> **⚠️ Note**: This is a proof-of-concept demonstration. Production implementation would involve additional complexity including real-time data integration, enterprise security, scalable infrastructure, and extensive domain expertise integration.

## 🌟 **Key Features & Innovation**

- **🎯 Intelligent Content Processing**: Domain-specific web crawling optimized for satellite documentation
- **🧠 LLM-Powered Knowledge Extraction**: Automated extraction of structured knowledge graphs from unstructured content
- **🔍 Dual-Mode RAG Architecture**: Combines structured knowledge graphs with semantic vector search
- **⚡ GPU-Accelerated Processing**: 3-10x speedup for large-scale document processing
- **🎨 Interactive Interface**: Professional dashboard with live pipeline execution and Q&A
- **🎤 Future Voice Interface**: Planned conversational AI for hands-free satellite data queries

## 🏛️ **System Architecture**

```mermaid
graph TB
    subgraph "🌐 Data Sources"
        A[🛰️ MOSDAC Website<br/>Satellite Documentation]
    end

    subgraph "📥 Processing Pipeline"
        B[🕷️ Smart Crawler<br/>Crawl4AI + Playwright]
        C[🤖 LLM Analysis<br/>Gemini 2.0 Flash]
        D[🕸️ Knowledge Graph<br/>Entity Extraction]
        E[⚡ Vector Embeddings<br/>GPU Accelerated]
    end

    subgraph "🔍 RAG System"
        F[🤝 Hybrid Retrieval<br/>Structured + Semantic]
        G[🎨 User Interface<br/>Streamlit Dashboard]
    end

    A --> B --> C
    C --> D
    C --> E
    D --> F
    E --> F
    F --> G

    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef process fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef interface fill:#fff3e0,stroke:#e65100,stroke-width:2px

    class A source
    class B,C,D,E process
    class F,G interface
```

**Innovation Points**: Selective crawling, automated knowledge graph generation, GPU optimization, hybrid retrieval combining structured and unstructured search.

## 🚀 **Quick Start**

### 🌐 **Live Demo (Recommended)**

**🚀 Instant Access**: [spacey-mosdac.streamlit.app](https://spacey-mosdac.streamlit.app/)

### 💻 **Local Setup**

```bash
# Clone and setup
git clone https://github.com/garg-tejas/rag-mosdac.git
cd rag-mosdac
pip install -r requirements.txt

# Add your Gemini API key to .env file
cp .env.example .env

# Launch demo
streamlit run streamlit_app.py
```

**Pipeline Commands**:

```bash
python run_pipeline.py --step all    # Full pipeline
python run_pipeline.py --step crawl  # Data acquisition only
python check_gpu.py                  # Verify GPU acceleration
```

## 🛰️ **Space Technology Applications**

**Immediate Value**:

- **Mission Planning**: Quick satellite capability discovery for specific objectives
- **Knowledge Preservation**: Convert documentation into searchable, structured formats
- **Training & Education**: Interactive learning tool for satellite data and missions
- **Cross-Mission Analysis**: Understand relationships between different programs

## 🎯 **Technical Excellence**

**Performance**: GPU acceleration, smart batching, memory optimization

**Technology Stack**: Crawl4AI + Playwright (crawling), Gemini 2.0 Flash (LLM), SentenceTransformers (embeddings), Neo4j (knowledge graph), Pinecone (vector search), Streamlit (interface), PyTorch (acceleration)

## 🏆 **Proof-of-Concept Scope**

**What This Demonstrates**:

✅ RAG architecture for satellite data  
✅ Knowledge graph extraction from documentation  
✅ GPU-accelerated processing pipeline  
✅ Interactive query interface  
✅ Professional presentation layer

**Production Considerations**:

🔧 Enterprise security & authentication  
🔧 Real-time satellite data feed integration  
🔧 Scalable cloud infrastructure  
🔧 Domain expert validation systems  
🔧 Regulatory compliance & data governance  
🔧 Multi-user concurrent access  
🔧 Advanced voice interface implementation

---

> **💡 Innovation Summary**: This proof-of-concept demonstrates how modern AI can transform static satellite documentation into intelligent, queryable knowledge systems - showcasing our approach for the future of space data management and mission planning.

## 🆕 **Latest Improvements**

**Knowledge Graph Enhancements**:

- ✅ **Smart Entity Normalization**: Converts "INSAT-3D", "INSAT 3D", "insat_3d" to consistent format, preventing duplicates
- ✅ **Relationship Standardization**: Normalizes relations like "operates", "manages", "runs" into consistent vocabulary
- ✅ **Case-Insensitive Matching**: Handles variations in capitalization and spacing automatically
- ✅ **Interactive QA Visualization**: Knowledge graph appears during Q&A sessions showing relevant entities and relationships
- 🆕 **BFS Graph Expansion**: Search now finds ALL connected nodes using Breadth-First Search algorithm
- 🆕 **Depth-Controlled Exploration**: Adjustable search depth (1-5 hops) for comprehensive or focused results
- 🆕 **Visual Highlighting**: Original search matches highlighted in gold, connected nodes in different colors

**User Experience**:

- 🎨 **Real-time Graph Visualization**: See related entities and connections for every question answered
- 🔍 **Enhanced Entity Discovery**: Improved matching algorithm finds more relevant knowledge graph content
- 📊 **Duplicate Prevention**: Cleaner knowledge graphs with consolidated entity representations
- 🌐 **Connected Component Analysis**: See entire networks of related entities, not just direct matches
- 📈 **Depth Distribution**: Visual feedback showing how entities are connected at different depths
- 🎯 **Smart Search**: Handles multiple name formats ("INSAT-3D", "INSAT 3D", "insat") seamlessly

**BFS Search Examples**:

- **Search "INSAT-3D"** → Find satellite + organization that operates it + instruments it carries + data it measures
- **Search "temperature"** → Find parameter + satellites that measure it + organizations that process it + related data products
- **Depth Control**: Limit to immediate connections (depth 1) or explore the full network (depth 3-5)
