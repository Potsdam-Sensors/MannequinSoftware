@echo off
cd /d "%~dp0/../mannequin-compose-app"
SET COMPOSE_CONVERT_WINDOWS_PATHS=1
docker compose build
@echo off
if %ERRORLEVEL% neq 0 (
    echo Docker compose build failed. Please copy this output and contact developer. Press any key to close this window.
    pause > nul
    exit /b %ERRORLEVEL%
) else (
    echo Docker compose build succeeded
)
