@echo off
rem PUBLICAR.bat - sube el kit a GitHub. Antes: crea en github.com un repositorio VACIO (sin README ni licencia) y copia su URL.
rem Uso: doble clic y pega la URL (https://github.com/USUARIO/solidcraft-claude-kit.git)
setlocal
cd /d "%~dp0"
where git >nul 2>&1 || (echo Instala Git para Windows primero: https://git-scm.com & pause & exit /b 1)
set /p URL=URL del repositorio vacio: 
if not exist .git git init -b main
git add .
git status --short
echo.
echo Revisa la lista de arriba: no debe haber datos personales. Enter para continuar, Ctrl+C para cancelar.
pause >nul
git commit -m "Kit inicial: prompt principal, docs y scripts de SolidCraft"
git remote remove origin >nul 2>&1
git remote add origin %URL%
git push -u origin main
pause
