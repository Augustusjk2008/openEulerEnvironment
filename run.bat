@echo off
setlocal

set PYI_SPEC=openEulerManage.spec
set BUILD_DIR=dist\openEulerManage
set BUILD_EXE=%BUILD_DIR%\openEulerManage.exe
set BUILD_ROOT=build
set INSTALL_DIR=H:\Resources\RTLinux\Environment
set INSTALL_EXE=%INSTALL_DIR%\openEulerManage.exe
set INSTALL_INTERNAL=%INSTALL_DIR%\_internal
set BUILD_WORK_DIR=build\openEulerManage
set BUILD_ALT_WORK_DIR=build\openEulerManage.exe
set BUILD_ALT_EXE=dist\openEulerManage.exe
set CX_VENV_DIR=.venvs\cxfreeze38
set CX_PYTHON=%CX_VENV_DIR%\Scripts\python.exe
set CX_REQUIREMENTS=requirements-cxfreeze38.txt
set CX_SETUP=setup_cxfreeze.py
set CX_BUILD_DIR=dist\openEulerManage_cxfreeze
set CX_BUILD_EXE=%CX_BUILD_DIR%\openEulerManage_cxfreeze.exe
set CX_INSTALL_EXE=%INSTALL_DIR%\openEulerManage_cxfreeze.exe
set CX_INSTALL_LIB=%INSTALL_DIR%\lib
set CX_WHEELHOUSE=.cache\cxfreeze-wheelhouse
set CX_BOOTSTRAP_PIP=pip==24.0
set CX_BOOTSTRAP_SETUPTOOLS=setuptools==75.3.4
set CX_BOOTSTRAP_WHEEL=wheel==0.45.1

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
    call :ensure_packaging_env
    if errorlevel 1 exit /b 1
    call :clean_pyinstaller_artifacts
    echo Building executable...
    python -m PyInstaller -y "%PYI_SPEC%"
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
    call :ensure_packaging_env
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

if "%~1"=="cxfreeze-env" (
    call :ensure_cxfreeze_env
    exit /b %errorlevel%
)

if "%~1"=="cxfreeze-build" (
    call :ensure_cxfreeze_env
    if errorlevel 1 exit /b 1
    call :clean_cxfreeze_artifacts
    echo Building cx_Freeze package...
    set "CXFREEZE_BUILD_DIR=%CD%\%CX_BUILD_DIR%"
    "%CX_PYTHON%" "%CX_SETUP%" build_exe
    exit /b %errorlevel%
)

if "%~1"=="cxfreeze-install" (
    echo Installing cx_Freeze package to %INSTALL_DIR%...
    if not exist "%CX_BUILD_EXE%" (
        echo [ERROR] cx_Freeze build file not found. Please run 'run.bat cxfreeze-build' first.
        exit /b 1
    )
    powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%CX_INSTALL_LIB%') { Remove-Item -LiteralPath '%CX_INSTALL_LIB%' -Recurse -Force }; if (Test-Path '%CX_INSTALL_EXE%') { Remove-Item -LiteralPath '%CX_INSTALL_EXE%' -Force }; Copy-Item -Path '%CX_BUILD_DIR%\\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
    goto :eof
)

if "%~1"=="cxfreeze-all" (
    call :ensure_cxfreeze_env
    if errorlevel 1 exit /b 1
    call :clean_cxfreeze_artifacts
    echo [1/2] Building cx_Freeze package...
    set "CXFREEZE_BUILD_DIR=%CD%\%CX_BUILD_DIR%"
    "%CX_PYTHON%" "%CX_SETUP%" build_exe
    if errorlevel 1 (
        echo [ERROR] cx_Freeze build failed.
        exit /b 1
    )
    echo [2/2] Installing cx_Freeze package...
    powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%CX_INSTALL_LIB%') { Remove-Item -LiteralPath '%CX_INSTALL_LIB%' -Recurse -Force }; if (Test-Path '%CX_INSTALL_EXE%') { Remove-Item -LiteralPath '%CX_INSTALL_EXE%' -Force }; Copy-Item -Path '%CX_BUILD_DIR%\\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
    echo Done.
    goto :eof
)

goto help

:clean_pyinstaller_artifacts
echo Cleaning previous PyInstaller build artifacts...
powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%BUILD_DIR%') { Remove-Item -LiteralPath '%BUILD_DIR%' -Recurse -Force }; if (Test-Path '%BUILD_ALT_EXE%') { Remove-Item -LiteralPath '%BUILD_ALT_EXE%' -Force }; if (Test-Path '%BUILD_WORK_DIR%') { Remove-Item -LiteralPath '%BUILD_WORK_DIR%' -Recurse -Force }; if (Test-Path '%BUILD_ALT_WORK_DIR%') { Remove-Item -LiteralPath '%BUILD_ALT_WORK_DIR%' -Recurse -Force }"
goto :eof

:clean_cxfreeze_artifacts
echo Cleaning previous cx_Freeze build artifacts...
powershell -ExecutionPolicy Bypass -Command "if (Test-Path '%CX_BUILD_DIR%') { Remove-Item -LiteralPath '%CX_BUILD_DIR%' -Recurse -Force }"
goto :eof

:ensure_packaging_env
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) else 1)"
if errorlevel 1 (
    echo [ERROR] Packaging for Win7 compatibility must use Python 3.8.
    echo [ERROR] Please activate the expected environment first:
    echo conda activate pyqt5_env
    exit /b 1
)
goto :eof

:ensure_cxfreeze_env
call :ensure_python38_launcher
if errorlevel 1 exit /b 1
call :ensure_cxfreeze_wheelhouse
if errorlevel 1 exit /b 1

if not exist "%CX_PYTHON%" (
    echo Creating Python 3.8 venv at %CX_VENV_DIR%...
    py -3.8 -m venv "%CX_VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create Python 3.8 venv.
        exit /b 1
    )
)

echo Syncing cx_Freeze migration environment...
"%CX_PYTHON%" -m pip install --no-index --find-links="%CX_WHEELHOUSE%" %CX_BOOTSTRAP_PIP% %CX_BOOTSTRAP_SETUPTOOLS% %CX_BOOTSTRAP_WHEEL%
if errorlevel 1 (
    echo [ERROR] Failed to bootstrap pip tooling in the cx_Freeze venv from the local wheelhouse.
    exit /b 1
)

"%CX_PYTHON%" -m pip install --no-index --find-links="%CX_WHEELHOUSE%" -r "%CX_REQUIREMENTS%"
if errorlevel 1 (
    echo [ERROR] Failed to install cx_Freeze migration requirements from the local wheelhouse.
    exit /b 1
)

"%CX_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) else 1)"
if errorlevel 1 (
    echo [ERROR] The cx_Freeze venv is not running on Python 3.8.
    exit /b 1
)
goto :eof

:ensure_cxfreeze_wheelhouse
call :resolve_bootstrap_python
if errorlevel 1 exit /b 1

if not exist "%CX_WHEELHOUSE%" (
    mkdir "%CX_WHEELHOUSE%"
)

echo Preparing local cx_Freeze wheelhouse...
%BOOTSTRAP_PYTHON% -m pip download %CX_BOOTSTRAP_PIP% %CX_BOOTSTRAP_SETUPTOOLS% %CX_BOOTSTRAP_WHEEL% -d "%CX_WHEELHOUSE%"
if errorlevel 1 (
    echo [ERROR] Failed to download pip bootstrap wheels for the cx_Freeze environment.
    exit /b 1
)

%BOOTSTRAP_PYTHON% -m pip download -r "%CX_REQUIREMENTS%" -d "%CX_WHEELHOUSE%" --platform win_amd64 --implementation cp --python-version 38 --only-binary=:all:
if errorlevel 1 (
    echo [ERROR] Failed to download the cx_Freeze migration wheelhouse.
    exit /b 1
)
goto :eof

:resolve_bootstrap_python
set "BOOTSTRAP_PYTHON="
python -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 11) else 1)" >nul 2>&1
if not errorlevel 1 set "BOOTSTRAP_PYTHON=python"
if not defined BOOTSTRAP_PYTHON (
    py -3.13 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PYTHON=py -3.13"
)
if not defined BOOTSTRAP_PYTHON (
    py -3.11 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "BOOTSTRAP_PYTHON=py -3.11"
)
if not defined BOOTSTRAP_PYTHON (
    echo [ERROR] A bootstrap Python 3.11+ interpreter is required to prepare the cx_Freeze wheelhouse.
    exit /b 1
)
goto :eof

:ensure_python38_launcher
py -3.8 -c "import sys; print(sys.executable)"
if errorlevel 1 (
    echo [ERROR] Python 3.8 launcher not available.
    echo [ERROR] Please install Python 3.8 from python.org first.
    exit /b 1
)
goto :eof

:help
echo Usage: %~nx0 [dev^|simple^|build^|install^|pack^|all^|cxfreeze-env^|cxfreeze-build^|cxfreeze-install^|cxfreeze-all^|help]
echo.
echo Commands:
echo   dev     - Run the application in development mode
echo   simple  - Run the application in simple mode
echo   build   - Build the application into an onedir package
echo   install - Copy the built package to the resource directory
echo   pack    - Run the backup and packaging script
echo   all     - Build and install and pack
echo   cxfreeze-env     - Create or update the pure Python 3.8 venv for cx_Freeze
echo   cxfreeze-build   - Build the cx_Freeze package
echo   cxfreeze-install - Copy the cx_Freeze package to the resource directory
echo   cxfreeze-all     - Create or update the venv, build, and install the cx_Freeze package
echo   help    - Show this help message
echo.
echo [Environment Tip]
echo Please ensure your virtual environment is activated:
echo conda activate pyqt5_env
echo.
echo [cx_Freeze Tip]
echo The cx_Freeze workflow uses Python 3.8 from the py launcher and stores its venv in %CX_VENV_DIR%.
goto :eof
