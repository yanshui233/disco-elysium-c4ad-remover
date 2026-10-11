@echo off
setlocal
title Disco Elysium - Zero Parades Ad Remover
set "HERE=%~dp0"

echo ============================================================
echo   Disco Elysium - Zero Parades (C4Ad) banner remover
echo ============================================================
echo.
echo   Patch target : disco_Data\level2  (moves the banner off-screen)
echo   The original is backed up next to it automatically.
echo.
echo   Make sure the game is CLOSED before continuing.
echo.

if not "%~1"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action apply -GameDir "%~1"
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%patch.ps1" -Action apply
)

echo.
if errorlevel 1 (
    echo [!] The patch did not complete. Read the messages above.
    echo     If the game folder was not found, run:
    echo       install.bat "D:\Steam\steamapps\common\Disco Elysium"
) else (
    echo [OK] Done. Launch the game - the ZERO PARADES banner is gone.
    echo      To undo          : run revert.bat    (restore, keep the backup)
    echo      To remove fully  : run uninstall.bat (restore + delete backup)
)
echo.
pause
