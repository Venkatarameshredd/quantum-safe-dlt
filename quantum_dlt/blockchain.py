"""Quantum-Safe Distributed Ledger Core for Land Records & Supply Chains.

Integrates:
1. NIST Post-Quantum Cryptography (ML-DSA / Dilithium) signatures on every transaction & block.
2. Qiskit BB84 Quantum Key Distribution (QKD) session keys securing validator gossip channels.
3. 4-Qubit Variational Quantum Classifier (VQC) fraud detection intercepting tampered records.
4. Tamper-evident Merkle-tree hashing with SHA-256 / SHAKE-256.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, List, Optional

from . import config
from .crypto_pqc import PQCDigitalSignatureScheme, PQCSignature, PQCVerificationResult, get_pqc_engine
from .qkd_qiskit import BB84QKDProtocol, QKDSessionKey, get_qkd_engine
from .qml_detector import QuantumFraudDetectorEngine, TransactionRiskAssessment, get_qml_engine


def calculate_merkle_root(transactions_data: list[str]) -> str:
    """Compute Merkle Tree Root hash for a list of transaction serialized strings."""
    if not transactions_data:
        return hashlib.sha256(b"EMPTY_TRANSACTION_TREE").hexdigest()

    hashes = [hashlib.sha256(tx.encode("utf-8")).hexdigest() for tx in transactions_data]

    while len(hashes) > 1:
        if len(hashes) % 2 != 0:
            hashes.append(hashes[-1])
        new_level = []
        for i in range(0, len(hashes), 2):
            combined = (hashes[i] + hashes[i + 1]).encode("utf-8")
            new_level.append(hashlib.sha256(combined).hexdigest())
        hashes = new_level

    return hashes[0]


@dataclass
class Transaction:
    """Distributed Ledger Transaction representing Land Deeds, Pharma Batches, or Certificates."""
    tx_id: str
    tx_type: str                         # "LAND_RECORD", "PHARMA_SUPPLY_CHAIN", "GOVT_CERTIFICATE"
    sender_id: str                       # e.g., "AP_REVENUE_DEPT_AMARAVATI", "PHARMA_MANUFACTURER_HYD"
    recipient_id: str                    # e.g., "PATTADAR_FARMER_GUNTUR", "DISTRIBUTOR_VIZAG"
    payload: dict[str, Any]              # Domain-specific payload (Bhudhaar, Cadastral, Batch, etc.)
    timestamp: float = field(default_factory=time.time)
    pqc_signature: Optional[dict[str, Any]] = None  # Serialized PQCSignature
    sender_pqc_pubkey: Optional[str] = None         # Base64 public key
    risk_assessment: Optional[dict[str, Any]] = None  # Quantum VQC fraud evaluation
    is_screened_by_qml: bool = False
    status: str = "PENDING"              # "PENDING", "APPROVED", "REJECTED_FRAUD", "COMMITTED"

    def compute_hash(self) -> str:
        """Deterministically hash the canonical transaction body (excluding signature and status)."""
        body = {
            "tx_id": self.tx_id,
            "tx_type": self.tx_type,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "payload": self.payload,
            "timestamp": round(self.timestamp, 4),
        }
        canonical_str = json.dumps(body, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def sign_transaction(self, pqc_engine: PQCDigitalSignatureScheme, secret_key: bytes, public_key: bytes) -> None:
        """Sign transaction using Post-Quantum lattice cryptography."""
        tx_hash = self.compute_hash()
        sig = pqc_engine.sign(tx_hash.encode("utf-8"), secret_key, public_key)
        self.pqc_signature = asdict(sig)
        self.sender_pqc_pubkey = sig.public_key_b64

    def verify_signature(self, pqc_engine: PQCDigitalSignatureScheme) -> PQCVerificationResult:
        """Verify the post-quantum signature against the transaction hash."""
        if not self.pqc_signature:
            return PQCVerificationResult(
                is_valid=False,
                algorithm="NONE",
                details="No signature present on transaction.",
                latency_ms=0.0,
            )
        tx_hash = self.compute_hash()
        sig = PQCSignature(**self.pqc_signature)
        return pqc_engine.verify(tx_hash.encode("utf-8"), sig)


@dataclass
class Block:
    """Immutable Ledger Block sealed with Post-Quantum signature and QKD validator session key."""
    index: int
    timestamp: float
    transactions: list[dict[str, Any]]
    previous_hash: str
    merkle_root: str
    validator_node: str
    qkd_session_key_id: str               # ID of QKD key used to authorize inter-validator gossip
    qkd_auth_tag: str                     # Keyed HMAC/digest verifying quantum channel integrity
    quantum_entropy_seed: str = ""        # 256-bit certified quantum entropy seed (PoQE consensus)
    block_hash: str = ""
    validator_pqc_signature: Optional[dict[str, Any]] = None
    validator_pqc_pubkey: Optional[str] = None

    def compute_hash(self) -> str:
        """Compute SHA-256 block hash over all block contents except the signature."""
        block_dict = {
            "index": self.index,
            "timestamp": round(self.timestamp, 4),
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "validator_node": self.validator_node,
            "qkd_session_key_id": self.qkd_session_key_id,
            "qkd_auth_tag": self.qkd_auth_tag,
            "quantum_entropy_seed": self.quantum_entropy_seed,
        }
        canonical_str = json.dumps(block_dict, sort_keys=True)
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def seal_and_sign(
        self,
        pqc_engine: PQCDigitalSignatureScheme,
        secret_key: bytes,
        public_key: bytes,
    ) -> str:
        """Seal the block by calculating its hash and appending validator's PQC signature."""
        self.block_hash = self.compute_hash()
        sig = pqc_engine.sign(self.block_hash.encode("utf-8"), secret_key, public_key)
        self.validator_pqc_signature = asdict(sig)
        self.validator_pqc_pubkey = sig.public_key_b64
        return self.block_hash

    def verify_block_signature(self, pqc_engine: PQCDigitalSignatureScheme) -> PQCVerificationResult:
        """Verify validator PQC signature on block hash."""
        if not self.validator_pqc_signature:
            return PQCVerificationResult(
                is_valid=False,
                algorithm="NONE",
                details="No validator PQC signature on block.",
                latency_ms=0.0,
            )
        sig = PQCSignature(**self.validator_pqc_signature)
        return pqc_engine.verify(self.block_hash.encode("utf-8"), sig)


class QuantumSafeBlockchain:
    """Full-featured Quantum-Safe Distributed Ledger implementation."""

    def __init__(self, node_id: str = "NODE_AP_SECRETARIAT_01"):
        self.node_id = node_id
        self.chain: list[Block] = []
        self.pending_transactions: list[Transaction] = []
        self.rejected_transactions: list[Transaction] = []
        self.pqc = get_pqc_engine()
        self.qkd = get_qkd_engine()
        self.qml = get_qml_engine()

        # Generate validator node PQC keypair
        self.validator_pubkey, self.validator_privkey = self.pqc.generate_keypair()

        # Initialize Genesis Block
        self._create_genesis_block()

    def _create_genesis_block(self) -> Block:
        """Mint the tamper-evident Genesis Block with foundational state."""
        genesis_qkd = self.qkd.negotiate_session_key(alice_id="GENESIS_ORACLE", bob_id=self.node_id)
        merkle = calculate_merkle_root([])

        genesis_block = Block(
            index=0,
            timestamp=1700000000.0,
            transactions=[{
                "tx_id": "TX_GENESIS_000000",
                "tx_type": "GENESIS_ROOT",
                "sender_id": "AP_STATE_QUANTUM_REGISTRY",
                "recipient_id": "ALL_NODES",
                "payload": {
                    "network": config.NETWORK_NAME,
                    "genesis_message": "Quantum-Safe DLT for AP Land Records & Supply Chains initialized.",
                    "security_standard": "NIST FIPS 204 ML-DSA Lattice Cryptography + BB84 QKD + 4-Qubit VQC",
                },
                "status": "COMMITTED",
            }],
            previous_hash="0" * 64,
            merkle_root=merkle,
            validator_node=self.node_id,
            qkd_session_key_id=genesis_qkd.key_id,
            qkd_auth_tag=hashlib.sha256(genesis_qkd.key_hex.encode()).hexdigest()[:32],
            quantum_entropy_seed=genesis_qkd.quantum_entropy_hex or hashlib.sha3_256(b"GENESIS_QUANTUM_ENTROPY").hexdigest(),
        )
        genesis_block.seal_and_sign(self.pqc, self.validator_privkey, self.validator_pubkey)
        self.chain.append(genesis_block)
        return genesis_block

    def submit_transaction(
        self,
        transaction: Transaction,
        feature_vector: Optional[list[float]] = None,
        auto_sign_secret: Optional[bytes] = None,
        auto_sign_public: Optional[bytes] = None,
    ) -> tuple[bool, str, Optional[TransactionRiskAssessment]]:
        """Screen and ingest an incoming transaction with PQC verification and QML fraud detection."""
        # 1. Sign if auto-sign keys provided
        if auto_sign_secret and auto_sign_public and not transaction.pqc_signature:
            transaction.sign_transaction(self.pqc, auto_sign_secret, auto_sign_public)

        # 2. Verify Post-Quantum Signature
        if transaction.pqc_signature:
            v_res = transaction.verify_signature(self.pqc)
            if not v_res.is_valid:
                transaction.status = "REJECTED_INVALID_PQC_SIGNATURE"
                self.rejected_transactions.append(transaction)
                return False, f"Signature rejected: {v_res.details}", None

        # 3. Extract Feature Vector for QML Fraud Classifier
        if feature_vector is None:
            feature_vector = self._extract_features(transaction)

        # 4. Evaluate via 4-Qubit Variational Quantum Classifier (VQC)
        risk_assess = self.qml.evaluate_transaction(feature_vector)
        transaction.risk_assessment = asdict(risk_assess)
        transaction.is_screened_by_qml = True

        if risk_assess.is_fraud:
            transaction.status = "REJECTED_FRAUD"
            self.rejected_transactions.append(transaction)
            return (
                False,
                f"Blocked by Quantum VQC Classifier (Risk: {risk_assess.risk_score:.4f}, Factors: {', '.join(risk_assess.risk_factors)})",
                risk_assess,
            )

        # 5. Approve transaction into pending mempool
        transaction.status = "APPROVED"
        self.pending_transactions.append(transaction)
        return (
            True,
            f"Transaction approved and queued into mempool (Quantum Risk: {risk_assess.risk_score:.4f})",
            risk_assess,
        )

    def _extract_features(self, tx: Transaction) -> list[float]:
        """Synthesize normalized 4-dimensional feature vector from transaction attributes."""
        p = tx.payload
        # Feature 0: Boundary discrepancy or cold-chain temp excursion
        if tx.tx_type == "LAND_RECORD":
            f0 = float(p.get("boundary_discrepancy_score", 0.05))
            f1 = float(p.get("transfer_velocity_score", 0.08))
            f2 = float(p.get("coordinate_hash_divergence", 0.02))
            f3 = 0.0 if tx.pqc_signature else 0.85
        elif tx.tx_type == "PHARMA_SUPPLY_CHAIN":
            temp = float(p.get("telemetry_temp_c", 4.0))
            f0 = min(1.0, max(0.0, abs(temp - 4.0) / 10.0))  # deviation from 2-8 C
            f1 = float(p.get("transit_delay_score", 0.05))
            f2 = float(p.get("rfid_seal_tamper_score", 0.03))
            f3 = 0.0 if tx.pqc_signature else 0.90
        else:
            f0 = float(p.get("risk_factor_0", 0.05))
            f1 = float(p.get("risk_factor_1", 0.05))
            f2 = float(p.get("risk_factor_2", 0.05))
            f3 = 0.05
        return [f0, f1, f2, f3]

    def mine_block(
        self,
        peer_validator_id: str = "NODE_AP_REVENUE_HQ_VIZAG",
        simulate_eavesdropping: bool = False,
    ) -> tuple[Optional[Block], str]:
        """Forge and commit a new block sealed with QKD session key and PQC validator signature."""
        if not self.pending_transactions:
            return None, "No transactions in mempool to commit."

        # 1. Establish Quantum Key Distribution (QKD) Channel between validators
        qkd_session = self.qkd.negotiate_session_key(
            alice_id=self.node_id,
            bob_id=peer_validator_id,
            simulate_eve=simulate_eavesdropping,
        )

        if not qkd_session.is_secure:
            return (
                None,
                f"Block forging aborted! QKD channel compromised: {qkd_session.abort_reason} (QBER: {qkd_session.qber*100:.1f}%)",
            )

        # 2. Serialize approved transactions
        tx_dicts = []
        serialized_strings = []
        for tx in self.pending_transactions:
            tx.status = "COMMITTED"
            d = asdict(tx)
            tx_dicts.append(d)
            serialized_strings.append(json.dumps(d, sort_keys=True))

        merkle_root = calculate_merkle_root(serialized_strings)
        previous_block = self.chain[-1]

        # 3. Construct Block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=tx_dicts,
            previous_hash=previous_block.block_hash,
            merkle_root=merkle_root,
            validator_node=self.node_id,
            qkd_session_key_id=qkd_session.key_id,
            qkd_auth_tag=hashlib.sha256(qkd_session.key_hex.encode()).hexdigest()[:32],
            quantum_entropy_seed=qkd_session.quantum_entropy_hex,
        )

        # 4. Seal & Sign with PQC Signature
        new_block.seal_and_sign(self.pqc, self.validator_privkey, self.validator_pubkey)

        # 5. Append to ledger and drain mempool
        self.chain.append(new_block)
        self.pending_transactions.clear()

        return new_block, f"Block #{new_block.index} forged with {len(tx_dicts)} transactions! (PoQE Entropy: {qkd_session.quantum_entropy_hex[:16]}...)"

    def audit_chain(self) -> dict[str, Any]:
        """Verify complete cryptographic, hash-chain, PoQE, and post-quantum integrity of the ledger."""
        t0 = time.perf_counter()
        audit_results = {
            "total_blocks": len(self.chain),
            "is_tamper_free": True,
            "corrupted_blocks": [],
            "signature_failures": [],
            "hash_mismatches": [],
            "merkle_mismatches": [],
            "poqe_failures": [],
            "audit_latency_ms": 0.0,
        }

        for i in range(len(self.chain)):
            block = self.chain[i]

            # 1. Check recalculation of block hash
            expected_hash = block.compute_hash()
            if block.block_hash != expected_hash:
                audit_results["is_tamper_free"] = False
                audit_results["hash_mismatches"].append({
                    "block_index": i,
                    "recorded_hash": block.block_hash,
                    "computed_hash": expected_hash,
                })

            # 2. Check previous hash continuity
            if i > 0:
                prev_block = self.chain[i - 1]
                if block.previous_hash != prev_block.block_hash:
                    audit_results["is_tamper_free"] = False
                    audit_results["corrupted_blocks"].append({
                        "block_index": i,
                        "expected_prev": prev_block.block_hash,
                        "found_prev": block.previous_hash,
                    })

            # 3. Check Merkle Root consistency
            tx_strings = [json.dumps(tx, sort_keys=True) for tx in block.transactions]
            computed_merkle = calculate_merkle_root(tx_strings) if i > 0 else block.merkle_root
            if i > 0 and block.merkle_root != computed_merkle:
                audit_results["is_tamper_free"] = False
                audit_results["merkle_mismatches"].append({
                    "block_index": i,
                    "expected_merkle": computed_merkle,
                    "found_merkle": block.merkle_root,
                })

            # 4. Check Validator PQC Signature
            sig_res = block.verify_block_signature(self.pqc)
            if not sig_res.is_valid:
                audit_results["is_tamper_free"] = False
                audit_results["signature_failures"].append({
                    "block_index": i,
                    "reason": sig_res.details,
                })

            # 5. Check Proof-of-Quantum-Entropy (PoQE) Consensus Seed
            if i > 0 and (not block.quantum_entropy_seed or len(block.quantum_entropy_seed) < 32):
                audit_results["is_tamper_free"] = False
                audit_results["poqe_failures"].append({
                    "block_index": i,
                    "reason": "Missing or degenerate quantum entropy seed in block header.",
                })

        audit_results["audit_latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return audit_results

    def get_ledger_summary(self) -> dict[str, Any]:
        """Summarize current state of the ledger."""
        total_txs = sum(len(b.transactions) for b in self.chain)
        return {
            "network_name": config.NETWORK_NAME,
            "validator_node": self.node_id,
            "consensus_mechanism": config.CONSENSUS_MECHANISM,
            "total_blocks": len(self.chain),
            "total_committed_txs": total_txs,
            "pending_mempool_txs": len(self.pending_transactions),
            "rejected_fraud_txs": len(self.rejected_transactions),
            "latest_block_hash": self.chain[-1].block_hash if self.chain else "None",
            "pqc_security_level": self.pqc.scheme_name,
            "qkd_protocol": config.QKD_PROTOCOL,
            "qml_classifier": "Qiskit 4-Qubit Variational Quantum Classifier (VQC)",
        }

    def export_to_json(self, filepath: Any = None) -> str:
        """Export ledger chain and mempool state to JSON."""
        from pathlib import Path
        target = Path(filepath or (config.ARTIFACTS_DIR / "ledger_chain.json"))
        data = {
            "node_id": self.node_id,
            "blocks": [asdict(b) for b in self.chain],
            "pending_count": len(self.pending_transactions),
            "rejected_count": len(self.rejected_transactions),
        }
        json_str = json.dumps(data, indent=2)
        target.write_text(json_str)
        return json_str


# Singleton ledger instance
_GLOBAL_LEDGER: Optional[QuantumSafeBlockchain] = None

def get_ledger() -> QuantumSafeBlockchain:
    global _GLOBAL_LEDGER
    if _GLOBAL_LEDGER is None:
        _GLOBAL_LEDGER = QuantumSafeBlockchain()
    return _GLOBAL_LEDGER
