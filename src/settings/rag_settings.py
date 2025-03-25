from pydantic import Field, field_validator
from src.logging import api_logger
from .common_settings import CommonSettings

# Constants
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
DEFAULT_TOP_K = 3
RATE_LIMIT_DELAY = 0.5

class RAGSettings(CommonSettings):
    """Configuration for Retrieval Augmented Generation (RAG)"""
    
    # Embedding settings
    embedding_dimension: int = Field(1536, description="Dimension of the embedding vectors")
    embedding_model: str = Field(
        "text-embedding-ada-002",
        description="OpenAI embedding model to use"
    )
    
    # Vector store settings
    index_name: str = Field(
        "wcag-guidelines",
        description="Name of the vector store index"
    )
    similarity_metric: str = Field("cosine", description="Vector similarity metric type")
    
    # Text processing settings
    chunk_size: int = Field(default=CHUNK_SIZE, description="Size of text chunks for embedding")
    chunk_overlap: int = Field(default=CHUNK_OVERLAP, description="Overlap between consecutive chunks")
    
    # Retrieval settings
    max_results: int = Field(default=DEFAULT_TOP_K, description="Maximum number of results to retrieve")
    rate_limit_delay: float = Field(default=RATE_LIMIT_DELAY, description="Delay between API calls in seconds")
    
    # Local embeddings flag
    use_local_embeddings: bool = Field(default=False, description="Whether to use local embeddings")

    # Scanner settings
    scanner_model: str = Field(
        default="gpt-4",
        description="Model to use for scanning"
    )
    scanner_temperature: float = Field(
        default=0.0,
        description="Temperature setting for scanner model"
    )
    scanner_agent_type: str = Field(
        default="zero-shot-react-description",
        description="Type of agent to use for scanning"
    )

    class Config:
        extra = "ignore"  # This will ignore extra fields

    def __init__(self, **kwargs):
        api_logger.info("Initializing RAGSettings")
        super().__init__(**kwargs)

    @field_validator('openai_api_key', 'pinecone_api_key', 'ragas_app_token')
    @classmethod
    def validate_api_keys(cls, v: str, info) -> str:
        api_logger.info(f"Validating {info.field_name}: {'present' if v else 'missing'}")
        if not v:
            raise ValueError(f"{info.field_name} is required")
        return v 