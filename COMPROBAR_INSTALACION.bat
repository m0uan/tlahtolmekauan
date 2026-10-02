@echo off
setlocal
cd /d "%~dp0"
title Comprobar tlahtolmekauan

echo === CARPETA ===
echo %CD%
echo.
echo === PYTHON ===
where py 2>nul
where python 2>nul
py -3 --version 2>nul
python --version 2>nul
echo.
echo === ARCHIVOS PRINCIPALES ===
if exist servidor.py (echo OK servidor.py) else (echo FALTA servidor.py)
if exist index.html (echo OK index.html) else (echo FALTA index.html)
if exist app.js (echo OK app.js) else (echo FALTA app.js)
if exist motor\Nahuatl_Translator.py (echo OK motor\Nahuatl_Translator.py) else (echo FALTA motor\Nahuatl_Translator.py)
echo.
pause
endlocal
