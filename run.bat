@echo off
setlocal

if "%~1"=="" goto help
if "%~1"=="help" goto help

if "%~1"=="dev" (
    echo Starting in development mode...
    python src/main.py -d H:\Resources\RTLinux\Environment --skip-login
    goto :eof
)

if "%~1"=="build" (
    echo Building executable...
    pyinstaller --noconsole --onefile .\src\main.py --name=openEulerManage.exe
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

if "%~1"=="all" (
    echo [1/2] Building executable...
    pyinstaller --noconsole --onefile .\src\main.py --name=openEulerManage.exe
    if errorlevel 1 (
        echo [ERROR] Build failed.
        exit /b 1
    )
    echo [2/2] Installing executable...
    copy /y "dist\openEulerManage.exe" "H:\Resources\RTLinux\Environment\"
    echo Done.
    goto :eof
)

:help
echo Usage: %~nx0 [dev^|build^|install^|all^|help]
echo.
echo Commands:
echo   dev     - Run the application in development mode
echo   build   - Build the application into an executable
echo   install - Copy the built executable to the resource directory
echo   all     - Build and then install
echo   help    - Show this help message
echo.
echo [Environment Tip]
echo Please ensure your virtual environment is activated:
echo conda activate pyqt5_env
goto :eof
