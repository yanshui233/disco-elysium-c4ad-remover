@echo off
setlocal
title Disco Elysium - Zero Parades Ad Remover (uninstall)
set "HERE=%~dp0"

echo ============================================================
echo   UNINSTALL the Zero Parades (C4Ad) banner remover
echo ============================================================
echo.
echo   This will:
echo     1. restore  disco_Data\level2  to the original ZA/UM file
echo     2. delete the backup this tool created (.c4ad-backup)
echo     3. verify the file is back to the shipped state
echo.
echo   Make sure the game is CLOSED before continuing.
echo.

if not "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action uninstall -GameDir "%~1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action uninstall
)

echo.
if errorlevel 1 (
    echo [!] Uninstall did not complete. Read the messages above.
    echo     If the game folder was not found, run:
    echo       uninstall.bat "D:\Steam\steamapps\common\Disco Elysium"
) else (
    echo [OK] Uninstalled. The game is back to the original, ad included.
    echo      You may now delete this folder.
)
echo.
pause
