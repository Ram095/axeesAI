from fastapi import HTTPException

class AccessibilityError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

class ValidationError(AccessibilityError):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)

class AuthenticationError(AccessibilityError):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid or missing API key")
