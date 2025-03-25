from pydantic import Field, validator
from typing import List
from .common_settings import CommonSettings

class APISettings(CommonSettings):
    """API-specific settings for FastAPI application"""
    
    # API Settings
    host: str = Field("0.0.0.0", description="API host address", alias="HOST")
    port: int = Field(8000, description="API port number", alias="PORT")
    timeout_keep_alive: int = Field(60, description="Timeout for keep-alive connections", alias="TIMEOUT_KEEP_ALIVE")
    
    # Security Settings
    allowed_origins: List[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
        alias="ALLOWED_ORIGINS"
    )
    
    # Scanner Settings
    scanner_model: str = Field(
        default="gpt-4",
        description="Model to use for accessibility scanning",
        alias="SCANNER_MODEL"
    )
    scanner_temperature: float = Field(
        default=0.0,
        description="Temperature for scanner model responses",
        alias="SCANNER_TEMPERATURE"
    )
    scanner_agent_type: str = Field(
        default="zero-shot-react-description",
        description="Type of LangChain agent to use for scanning",
        alias="SCANNER_AGENT_TYPE"
    )

    class Config:
        extra = "ignore"  # This will ignore extra fields

    @validator("port")
    def validate_port(cls, v: int) -> int:
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @validator("allowed_origins")
    def validate_origins(cls, v: List[str]) -> List[str]:
        if not isinstance(v, list):
            try:
                # Try to parse string representation of list from .env
                import ast
                v = ast.literal_eval(v)
            except:
                raise ValueError("ALLOWED_ORIGINS must be a valid list")
        return v 