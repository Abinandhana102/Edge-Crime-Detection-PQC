"""
Evidence Integrity Module
Computes cryptographic SHA-256 digests over digital evidence and performs tamper verification.
"""

import hashlib
from typing import Tuple


class EvidenceIntegrity:
    """
    Computes SHA-256 hashes and verifies digital evidence integrity.
    """

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Computes SHA-256 hexadecimal hash string for binary data."""
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()

    @staticmethod
    def calculate_file_sha256(filepath: str) -> str:
        """Computes SHA-256 hash for a file on disk in chunks."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def verify_integrity(data: bytes, expected_hash: str) -> Tuple[bool, str]:
        """
        Verifies if calculated SHA-256 matches expected hash.
        Returns: (is_valid, message)
        """
        actual_hash = EvidenceIntegrity.calculate_sha256(data)
        if actual_hash.lower() == expected_hash.lower():
            return True, "✅ Evidence Integrity Verified: SHA-256 matches exactly."
        else:
            return False, f"❌ Evidence Integrity Check Failed: Expected {expected_hash}, got {actual_hash}"
