"""Domain Services for AP Land Records, Pharma Supply Chain, and Ledger Management."""
from __future__ import annotations

import hashlib
import random
import time
import uuid
from typing import Any, Optional

from . import config
from .blockchain import Block, QuantumSafeBlockchain, Transaction, get_ledger
from .crypto_pqc import get_pqc_engine
from .qkd_qiskit import get_qkd_engine
from .qml_detector import get_qml_engine


class QuantumDLTService:
    """High-level application coordinator managing land titles, pharma provenance, and security."""

    def __init__(self, ledger: Optional[QuantumSafeBlockchain] = None):
        self.ledger = ledger or get_ledger()
        self.pqc = get_pqc_engine()
        self.qkd = get_qkd_engine()
        self.qml = get_qml_engine()

        # Generate sample registrar and pharma authority keys
        self.registrar_pubkey, self.registrar_privkey = self.pqc.generate_keypair()
        self.pharma_pubkey, self.pharma_privkey = self.pqc.generate_keypair()

    # ==========================================
    # 1. Andhra Pradesh Land Registry (Bhudhaar)
    # ==========================================
    def register_ap_land_record(
        self,
        district: str,
        mandal: str,
        village: str,
        survey_number: str,
        area_cents: float,
        pattadar_name: str,
        land_classification: str = "Agricultural / Wet Land",
        is_tampered_attempt: bool = False,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Register or transfer an Andhra Pradesh land record secured by Bhudhaar 14-digit ID."""
        bhudhaar_id = f"AP-{district[:3].upper()}-{random.randint(10000000, 99999999)}"
        tx_id = f"TX-LAND-{uuid.uuid4().hex[:12].upper()}"

        # Coordinate synthesis for cadastral mapping
        lat_base, lon_base = config.AP_DISTRICT_COORDINATES.get(district, (16.5062, 80.6480))
        lat = lat_base + random.uniform(-0.02, 0.02)
        lon = lon_base + random.uniform(-0.02, 0.02)
        survey_hash = hashlib.sha256(f"{district}_{mandal}_{village}_{survey_number}".encode()).hexdigest()

        # Set risk factors (high if simulating fraud attempt)
        if is_tampered_attempt:
            boundary_discrepancy = random.uniform(0.70, 0.95)
            transfer_velocity = random.uniform(0.65, 0.90)
            coord_divergence = random.uniform(0.70, 0.92)
            notes = "COLLUSION ALERT: Cadastral boundary coordinates conflict with satellite records!"
        else:
            boundary_discrepancy = random.uniform(0.01, 0.12)
            transfer_velocity = random.uniform(0.01, 0.15)
            coord_divergence = random.uniform(0.01, 0.08)
            notes = "Clear title verified via AP Webland cadastral survey database."

        payload = {
            "bhudhaar_id": bhudhaar_id,
            "district": district,
            "mandal": mandal,
            "village": village,
            "survey_number": survey_number,
            "area_cents": area_cents,
            "pattadar_name": pattadar_name,
            "land_classification": land_classification,
            "coordinates": {"latitude": round(lat, 6), "longitude": round(lon, 6)},
            "cadastral_survey_hash": survey_hash,
            "boundary_discrepancy_score": boundary_discrepancy,
            "transfer_velocity_score": transfer_velocity,
            "coordinate_hash_divergence": coord_divergence,
            "notes": notes,
        }

        tx = Transaction(
            tx_id=tx_id,
            tx_type="LAND_RECORD",
            sender_id=f"AP_REGISTRAR_{mandal.upper()}",
            recipient_id=f"PATTADAR_{pattadar_name.replace(' ', '_').upper()}",
            payload=payload,
            timestamp=time.time(),
        )

        # Sign transaction with Registrar Post-Quantum secret key
        tx.sign_transaction(self.pqc, self.registrar_privkey, self.registrar_pubkey)

        # Ingest into ledger with QML screening
        success, message, risk_assess = self.ledger.submit_transaction(
            transaction=tx,
            feature_vector=[boundary_discrepancy, transfer_velocity, coord_divergence, 0.02],
        )

        detail = {
            "tx_id": tx_id,
            "bhudhaar_id": bhudhaar_id,
            "pattadar_name": pattadar_name,
            "risk_score": risk_assess.risk_score if risk_assess else 0.0,
            "quantum_expectations": risk_assess.quantum_expectations if risk_assess else [],
            "status": tx.status,
            "pqc_signature_valid": True,
            "message": message,
        }
        return success, message, detail

    # ==========================================
    # 2. Pharma Cold-Chain Provenance Tracking
    # ==========================================
    def log_pharma_supply_chain_step(
        self,
        batch_id: str,
        drug_name: str,
        manufacturer: str,
        checkpoint_location: str,
        telemetry_temp_c: float,
        humidity_percent: float,
        is_tampered_attempt: bool = False,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Log pharmaceutical supply chain telemetry with cold-chain provenance validation."""
        tx_id = f"TX-PHARMA-{uuid.uuid4().hex[:12].upper()}"

        if is_tampered_attempt or telemetry_temp_c > 8.0 or telemetry_temp_c < 2.0:
            temp_excursion_score = random.uniform(0.75, 0.95)
            delay_score = random.uniform(0.60, 0.85)
            rfid_tamper_score = random.uniform(0.70, 0.90)
            notes = f"COLD-CHAIN VIOLATION: Current temp {telemetry_temp_c}°C exceeds allowable range (2-8°C)!"
        else:
            temp_excursion_score = random.uniform(0.02, 0.10)
            delay_score = random.uniform(0.01, 0.12)
            rfid_tamper_score = random.uniform(0.01, 0.05)
            notes = f"Optimal cold storage maintained at {telemetry_temp_c}°C."

        payload = {
            "batch_id": batch_id,
            "drug_name": drug_name,
            "manufacturer": manufacturer,
            "checkpoint_location": checkpoint_location,
            "telemetry_temp_c": telemetry_temp_c,
            "humidity_percent": humidity_percent,
            "temp_excursion_score": temp_excursion_score,
            "transit_delay_score": delay_score,
            "rfid_seal_tamper_score": rfid_tamper_score,
            "notes": notes,
        }

        tx = Transaction(
            tx_id=tx_id,
            tx_type="PHARMA_SUPPLY_CHAIN",
            sender_id=f"FACILITY_{checkpoint_location.upper()}",
            recipient_id=f"NEXT_HOP_DISTRIBUTOR",
            payload=payload,
            timestamp=time.time(),
        )

        tx.sign_transaction(self.pqc, self.pharma_privkey, self.pharma_pubkey)

        success, message, risk_assess = self.ledger.submit_transaction(
            transaction=tx,
            feature_vector=[temp_excursion_score, delay_score, rfid_tamper_score, 0.03],
        )

        detail = {
            "tx_id": tx_id,
            "batch_id": batch_id,
            "drug_name": drug_name,
            "risk_score": risk_assess.risk_score if risk_assess else 0.0,
            "quantum_expectations": risk_assess.quantum_expectations if risk_assess else [],
            "status": tx.status,
            "notes": notes,
            "message": message,
        }
        return success, message, detail

    # ==========================================
    # 3. Block Mining & QKD Inter-Validator Gossip
    # ==========================================
    def mine_pending_block(
        self,
        peer_node_id: str = "NODE_AP_REVENUE_HQ_VIZAG",
        simulate_eavesdropping: bool = False,
    ) -> tuple[bool, str, Optional[Block]]:
        """Forge a block protected by BB84 QKD channel negotiation."""
        block, msg = self.ledger.mine_block(
            peer_validator_id=peer_node_id,
            simulate_eavesdropping=simulate_eavesdropping,
        )
        if block is None:
            return False, msg, None
        return True, msg, block

    # ==========================================
    # 4. Cryptographic Tamper Audit
    # ==========================================
    def run_security_audit(self) -> dict[str, Any]:
        """Perform comprehensive cryptographic audit of the ledger."""
        return self.ledger.audit_chain()

    # ==========================================
    # 5. Seed Initial Demo Data
    # ==========================================
    def seed_initial_demo_records(self) -> None:
        """Seed a clean initial state with legitimate and committed transactions."""
        if len(self.ledger.chain) > 1:
            return  # Already seeded

        # Register 3 legitimate land records across AP
        records = [
            ("Guntur", "Mangalagiri", "Navuluru", "244/1A", 45.5, "K. Venkata Ramana", "Wet Land"),
            ("Visakhapatnam", "Anandapuram", "Vemulavalasa", "108/3B", 82.0, "P. Lakshmi Devi", "Dry Land"),
            ("Krishna", "Gannavaram", "Kesarapalle", "312/2", 60.0, "M. Subba Rao", "Agricultural Land"),
        ]
        for dist, mandal, vill, s_no, cents, name, l_type in records:
            self.register_ap_land_record(dist, mandal, vill, s_no, cents, name, l_type, False)

        # Add 2 pharma batches
        self.log_pharma_supply_chain_step(
            "BATCH-AP-VAX-901",
            "COVID-19 mRNA Booster Vaccine",
            "Bharat Biotech / Hyderabad-Vizag Hub",
            "Vijayawada Central Cold Hub",
            4.2,
            45.0,
            False,
        )
        self.log_pharma_supply_chain_step(
            "BATCH-AP-ONCO-404",
            "Trastuzumab Oncology Monoclonal Antibody",
            "Dr. Reddy's Laboratories",
            "Guntur District Hospital Depot",
            3.8,
            42.0,
            False,
        )

        # Forge into Block #1
        self.mine_pending_block("NODE_AP_REVENUE_HQ_VIZAG", False)


# Singleton service instance
_GLOBAL_SERVICE: Optional[QuantumDLTService] = None

def get_service() -> QuantumDLTService:
    global _GLOBAL_SERVICE
    if _GLOBAL_SERVICE is None:
        _GLOBAL_SERVICE = QuantumDLTService()
        _GLOBAL_SERVICE.seed_initial_demo_records()
    return _GLOBAL_SERVICE
