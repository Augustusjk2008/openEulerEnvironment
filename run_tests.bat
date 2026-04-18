@echo off
REM Automation Test Runner
REM Auto-detect VM and run all tests

REM Set UTF-8 encoding for Chinese characters
chcp 65001 >nul 2>&1

echo ========================================
echo   Test Automation Runner
echo ========================================
echo.

echo [1/5] Environment check...
python --version
if errorlevel 1 (
    echo Error: Python is not available in the current environment
    exit /b 1
)
echo.

set "VM_HOST=%UBUNTU_VM_HOST%"
set "VM_USER=%UBUNTU_VM_USER%"

echo [2/5] Verify VM connection...
if defined VM_HOST if defined VM_USER (
    ssh -o PasswordAuthentication=no -o ConnectTimeout=2 %VM_USER%@%VM_HOST% "echo VM_OK" 2>nul
    if %errorlevel% == 0 (
        echo VM %VM_HOST% connected
        set UBUNTU_VM_AVAILABLE=1
    ) else (
        echo VM %VM_HOST% not connected, integration tests skipped
    )
) else (
    echo VM probe skipped. Set UBUNTU_VM_USER and UBUNTU_VM_HOST to enable integration tests.
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
