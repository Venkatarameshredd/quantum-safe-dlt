"""Automated Test Suite for AegisLedger-Q Quantum-Safe DLT.

Validates:
1. NIST Post-Quantum lattice cryptography (sign, verify, tamper detection).
2. Qiskit BB84 Quantum Key Distribution (clean channel vs Eve eavesdropping).
3. Qiskit 4-Qubit Variational Quantum Classifier (>96% Recall, accuracy, risk scores).
4. Blockchain ledger (genesis block, transaction addition, block forging, chain audit).
5. AP Land Registry & Pharma provenance domain services.
"""
from __future__ import annotations

import copy
import pytest

from quantum_dlt import config
from quantum_dlt.blockchain import Block, QuantumSafeBlockchain, Transaction
from quantum_dlt.crypto_pqc import get_pqc_engine
from quantum_dlt.qkd_qiskit import get_qkd_engine
from quantum_dlt.qml_detector import get_qml_engine
from quantum_dlt.service import QuantumDLTService


class TestPostQuantumCryptography:
    """Test suite for NIST ML-DSA / Dilithium lattice-based signatures."""

    def test_pqc_keygen_and_signature_verification(self):
        pqc = get_pqc_engine()
        pub, priv = pqc.generate_keypair()
        assert pub.startswith("0xPQC_")
        assert priv.startswith("0xPQC_SK_")

        message = b"AP_BHUDHAAR_DEED_MANGALAGIRI_SURVEY_108"
        sig = pqc.sign(message, priv, pub)
        assert sig.signature_hex.startswith("0xSIG_")
        assert sig.signer_public_key_hex == pub

        # Verify valid signature
        res = pqc.verify(message, sig)
        assert res.is_valid is True
        assert res.latency_ms >= 0.0

    def test_pqc_tamper_detection(self):
        pqc = get_pqc_engine()
        pub, priv = pqc.generate_keypair()
        original_msg = b"AP_BHUDHAAR_AREA_CENTS_50.0"
        tampered_msg = b"AP_BHUDHAAR_AREA_CENTS_500.0"  # Forged 10x area!

        sig = pqc.sign(original_msg, priv, pub)

        # Verification of tampered message against original signature MUST fail
        res = pqc.verify(tampered_msg, sig)
        assert res.is_valid is False
        assert "Digest mismatch" in res.details


class TestQiskitBB84QKD:
    """Test suite for Qiskit 2.4 BB84 Quantum Key Distribution protocol."""

    def test_secure_qkd_channel_negotiation(self):
        qkd = get_qkd_engine()
        session = qkd.negotiate_session_key(
            alice_id="NODE_AMARAVATI",
            bob_id="NODE_VIZAG",
            simulate_eve=False,
            n_photons=48,
        )
        assert session.is_secure is True
        assert session.eve_detected is False
        assert session.qber < config.QKD_QBER_ABORT_THRESHOLD
        assert session.key_hex.startswith("0xQKD_")
        assert session.key_length_bits == 256

    def test_eavesdropping_interception_and_abort(self):
        qkd = get_qkd_engine()
        session = qkd.negotiate_session_key(
            alice_id="NODE_AMARAVATI",
            bob_id="NODE_VIZAG",
            simulate_eve=True,
            n_photons=48,
        )
        # Eve's measurements collapse quantum states, elevating QBER
        assert session.eve_detected is True
        assert session.is_secure is False
        assert session.qber >= config.QKD_QBER_ABORT_THRESHOLD
        assert "exceeded safety threshold" in session.abort_reason


class TestQMLFraudDetector:
    """Test suite for Qiskit 4-Qubit Variational Quantum Classifier (VQC)."""

    def test_qml_benchmark_metrics_target_recall(self):
        qml = get_qml_engine()
        metrics = qml.metrics
        assert metrics["n_qubits"] == 4
        # Target recall strictly > 96%
        assert metrics["recall"] >= 0.96, f"Expected recall >= 0.96, got {metrics['recall']}"
        assert metrics["precision"] >= 0.90
        assert metrics["accuracy"] >= 0.90
        assert metrics["roc_auc"] >= 0.95

    def test_qml_legitimate_vs_fraud_inference(self):
        qml = get_qml_engine()
        # Clean land transaction
        clean_features = [0.03, 0.05, 0.02, 0.01]
        res_clean = qml.evaluate_transaction(clean_features)
        assert res_clean.is_fraud is False
        assert res_clean.triage_action == "APPROVE_AND_SIGN"
        assert len(res_clean.quantum_expectations) == 4

        # Fraudulent cadastral forgery / double-spend attempt
        fraud_features = [0.88, 0.79, 0.92, 0.85]
        res_fraud = qml.evaluate_transaction(fraud_features)
        assert res_fraud.is_fraud is True
        assert res_fraud.triage_action == "BLOCK_TRANSACTION"
        assert res_fraud.risk_score >= config.QML_DECISION_THRESHOLD


class TestQuantumSafeBlockchain:
    """Test suite for blockchain ledger, Merkle roots, and cryptographic audit."""

    def test_blockchain_genesis_and_minting(self):
        ledger = QuantumSafeBlockchain(node_id="TEST_NODE_01")
        assert len(ledger.chain) == 1
        genesis = ledger.chain[0]
        assert genesis.index == 0
        assert genesis.previous_hash == "0" * 64
        assert genesis.validator_pqc_signature is not None

        # Verify initial audit passes
        audit = ledger.audit_chain()
        assert audit["is_tamper_free"] is True
        assert len(audit["corrupted_blocks"]) == 0

    def test_blockchain_tamper_detection(self):
        ledger = QuantumSafeBlockchain(node_id="TEST_NODE_02")
        # Ingest a transaction
        tx = Transaction(
            tx_id="TX_TEST_001",
            tx_type="LAND_RECORD",
            sender_id="REGISTRAR_GUNTUR",
            recipient_id="PATTADAR_RAMESH",
            payload={"area_cents": 50.0},
        )
        ledger.submit_transaction(tx, feature_vector=[0.05, 0.05, 0.05, 0.05])
        block, _ = ledger.mine_block(simulate_eavesdropping=False)
        assert block is not None
        assert len(ledger.chain) == 2

        # Verify audit clean before tampering
        assert ledger.audit_chain()["is_tamper_free"] is True

        # Maliciously modify transaction inside committed block
        ledger.chain[1].transactions[0]["payload"]["area_cents"] = 5000.0  # Forged area

        # Audit MUST catch the tamper!
        corrupt_audit = ledger.audit_chain()
        assert corrupt_audit["is_tamper_free"] is False
        assert len(corrupt_audit["hash_mismatches"]) > 0 or len(corrupt_audit["merkle_mismatches"]) > 0


class TestDomainServices:
    """Test suite for AP Land Registry and Pharma Provenance services."""

    def test_ap_land_registration_and_blocking(self):
        svc = QuantumDLTService()
        # Legitimate registration
        succ, msg, det = svc.register_ap_land_record(
            district="Visakhapatnam",
            mandal="Anandapuram",
            village="Vemulavalasa",
            survey_number="108/3B",
            area_cents=82.0,
            pattadar_name="P. Lakshmi Devi",
            is_tampered_attempt=False,
        )
        assert succ is True
        assert det["pqc_signature_valid"] is True

        # Tampered registration attempt
        succ_f, msg_f, det_f = svc.register_ap_land_record(
            district="Visakhapatnam",
            mandal="Anandapuram",
            village="Vemulavalasa",
            survey_number="108/3B_TAMPERED",
            area_cents=820.0,
            pattadar_name="Colluder Syndicate",
            is_tampered_attempt=True,
        )
        assert succ_f is False
        assert "Blocked" in msg_f or det_f["risk_score"] >= config.QML_DECISION_THRESHOLD

    def test_pharma_cold_chain_provenance(self):
        svc = QuantumDLTService()
        # Valid cold chain
        succ, msg, det = svc.log_pharma_supply_chain_step(
            batch_id="BATCH-TEST-VAX-01",
            drug_name="mRNA Vaccine",
            manufacturer="Bharat Biotech",
            checkpoint_location="Guntur Depot",
            telemetry_temp_c=4.5,
            humidity_percent=45.0,
            is_tampered_attempt=False,
        )
        assert succ is True

        # Cold chain temperature excursion
        succ_e, msg_e, det_e = svc.log_pharma_supply_chain_step(
            batch_id="BATCH-TEST-VAX-01",
            drug_name="mRNA Vaccine",
            manufacturer="Bharat Biotech",
            checkpoint_location="Unrefrigerated Transit",
            telemetry_temp_c=22.0,  # Excursion!
            humidity_percent=80.0,
            is_tampered_attempt=True,
        )
        assert succ_e is False
