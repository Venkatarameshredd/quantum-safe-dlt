"""Configuration for AegisLedger-Q: Quantum-Safe Distributed Ledger Technology."""
from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = Path(os.getenv("QUANTUM_DLT_ARTIFACTS", ROOT_DIR / "artifacts"))
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Post-Quantum Cryptography (PQC) Parameters
# -----------------------------------------------------------------------------
# Based on NIST FIPS 204 (ML-DSA / Dilithium) and hash-based signatures
PQC_SCHEME = "ML-DSA-65 (Dilithium-3)"
LATTICE_DIM_N = 256
LATTICE_MODULUS_Q = 8380417
PQC_SECURITY_LEVEL = "NIST Level 3 (AES-192 equivalent post-quantum)"

# -----------------------------------------------------------------------------
# 2. Qiskit Quantum Key Distribution (QKD) Parameters
# -----------------------------------------------------------------------------
QKD_PROTOCOL = "BB84 Protocol (Bennett-Brassard 1984)"
QKD_DEFAULT_PHOTONS = 64
QKD_QBER_ABORT_THRESHOLD = 0.110  # 11% theoretical intercept-resend eavesdropping threshold
QKD_BASIS_RECTILINEAR = 0         # Computational (Z) basis {|0>, |1>}
QKD_BASIS_DIAGONAL = 1            # Hadamard (X) basis {|+>, |->}

# -----------------------------------------------------------------------------
# 3. Qiskit Quantum Machine Learning (QML) Detector Parameters
# -----------------------------------------------------------------------------
QML_N_QUBITS = 4
QML_CIRCUIT_DEPTH = 2
QML_FEATURE_DIM = 4
QML_DECISION_THRESHOLD = 0.50
QML_EPOCHS = 35
QML_LEARNING_RATE = 0.025
QML_RECALL_TARGET = 0.96          # Target > 96% Recall on fraud/tamper detection

# -----------------------------------------------------------------------------
# 4. Andhra Pradesh Cadastral & Supply-Chain Registries
# -----------------------------------------------------------------------------
AP_DISTRICTS = [
    "Visakhapatnam",
    "Amaravati",
    "Vijayawada (NTR)",
    "Guntur",
    "Tirupati",
    "Kurnool",
    "Anantapur",
    "Kakinada",
]

LAND_USE_CATEGORIES = [
    "Agricultural (Wet Land)",
    "Agricultural (Dry Land)",
    "Commercial Development",
    "Residential Cadastral",
    "Government / Forest Reserve",
]

PHARMA_DRUG_CATALOG = [
    {"name": "Trastuzumab (Oncology mAb)", "min_temp": 2.0, "max_temp": 8.0, "dose": "440mg"},
    {"name": "mRNA COVID-19 Vaccine", "min_temp": -25.0, "max_temp": -15.0, "dose": "0.5mL"},
    {"name": "Recombinant Human Insulin", "min_temp": 2.0, "max_temp": 8.0, "dose": "100IU/mL"},
    {"name": "Pembro-Immuno Oncology Infusion", "min_temp": 2.0, "max_temp": 8.0, "dose": "100mg"},
]

CERTIFICATE_TYPES = [
    "Integrated Caste & Community Certificate",
    "Land Title Deed (Pattadar Passbook)",
    "Agricultural Income Certificate",
    "University Degree Credential",
]

# -----------------------------------------------------------------------------
# 5. Distributed Ledger & Network Settings
# -----------------------------------------------------------------------------
NETWORK_NAME = "AegisLedger-Q Mainnet (AP-Secure-DLT)"
GENESIS_PREV_HASH = "0" * 64
BLOCK_REWARD_BHUCOIN = 10.0
HASH_ALGORITHM = "SHA3-256 (Post-Quantum Collision Resistant)"
UI_PORT = int(os.getenv("QUANTUM_DLT_UI_PORT", "8503"))
APP_PORT = UI_PORT
API_PORT = int(os.getenv("QUANTUM_DLT_API_PORT", "8504"))
API_HOST = os.getenv("QUANTUM_DLT_API_HOST", "127.0.0.1")

AP_DISTRICT_COORDINATES = {
    "Visakhapatnam": (17.6868, 83.2185),
    "Amaravati": (16.5735, 80.3575),
    "Vijayawada (NTR)": (16.5062, 80.6480),
    "Guntur": (16.3067, 80.4365),
    "Tirupati": (13.6288, 79.4192),
    "Kurnool": (15.8281, 78.0373),
    "Anantapur": (14.6819, 77.6006),
    "Kakinada": (16.9891, 82.2475),
}
