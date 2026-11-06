@echo off
rem lanzar_solidcraft.bat v0.1 (borrador, sin probar en Windows)
rem   lanzar_solidcraft.bat           arranca el demonio minimizado
rem   lanzar_solidcraft.bat fg        lo arranca en esta ventana
rem   lanzar_solidcraft.bat stop      deja flag.stop (el demonio lo borra y se para)
rem   lanzar_solidcraft.bat check     deja flag.check (repite las comprobaciones)
rem   lanzar_solidcraft.bat install   deja flag.install (instala si falta y comprueba)
rem   lanzar_solidcraft.bat estado    muestra status.json y el final del log
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (
  echo No encuentro Python. Instalalo con: winget install Python.Python.3.12
  pause
  exit /b 1
)
if /i "%~1"=="" (
  start "SolidCraft demonio" /min %PY% "%~dp0instalar_solidcraft.py"
  echo Demonio lanzado en una ventana minimizada.
  echo Log: %~dp0logs\solidcraft.log
  echo Parar: lanzar_solidcraft.bat stop
  exit /b 0
)
if /i "%~1"=="fg" (
  %PY% "%~dp0instalar_solidcraft.py"
  exit /b %errorlevel%
)
%PY% "%~dp0instalar_solidcraft.py" --%~1
