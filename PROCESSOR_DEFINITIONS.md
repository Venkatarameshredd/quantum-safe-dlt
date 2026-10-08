# AegisLedger-Q: Processor Definitions & Hardware Specifications

## 1. Classical Processing Tier (Validator Node Nodes)
- **Host Architecture:** x86_64 / ARM64 Multi-Core Systems
- **Reference CPU:** AMD Ryzen 9 / Intel Xeon E5 / Apple Silicon (M-series)
- **RAM Minimum:** 16 GB DDR4/DDR5 ECC RAM (32 GB recommended for high-throughput validator pools)
- **Cryptographic Coprocessor:** Hardware AES-NI and SHA-3 / SHAKE acceleration extensions
- **Operating Environments:** Ubuntu 22.04 LTS / 24.04 LTS, Windows 11 Enterprise, RHEL 9

---

## 2. Quantum Processing Unit (QPU) Specifications & Simulation Topology

### A. QPU Backend Architecture (Qiskit 2.4 / IBM Quantum Eagle & Heron Compatibility)
- **Architecture Family:** Heavy-Hex Superconducting Transmon Lattice
- **Primary Processor Target:** IBM Quantum Heron (`ibm_torino` / `ibm_fez`) / FakeHeron Simulation Backends
- **Qubit Allocation:** 4 Physical Qubits allocated in a circular ring topology with nearest-neighbor coupling:
  - $Q_0 \leftrightarrow Q_1 \leftrightarrow Q_2 \leftrightarrow Q_3 \leftrightarrow Q_0$
- **Single-Qubit Gate Set:** $\{R_y(\theta), R_z(\phi), X, H\}$
  - Average Gate Fidelity: $> 99.94\%$
  - Average Gate Duration: $20\text{ ns}$
- **Two-Qubit Entangling Gates:** $\{CZ, CX\ (\text{CNOT})\}$
  - Entangling Gate Fidelity: $> 99.40\%$
  - Coherence Times: $T_1 \approx 280\ \mu\text{s}$, $T_2 \approx 210\ \mu\text{s}$

### B. Optical Quantum Channel / QKD BB84 Interface
- **Wavelength Target:** $1550\text{ nm}$ (Standard telecom C-band for dense wavelength division multiplexing fiber)
- **Photon Source:** Attenuated Weak Coherent Pulses (WCP) with mean photon number $\mu = 0.1$
- **Polarization Modulation:** High-speed Electro-Optic Modulators (EOM) for rectilinear ($0^\circ, 90^\circ$) and diagonal ($45^\circ, 135^\circ$) basis encoding
- **Single-Photon Detectors:** Superconducting Nanowire Single-Photon Detectors (SNSPD)
  - Quantum Detection Efficiency: $> 85\%$
  - Dark Count Rate: $< 10\text{ Hz}$
  - Jitter: $< 25\text{ ps}$
- **QBER Abort Threshold:** $\eta_{\text{abort}} = 11.0\%$ (Theoretical limit for intercept-resend attack interception)

---

## 3. Cryptographic Co-Processor Architecture (NIST FIPS 204 ML-DSA)
- **Lattice Parameters:**
  - Ring Modulus: $q = 8,380,417$
  - Polynomial Degree: $n = 256$
  - Ring Algebra: $\mathcal{R}_q = \mathbb{Z}_q[X]/(X^n + 1)$
  - Matrix Dimensions: $k = 6, l = 5$ (ML-DSA-65 / Dilithium Level 3)
- **Security Strength:** Category 3 (Equivalent to NIST AES-192 security level against classical and quantum cryptanalysis)
- **Public Key Size:** 1,952 bytes
- **Signature Size:** 3,309 bytes
- **Collision-Resistant Hash:** Keccak-based SHAKE-256 and SHA3-256 (NIST FIPS 202)
