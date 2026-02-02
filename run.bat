@echo off
setlocal

set PYI_ARGS=--noconsole --onefile --paths=src --paths=. --hidden-import pyimod04_pywin32 --name=openEulerManage.exe

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
    echo Installing executable to H:\Resources\RTLinux\Environment...
    if not exist "dist\openEulerManage.exe" (
        echo [ERROR] Build file not found. Please run 'run.bat build' first.
        exit /b 1
    )
    copy /y "dist\openEulerManage.exe" "H:\Resources\RTLinux\Environment\"
    goto :eof
)

if "%~1"=="pack" (
    echo Packaging...
    powershell -ExecutionPolicy Bypass -File "H:\Resources\RTLinux\Environment\back_and_pack.ps1"
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
    echo [2/3] Installing executable...
    copy /y "dist\openEulerManage.exe" "H:\Resources\RTLinux\Environment\"
    echo [3/3] Packaging...
    powershell -ExecutionPolicy Bypass -File "H:\Resources\RTLinux\Environment\back_and_pack.ps1"
    echo Done.
    goto :eof
)

:help
echo Usage: %~nx0 [dev^|simple^|build^|install^|pack^|all^|help]
echo.
echo Commands:
echo   dev     - Run the application in development mode
echo   simple  - Run the application in simple mode
echo   build   - Build the application into an executable
echo   install - Copy the built executable to the resource directory
echo   pack    - Run the backup and packaging script
echo   all     - Build and install and pack
echo   help    - Show this help message
echo.
echo [Environment Tip]
echo Please ensure your virtual environment is activated:
echo conda activate pyqt5_env
goto :eof
