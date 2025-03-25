import os
from typing import Tuple
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv
import pathlib

# Get the project root directory
PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / '.env'

# Load environment variables
load_dotenv(ENV_PATH)

class CommonSettings(BaseSettings):
    """Base configuration class with common settings and utilities"""
    
    # API Keys
    openai_api_key: str = Field(alias="OPENAI_API_KEY", description="OpenAI API key")
    pinecone_api_key: str = Field(alias="PINECONE_API_KEY", description="Pinecone API key")
    ragas_app_token: str = Field(alias="RAGAS_APP_TOKEN", description="Ragas API key")

    class Config:
        env_file = str(ENV_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = True
        populate_by_name = True
        extra = "ignore"  # This will ignore extra fields

    @staticmethod
    def get_env_or_raise(key: str) -> str:
        """Get environment variable or raise error if not found"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"{key} environment variable not set")
        return value

    def get_api_keys(self) -> Tuple[str, str, str]:
        """Get all API keys"""
        return self.openai_api_key, self.pinecone_api_key, self.ragas_app_token 