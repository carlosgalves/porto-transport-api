from fastapi import APIRouter, Depends
from app.core.dependencies import get_api_key

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/verify")
def verify_api_key(api_key: str = Depends(get_api_key)):
    """Verify that the API key is valid."""
    return {"status": "valid", "message": "API key is valid"}