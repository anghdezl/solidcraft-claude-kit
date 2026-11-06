@echo off
rem instalar_entorno.bat v0.1 - prepara el PC (Python, SolidCraft, configuracion de Claude Desktop). Sin probar en un Windows limpio.
rem Uso: doble clic = asistente completo (todo). Con argumento: diagnostico | instalar | configurar [--aplicar] | todo
rem La logica esta en sistema\instalar_entorno.py; este .bat solo localiza Python. Log: sistema\logs\instalar_entorno.log
setlocal
set "ACCION=%~1"
if "%ACCION%"=="" set "ACCION=todo"
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY where python >nul 2>&1 && set "PY=python"
if defined PY %PY% -c "import sys" >nul 2>&1 || set "PY="
if defined PY goto hay_python
echo No encuentro Python 3.
where winget >nul 2>&1 || goto sin_winget
set /p R=Instalar Python 3.12 con winget ahora? [S/N] 
if /i not "%R%"=="S" goto fin
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
echo.
echo Cierra esta ventana y vuelve a ejecutar este fichero para que Windows vea Python.
goto fin
:sin_winget
echo Instala Python 3.8 o superior desde https://www.python.org/downloads/ (marca "Add python.exe to PATH") y repite.
goto fin
:hay_python
%PY% "%~dp0sistema\instalar_entorno.py" %ACCION% %2 %3 %4 %5 %6
:fin
echo.
pause
