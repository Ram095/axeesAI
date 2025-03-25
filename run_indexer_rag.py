import argparse
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.rag.retriever import Retriever
from src.settings import RAGSettings
from src.rag.indexer import Indexer

def index_data(file_name, use_local_embeddings=False):
    """Index data from a text file into vector db"""
    rag_config = RAGSettings()
    open_api_key, pine_cone_key, _ = rag_config.get_api_keys()
    indexer = Indexer(open_api_key, pine_cone_key, use_local_embeddings=use_local_embeddings)
    
    print(f"Loading and chunking file: {file_name}")
    chunks = indexer.load_data_from_txt(file_name)
    
    print(f"Creating embeddings and storing {len(chunks)} chunks in vector db...")
    indexer.store_embeddings_in_db(chunks)
    
    print("Indexing completed successfully!")

def query_data(query_text, top_k=3, use_local_embeddings=False):
    """Query the vector db index with the given text"""
    rag_config = RAGSettings()
    open_api_key, pine_cone_key, _ = rag_config.get_api_keys()
    retriever = Retriever(open_api_key, pine_cone_key, use_local_embeddings=use_local_embeddings)
    
    print(f"Querying vector db index with: '{query_text}'")
    results = retriever.retrieve_context(query_text, top_k=top_k)
    
    print("\nQuery Results:")
    print("==============")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} (Score: {result['score']:.4f}):")
        print(f"{result['text']}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Vector db RAG Demo')
    parser.add_argument('--mode', choices=['index', 'query', 'both'], default='query',
                      help='Mode: index, query, or both')
    parser.add_argument('--file', type=str, default='techniques.txt',
                      help='File to index (must be in the data directory)')
    parser.add_argument('--query', type=str, 
                      default='Ensure <img> elements have alternative text or a role of none or presentation',
                      help='Query text')
    parser.add_argument('--top_k', type=int, default=3,
                      help='Number of results to return')
    parser.add_argument('--local', action='store_true',
                      help='Use local embeddings instead of OpenAI')
    
    args = parser.parse_args()
    
    try:
        if args.mode in ['index', 'both']:
            index_data(args.file, args.local)
            
        if args.mode in ['query', 'both']:
            query_text = "How to fix accessibility issue:" + args.query + ". Retrieve understanding and examples."
            query_data(query_text, args.top_k, args.local)
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
