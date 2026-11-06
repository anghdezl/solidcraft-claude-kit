@echo off
rem lanzar_todo.bat v0.6 - arranca todo lo necesario para disenar con Claude: ventana de SolidCraft (puerto 27878) + ejecutor de trabajos + demonio de ordenes
rem Uso: doble clic. No duplica: si la ventana ya escucha o el ejecutor / el demonio ya laten, no los vuelve a abrir.
rem   stop = para ejecutor y demonio de ordenes (la ventana se cierra a mano, guardando antes)
rem LOG para Claude: sistema\logs\lanzar_todo.log (se sobrescribe en cada ejecucion). Las comprobaciones las hace sistema\comprobar_todo.py
setlocal
set "SIS=%~dp0sistema"
set "LOG=%SIS%\logs\lanzar_todo.log"
if not exist "%SIS%\logs" mkdir "%SIS%\logs"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY (echo No encuentro Python & pause & exit /b 1)
if /i "%~1"=="stop" (
  call "%SIS%\lanzar_ejecutor.bat" stop
  call "%SIS%\lanzar_ordenes.bat" stop
  %PY% "%SIS%\comprobar_todo.py" log "STOP solicitado: flags de parada dejados para ejecutor y demonio de ordenes"
  exit /b 0
)
type nul > "%LOG%"
%PY% "%SIS%\comprobar_todo.py" log "=== lanzar_todo v0.6 inicio; carpeta %~dp0; python: %PY%"

rem 1) Ventana (ya evita duplicados por si sola)
%PY% "%SIS%\comprobar_todo.py" vivo ventana
if errorlevel 1 (
  %PY% "%SIS%\comprobar_todo.py" log "1 ventana: no escucha en 27878, se lanza"
) else (
  %PY% "%SIS%\comprobar_todo.py" log "1 ventana: ya escuchaba en 27878"
)
call "%SIS%\lanzar_solidcraft_ventana.bat"

rem 2) Ejecutor
%PY% "%SIS%\comprobar_todo.py" vivo ejecutor
if errorlevel 1 (
  if exist "%SIS%\flag.stop_ejecutor" del "%SIS%\flag.stop_ejecutor"
  %PY% "%SIS%\comprobar_todo.py" log "2 ejecutor: parado, se lanza"
  call "%SIS%\lanzar_ejecutor.bat"
) else (
  echo Ejecutor ya en marcha. No lo duplico.
  %PY% "%SIS%\comprobar_todo.py" log "2 ejecutor: ya estaba en marcha"
)

rem 3) Demonio de ordenes
%PY% "%SIS%\comprobar_todo.py" vivo ordenes
if errorlevel 1 (
  if exist "%SIS%\flag.stop_ordenes" del "%SIS%\flag.stop_ordenes"
  %PY% "%SIS%\comprobar_todo.py" log "3 ordenes: parado, se lanza"
  call "%SIS%\lanzar_ordenes.bat"
) else (
  echo Demonio de ordenes ya en marcha. No lo duplico.
  %PY% "%SIS%\comprobar_todo.py" log "3 ordenes: ya estaba en marcha"
)

rem 4) Comprobacion final (hasta 30 s) y resultado en el log
%PY% "%SIS%\comprobar_todo.py" final 30
if errorlevel 1 (echo Resultado: FALLO. Detalle en %LOG%) else (echo Resultado: OK)
timeout /t 4 >nul
exit /b 0
