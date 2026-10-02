@echo off
setlocal

cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
	echo.
	echo No se encontro Python en el PATH.
	echo Verifica que Python este instalado y disponible como "python".
	echo.
	pause
	exit /b 1
)

start "" http://localhost:8000/lsm/alfabeto/

python -m http.server 8000

endlocal
