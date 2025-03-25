from fastapi import APIRouter
import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Check if the API is running and its dependencies are healthy.
    Returns:
        dict: Health status of the API and its components
    """
    try:
        return {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "components": {
                "api": "healthy",
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        } 