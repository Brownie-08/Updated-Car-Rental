@echo off
echo Starting Docker Desktop...
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo Waiting for Docker to start...
timeout /t 30 /nobreak
echo Docker Desktop should now be starting. Please wait a moment and then run docker-compose.
pause
