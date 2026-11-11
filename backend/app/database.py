"""
Database Connection and Session Management
Supports SQLite and PostgreSQL/MySQL with SQLAlchemy 2.0.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.config import settings
from backend.crypto.ml_kem import generate_police_keypair

# Create SQLAlchemy Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 20} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_police_keys():
    """
    Ensures that ML-KEM-768 public and secret keys exist on the Police server.
    If not, generates a fresh quantum-safe keypair and stores securely in police_keys/.
    """
    pub_path = settings.POLICE_PUBLIC_KEY_PATH
    sec_path = settings.POLICE_SECRET_KEY_PATH

    if not pub_path.exists() or not sec_path.exists():
        pk, sk = generate_police_keypair()
        with open(pub_path, "wb") as f:
            f.write(pk)
        with open(sec_path, "wb") as f:
            f.write(sk)


def get_police_public_key() -> bytes:
    """Reads Police HQ ML-KEM Public Key"""
    ensure_police_keys()
    with open(settings.POLICE_PUBLIC_KEY_PATH, "rb") as f:
        return f.read()


def get_police_secret_key() -> bytes:
    """Reads Police HQ ML-KEM Secret Key for authorized decapsulation"""
    ensure_police_keys()
    with open(settings.POLICE_SECRET_KEY_PATH, "rb") as f:
        return f.read()
