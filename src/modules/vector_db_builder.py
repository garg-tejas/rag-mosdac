# src/modules/vector_db_builder.py
import os
import logging
import torch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import pinecone
from pinecone import Pinecone, ServerlessSpec
import pypdf
import docx
from src import config
from src.modules.gpu_utils import get_device, optimize_gpu_settings, get_recommended_batch_size

def read_text_from_file(file_path):
    ext = file_path.suffix.lower()
    try:
        if ext in [".md", ".txt"]: return file_path.read_text(encoding="utf-8")
        if ext == ".pdf": return "".join(p.extract_text() for p in pypdf.PdfReader(file_path).pages)
        if ext == ".docx": return "\n".join(p.text for p in docx.Document(file_path).paragraphs)
    except Exception as e:
        logging.error(f"Error reading {file_path}: {e}")
    return ""

def build_vector_database():
    """Creates embeddings and stores them in Pinecone with GPU acceleration."""
    logging.info("Starting vector database construction with Pinecone.")
    
    # Get the best available device and apply optimizations
    device = get_device()
    optimize_gpu_settings()
    
    # Check for Pinecone API key
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        logging.error("PINECONE_API_KEY not found in environment variables.")
        return
    
    # Initialize Pinecone
    pc = Pinecone(api_key=pinecone_api_key)
    
    # Check if index exists, if not create it
    if config.PINECONE_INDEX_NAME not in pc.list_indexes().names():
        logging.info(f"Creating Pinecone index: {config.PINECONE_INDEX_NAME}")
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.PINECONE_DIMENSION,
            metric=config.PINECONE_METRIC,
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'  # Change to your preferred region
            )
        )
    else:
        logging.info(f"Using existing Pinecone index: {config.PINECONE_INDEX_NAME}")
    
    # Connect to the index
    index = pc.Index(config.PINECONE_INDEX_NAME)
    
    # Read and process documents
    all_docs = []
    for f in config.MARKDOWN_DIR.rglob("*.md"):
        content = read_text_from_file(f)
        if content: all_docs.append({"source": str(f.relative_to(config.ROOT_DIR)), "content": content})
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = []
    for doc in all_docs:
        doc_chunks = text_splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(doc_chunks):
            chunks.append({
                "source": doc["source"], 
                "id": f"{os.path.basename(doc['source'])}_{i}", 
                "text": chunk_text
            })
    
    # Initialize SentenceTransformer with GPU support
    logging.info(f"Loading embedding model '{config.EMBEDDING_MODEL}' on {device}")
    model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
    
    logging.info(f"Creating embeddings for {len(chunks)} chunks using {device}...")
    
    # Use recommended batch size based on available GPU memory
    batch_size = get_recommended_batch_size()
    logging.info(f"Using batch size: {batch_size}")
    
    # Process chunks in batches and upload to Pinecone
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i+batch_size]
        batch_texts = [c['text'] for c in batch_chunks]
        
        # Generate embeddings
        batch_embeddings = model.encode(
            batch_texts, 
            show_progress_bar=True,
            batch_size=batch_size,
            convert_to_tensor=True,  # Keep tensors on GPU until the end
            normalize_embeddings=True  # L2 normalization for better similarity search
        )
        
        # Convert to CPU numpy arrays for upload
        if isinstance(batch_embeddings, torch.Tensor):
            batch_embeddings = batch_embeddings.cpu().numpy()
        
        # Prepare vectors for Pinecone
        vectors_to_upsert = []
        for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
            vectors_to_upsert.append({
                "id": chunk["id"],
                "values": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                "metadata": {
                    "text": chunk["text"],
                    "source": chunk["source"]
                }
            })
        
        # Upsert to Pinecone with namespace
        index.upsert(vectors=vectors_to_upsert, namespace=config.PINECONE_NAMESPACE)
        logging.info(f"Uploaded batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} to Pinecone namespace '{config.PINECONE_NAMESPACE}'")
        
        # Clear GPU cache periodically to prevent memory issues
        if device.type == "cuda" and i % (batch_size * 10) == 0:
            torch.cuda.empty_cache()
    
    # Final GPU memory cleanup
    if device.type == "cuda":
        torch.cuda.empty_cache()
        logging.info(f"GPU memory usage: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
    
    # Get index stats
    stats = index.describe_index_stats()
    logging.info(f"Pinecone index '{config.PINECONE_INDEX_NAME}' created successfully.")
    logging.info(f"Total vectors: {stats['total_vector_count']}")
    logging.info(f"Embedding generation completed using {device}")

def get_pinecone_index():
    """Get Pinecone index for querying."""
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not found in environment variables.")
    
    pc = Pinecone(api_key=pinecone_api_key)
    return pc.Index(config.PINECONE_INDEX_NAME)