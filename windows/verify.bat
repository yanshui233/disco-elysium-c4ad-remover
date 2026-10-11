@echo off
setlocal
title Disco Elysium - Zero Parades Ad Remover (check status)
set "HERE=%~dp0"

if not "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action verify -GameDir "%~1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action verify
)

echo.
pause
