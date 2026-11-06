@echo off
rem parar_todo.bat v0.1 - para ejecutor y demonio de ordenes (llama a lanzar_todo.bat stop). La ventana de SolidCraft se cierra a mano, guardando antes.
call "%~dp0lanzar_todo.bat" stop
echo Parada solicitada para ejecutor y demonio de ordenes. SolidCraft: cierralo a mano guardando antes.
timeout /t 4 >nul
