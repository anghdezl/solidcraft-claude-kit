@echo off
rem lanzar_ejecutor.bat v0.1 - arranca el ejecutor de trabajos de SolidCraft (ejecutor_trabajos.py)
rem   sin argumentos: SIN ventana (pyw; si no hay, minimizado) | fg: en esta ventana | stop: lo para
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (echo No encuentro Python & pause & exit /b 1)
if /i "%~1"=="stop" (type nul > flag.stop_ejecutor & echo Parada solicitada & exit /b 0)
if /i "%~1"=="fg" (%PY% "%~dp0ejecutor_trabajos.py" & exit /b %errorlevel%)
set "PYW="
where pyw >nul 2>&1 && set "PYW=pyw -3"
if not defined PYW where pythonw >nul 2>&1 && set "PYW=pythonw"
if defined PYW (start "" /min %PYW% "%~dp0ejecutor_trabajos.py") else (start "SolidCraft ejecutor" /min %PY% "%~dp0ejecutor_trabajos.py")
echo Ejecutor lanzado (minimizado). Resultados en %~dp0resultados
