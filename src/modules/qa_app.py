# src/modules/qa_app.py
import os
import logging
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from litellm import completion
from src import config
from src.modules.gpu_utils import get_device
from src.modules.vector_db_builder import get_pinecone_index

class RAGPipeline:
    def __init__(self):
        logging.info("Initializing RAG Pipeline with Pinecone...")
        
        # Use GPU if available for embedding model
        device = get_device()
        self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL, device=device)
        
        # Connect to Pinecone vector database
        try:
            self.index = get_pinecone_index()
            # Get index stats to verify connection
            stats = self.index.describe_index_stats()
            logging.info(f"RAG Pipeline initialized successfully on {device}.")
            logging.info(f"Pinecone index contains {stats['total_vector_count']} vectors.")
        except Exception as e:
            logging.error(f"Failed to connect to Pinecone: {e}")
            raise
    
    def answer_question(self, query: str, n_results: int = 5):
        """Answer a question using the RAG pipeline."""
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query, normalize_embeddings=True).tolist()
            
            # Retrieve relevant documents from Pinecone
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True,
                namespace=config.PINECONE_NAMESPACE
            )
            
            # Debug logging
            logging.info(f"Pinecone query returned {len(results.get('matches', []))} matches")
            for i, match in enumerate(results.get('matches', [])):
                logging.info(f"Match {i+1}: score={match.get('score', 0):.4f}, metadata keys={list(match.get('metadata', {}).keys())}")
            
            if not results['matches']:
                logging.warning("No matches returned from Pinecone")
                return "I couldn't find any relevant information to answer your question."
            
            # Prepare context from retrieved documents
            context_parts = []
            sources = []
            confidence_scores = []
            
            for match in results['matches']:
                metadata = match.get('metadata', {})
                text = metadata.get('text', '')
                source = metadata.get('source', f'Document')
                score = match.get('score', 0.0)
                
                logging.info(f"Processing match: score={score:.4f}, text_length={len(text)}, source={source}")
                
                if text:
                    context_parts.append(f"[Source: {source}]\n{text}")
                    sources.append(source)
                    confidence_scores.append(score)
                else:
                    logging.warning(f"Empty text in match with source: {source}")
            
            if not context_parts:
                logging.warning("No context parts found despite having matches")
                return "I couldn't find any relevant content to answer your question."
            
            logging.info(f"Found {len(context_parts)} context parts for LLM")
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
                "sources": sources,
                "confidence_scores": confidence_scores,
                "context_used": len(context_parts)
            }
            
        except Exception as e:
            logging.error(f"Error in RAG pipeline: {e}")
            return f"I encountered an error while processing your question: {str(e)}"
    
    def get_similar_documents(self, query: str, n_results: int = 3):
        """Get similar documents for a query without generating an answer."""
        try:
            query_embedding = self.embedding_model.encode(query, normalize_embeddings=True).tolist()
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True,
                namespace=config.PINECONE_NAMESPACE
            )
            
            # Format results to match the old ChromaDB format for compatibility
            formatted_results = {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
            
            for match in results['matches']:
                metadata = match.get('metadata', {})
                text = metadata.get('text', '')
                source = metadata.get('source', 'Unknown')
                # Convert similarity score to distance (lower is more similar)
                distance = 1.0 - match.get('score', 0.0)
                
                formatted_results['documents'][0].append(text)
                formatted_results['metadatas'][0].append({'source': source})
                formatted_results['distances'][0].append(distance)
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error retrieving similar documents: {e}")
            return None

def start_qa_session():
    """Starts an interactive Q&A session (command line interface)."""
    # Check if Pinecone API key is available
    if not os.getenv("PINECONE_API_KEY"):
        logging.error("PINECONE_API_KEY not found. Please set up your Pinecone credentials.")
        return
    
    print("🚀 RAG-Crawl4AI Interactive Q&A Session (Pinecone)")
    print("=" * 50)
    print("Ask questions about MOSDAC data and services!")
    print("Type 'quit' to exit.")
    print()
    
    try:
        rag_system = RAGPipeline()
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {e}")
        return
    
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
                if result['confidence_scores']:
                    avg_confidence = sum(result['confidence_scores']) / len(result['confidence_scores'])
                    print(f"🎯 Average confidence: {avg_confidence:.3f}")
            else:
                print(f"\n✅ Answer: {result}")
            
            print("\n" + "="*50 + "\n")
            
        except KeyboardInterrupt:
            print("\n👋 Thanks for using RAG-Crawl4AI!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again with a different question.\n")