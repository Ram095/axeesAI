from pydantic import Field, BaseModel
from typing import List, Optional, Any, Dict

class BaseQuery(BaseModel):
    """Base query model for API requests"""
    pass

class BaseResponse(BaseModel):
    """Base response model for API responses"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None

class AccessibilityQuery(BaseQuery):
    """Query model for accessibility questions"""
    pass

class AccessibilityResponse(BaseResponse):
    """Response model for accessibility answers"""
    answer: str = Field(..., description="Direct answer to the accessibility question")
    explanation: str = Field(..., description="Detailed explanation of the accessibility considerations")
    guidelines: str = Field(..., description="Relevant accessibility guidelines and standards")
    examples: str = Field(..., description="Practical examples and implementations")
