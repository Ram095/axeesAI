import os
import time 
from openai import OpenAI
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from src.settings import RAGSettings
from src.logging import api_logger
from src.logging.mlflow_logger import MLflowLogger
from src.utils.similarity_calculator import calculate_average_score

class Retriever:
    """
    Handles retrieval operations from vector database:
    - Creating embeddings
    - Querying vector db index
    - Retrieving relevant context
    """
    def __init__(self, config: RAGSettings):
        """Initialize retriever with configuration"""
        api_logger.info("Initializing Retriever")
        try:
            self.config = config
            
            # Validate API keys
            if not config.pinecone_api_key:
                raise ValueError("Pinecone API key is required")
            if not config.openai_api_key:
                raise ValueError("OpenAI API key is required")
                
            # Initialize clients
            self.pc = Pinecone(api_key=config.pinecone_api_key)
            self.client = OpenAI(api_key=config.openai_api_key)
            
            # Verify Pinecone index exists
            if config.index_name not in self.pc.list_indexes().names():
                raise ValueError(f"Pinecone index '{config.index_name}' does not exist")
            
            # Initialize embedding model if using local embeddings
            if config.use_local_embeddings:
                self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
                api_logger.info("Initialized local embedding model")
            
            self.use_local_embeddings = config.use_local_embeddings
            self.embedding_dimension = 384 if self.use_local_embeddings else config.embedding_dimension
            self.index_name = config.index_name
            self.metric_type = config.similarity_metric
            self.embedding_model = config.embedding_model            
            
            self.logger = MLflowLogger()
            
            api_logger.info("Retriever initialized successfully")
        except Exception as e:
            api_logger.error(f"Failed to initialize Retriever: {str(e)}")
            raise ValueError(f"Failed to initialize Retriever: {str(e)}")
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embeddings for text using OpenAI or local model"""
        try:
            if self.use_local_embeddings:
                return self.local_model.encode(text).tolist()
            else:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                return response.data[0].embedding
        except Exception as e:
            api_logger.error(f"Error getting embeddings: {str(e)}")
            raise
    
    def retrieve_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context based on query"""
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
            
        if top_k is None:
            top_k = self.config.max_results
            
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            
            # Query vector store
            index = self.pc.Index(self.index_name)
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            contexts = []
            for match in results.matches:
                contexts.append({
                    'text': match.metadata.get('text', ''),
                    'score': match.score
                })
            
            return contexts
        except Exception as e:
            api_logger.error(f"Error retrieving context: {str(e)}")
            raise
