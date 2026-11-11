"""
Hybrid Quantum-Safe Evidence Packaging & Envelope Module
Implements the hybrid post-quantum cryptographic architecture:
CCTV Raw Video -> AES-256-GCM Encryption -> ML-KEM/CRYSTALS-Kyber Protected AES Key -> SHA-256 Integrity Digest
"""

import json
import base64
import os
from typing import Dict, Any, Tuple
from backend.crypto.aes_gcm import AES256GCMCipher
from backend.crypto.ml_kem import kyber768
from backend.crypto.integrity import EvidenceIntegrity


class QuantumSafeEvidencePackage:
    """
    Constructs and unpacks Quantum-Safe Evidence Packages (.qsep).
    """

    @staticmethod
    def encrypt_and_package(
        video_bytes: bytes,
        police_public_key: bytes,
        metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Executes complete hybrid post-quantum encryption on digital video evidence:
        1. Generates ephemeral AES-256 symmetric key.
        2. Computes SHA-256 digest of plaintext evidence before encryption.
        3. Encrypts video with AES-256-GCM (producing ciphertext, 96-bit nonce, 128-bit auth tag).
        4. Uses ML-KEM-768 to encapsulate the symmetric key using Police Public Key.
        5. Bundles everything into a self-authenticating Quantum-Safe Evidence Package (.qsep).
        
        Returns:
            (qsep_binary_package, package_metadata_dict)
        """
        # Step 1: Pre-encryption integrity hash
        plaintext_sha256 = EvidenceIntegrity.calculate_sha256(video_bytes)

        # Step 2: Encapsulate shared secret using ML-KEM against Police Public Key
        # The ML-KEM shared secret (32 bytes) serves as our AES-256 encryption key
        aes_session_key, kem_ciphertext = kyber768.encaps(police_public_key)

        # Step 3: Encrypt video with AES-256-GCM
        associated_data = f"INCIDENT:{metadata.get('incident_id', 'UNKNOWN')}".encode("utf-8")
        ciphertext, nonce, tag = AES256GCMCipher.encrypt(
            key=aes_session_key,
            plaintext_data=video_bytes,
            associated_data=associated_data
        )

        # Step 4: Compute encrypted payload hash
        encrypted_sha256 = EvidenceIntegrity.calculate_sha256(ciphertext)

        # Step 5: Construct Package Header & Metadata
        header = {
            "format": "QSEP/1.0",
            "crypto_scheme": "HYBRID:AES-256-GCM+ML-KEM-768",
            "pqc_algorithm": "NIST FIPS 203 ML-KEM-768",
            "symmetric_cipher": "AES-256-GCM",
            "integrity_algorithm": "SHA-256",
            "incident_id": metadata.get("incident_id"),
            "camera_id": metadata.get("camera_id"),
            "timestamp": metadata.get("timestamp"),
            "detection_type": metadata.get("detection_type"),
            "confidence": metadata.get("confidence"),
            "plaintext_sha256": plaintext_sha256,
            "encrypted_sha256": encrypted_sha256,
            "kem_ciphertext_b64": base64.b64encode(kem_ciphertext).decode("utf-8"),
            "nonce_b64": base64.b64encode(nonce).decode("utf-8"),
            "tag_b64": base64.b64encode(tag).decode("utf-8"),
            "payload_length": len(ciphertext),
            "original_filename": metadata.get("original_filename", "evidence.mp4"),
            "encrypted_filename": metadata.get("encrypted_filename", f"{metadata.get('incident_id')}.qsep")
        }

        header_bytes = json.dumps(header).encode("utf-8")
        header_len = len(header_bytes)

        # Binary structure: [4 bytes header length (uint32)] + [JSON Header] + [Ciphertext]
        package_bytes = header_len.to_bytes(4, byteorder="big") + header_bytes + ciphertext

        return package_bytes, header

    @staticmethod
    def parse_package_header(package_bytes: bytes) -> Tuple[Dict[str, Any], bytes]:
        """
        Parses header from .qsep binary package without decrypting.
        Returns: (header_dict, ciphertext_bytes)
        """
        if len(package_bytes) < 4:
            raise ValueError("Invalid QSEP package: too short")
        
        header_len = int.from_bytes(package_bytes[:4], byteorder="big")
        if len(package_bytes) < 4 + header_len:
            raise ValueError("Corrupt QSEP package: header truncated")
        
        header_bytes = package_bytes[4 : 4 + header_len]
        header = json.loads(header_bytes.decode("utf-8"))
        ciphertext = package_bytes[4 + header_len :]
        return header, ciphertext

    @staticmethod
    def decrypt_and_verify(
        package_bytes: bytes,
        police_secret_key: bytes
    ) -> Tuple[bytes, bool, str, Dict[str, Any]]:
        """
        Authorized Decryption and Verification:
        1. Parses QSEP header.
        2. Uses ML-KEM-768 decapsulation with Police Secret Key to recover AES-256 session key.
        3. Decrypts video ciphertext using AES-256-GCM.
        4. Verifies SHA-256 integrity hash of decrypted video against header digest.
        
        Returns:
            (decrypted_video_bytes, is_integrity_valid, integrity_message, header_metadata)
        """
        header, ciphertext = QuantumSafeEvidencePackage.parse_package_header(package_bytes)

        kem_ciphertext = base64.b64decode(header["kem_ciphertext_b64"])
        nonce = base64.b64decode(header["nonce_b64"])
        tag = base64.b64decode(header["tag_b64"])
        expected_sha256 = header["plaintext_sha256"]
        associated_data = f"INCIDENT:{header.get('incident_id', 'UNKNOWN')}".encode("utf-8")

        # Step 1: Post-quantum ML-KEM Decapsulation
        recovered_aes_key = kyber768.decaps(police_secret_key, kem_ciphertext)

        # Step 2: AES-256-GCM Authenticated Decryption
        decrypted_video = AES256GCMCipher.decrypt(
            key=recovered_aes_key,
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            associated_data=associated_data
        )

        # Step 3: Evidence Integrity Verification
        is_valid, msg = EvidenceIntegrity.verify_integrity(decrypted_video, expected_sha256)

        return decrypted_video, is_valid, msg, header
