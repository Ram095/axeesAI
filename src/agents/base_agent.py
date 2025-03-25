from typing import Dict, Any, Optional
import time
import dspy
from src.core.models import BaseQuery, BaseResponse
from src.core import BaseLogger
from src.logging import mlflow_logger, api_logger
import mlflow

class BaseAgent:
    """Base class for all agents with common functionality"""
    def __init__(self, api_key: Optional[str] = None, logger: Optional[BaseLogger] = None):
        if not api_key:
            api_logger.error("No API key provided to agent")
            raise ValueError("API key is required")
            
        self.api_key = api_key
        self.logger = logger or mlflow_logger
        
        # Ensure any existing runs are ended
        if mlflow.active_run():
            mlflow.end_run()
            
        self.lm = self._setup_language_model()
        
    def _setup_language_model(self) -> Any:
        """Configure the language model for DSPy"""
        try:
            if not self.api_key:
                raise ValueError("API key is required for language model setup")
                
            api_logger.info("Configuring language model with provided API key")
            language_model = dspy.LM('openai/gpt-4-turbo', api_key=self.api_key)
            dspy.configure(lm=language_model)
            self.logger.log_parameters({"language_model": "openai/gpt-4-turbo"})
            api_logger.info("Language model configured successfully")
            return language_model
            
        except Exception as e:
            api_logger.error(f"Failed to setup language model: {str(e)}")
            raise ValueError(f"Failed to initialize language model: {str(e)}")
    
    def _track_execution(self, run_name: str, func, *args, **kwargs) -> Dict[str, Any]:
        """Execute a function with logging"""
        # Ensure any existing runs are ended
        if mlflow.active_run():
            mlflow.end_run()
            
        try:
            with self.logger.start_session(session_name=run_name) as session:
                start_time = time.time()
                
                # Execute the function
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    api_logger.error(f"Error during function execution: {str(e)}")
                    raise
                
                # Log execution time                
                self.logger.log_metrics({"execution_time": round(time.time() - start_time, 3)})
                
                # Log language model usage if available
                if hasattr(self, 'lm') and hasattr(self.lm, 'history'):
                    self.logger.log_lm_usage(self.lm.history)
                
                return result
        except Exception as e:
            api_logger.error(f"Error in tracking execution: {str(e)}")
            raise
    
    def process_query(self, query: BaseQuery) -> BaseResponse:
        """Process a query and return a response"""
        raise NotImplementedError("Subclasses must implement process_query") 