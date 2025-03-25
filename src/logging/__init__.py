"""
Logging initialization module providing both MLflow and API loggers
"""
from .mlflow_logger import MLflowLogger
from .api_logger import APILogger

# Create and configure the default MLflow logger instance for agent metrics
mlflow_logger = MLflowLogger()
mlflow_logger.setup()

# Create and configure the default API logger instance
api_logger = APILogger()
api_logger.setup()

