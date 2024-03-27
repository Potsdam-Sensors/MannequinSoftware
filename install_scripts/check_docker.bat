@echo off
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo Docker is installed.
    exit 0
) else (
    echo Docker is not installed. Please install Docker desktop on this machine before installing.
    echo Press any button to close this message...
    pause > nul
    exit 1
)