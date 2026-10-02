@echo off
setlocal

set "PROYECTO=C:\Users\mouan\Documents\tlahtolmekauan\tlahtolmekauan_v2"

if not exist "%PROYECTO%\index.html" (
	echo.
	echo ERROR: No se encontro index.html en:
	echo %PROYECTO%
	echo.
	pause
	exit /b 1
)

cd /d "%PROYECTO%"

where py >nul 2>nul
if not errorlevel 1 (
	start "Servidor tlahtolmekauan" cmd /k "cd /d ""%PROYECTO%"" && py -m http.server 8000"
	timeout /t 2 /nobreak >nul
	start "" "http://localhost:8000/lsm/alfabeto/"
	exit /b 0
)

where python >nul 2>nul
if not errorlevel 1 (
	start "Servidor tlahtolmekauan" cmd /k "cd /d ""%PROYECTO%"" && python -m http.server 8000"
	timeout /t 2 /nobreak >nul
	start "" "http://localhost:8000/lsm/alfabeto/"
	exit /b 0
)

echo.
echo ERROR: No se encontro Python ni el comando py.
echo.
pause
exit /b 1
