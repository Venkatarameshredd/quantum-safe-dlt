"""FastAPI REST Service for Quantum-Safe Distributed Ledger."""
from __future__ import annotations

from typing import Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import config
from .blockchain import Block, Transaction
from .crypto_pqc import get_pqc_engine
from .qkd_qiskit import get_qkd_engine
from .qml_detector import get_qml_engine
from .service import get_service

app = FastAPI(
    title="AegisLedger-Q: Quantum-Safe DLT for AP Land Records & Supply Chains",
    description="REST API powered by NIST ML-DSA Lattice Cryptography, Qiskit BB84 QKD, and 4-Qubit VQC Fraud Detection.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Pydantic Request / Response Schemas
# ==========================================
class LandRecordRequest(BaseModel):
    district: str = Field(default="Guntur", example="Guntur")
    mandal: str = Field(default="Mangalagiri", example="Mangalagiri")
    village: str = Field(default="Navuluru", example="Navuluru")
    survey_number: str = Field(default="244/1A", example="244/1A")
    area_cents: float = Field(default=45.5, example=45.5)
    pattadar_name: str = Field(default="K. Venkata Ramana", example="K. Venkata Ramana")
    land_classification: str = Field(default="Agricultural / Wet Land", example="Agricultural / Wet Land")
    simulate_fraud_attempt: bool = Field(default=False, example=False)


class PharmaLogRequest(BaseModel):
    batch_id: str = Field(default="BATCH-AP-VAX-902", example="BATCH-AP-VAX-902")
    drug_name: str = Field(default="COVID-19 mRNA Vaccine", example="COVID-19 mRNA Vaccine")
    manufacturer: str = Field(default="Bharat Biotech", example="Bharat Biotech")
    checkpoint_location: str = Field(default="Vijayawada Central Hub", example="Vijayawada Central Hub")
    telemetry_temp_c: float = Field(default=4.5, example=4.5)
    humidity_percent: float = Field(default=46.0, example=46.0)
    simulate_fraud_attempt: bool = Field(default=False, example=False)


class QKDSimulationRequest(BaseModel):
    alice_id: str = Field(default="NODE_AP_AMARAVATI", example="NODE_AP_AMARAVATI")
    bob_id: str = Field(default="NODE_AP_VIZAG", example="NODE_AP_VIZAG")
    n_bits: int = Field(default=64, example=64)
    simulate_eve: bool = Field(default=False, example=False)


class QMLEvaluationRequest(BaseModel):
    features: list[float] = Field(default=[0.05, 0.08, 0.02, 0.01], example=[0.05, 0.08, 0.02, 0.01])


class MineBlockRequest(BaseModel):
    peer_validator_id: str = Field(default="NODE_AP_REVENUE_HQ_VIZAG", example="NODE_AP_REVENUE_HQ_VIZAG")
    simulate_eavesdropping: bool = Field(default=False, example=False)


# ==========================================
# API Routes
# ==========================================
@app.get("/api/health")
def get_health() -> dict[str, Any]:
    svc = get_service()
    return {
        "status": "HEALTHY",
        "service": "AegisLedger-Q Quantum-Safe DLT",
        "node_id": svc.ledger.node_id,
        "pqc_engine": svc.pqc.scheme_name,
        "qkd_engine": "Qiskit 2.4 BB84 Protocol",
        "qml_engine": "4-Qubit Variational Quantum Classifier (VQC)",
    }


@app.get("/api/ledger/summary")
def get_ledger_summary() -> dict[str, Any]:
    svc = get_service()
    return svc.ledger.get_ledger_summary()


@app.get("/api/ledger/blocks")
def get_all_blocks() -> list[dict[str, Any]]:
    svc = get_service()
    return [
        {
            "index": b.index,
            "timestamp": b.timestamp,
            "previous_hash": b.previous_hash,
            "merkle_root": b.merkle_root,
            "block_hash": b.block_hash,
            "validator_node": b.validator_node,
            "qkd_session_key_id": b.qkd_session_key_id,
            "tx_count": len(b.transactions),
            "transactions": b.transactions,
            "validator_pqc_signature": b.validator_pqc_signature,
        }
        for b in svc.ledger.chain
    ]


@app.get("/api/ledger/audit")
def run_ledger_audit() -> dict[str, Any]:
    svc = get_service()
    return svc.run_security_audit()


@app.post("/api/land/register")
def register_land(req: LandRecordRequest) -> dict[str, Any]:
    svc = get_service()
    success, msg, detail = svc.register_ap_land_record(
        district=req.district,
        mandal=req.mandal,
        village=req.village,
        survey_number=req.survey_number,
        area_cents=req.area_cents,
        pattadar_name=req.pattadar_name,
        land_classification=req.land_classification,
        is_tampered_attempt=req.simulate_fraud_attempt,
    )
    return {"success": success, "message": msg, "transaction_detail": detail}


@app.post("/api/pharma/log")
def log_pharma_checkpoint(req: PharmaLogRequest) -> dict[str, Any]:
    svc = get_service()
    success, msg, detail = svc.log_pharma_supply_chain_step(
        batch_id=req.batch_id,
        drug_name=req.drug_name,
        manufacturer=req.manufacturer,
        checkpoint_location=req.checkpoint_location,
        telemetry_temp_c=req.telemetry_temp_c,
        humidity_percent=req.humidity_percent,
        is_tampered_attempt=req.simulate_fraud_attempt,
    )
    return {"success": success, "message": msg, "batch_detail": detail}


@app.post("/api/ledger/mine")
def mine_block(req: MineBlockRequest) -> dict[str, Any]:
    svc = get_service()
    success, msg, block = svc.mine_pending_block(
        peer_node_id=req.peer_validator_id,
        simulate_eavesdropping=req.simulate_eavesdropping,
    )
    if not success:
        return {"success": False, "message": msg, "block": None}
    return {
        "success": True,
        "message": msg,
        "block_index": block.index,
        "block_hash": block.block_hash,
        "merkle_root": block.merkle_root,
        "qkd_session_key_id": block.qkd_session_key_id,
        "tx_count": len(block.transactions),
    }


@app.post("/api/qkd/simulate")
def simulate_qkd_channel(req: QKDSimulationRequest) -> dict[str, Any]:
    qkd = get_qkd_engine()
    session = qkd.negotiate_session_key(
        alice_id=req.alice_id,
        bob_id=req.bob_id,
        simulate_eve=req.simulate_eve,
    )
    return {
        "key_id": session.key_id,
        "alice_id": session.alice_id,
        "bob_id": session.bob_id,
        "is_secure": session.is_secure,
        "qber": round(session.qber, 4),
        "qber_percent": f"{session.qber * 100:.2f}%",
        "threshold_percent": f"{config.QKD_QBER_THRESHOLD * 100:.1f}%",
        "key_length_bits": session.key_length_bits,
        "key_hex_sample": session.key_hex[:32] + "..." if session.key_hex else "N/A",
        "eve_detected": session.eve_detected,
        "abort_reason": session.abort_reason,
        "exchange_latency_ms": session.exchange_latency_ms,
        "raw_bit_count": len(session.telemetry.get("alice_bits", [])),
        "sifted_bit_count": len(session.telemetry.get("sifted_bits", [])),
    }


@app.post("/api/qml/evaluate")
def evaluate_transaction_risk(req: QMLEvaluationRequest) -> dict[str, Any]:
    qml = get_qml_engine()
    assessment = qml.evaluate_transaction(req.features)
    return {
        "is_fraud": assessment.is_fraud,
        "risk_score": round(assessment.risk_score, 4),
        "classification": assessment.classification,
        "triage_action": assessment.triage_action,
        "quantum_expectations": [round(x, 4) for x in assessment.quantum_expectations],
        "risk_factors": assessment.risk_factors,
        "latency_ms": round(assessment.latency_ms, 2),
    }


@app.get("/api/qml/metrics")
def get_qml_benchmark_metrics() -> dict[str, Any]:
    qml = get_qml_engine()
    return qml.metrics


@app.post("/api/pqc/keygen")
def generate_pqc_keypair() -> dict[str, Any]:
    pqc = get_pqc_engine()
    pub, priv = pqc.generate_keypair()
    return {
        "algorithm": pqc.scheme_name,
        "public_key_b64": pub.hex(),
        "private_key_length_bytes": len(priv),
        "public_key_length_bytes": len(pub),
        "security_level": "NIST Post-Quantum Level 3 (AES-192 equivalent)",
    }
