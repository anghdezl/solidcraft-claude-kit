@echo off
rem lanzar_solidcraft_ventana.bat v0.1 - abre SolidCraft con el puerto de control 27878 para que Claude se conecte
rem Uso: doble clic. Si ya hay una ventana escuchando en 27878, no abre otra.
set "EXE=C:\Program Files\SolidCraft\solidcraft.exe"
set "PORT=27878"
if not exist "%EXE%" (
  echo No encuentro "%EXE%". Revisa la instalacion.
  pause
  exit /b 1
)
netstat -ano | findstr /R /C:":%PORT% .*LISTENING" >nul
if %errorlevel%==0 (
  echo SolidCraft ya esta escuchando en el puerto %PORT%. No abro otra ventana.
  timeout /t 4 >nul
  exit /b 0
)
start "" "%EXE%" --control %PORT%
echo SolidCraft lanzado con --control %PORT%. Avisa a Claude cuando se vea la ventana.
timeout /t 4 >nul
