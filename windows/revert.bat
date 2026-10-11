@echo off
setlocal
title Disco Elysium - Zero Parades Ad Remover (revert)
set "HERE=%~dp0"

echo ============================================================
echo   Restore the original  disco_Data\level2
echo ============================================================
echo.

if not "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action revert -GameDir "%~1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action revert
)

echo.
if errorlevel 1 (
    echo [!] Revert failed. Read the messages above.
) else (
    echo [OK] Original file restored.
)
echo.
pause
