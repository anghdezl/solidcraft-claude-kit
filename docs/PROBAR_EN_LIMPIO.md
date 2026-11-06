# Prueba en un Windows limpio (máquina virtual)

Objetivo: comprobar que un usuario nuevo llega de cero a una pieza laminada. **Anota solo lo que veas**; lo que no pase, se queda como "no verificado".

## Antes
- VM con Windows 10/11 recién instalado y actualizado, con `winget` (`winget --version` en una terminal).
- Cuenta de Claude con la app de escritorio (la misma cuenta sirve) y acceso a ordenador activado si la app lo pide.
- Una foto de una pieza sencilla con alguna cota.

## Lista de pasos
| # | Paso | Resultado esperado | ¿Pasó? |
|---|---|---|---|
| 1 | Descargar el repo (ZIP de GitHub) y descomprimir | Carpeta con `instalar_todo.bat` | |
| 2 | Doble clic en `instalar_todo.bat` | Detecta/ofrece instalar Python | |
| 3 | Aceptar instalar SolidCraft | SmartScreen avisa (instalador sin firmar); se instala | |
| 4 | Aceptar el bloque de configuración de Claude (con Claude **cerrado del todo**) | Crea copia `.bak-FECHA` y escribe el bloque | |
| 5 | Autorizar scripts del demonio (escribir SI) | Hash mostrado y guardado | |
| 6 | `instalar_entorno.log` | Termina en `RESULTADO: OK` o `AVISOS` explicados | |
| 7 | Reiniciar Claude Desktop | Aparecen las herramientas `solidcraft` | |
| 8 | Crear Project, pegar el prompt, abrir chat en la app de escritorio, conectar la carpeta de trabajo | Claude ve `device_*` y `solidcraft__*` | |
| 9 | Doble clic en `lanzar_todo.bat` | `lanzar_todo.log` acaba en `RESULTADO: OK` | |
| 10 | Pedir "Empieza el arranque inicial" | Caja 40×30×20 mide 24000 mm³ y se exporta un STL | |
| 11 | Mandar la foto | Claude pregunta ≤3 cosas y modela | |
| 12 | Exportación y 3MF | Ficheros en `salida\<pieza>\` con nombre `pieza_vX_medidas.ext` | |
| 13 | Abrir el 3MF en el laminador y laminar | Claude comprueba filamentos por captura y **para antes de imprimir** | |
| 14 | Decir "GUARDA PROYECTO" | Escribe los ficheros de memoria y dice cuáles | |

## Qué enviar si algo falla
`instalar_entorno.log`, `lanzar_todo.log`, versión de Windows y de Claude Desktop, en un issue (revisa que no lleven tu nombre de usuario).
