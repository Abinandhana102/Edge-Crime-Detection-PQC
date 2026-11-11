"""
AES-256-GCM Authenticated Encryption Module
Provides high-speed authenticated symmetric encryption for video evidence files.

Features:
- 256-bit symmetric security
- 96-bit cryptographically secure random nonce (IV) per encryption
- 128-bit authentication tag (GCM mode) to guarantee ciphertext integrity and detect tampering
"""

import os
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AES256GCMCipher:
    """
    AES-256-GCM symmetric encryption for CCTV evidence video files.
    """

    @staticmethod
    def generate_key() -> bytes:
        """Generates a cryptographically strong 256-bit (32 bytes) random AES key."""
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def encrypt(key: bytes, plaintext_data: bytes, associated_data: bytes = b"") -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts binary data with AES-256-GCM.
        Returns: (ciphertext, nonce_12bytes, tag_16bytes)
        """
        if len(key) != 32:
            raise ValueError("AES-256 key must be exactly 32 bytes (256 bits)")

        nonce = os.urandom(12)  # Standard 96-bit GCM nonce
        aesgcm = AESGCM(key)
        # AESGCM.encrypt in cryptography library appends the 16-byte tag to the ciphertext
        encrypted_payload = aesgcm.encrypt(nonce, plaintext_data, associated_data)
        ciphertext = encrypted_payload[:-16]
        tag = encrypted_payload[-16:]
        return ciphertext, nonce, tag

    @staticmethod
    def decrypt(key: bytes, ciphertext: bytes, nonce: bytes, tag: bytes, associated_data: bytes = b"") -> bytes:
        """
        Decrypts ciphertext with AES-256-GCM and verifies 16-byte authentication tag.
        Raises InvalidTag if tampered or corrupt.
        """
        if len(key) != 32:
            raise ValueError("AES-256 key must be exactly 32 bytes")
        if len(nonce) != 12:
            raise ValueError("AES-GCM nonce must be 12 bytes")
        if len(tag) != 16:
            raise ValueError("AES-GCM authentication tag must be 16 bytes")

        aesgcm = AESGCM(key)
        # Combine ciphertext and tag for cryptography AESGCM.decrypt
        full_payload = ciphertext + tag
        return aesgcm.decrypt(nonce, full_payload, associated_data)
