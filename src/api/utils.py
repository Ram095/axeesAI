import time
from contextlib import contextmanager
from src.logging import api_logger

@contextmanager
def log_timing(operation: str):
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        api_logger.info(f"{operation} took {duration:.2f} seconds")
