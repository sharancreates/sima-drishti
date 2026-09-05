from fastapi import Header, HTTPException, status
import os

# Default fallback key for local dev and hackathon testing
API_KEY = os.getenv("SIMA_API_KEY", "sima-drishti-secure-key-2026")

def verify_api_key(x_api_key: str = Header(default=None)):
    """Validates the incoming X-API-Key header against the environment configuration."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Unauthorized access.",
        )
    return x_api_key