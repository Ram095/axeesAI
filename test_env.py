import os
from dotenv import load_dotenv
from src.logging import api_logger

def main():
    # Try to load environment variables
    load_dotenv(verbose=True)
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    pinecone_key = os.getenv('PINECONE_API_KEY')
    
    print("Environment variables check:")
    print(f"OPENAI_API_KEY: {'present' if openai_key else 'missing'}")
    print(f"PINECONE_API_KEY: {'present' if pinecone_key else 'missing'}")
    
    # Print the first few characters of each key if present
    if openai_key:
        print(f"OpenAI key starts with: {openai_key[:10]}...")
    if pinecone_key:
        print(f"Pinecone key starts with: {pinecone_key[:10]}...")

if __name__ == "__main__":
    main() 