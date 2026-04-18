# Automated Test Runner (PowerShell)
# Auto-detect VM and run all tests

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Test Automation Runner" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Environment check..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python is not available in the current environment" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verify VM connection
Write-Host "[2/6] Verifying VM connection..." -ForegroundColor Yellow
$vmHost = $env:UBUNTU_VM_HOST
$vmUser = $env:UBUNTU_VM_USER
if ($vmHost -and $vmUser) {
    $vmTest = ssh -o PasswordAuthentication=no -o ConnectTimeout=2 -o StrictHostKeyChecking=no "$vmUser@$vmHost" "echo ok" 2>$null
    if ($vmTest -eq "ok") {
        Write-Host "VM $vmHost connected" -ForegroundColor Green
        $env:UBUNTU_VM_AVAILABLE = "1"
    } else {
        Write-Host "VM $vmHost not connected, integration tests skipped" -ForegroundColor Yellow
    }
} else {
    Write-Host "VM probe skipped. Set UBUNTU_VM_USER and UBUNTU_VM_HOST to enable integration tests." -ForegroundColor Yellow
}
Write-Host ""

# Run verification script
Write-Host "[3/6] Running verification script..." -ForegroundColor Yellow
python tests/verify_setup.py
Write-Host ""

# Run core module unit tests
Write-Host "[4/6] Running core module tests..." -ForegroundColor Yellow
pytest tests/unit/core/ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host "Core module tests failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Run integration tests
Write-Host "[5/6] Running integration tests..." -ForegroundColor Yellow
pytest tests/integration/ -v --tb=short
$integrationResult = $LASTEXITCODE
Write-Host ""

# Generate coverage report
Write-Host "[Extra] Generating coverage report..." -ForegroundColor Yellow
pytest tests/unit/core/ --cov=src --cov-report=html --cov-report=term 2>$null
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Test execution completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "View reports:" -ForegroundColor Yellow
Write-Host "  - docs/test_execution_report_v2.md"
Write-Host "  - htmlcov/index.html (coverage report)"
Write-Host ""

if ($integrationResult -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Some tests failed, check detailed report" -ForegroundColor Yellow
}

Read-Host "Press Enter to continue..."
