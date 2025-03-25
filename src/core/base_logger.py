from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from contextlib import contextmanager
from datetime import datetime

class BaseLogger(ABC):
    """Abstract base class for logging implementations"""
    
    @abstractmethod
    def setup(self) -> None:
        """Setup logging configuration"""
        pass
    
    @abstractmethod
    @contextmanager
    def start_session(self, session_name: Optional[str] = None, **kwargs):
        """Start a logging session"""
        pass
    
    @abstractmethod
    def log_parameters(self, params: Dict[str, Any]) -> None:
        """Log parameters"""
        pass
    
    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log metrics"""
        pass
    
    @abstractmethod
    def log_artifact(self, local_path: str) -> None:
        """Log an artifact file"""
        pass
    
    @abstractmethod
    def end_session(self) -> None:
        """End the current logging session"""
        pass

class TokenUsageTracker:
    """Track and calculate token usage and costs"""
    
    def __init__(self, input_token_cost, 
                 output_token_cost):
        self.input_token_cost = input_token_cost
        self.output_token_cost = output_token_cost
    
    def calculate_usage(self, 
                       prompt_tokens: int, 
                       completion_tokens: int) -> Dict[str, float]:
        """Calculate token usage and costs"""
        total_tokens = prompt_tokens + completion_tokens
        input_cost = round(prompt_tokens * self.input_token_cost, 6)
        completion_cost = round(completion_tokens * self.output_token_cost, 6)
        total_cost = round(input_cost + completion_cost, 6)
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "input_token_cost": input_cost,
            "completion_token_cost": completion_cost,
            "total_cost": total_cost
        }