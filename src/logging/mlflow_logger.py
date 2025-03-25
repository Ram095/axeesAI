import mlflow
import os
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from src.core import BaseLogger, TokenUsageTracker
from src.settings import MLflowSettings
# Constants for token costs
COST_PER_INPUT_TOKEN = 0.15 / 1000000  # $0.15 per 1 million input tokens
COST_PER_COMPLETION_TOKEN = 0.60 / 1000000  # $0.60 per 1 million output tokens

class MLflowLogger(BaseLogger):
    """MLflow implementation of the logging interface"""
    
    def __init__(
        self,
        experiment_name: Optional[str] = None,
        tracking_uri: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        self.settings = MLflowSettings()
        self.experiment_name = experiment_name or self.settings.experiment_name
        self.tracking_uri = tracking_uri or self.settings.tracking_uri
        self.tags = tags or {
            "project": "axessai",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        self.token_tracker = TokenUsageTracker(
            input_token_cost=self.settings.input_token_cost,
            output_token_cost=self.settings.output_token_cost
        )
        self._active_runs = []  # Stack to track nested runs
        self.setup()
        
    def setup(self) -> None:
        """Setup MLflow tracking configuration"""
        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment(self.experiment_name)
        # End any active runs to ensure clean state
        if mlflow.active_run():
            mlflow.end_run()
        self._active_runs = []
    
    @contextmanager
    def start_session(self, session_name: Optional[str] = None, nested: bool = False):
        """Start an MLflow tracking session"""
        if not session_name:
            session_name = f"axessai-run-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # If there's an active run and we're not nesting, end it
        if mlflow.active_run() and not nested:
            mlflow.end_run()
            self._active_runs = []
            
        try:
            run = mlflow.start_run(run_name=session_name, nested=nested, tags=self.tags)
            self._active_runs.append(run)
            yield run
        finally:
            # Only end the run if it's still active
            if mlflow.active_run():
                current_run = self._active_runs.pop() if self._active_runs else None
                if current_run and current_run.info.run_id == mlflow.active_run().info.run_id:
                    mlflow.end_run()
    
    def end_session(self) -> None:
        """End the current MLflow run if active"""
        if mlflow.active_run():
            if self._active_runs:
                self._active_runs.pop()
            mlflow.end_run()
    
    def log_parameters(self, params: Dict[str, Any]) -> None:
        """Log parameters to MLflow"""
        if mlflow.active_run():
            mlflow.log_params(params)
    
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        """Log metrics to MLflow"""
        if mlflow.active_run():
            mlflow.log_metrics(metrics, step=step)
    
    def log_artifact(self, local_path: str) -> None:
        """Log an artifact file to MLflow"""
        if mlflow.active_run():
            mlflow.log_artifact(local_path)
    
    def log_lm_usage(self, lm_history: list) -> None:
        """Log language model usage metrics"""
        if not lm_history or not mlflow.active_run():
            return
            
        latest_interaction = lm_history[-1]
        usage_stats = latest_interaction.get('usage', {})
        model_name = latest_interaction.get('model', 'unknown_model')
        
        # Calculate token usage and costs
        usage_metrics = self.token_tracker.calculate_usage(
            prompt_tokens=usage_stats.get('prompt_tokens', 0),
            completion_tokens=usage_stats.get('completion_tokens', 0)
        )
        
        # Log metrics and model name
        self.log_metrics(usage_metrics)
        self.log_parameters({"model_name": model_name})
    
    @property
    def active_run_name(self) -> Optional[str]:
        """Get the name of the active run"""
        current_run = mlflow.active_run()
        if current_run:
            return current_run.data.tags.get("mlflow.runName")
        return None

# Global instance for backward compatibility
default_logger = MLflowLogger()
