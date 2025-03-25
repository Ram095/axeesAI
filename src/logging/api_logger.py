"""
API logging module providing console-based logging for the API
"""
import logging
from typing import Optional
from datetime import datetime

class APILogger:
    """Console-based logger for API operations"""
    
    def __init__(self, name: str = "api-logger", level: int = logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.propagate = False  # Prevent propagation to root logger
        
        # Create console handler with formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger if it doesn't already have one
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
    
    def setup(self) -> None:
        """Setup method to maintain compatibility with other loggers"""
        pass
    
    def info(self, message: str) -> None:
        """Log info level message"""
        self.logger.info(message)
    
    def error(self, message: str) -> None:
        """Log error level message"""
        self.logger.error(message)
    
    def warning(self, message: str) -> None:
        """Log warning level message"""
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        """Log debug level message"""
        self.logger.debug(message)
    
    def critical(self, message: str) -> None:
        """Log critical level message"""
        self.logger.critical(message)

# Global instance for easy access
default_api_logger = APILogger() 