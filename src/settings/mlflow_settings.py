from pydantic import Field, validator
from .common_settings import CommonSettings

class MLflowSettings(CommonSettings):
    """MLflow-specific settings for logging and tracking"""
    
    # MLflow Settings
    tracking_uri: str = Field(
        default="sqlite:///mlflow.db",
        description="MLflow tracking URI",
        alias="MLFLOW_TRACKING_URI"
    )
    
    experiment_name: str = Field(
        default="axess-ai-metrics",
        description="Default MLflow experiment name",
        alias="MLFLOW_EXPERIMENT_NAME"
    )
    
    # Token Cost Settings
    input_token_cost: float = Field(
        default=0.15 / 1000000,  # $0.15 per 1 million input tokens
        description="Cost per input token"
    )
    
    output_token_cost: float = Field(
        default=0.60 / 1000000,  # $0.60 per 1 million output tokens
        description="Cost per output token"
    )

    class Config:
        extra = "ignore"  # This will ignore extra fields

    @validator("tracking_uri")
    def validate_tracking_uri(cls, v: str) -> str:
        valid_prefixes = ("sqlite:///", "postgresql://", "mysql://")
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"Invalid tracking URI format. Must start with one of: {valid_prefixes}")
        return v
    
    @validator("input_token_cost", "output_token_cost")
    def validate_costs(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Token cost cannot be negative")
        if v > 1:  # Assuming cost should be less than $1 per token
            raise ValueError("Token cost seems unusually high")
        return v 