@echo off
setlocal

set "PYI_SPEC=openEulerManage.spec"
set "BUILD_DIR=dist\openEulerManage"
set "BUILD_EXE=%BUILD_DIR%\openEulerManage.exe"
set "RESOURCE_DIR=%OPENEULER_RESOURCE_DIR%"
set "INSTALL_DIR=%OPENEULER_INSTALL_DIR%"
set "INSTALL_EXE=%INSTALL_DIR%\openEulerManage.exe"
set "INSTALL_INTERNAL=%INSTALL_DIR%\_internal"
set "BUILD_WORK_DIR=build\openEulerManage"
set "BUILD_ALT_WORK_DIR=build\openEulerManage.exe"
set "BUILD_ALT_EXE=dist\openEulerManage.exe"

if "%~1"=="" goto help
if "%~1"=="help" goto help

if "%~1"=="simple" (
    echo Starting in development mode...
    if defined RESOURCE_DIR (
        python src/main.py -d "%RESOURCE_DIR%"
    ) else (
        python src/main.py
    )
    goto :eof
)

if "%~1"=="dev" (
    echo Starting in development mode...
    if defined RESOURCE_DIR (
        python src/main.py -d "%RESOURCE_DIR%" --skip-login
    ) else (
        python src/main.py --skip-login
    )
    goto :eof
)

if "%~1"=="build" (
    call :ensure_packaging_env
    if errorlevel 1 exit /b 1
    call :clean_pyinstaller_artifacts
    echo Building executable...
    python -m PyInstaller -y "%PYI_SPEC%"
    goto :eof
)

if "%~1"=="install" (
    call :require_install_dir
    if errorlevel 1 exit /b 1
    echo Installing application package to %INSTALL_DIR%...
    if not exist "%BUILD_EXE%" (
        echo [ERROR] Build file not found. Please run 'run.bat build' first.
        exit /b 1
    )
    powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%INSTALL_INTERNAL%') { Remove-Item -LiteralPath '%INSTALL_INTERNAL%' -Recurse -Force }; if (Test-Path '%INSTALL_EXE%') { Remove-Item -LiteralPath '%INSTALL_EXE%' -Force }; Copy-Item -Path '%BUILD_DIR%\\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
    goto :eof
)

if "%~1"=="pack" (
    call :require_install_dir
    if errorlevel 1 exit /b 1
    echo Packaging...
    powershell -ExecutionPolicy Bypass -File "%INSTALL_DIR%\back_and_pack.ps1"
    goto :eof
)

if "%~1"=="all" (
    call :ensure_packaging_env
    if errorlevel 1 exit /b 1
    call :require_install_dir
    if errorlevel 1 exit /b 1
    echo [1/3] Building executable...
    call :clean_pyinstaller_artifacts
    python -m PyInstaller -y "%PYI_SPEC%"
    if errorlevel 1 (
        echo [ERROR] Build failed.
        exit /b 1
    )
    echo [2/3] Installing application package...
    powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%INSTALL_INTERNAL%') { Remove-Item -LiteralPath '%INSTALL_INTERNAL%' -Recurse -Force }; if (Test-Path '%INSTALL_EXE%') { Remove-Item -LiteralPath '%INSTALL_EXE%' -Force }; Copy-Item -Path '%BUILD_DIR%\\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
    echo [3/3] Packaging...
    powershell -ExecutionPolicy Bypass -File "%INSTALL_DIR%\back_and_pack.ps1"
    echo Done.
    goto :eof
)

goto help

:clean_pyinstaller_artifacts
echo Cleaning previous PyInstaller build artifacts...
powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%BUILD_DIR%') { Remove-Item -LiteralPath '%BUILD_DIR%' -Recurse -Force }; if (Test-Path '%BUILD_ALT_EXE%') { Remove-Item -LiteralPath '%BUILD_ALT_EXE%' -Force }; if (Test-Path '%BUILD_WORK_DIR%') { Remove-Item -LiteralPath '%BUILD_WORK_DIR%' -Recurse -Force }; if (Test-Path '%BUILD_ALT_WORK_DIR%') { Remove-Item -LiteralPath '%BUILD_ALT_WORK_DIR%' -Recurse -Force }"
goto :eof

:require_install_dir
if defined INSTALL_DIR goto :eof
echo [ERROR] OPENEULER_INSTALL_DIR is not set.
exit /b 1

:ensure_packaging_env
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) else 1)"
if errorlevel 1 (
    echo [ERROR] Packaging for Win7 compatibility must use Python 3.8.
    echo [ERROR] Please use a Python 3.8 environment.
    exit /b 1
)
goto :eof

:help
echo Usage: %~nx0 [dev^|simple^|build^|install^|pack^|all^|help]
echo.
echo Commands:
echo   dev     - Run the application in development mode
echo   simple  - Run the application in simple mode
echo   build   - Build the application into an onedir package
echo   install - Copy the built package to the resource directory
echo   pack    - Run the backup and packaging script
echo   all     - Build and install and pack
echo   help    - Show this help message
echo.
echo [Environment Variables]
echo OPENEULER_RESOURCE_DIR - optional resource directory passed to src/main.py -d
echo OPENEULER_INSTALL_DIR  - required for install and packaging copy steps
goto :eof
