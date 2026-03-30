@echo off
setlocal

set PYI_ARGS=-y --noconsole --onedir --paths=src --paths=. --hidden-import pyimod04_pywin32 --name=openEulerManage
set BUILD_DIR=dist\openEulerManage
set BUILD_EXE=%BUILD_DIR%\openEulerManage.exe
set INSTALL_DIR=H:\Resources\RTLinux\Environment
set INSTALL_EXE=%INSTALL_DIR%\openEulerManage.exe
set INSTALL_INTERNAL=%INSTALL_DIR%\_internal

if "%~1"=="" goto help
if "%~1"=="help" goto help

if "%~1"=="simple" (
    echo Starting in development mode...
    python src/main.py -d H:\Resources\RTLinux\Environment
    goto :eof
)

if "%~1"=="dev" (
    echo Starting in development mode...
    python src/main.py -d H:\Resources\RTLinux\Environment --skip-login
    goto :eof
)

if "%~1"=="build" (
    echo Building executable...
    python -c "import pyimod04_pywin32 as p; p.patch_pyinstaller_loader_for_win7()"
    python -m PyInstaller %PYI_ARGS% .\src\main.py
    goto :eof
)

if "%~1"=="install" (
    echo Installing application package to %INSTALL_DIR%...
    if not exist "%BUILD_EXE%" (
        echo [ERROR] Build file not found. Please run 'run.bat build' first.
        exit /b 1
    )
    powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%INSTALL_INTERNAL%') { Remove-Item -LiteralPath '%INSTALL_INTERNAL%' -Recurse -Force }; if (Test-Path '%INSTALL_EXE%') { Remove-Item -LiteralPath '%INSTALL_EXE%' -Force }; Copy-Item -Path '%BUILD_DIR%\\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
    goto :eof
)

if "%~1"=="pack" (
    echo Packaging...
    powershell -ExecutionPolicy Bypass -File "%INSTALL_DIR%\back_and_pack.ps1"
    goto :eof
)

if "%~1"=="all" (
    echo [1/3] Building executable...
    python -c "import pyimod04_pywin32 as p; p.patch_pyinstaller_loader_for_win7()"
    python -m PyInstaller %PYI_ARGS% .\src\main.py
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
echo [Environment Tip]
echo Please ensure your virtual environment is activated:
echo conda activate pyqt5_env
goto :eof
