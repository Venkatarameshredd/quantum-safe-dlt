@echo off
title AegisLedger-Q Quantum-Safe DLT Command Center
color 0B
echo ===============================================================================
echo     AEGISLEDGER-Q: QUANTUM-SAFE DLT FOR AP LAND RECORDS & SUPPLY CHAINS
echo     NIST ML-DSA Lattice Signatures ^| Qiskit BB84 QKD ^| 4-Qubit VQC Fraud Shield
echo ===============================================================================
echo.
echo [1] Run Automated Test Suite (10/10 Verification)
echo [2] Run Full CLI Demonstration & Generate Figures
echo [3] Launch Streamlit Interactive Command Center (Port 8503)
echo [4] Launch FastAPI REST Microservice (Port 8504)
echo [5] Exit
echo.
set /p opt="Select an option (1-5): "

if "%opt%"=="1" (
    echo.
    echo Running automated unit tests...
    python -m pytest tests/test_quantum_dlt.py -v
    pause
)
if "%opt%"=="2" (
    echo.
    echo Running full end-to-end demonstration...
    python main.py
    pause
)
if "%opt%"=="3" (
    echo.
    echo Launching Streamlit Dashboard on http://localhost:8503...
    streamlit run app.py --server.port 8503
)
if "%opt%"=="4" (
    echo.
    echo Launching FastAPI Server on http://localhost:8504...
    python main.py --serve-api
)
