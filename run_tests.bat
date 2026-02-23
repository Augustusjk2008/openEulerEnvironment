@echo off
REM Automation Test Runner
REM Auto-detect VM and run all tests

REM Set UTF-8 encoding for Chinese characters
chcp 65001 >nul 2>&1

echo ========================================
echo   Test Automation Runner
echo ========================================
echo.

REM Activate conda environment
call conda activate pyqt5_env

REM Check if conda environment is activated
if errorlevel 1 (
    echo Error: Failed to activate conda environment pyqt5_env
    exit /b 1
)

echo [1/5] Environment check...
python --version
echo.

echo [2/5] Verify VM connection...
ssh -o PasswordAuthentication=no -o ConnectTimeout=2 jiangkai@192.168.56.132 "echo VM_OK" 2>nul
if %errorlevel% == 0 (
    echo VM 192.168.56.132 connected
    set UBUNTU_VM_AVAILABLE=1
) else (
    echo VM 192.168.56.132 not connected, integration tests skipped
)
echo.

echo [3/5] Running core module tests...
pytest tests/unit/core/ -v --tb=short
if errorlevel 1 (
    echo Core module tests failed
    exit /b 1
)
echo.

echo [4/5] Running integration tests...
pytest tests/integration/ -v --tb=short
echo.

echo [5/5] Running UI tests...
pytest tests/unit/ui/ -v --tb=short -m "not gui" 2>nul
if errorlevel 1 (
    echo UI tests partially failed, continuing...
)
echo.

echo ========================================
echo   Test execution completed
echo ========================================
echo.
echo View reports:
echo   - docs/test_execution_report_v2.md
echo   - htmlcov/index.html (coverage report)
echo.

pause
