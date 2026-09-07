@echo off
chcp 65001 >nul
cd /d "%~dp0\.."
title Compilador de LET IT DIE Save Editor Lite (.EXE)
echo ========================================================
echo    COMPILANDO LET IT DIE SAVE EDITOR LITE A .EXE
echo ========================================================
echo.
python build_exe.py --lite
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo ¡COMPILACIÓN EXITOSA!
    echo El ejecutable está listo en "dist\LetItDieSaveEditor_Lite.exe"
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo ERROR: Falló la compilación. Revisa los mensajes arriba.
    echo ========================================================
)
pause
