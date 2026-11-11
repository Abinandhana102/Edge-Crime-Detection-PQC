"""
Unit Tests for Quantum-Safe Cryptography Module
Tests NIST FIPS 203 ML-KEM-768 + AES-256-GCM + SHA-256 integrity and tamper resistance.
"""

import pytest
from backend.crypto.ml_kem import kyber768, generate_police_keypair, ml_kem_encapsulate, ml_kem_decapsulate
from backend.crypto.aes_gcm import AES256GCMCipher
from backend.crypto.integrity import EvidenceIntegrity
from backend.crypto.hybrid_envelope import QuantumSafeEvidencePackage


def test_ml_kem_768_keypair_generation():
    """Validates ML-KEM-768 public and secret key lengths"""
    pk, sk = generate_police_keypair()
    assert len(pk) == kyber768.pk_size
    assert len(sk) == kyber768.sk_size


def test_ml_kem_768_encap_decap_roundtrip():
    """Validates that ML-KEM decapsulation recovers the exact 256-bit symmetric shared secret"""
    pk, sk = generate_police_keypair()
    shared_secret_encap, ciphertext = ml_kem_encapsulate(pk)
    
    assert len(shared_secret_encap) == 32  # 256 bits
    assert len(ciphertext) == kyber768.ct_size

    shared_secret_decap = ml_kem_decapsulate(sk, ciphertext)
    assert shared_secret_encap == shared_secret_decap


def test_aes_256_gcm_authenticated_encryption():
    """Validates AES-256-GCM encryption, decryption, and authentication tag"""
    key = AES256GCMCipher.generate_key()
    assert len(key) == 32

    plaintext = b"SURVEILLANCE_VIDEO_STREAM_TEST_PACKET_FIPS_203"
    associated_data = b"INCIDENT:INC-20260827-0001"

    ciphertext, nonce, tag = AES256GCMCipher.encrypt(key, plaintext, associated_data)
    assert len(nonce) == 12
    assert len(tag) == 16
    assert ciphertext != plaintext

    decrypted = AES256GCMCipher.decrypt(key, ciphertext, nonce, tag, associated_data)
    assert decrypted == plaintext


def test_aes_256_gcm_tamper_detection():
    """Validates that any tampering in AES ciphertext or tag is rejected"""
    key = AES256GCMCipher.generate_key()
    plaintext = b"CRITICAL_CRIME_EVIDENCE_PAYLOAD"
    associated_data = b"INCIDENT:INC-20260827-0001"

    ciphertext, nonce, tag = AES256GCMCipher.encrypt(key, plaintext, associated_data)
    
    # Tamper with 1 byte of ciphertext
    tampered_ct = bytearray(ciphertext)
    tampered_ct[0] ^= 0xFF

    with pytest.raises(Exception):
        AES256GCMCipher.decrypt(key, bytes(tampered_ct), nonce, tag, associated_data)


def test_hybrid_quantum_safe_evidence_package_roundtrip():
    """Validates full end-to-end QuantumSafeEvidencePackage (.qsep) lifecycle"""
    pk, sk = generate_police_keypair()
    raw_evidence = b"HIGH_RESOLUTION_CCTV_FOOTAGE_MP4_BINARY_DATA"
    metadata = {
        "incident_id": "INC-20260827-0001",
        "camera_code": "CAM-01",
        "location": "Main Gate North",
        "detection_type": "Weapon",
        "confidence": 94.2
    }

    # Encrypt & Package
    qsep_package, header = QuantumSafeEvidencePackage.encrypt_and_package(raw_evidence, pk, metadata)
    assert len(qsep_package) > len(raw_evidence)
    assert header["crypto_scheme"] == "HYBRID:AES-256-GCM+ML-KEM-768"

    # Authorized Decryption & Integrity Verification
    decrypted, is_valid, msg, hdr = QuantumSafeEvidencePackage.decrypt_and_verify(qsep_package, sk)
    assert decrypted == raw_evidence
    assert is_valid is True
    assert hdr["incident_id"] == "INC-20260827-0001"


def test_evidence_sha256_integrity():
    """Validates SHA-256 hash calculation and verification"""
    data = b"EVIDENCE_AUTHENTICITY_VERIFICATION"
    expected_hash = EvidenceIntegrity.calculate_sha256(data)

    is_valid, msg = EvidenceIntegrity.verify_integrity(data, expected_hash)
    assert is_valid is True

    # Tampered data
    is_valid_bad, msg_bad = EvidenceIntegrity.verify_integrity(b"MODIFIED_EVIDENCE", expected_hash)
    assert is_valid_bad is False
