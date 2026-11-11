"""
Application Configuration and Settings
Loaded from environment variables with secure defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
ENCRYPTED_EVIDENCE_DIR = STORAGE_DIR / "encrypted_evidence"
DECRYPTED_CACHE_DIR = STORAGE_DIR / "decrypted_cache"
POLICE_KEYS_DIR = STORAGE_DIR / "police_keys"
MODELS_DIR = BASE_DIR / "models"

# Ensure storage directories exist
for folder in [STORAGE_DIR, ENCRYPTED_EVIDENCE_DIR, DECRYPTED_CACHE_DIR, POLICE_KEYS_DIR, MODELS_DIR]:
    folder.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Quantum-Safe Crime Detection & Evidence Management Framework"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Security & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "quantum-safe-jwt-super-secret-key-2026-mcet-project")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/storage/surveillance_evidence.db")
    
    # Cryptography
    POLICE_PUBLIC_KEY_PATH: Path = POLICE_KEYS_DIR / "police_hq_mlkem768.pub"
    POLICE_SECRET_KEY_PATH: Path = POLICE_KEYS_DIR / "police_hq_mlkem768.key"
    
    # Edge AI Defaults
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.45
    WEAPON_CONFIDENCE_THRESHOLD: float = 0.50
    VIOLENCE_CONFIDENCE_THRESHOLD: float = 0.60
    ABANDONED_OBJECT_TIME_SEC: int = 10  # Seconds stationary before alert
    DEBOUNCE_COOLDOWN_SEC: int = 8       # Minimum interval between duplicate incident records
    PRE_EVENT_BUFFER_SEC: int = 5        # Pre-event recording duration
    POST_EVENT_BUFFER_SEC: int = 10      # Post-event recording duration

    # Server Host
    HOST: str = "0.0.0.0"
    PORT: int = 8000


settings = Settings()
