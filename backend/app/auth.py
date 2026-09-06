import os
from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

API_KEY = os.getenv("API_KEY", "sima-drishti-secure-key-2026")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sima_drishti.db")
SERIAL_PORT = os.getenv("SERIAL_PORT", "COM3")
SERIAL_BAUD = int(os.getenv("SERIAL_BAUD", 9600))

def verify_api_key(x_api_key: str = Header(default=None)):
    """Validates the incoming X-API-Key header against the environment configuration."""
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Unauthorized access.",
        )
    return x_api_key