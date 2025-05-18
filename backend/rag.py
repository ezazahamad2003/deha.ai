import os
from dotenv import load_dotenv
import groq
from pinecone import Pinecone, ServerlessSpec
import json
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize clients
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Constants
INDEX_NAME = "medical-records"
NAMESPACE = "patient-records"
EMBEDDING_MODEL = "llama2-70b-4096"
CHUNK_SIZE = 512

def create_index():
    """Create Pinecone index if it doesn't exist"""
    try:
        # Check if index exists
        if INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=INDEX_NAME,
                dimension=4096,  # Dimension for llama2 embeddings
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-west-2"
                )
            )
            logger.info(f"Created new index: {INDEX_NAME}")
        return pc.Index(INDEX_NAME)
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """Split text into chunks of specified size"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        current_chunk.append(word)
        current_size += len(word) + 1  # +1 for space
        
        if current_size >= chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_size = 0
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def get_embeddings(text: str) -> List[float]:
    """Get embeddings from Groq"""
    try:
        response = groq_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embeddings: {str(e)}")
        raise

def process_document(file_path: str, patient_id: str) -> None:
    """Process a document and store in Pinecone"""
    try:
        # Read document (dummy implementation)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Chunk the text
        chunks = chunk_text(text)
        logger.info(f"Split document into {len(chunks)} chunks")
        
        # Get index
        index = create_index()
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            # Get embeddings
            embedding = get_embeddings(chunk)
            
            # Create metadata
            metadata = {
                "patient_id": patient_id,
                "chunk_id": i,
                "text": chunk,
                "source": file_path
            }
            
            # Upsert to Pinecone
            index.upsert(
                vectors=[{
                    "id": f"{patient_id}_{i}",
                    "values": embedding,
                    "metadata": metadata
                }],
                namespace=NAMESPACE
            )
        
        logger.info(f"Successfully processed document for patient {patient_id}")
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise

def query_records(patient_id: str, query: str, top_k: int = 3) -> List[Dict]:
    """Query patient records using RAG"""
    try:
        # Get query embedding
        query_embedding = get_embeddings(query)
        
        # Get index
        index = create_index()
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=NAMESPACE,
            filter={"patient_id": patient_id}
        )
        
        # Format results
        formatted_results = []
        for match in results.matches:
            formatted_results.append({
                "text": match.metadata["text"],
                "score": match.score,
                "source": match.metadata["source"]
            })
        
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error querying records: {str(e)}")
        raise

def generate_response(query: str, context: List[Dict]) -> str:
    """Generate response using Groq"""
    try:
        # Format context
        context_text = "\n\n".join([f"Source {i+1}: {item['text']}" for i, item in enumerate(context)])
        
        # Create prompt
        prompt = f"""You are Deha AI, a medical assistant. Use the following context to answer the patient's question.
        If the context doesn't contain relevant information, say so.

        Context:
        {context_text}

        Question: {query}

        Answer:"""
        
        # Get response from Groq
        response = groq_client.chat.completions.create(
            model="llama2-70b-4096",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        raise

# Example usage
if __name__ == "__main__":
    # Dummy data
    patient_id = "patient_123"
    file_path = "dummy_medical_record.txt"
    
    # Process document
    process_document(file_path, patient_id)
    
    # Query example
    query = "What medications am I currently taking?"
    results = query_records(patient_id, query)
    
    # Generate response
    response = generate_response(query, results)
    print(f"Response: {response}") 