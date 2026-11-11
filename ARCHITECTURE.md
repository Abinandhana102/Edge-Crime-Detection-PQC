# System Architecture & Technical Specifications

**Project Title:** Edge AI-Based Crime Detection and Quantum-Safe Digital Evidence Management Framework

---

## 1. High-Level Architecture

The system operates across two primary tiers:
1. **Edge AI Surveillance Tier**: Deployed on edge nodes / CCTV processing units. Responsible for real-time video stream ingestion, multi-model AI inference, threat classification, debounce control, circular video buffering, and hybrid post-quantum encryption.
2. **Police Command HQ & Evidence Vault Tier**: Centralized backend server and web command center. Responsible for real-time alert broadcasting via WebSockets, post-quantum key generation, relational database management, evidence storage, cryptographic integrity verification, and authorized decryption.

```mermaid
graph TD
    subgraph Edge_AI_Surveillance_Node [Edge AI Surveillance Tier]
        CAM[CCTV / Webcam / RTSP Feed] --> CS[Camera Stream Ingest]
        CS --> VB[Circular Rolling Frame Buffer]
        CS --> AI[Multi-Threat Inference Engine]
        
        AI --> DET1[YOLO Weapon Detector]
        AI --> DET2[Temporal Optical-Flow Violence Classifier]
        AI --> DET3[Ray-Casting Restricted Zone Intrusion]
        AI --> DET4[Stationary Luggage Tracker]
        
        DET1 & DET2 & DET3 & DET4 --> EVT[Event Debounce & Priority Manager]
        EVT -->|Threat Triggered| CAP[MP4 Clip Compiler]
        VB -.->|Pre-Event Frames| CAP
        
        CAP --> PQC[Hybrid Cryptographic Packaging Engine]
        PQC --> ENC1[AES-256-GCM Symmetric Encryption]
        PQC --> ENC2[NIST FIPS 203 ML-KEM-768 Key Encapsulation]
        PQC --> ENC3[SHA-256 Digest Generator]
        ENC1 & ENC2 & ENC3 --> QSEP[Quantum-Safe Evidence Package .qsep]
        
        QSEP --> TX[Secure Edge Transmitter Client]
    end

    subgraph Police_HQ_Vault [Police HQ Tier]
        TX -->|HTTPS / REST API| API[FastAPI Backend Server]
        API --> WS[WebSocket Alert Broadcast Service]
        API --> DB[(Relational Database: SQLite / PostgreSQL)]
        API --> ST[(Encrypted Evidence Vault: storage/encrypted_evidence/)]
        
        WS --> UI[Police Command Dashboard SPA]
        UI -->|Officer Auth JWT| AUTH[RBAC & Security Handler]
        AUTH --> VER[SHA-256 Evidence Integrity Verifier]
        AUTH --> DEC[ML-KEM-768 Decapsulation & AES Decryption]
        DEC --> STRM[Secure Ephemeral Playback Player]
        AUTH --> AUD[(Immutable Forensic Audit Trail)]
    end
```

---

## 2. Hybrid Post-Quantum Cryptographic Specification

To protect digital surveillance evidence against future quantum computer attacks (running Shor's algorithm to break RSA/ECC) while maintaining wire-speed video encryption throughput, the framework implements a **KEM/DEM (Key Encapsulation / Data Encapsulation) Hybrid Architecture**:

```
+---------------------------------------------------------------------------------------+
|                       Quantum-Safe Evidence Package (.qsep)                           |
+---------------------------------------------------------------------------------------+
| 1. Header Metadata (JSON): Incident ID, Camera Code, Timestamp, Cryptographic Alg      |
| 2. KEM Ciphertext (1536 bytes): ML-KEM-768 Encapsulated 256-bit AES Session Key       |
| 3. AES-256 Nonce (12 bytes): Cryptographically Secure Random IV                       |
| 4. AES-256-GCM Auth Tag (16 bytes): 128-bit Galois Authentication Tag                 |
| 5. Pre-Encryption SHA-256 Digest (64 hex characters): Plaintext Verification Hash     |
| 6. Ciphertext Payload (Variable bytes): Authenticated AES-256-GCM Video Bitstream     |
+---------------------------------------------------------------------------------------+
```

### Mathematical Formulations:
- **Module Lattice Ring**: $\mathcal{R}_q = \mathbb{Z}_q[X] / (X^{256} + 1)$ with $q = 3329, n = 256$.
- **Key Generation**: 
  $$\mathbf{A} \leftarrow \text{Sample}(\rho), \quad \mathbf{s}, \mathbf{e} \leftarrow \text{CBD}_{\eta_1}^k(\sigma)$$
  $$\mathbf{t} = \mathbf{A}\mathbf{s} + \mathbf{e} \pmod q, \quad \text{pk} = (\text{Encode}(\mathbf{t}), \rho), \quad \text{sk} = (\text{Encode}(\mathbf{s}), \text{pk}, H(\text{pk}), z)$$
- **Encapsulation**:
  $$m \leftarrow \{0,1\}^{256}, \quad (\bar{K}, r) = H(m \parallel H(\text{pk}))$$
  $$\mathbf{u} = \mathbf{A}^T \mathbf{s}' + \mathbf{e}', \quad v = \mathbf{t}^T \mathbf{s}' + e'' + \text{Decompress}_1(m)$$
  $$c = (\mathbf{u}, v), \quad K_{\text{AES}} = \text{KDF}(\bar{K} \parallel H(c))$$
- **AES-256-GCM Authenticated Encryption**:
  $$C = \text{AES-CTR}_{K_{\text{AES}}}(\text{IV}, M), \quad T = \text{GHASH}_{H}(\text{AAD}, C, \text{Len}) \oplus \text{AES}_{K_{\text{AES}}}(\text{IV} \parallel 1)$$

---

## 3. Relational Database Schema

```mermaid
erDiagram
    USERS {
        int id PK
        string username UK
        string badge_number UK
        string full_name
        string role
        string hashed_password
        boolean is_active
        datetime created_at
    }

    CAMERAS {
        int id PK
        string camera_code UK
        string name
        string location
        string stream_source
        string status
        string ai_detection
        string ip_address
        datetime created_at
    }

    INCIDENTS {
        int id PK
        string incident_id UK
        string detection_type
        string object_detected
        string severity
        float confidence
        int camera_id FK
        string camera_code
        string location
        string status
        string transmission_status
        text notes
        datetime created_at
    }

    EVIDENCE {
        int id PK
        string incident_id FK,UK
        string original_filename
        string encrypted_filename
        string storage_path
        string crypto_scheme
        string pqc_algorithm
        string symmetric_cipher
        string plaintext_sha256
        string encrypted_sha256
        string encryption_status
        string integrity_status
        int file_size_bytes
        float duration_seconds
        datetime created_at
        datetime last_verified_at
        datetime last_retrieved_at
    }

    AUDIT_LOGS {
        int id PK
        datetime timestamp
        string username
        string action
        string incident_id
        text details
        string ip_address
        int user_id FK
    }

    RESTRICTED_ZONES {
        int id PK
        string zone_code UK
        string name
        int camera_id FK
        text polygon_points_json
        string severity
        boolean is_active
        datetime created_at
    }

    CAMERAS ||--o{ INCIDENTS : captures
    CAMERAS ||--o{ RESTRICTED_ZONES : monitors
    INCIDENTS ||--o| EVIDENCE : encapsulates
    USERS ||--o{ AUDIT_LOGS : performs
```

---

## 4. Threat Model & Security Evaluation

| Threat Vector | Mitigation Strategy | Verification Status |
| :--- | :--- | :--- |
| **Quantum Computer Attacks (Shor's Algorithm)** | NIST FIPS 203 ML-KEM-768 lattice-based key encapsulation | ✅ Verified in `test_crypto_hybrid.py` |
| **Evidence Tampering / Bit Modification** | AES-256-GCM 128-bit authentication tag + SHA-256 pre-encryption digest | ✅ Verified in `test_crypto_hybrid.py` |
| **Unauthorized Evidence Access** | JWT Bearer Authentication, Role-Based Access Control (RBAC) | ✅ Verified in `test_api_and_auth.py` |
| **Alert Storm / Denial of Service** | Sliding time-window debounce controller (`EventManager`) | ✅ Verified in `test_api_and_auth.py` |
| **Edge Network Outage** | Offline queue retention in `storage/offline_queue/` with retry | ✅ Implemented in `edge_transmitter.py` |
| **Repudiation of Forensic Actions** | Immutable append-only audit trail recording user badges and IPs | ✅ Verified in `run_demo.py` |
