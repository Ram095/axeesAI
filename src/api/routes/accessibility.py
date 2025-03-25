from fastapi import APIRouter, Header, Request
from typing import Dict, Any, Union
from src.api.models import AccessibilityQuery, AccessibilityResponse
from src.api.errors import AuthenticationError, ValidationError, AccessibilityError
from src.api.utils import log_timing
from src.agents.accessibility_expert_agent import AccessibilityExpertAgent
from src.agents.scanner_agent import ScannerAgent
from src.logging import api_logger
import time
from pydantic import BaseModel, HttpUrl

# Add new model for scan request
class ScanRequest(BaseModel):
    url: HttpUrl

# Add new model for scan response
class ScanResponse(BaseModel):
    url: str
    scan_result: str
    raw_violations: Dict[str, Any]

# Add new model for raw query
class RawQuery(BaseModel):
    query: str

router = APIRouter()

@router.post(
    "/api/accessibility/explain",
    response_model=AccessibilityResponse,
    summary="Get accessibility explanations",
    description="""
    Get expert explanations and guidance for accessibility concepts.
    
    This endpoint provides:
    - Detailed explanations of accessibility concepts
    - References to relevant WCAG guidelines
    - Practical implementation examples
    - Best practices and recommendations
    
    The API key must be provided in the X-Open-API-Key header.
    """,
    responses={
        200: {
            "description": "Successful response with accessibility explanation",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "The color contrast ratio should be at least 4.5:1 for normal text",
                        "explanation": "Color contrast is essential for users with visual impairments...",
                        "guidelines": "WCAG 2.1 Success Criterion 1.4.3 (Level AA)",
                        "examples": "Use tools like WebAIM Contrast Checker to verify contrast ratios..."
                    }
                }
            }
        },
        400: {"description": "Invalid request format"},
        401: {"description": "Missing or invalid API key"},
        500: {"description": "Internal server error"}
    }
)
async def explain_query(
    request: Request,
    query: Union[AccessibilityQuery, RawQuery],
    x_open_api_key: str = Header(..., alias="X-Open-API-Key", description="Your OpenAI API key")
):
    request_id = getattr(request.state, 'request_id', str(time.time()))
    
    if not x_open_api_key:
        api_logger.error(f"Request {request_id}: Missing API key")
        raise AuthenticationError()
        
    try:
        # Extract query string from either model
        query_text = query.query
        
        api_logger.info(f"Request {request_id}: Processing accessibility explanation query: {query_text}")
        
        with log_timing("accessibility_explain"):
            # Initialize agent with API key
            try:
                agent = AccessibilityExpertAgent(
                    api_key=x_open_api_key
                )
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to initialize agent: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to initialize accessibility agent: {str(e)}"
                )

            # Process query
            try:
                result, contexts = agent.answer_query(query_text)
                if not result or not isinstance(result, dict):
                    raise ValueError("Invalid response format from agent")
                
                # Validate response fields
                required_fields = {'answer', 'explanation', 'guidelines', 'examples'}
                missing_fields = required_fields - set(result.keys())
                
                if missing_fields:
                    raise ValueError(f"Missing required fields in response: {missing_fields}")
                
            except ValueError as ve:
                api_logger.error(f"Request {request_id}: Validation error in response: {str(ve)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Invalid response format: {str(ve)}"
                )
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to process query: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to process query: {str(e)}"
                )
                            
            api_logger.info(f"Request {request_id}: Successfully processed explanation query")
            return AccessibilityResponse(**result)
    
    except ValidationError as ve:
        api_logger.error(f"Request {request_id}: Validation error: {str(ve)}")
        raise AccessibilityError(
            status_code=400,
            detail=f"Validation error: {str(ve)}"
        )
    except AccessibilityError as ae:
        api_logger.error(f"Request {request_id}: Accessibility error: {str(ae)}")
        raise
    except Exception as e:
        api_logger.error(f"Request {request_id}: Unexpected error: {str(e)}")
        raise AccessibilityError(
            status_code=500,
            detail=f"An internal server error occurred: {str(e)}"
        )

@router.post(
    "/api/accessibility/fix",
    response_model=AccessibilityResponse,
    summary="Get accessibility issue fixes",
    description="""
    Get expert recommendations for fixing specific accessibility issues.
    
    This endpoint provides:
    - Specific solutions for accessibility violations
    - Step-by-step fix instructions
    - Code examples and fixes
    - Best practices for implementation
    
    The API key must be provided in the X-Open-API-Key header.
    """,
    responses={
        200: {
            "description": "Successful response with fix recommendations",
            "content": {
                "application/json": {
                    "example": {
                        "answer": "To fix the missing alt text issue, add descriptive alt attributes to all images",
                        "explanation": "Alt text is crucial for screen reader users to understand image content...",
                        "guidelines": "WCAG 2.1 Success Criterion 1.1.1 Non-text Content (Level A)",
                        "examples": "```html\n<img src='logo.png' alt='Company Logo'>\n```"
                    }
                }
            }
        },
        400: {"description": "Invalid request format"},
        401: {"description": "Missing or invalid API key"},
        500: {"description": "Internal server error"}
    }
)
async def fix_issue(
    request: Request,
    query: Union[AccessibilityQuery, RawQuery],
    x_open_api_key: str = Header(..., alias="X-Open-API-Key", description="Your OpenAI API key")
):
    request_id = getattr(request.state, 'request_id', str(time.time()))
    
    if not x_open_api_key:
        api_logger.error(f"Request {request_id}: Missing API key")
        raise AuthenticationError()
        
    try:
        # Extract query string from either model
        query_text = query.query if isinstance(query, AccessibilityQuery) else query.query
        
        api_logger.info(f"Request {request_id}: Processing fix request for query: {query_text}")
        
        with log_timing("accessibility_fix"):
            # Initialize agent with API key
            try:
                agent = AccessibilityExpertAgent(
                    api_key=x_open_api_key
                )
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to initialize agent: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to initialize accessibility agent: {str(e)}"
                )

            # Process fix request
            try:
                result, contexts = agent.answer_query(query_text)
                if not result or not isinstance(result, dict):
                    raise ValueError("Invalid response format from agent")
                
                # Validate response fields
                required_fields = {'answer', 'explanation', 'guidelines', 'examples'}
                missing_fields = required_fields - set(result.keys())
                
                if missing_fields:
                    raise ValueError(f"Missing required fields in response: {missing_fields}")
                
            except ValueError as ve:
                api_logger.error(f"Request {request_id}: Validation error in response: {str(ve)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Invalid response format: {str(ve)}"
                )
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to process fix request: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to process fix request: {str(e)}"
                )
                            
            api_logger.info(f"Request {request_id}: Successfully processed fix request")
            return AccessibilityResponse(**result)
    
    except ValidationError as ve:
        api_logger.error(f"Request {request_id}: Validation error: {str(ve)}")
        raise AccessibilityError(
            status_code=400,
            detail=f"Validation error: {str(ve)}"
        )
    except AccessibilityError as ae:
        api_logger.error(f"Request {request_id}: Accessibility error: {str(ae)}")
        raise
    except Exception as e:
        api_logger.error(f"Request {request_id}: Unexpected error: {str(e)}")
        raise AccessibilityError(
            status_code=500,
            detail=f"An internal server error occurred: {str(e)}"
        )

@router.post(
    "/api/accessibility/scan",
    response_model=ScanResponse,
    summary="Scan URL for accessibility issues",
    description="""
    Scan a URL for accessibility issues using axe-core.
    
    This endpoint provides:
    - Automated accessibility scanning of web pages
    - Detection of WCAG violations
    - Detailed technical analysis of issues
    - Raw violation data for further processing
    
    The API key must be provided in the X-Open-API-Key header.
    """,
    responses={
        200: {
            "description": "Successful scan with accessibility violations",
            "content": {
                "application/json": {
                    "example": {
                        "url": "https://example.com",
                        "scan_result": "Found 3 accessibility violations...",
                        "raw_violations": {
                            "critical": ["Contrast ratio too low", "Missing alt text"],
                            "serious": ["Incorrect ARIA usage"],
                            "moderate": ["Link purpose unclear"]
                        }
                    }
                }
            }
        },
        400: {"description": "Invalid URL or request format"},
        401: {"description": "Missing or invalid API key"},
        500: {"description": "Internal server error"}
    }
)
async def scan_url(
    request: Request,
    scan_request: ScanRequest,
    x_open_api_key: str = Header(..., alias="X-Open-API-Key", description="Your OpenAI API key")
):
    request_id = getattr(request.state, 'request_id', str(time.time()))
    
    if not x_open_api_key:
        api_logger.error(f"Request {request_id}: Missing API key")
        raise AuthenticationError()
        
    try:
        api_logger.info(f"Request {request_id}: Processing scan request for URL: {scan_request.url}")
        
        with log_timing("accessibility_scan"):
            # Initialize scanner agent with API key
            try:
                agent = ScannerAgent(api_key=x_open_api_key)
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to initialize scanner agent: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to initialize scanner agent: {str(e)}"
                )

            # Perform scan
            try:
                result = await agent.scan_url(str(scan_request.url))
                if not result or not isinstance(result, dict):
                    raise ValueError("Invalid response format from scanner agent")
                
                # Validate response fields
                required_fields = {'url', 'scan_result', 'raw_violations'}
                missing_fields = required_fields - set(result.keys())
                
                if missing_fields:
                    raise ValueError(f"Missing required fields in response: {missing_fields}")
                
            except ValueError as ve:
                api_logger.error(f"Request {request_id}: Validation error in scan response: {str(ve)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Invalid scan response format: {str(ve)}"
                )
            except Exception as e:
                api_logger.error(f"Request {request_id}: Failed to perform scan: {str(e)}")
                raise AccessibilityError(
                    status_code=500,
                    detail=f"Failed to perform scan: {str(e)}"
                )
                            
            api_logger.info(f"Request {request_id}: Successfully completed scan")
            return ScanResponse(**result)
    
    except ValidationError as ve:
        api_logger.error(f"Request {request_id}: Validation error: {str(ve)}")
        raise AccessibilityError(
            status_code=400,
            detail=f"Validation error: {str(ve)}"
        )
    except AccessibilityError as ae:
        api_logger.error(f"Request {request_id}: Accessibility error: {str(ae)}")
        raise
    except Exception as e:
        api_logger.error(f"Request {request_id}: Unexpected error: {str(e)}")
        raise AccessibilityError(
            status_code=500,
            detail=f"An internal server error occurred: {str(e)}"
        )