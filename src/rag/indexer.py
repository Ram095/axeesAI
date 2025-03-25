import os
import time
from openai import OpenAI
from pinecone import Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from typing import List
import mlflow
from mlflow_config import MLflowConfig
from src.settings import RAGSettings
from src.settings.rag_settings import CHUNK_SIZE, CHUNK_OVERLAP, RATE_LIMIT_DELAY

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Indexer:
    """
    Handles data pipeline operations for vector database:
    - Loading and chunking text files
    - Creating embeddings
    - Initializing vector db index
    - Storing data in vector db
    """
    def __init__(self, open_api_key, pine_cone_key, use_local_embeddings=False):
        self.pc = Pinecone(api_key=pine_cone_key)
        self.client = OpenAI(api_key=open_api_key)
        self.use_local_embeddings = use_local_embeddings
        self.rag_config = RAGSettings()
        self.embedding_dimension = 384 if use_local_embeddings else self.rag_config.embedding_dimension
        self.index_name = self.rag_config.index_name
        self.metric_type = self.rag_config.similarity_metric
        self.embedding_model = self.rag_config.embedding_model
        
        if self.use_local_embeddings:
            self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
            
        self.index = self.initialize_index()
        MLflowConfig.setup_tracking()

    def load_data_from_txt(self, file_name, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):        
        file_path = os.path.join(project_root, 'data', file_name)        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} does not exist. Please ensure the data directory exists and contains the file.")        
        try:            
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()            
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                is_separator_regex=False
            )            
            chunks = text_splitter.split_text(text)            
            return chunks
        
        except Exception as e:
            print(f"Error loading text file: {e}")
            raise

    def initialize_index(self):
        if self.index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric=self.metric_type,
                spec=self.rag_config.serverless_spec
            )
        return self.pc.Index(self.index_name)

    def get_embedding(self, text):
        if self.use_local_embeddings:            
            embedding = self.local_model.encode(text)
            return embedding.tolist()
        else:            
            response = self.client.embeddings.create(input=[text], model=self.embedding_model)
            return response.data[0].embedding

    def store_embeddings_in_db(self, chunks):
        try:
            with MLflowConfig.start_tracking(run_name="indexing"):
                start_time = time.time()
                total_chunks = len(chunks)
                
                for idx, chunk in enumerate(chunks, 1):            
                    embedding = self.get_embedding(chunk)        
                    self.index.upsert([(str(idx), embedding, {"text": chunk})])
                    time.sleep(RATE_LIMIT_DELAY)
                
                total_time = time.time() - start_time
                
                MLflowConfig.log_metrics({
                    "total_chunks": total_chunks,
                    "indexing_time": total_time,
                    "avg_time_per_chunk": total_time / total_chunks
                })
                
                MLflowConfig.log_params({
                    "embedding_model": self.embedding_model,
                    "use_local_embeddings": self.use_local_embeddings,
                    "chunk_size": CHUNK_SIZE,
                    "chunk_overlap": CHUNK_OVERLAP
                })
                
            print(f"Successfully stored {total_chunks} chunks in Pinecone index '{self.index_name}'")
        except Exception as e:
            print(f"Error storing embeddings: {e}")
            raise
