# src/modules/vector_db_builder.py
import os
import logging
import torch
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
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
    """Creates embeddings and stores them in ChromaDB with GPU acceleration."""
    logging.info("Starting vector database construction.")
    
    # Get the best available device and apply optimizations
    device = get_device()
    optimize_gpu_settings()
    
    all_docs = []
    for f in config.MARKDOWN_DIR.rglob("*.md"):
        content = read_text_from_file(f)
        if content: all_docs.append({"source": str(f.relative_to(config.ROOT_DIR)), "content": content})
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = []
    for doc in all_docs:
        doc_chunks = text_splitter.split_text(doc["content"])
        for i, chunk_text in enumerate(doc_chunks):
            chunks.append({"source": doc["source"], "id": f"{os.path.basename(doc['source'])}_{i}", "text": chunk_text})
    
    # Initialize SentenceTransformer with GPU support
    logging.info(f"Loading embedding model '{config.EMBEDDING_MODEL}' on {device}")
    model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
    
    logging.info(f"Creating embeddings for {len(chunks)} chunks using {device}...")
    
    # Use recommended batch size based on available GPU memory
    batch_size = get_recommended_batch_size()
    logging.info(f"Using batch size: {batch_size}")
    
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch_texts = [c['text'] for c in chunks[i:i+batch_size]]
        batch_embeddings = model.encode(
            batch_texts, 
            show_progress_bar=True,
            batch_size=batch_size,
            convert_to_tensor=True,  # Keep tensors on GPU until the end
            normalize_embeddings=True  # L2 normalization for better similarity search
        )
        
        # Convert to CPU numpy arrays for storage
        if isinstance(batch_embeddings, torch.Tensor):
            batch_embeddings = batch_embeddings.cpu().numpy()
        
        all_embeddings.extend(batch_embeddings)
        
        # Clear GPU cache periodically to prevent memory issues
        if device.type == "cuda" and i % (batch_size * 10) == 0:
            torch.cuda.empty_cache()
    
    # Final GPU memory cleanup
    if device.type == "cuda":
        torch.cuda.empty_cache()
        logging.info(f"GPU memory usage: {torch.cuda.memory_allocated() / 1024**2:.1f} MB")
    
    client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
    if config.VECTOR_DB_COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(name=config.VECTOR_DB_COLLECTION)
    collection = client.create_collection(name=config.VECTOR_DB_COLLECTION)
    
    # Convert embeddings to list format for ChromaDB
    embeddings_list = [emb.tolist() if hasattr(emb, 'tolist') else emb for emb in all_embeddings]
    
    collection.add(
        embeddings=embeddings_list,
        documents=[c['text'] for c in chunks],
        metadatas=[{"source": c['source']} for c in chunks],
        ids=[c['id'] for c in chunks]
    )
    logging.info(f"Vector DB created. Documents indexed: {collection.count()}")
    logging.info(f"Embedding generation completed using {device}")