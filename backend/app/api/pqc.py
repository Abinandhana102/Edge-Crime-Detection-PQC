"""
Post-Quantum Cryptography Public Key & Metadata API Routes
"""

import base64
from fastapi import APIRouter
from backend.app.database import get_police_public_key

router = APIRouter(prefix="/pqc", tags=["Post-Quantum Cryptography"])


@router.get("/public-key")
async def get_public_key():
    """
    Returns the Police HQ ML-KEM-768 public key (base64 encoded) for Edge AI video encapsulation.
    """
    pk_bytes = get_police_public_key()
    return {
        "algorithm": "NIST FIPS 203 ML-KEM-768 (CRYSTALS-Kyber-768)",
        "security_level": "NIST Category 3 (Quantum-Resistant 192-bit classical equivalent)",
        "public_key_len": len(pk_bytes),
        "public_key_b64": base64.b64encode(pk_bytes).decode("utf-8")
    }


@router.get("/info")
async def get_crypto_info():
    """Returns technical details of the hybrid quantum-safe cryptographic architecture"""
    return {
        "hybrid_scheme": "AES-256-GCM + NIST FIPS 203 ML-KEM-768",
        "symmetric_cipher": {
            "name": "AES-256-GCM",
            "key_size_bits": 256,
            "mode": "Galois/Counter Mode (Authenticated)",
            "nonce_size_bits": 96,
            "tag_size_bits": 128
        },
        "key_encapsulation": {
            "name": "ML-KEM-768",
            "fips_standard": "NIST FIPS 203",
            "quantum_attack_resistance": "Resistant to Shor's algorithm & Grover's attack",
            "lattice_basis": "Module Learning With Errors (M-LWE)",
            "polynomial_ring": "Z_3329[X] / (X^256 + 1)"
        },
        "integrity_hash": {
            "algorithm": "SHA-256 (FIPS 180-4)",
            "verification": "Computed over decrypted video bitstream before authorization"
        }
    }
