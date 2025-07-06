# src/modules/qa_app.py
import os
import logging
from sentence_transformers import SentenceTransformer
import chromadb
from litellm import completion
from src import config
from src.modules.gpu_utils import get_device

class RAGPipeline:
    def __init__(self):
        logging.info("Initializing RAG Pipeline...")
        
        # Use GPU if available for embedding model
        device = get_device()
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
        
        # Connect to vector database
        client = chromadb.PersistentClient(path=config.VECTOR_DB_PATH)
        self.collection = client.get_collection(name=config.VECTOR_DB_COLLECTION)
        
        logging.info(f"RAG Pipeline initialized successfully on {device}.")
        logging.info(f"Vector database contains {self.collection.count()} documents.")
    
    def answer_question(self, query: str, n_results: int = 5):
        """Answer a question using the RAG pipeline."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Retrieve relevant documents
            results = self.collection.query(
                query_embeddings=[query_embedding], 
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            if not results['documents'][0]:
                return "I couldn't find any relevant information to answer your question."
            
            # Prepare context from retrieved documents
            context_parts = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results.get('metadatas', [{}] * len(results['documents'][0]))[0],
                results.get('distances', [0] * len(results['documents'][0]))[0]
            )):
                source = metadata.get('source', f'Document {i+1}')
                context_parts.append(f"[Source: {source}]\n{doc}")
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Generate response using LLM
            prompt = f"""You are a helpful assistant specializing in MOSDAC (Meteorological & Oceanographic Satellite Data Archival Centre) information. 

Based on the context provided from the MOSDAC website, answer the user's question accurately and comprehensively. If the answer isn't fully covered in the context, acknowledge this and provide what information is available.

CONTEXT:
{context}

QUESTION: {query}

ANSWER:"""

            response = completion(
                model=config.LLM_PROVIDER,
                messages=[{"role": "user", "content": prompt}],
                api_key=os.getenv("GEMINI_API_KEY"),
                temperature=0.1,
                max_tokens=1024
            )
            
            answer = response.choices[0].message.content
            
            # Return structured response with metadata
            return {
                "answer": answer,
                "sources": [meta.get('source', 'Unknown') for meta in results.get('metadatas', [{}] * len(results['documents'][0]))[0]],
                "confidence_scores": results.get('distances', [0] * len(results['documents'][0]))[0],
                "context_used": len(results['documents'][0])
            }
            
        except Exception as e:
            logging.error(f"Error in RAG pipeline: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def get_similar_documents(self, query: str, n_results: int = 3):
        """Get similar documents for a query without generating an answer."""
        try:
            query_embedding = self.embedding_model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            return results
        except Exception as e:
            logging.error(f"Error retrieving similar documents: {e}")
            return None

def start_qa_session():
    """Starts an interactive Q&A session (command line interface)."""
    if not os.path.exists(config.VECTOR_DB_PATH):
        logging.error("Vector database not found. Please run the 'vectordb' step first.")
        return
    
    print("🚀 RAG-Crawl4AI Interactive Q&A Session")
    print("=" * 50)
    print("Ask questions about MOSDAC data and services!")
    print("Type 'quit' to exit.")
    print()
    
    rag_system = RAGPipeline()
    
    # Example questions
    example_questions = [
        "What are the main objectives of the INSAT-3DR mission?",
        "What kind of data does the 'Soil Moisture' product provide?",
        "What is MOSDAC's data access policy?",
        "Tell me about the Oceansat-2 satellite.",
        "What instruments are available on INSAT-3D?"
    ]
    
    print("💡 Example questions to try:")
    for i, q in enumerate(example_questions, 1):
        print(f"  {i}. {q}")
    print()
    
    while True:
        try:
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Thanks for using RAG-Crawl4AI!")
                break
            
            if not question:
                continue
            
            print("\n🔍 Searching knowledge base...")
            result = rag_system.answer_question(question)
            
            if isinstance(result, dict):
                print(f"\n✅ Answer: {result['answer']}")
                print(f"\n📊 Sources used: {', '.join(result['sources'][:3])}")
                print(f"📈 Retrieved {result['context_used']} relevant documents")
            else:
                print(f"\n✅ Answer: {result}")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Thanks for using RAG-Crawl4AI!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different question.\n")