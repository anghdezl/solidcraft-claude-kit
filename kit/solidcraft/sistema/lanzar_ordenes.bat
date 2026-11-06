@echo off
rem lanzar_ordenes.bat v0.1 - demonio de ordenes de lista cerrada (demonio_ordenes.py)
rem   sin argumentos: SIN ventana (pyw; si no hay, minimizado) | fg: en esta ventana | stop: lo para | autorizar [fichero.py]: autoriza el contenido actual (te pide SI)
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (echo No encuentro Python & pause & exit /b 1)
if /i "%~1"=="stop" (type nul > flag.stop_ordenes & echo Parada solicitada & exit /b 0)
if /i "%~1"=="fg" (%PY% "%~dp0demonio_ordenes.py" & exit /b %errorlevel%)
if /i "%~1"=="autorizar" (%PY% "%~dp0demonio_ordenes.py" --autorizar %2 %3 %4 %5 & pause & exit /b 0)
set "PYW="
where pyw >nul 2>&1 && set "PYW=pyw -3"
if not defined PYW where pythonw >nul 2>&1 && set "PYW=pythonw"
if defined PYW (start "" /min %PYW% "%~dp0demonio_ordenes.py") else (start "SolidCraft ordenes" /min %PY% "%~dp0demonio_ordenes.py")
echo Demonio de ordenes lanzado (minimizado). Log: %~dp0logs\ordenes.log
