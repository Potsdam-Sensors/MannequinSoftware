@echo off
docker stats --no-stream > nul
IF %ERRORLEVEL% == 0 (
    echo Docker is running.
    goto start_app
) ELSE (
    echo Docker is not running. Starting Docker...
    IF EXIST "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
        echo Located Docker Executable. Launching...
        "C:\Program Files\Docker\Docker\Docker Desktop.exe"
        echo Waiting for Docker to start...
        :loopstart
        docker stats --no-stream > nul
        IF NOT %ERRORLEVEL% == 0 (
            timeout 2 > nul
            goto loopstart
        )
        echo Docker started.
        goto start_app
    ) ELSE (
        echo Please install Docker Desktop. If you already have done so, please start Docker Desktop.
        goto end
    )
)


:start_app
cd /d "%~dp0"
SET COMPOSE_CONVERT_WINDOWS_PATHS=1
docker compose down
docker compose up -d
if %ERRORLEVEL% neq 0 (
    echo There was an issue starting the containers. Please copy this output for the developer.
    goto :end
) ELSE (
    echo Containers started successfully.
)

start cmd /k "..\data-acquisition\dist\app\app.exe"
exit
:end
pause