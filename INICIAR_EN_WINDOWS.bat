@echo off
setlocal
cd /d "%~dp0"
title tlahtolmekauan - servidor

echo ================================================================
echo tlahtolmekauan
echo ================================================================
echo.
echo No abras index.html directamente.
echo Este archivo inicia el motor y abre el sitio correcto.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PYTHONDONTWRITEBYTECODE=1
    py -3 servidor.py
    set "CODIGO=%errorlevel%"
    goto :resultado
)

where python >nul 2>nul
if %errorlevel%==0 (
    set PYTHONDONTWRITEBYTECODE=1
    python servidor.py
    set "CODIGO=%errorlevel%"
    goto :resultado
)

echo ERROR: No se encontro Python 3.
echo Instala Python y marca la opcion Add Python to PATH.
set "CODIGO=1"

:resultado
if not "%CODIGO%"=="0" (
    echo.
    echo El servidor no pudo iniciar.
    echo Copia o toma una foto del mensaje de error que aparece arriba.
    echo.
    pause
)
endlocal
