@echo off
rem parar_solidcraft.bat v0.1 (borrador)
rem Deja flag.stop: el demonio lo detecta, lo borra y se para de forma controlada.
setlocal
cd /d "%~dp0"
call "%~dp0lanzar_solidcraft.bat" stop
echo.
echo El demonio tarda unos segundos en pararse. Comprobar: lanzar_solidcraft.bat estado
timeout /t 5 >nul
