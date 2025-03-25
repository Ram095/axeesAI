from typing import Dict, Any, Optional
from pydantic import BaseModel

class BaseQuery(BaseModel):
    """Base class for all query types"""
    query: str
    context: Optional[Dict[str, Any]] = None

class BaseResponse(BaseModel):
    """Base class for all response types"""
    answer: str
    metadata: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None 