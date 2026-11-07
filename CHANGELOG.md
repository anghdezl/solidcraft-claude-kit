# Historial de cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/); versiones según [SemVer](https://semver.org/lang/es/).

## [Sin publicar]
### Corregido
- Instalador: si Python no valida el certificado de GitHub (Windows recién instalado, `CERTIFICATE_VERIFY_FAILED`), la descarga se reintenta con `curl.exe`/PowerShell, que usan el almacén de certificados de Windows. La verificación TLS nunca se desactiva. Hallado en la VM.
- Instalador: SolidCraft se instalaba con un ID de winget (`bherbruck.SolidCraft`) que **no está verificado** y falló en la VM (`winget` no lo encuentra). Ahora descarga el MSI oficial fijado a la 0.27.1 (la probada), muestra su sha256 y lo ejecuta con `msiexec`, con confirmación.
- Instalador: ya no falla (WinError 32) si se elige como carpeta de trabajo la del propio repo; la rechaza con un aviso y propone la carpeta que lo contiene. Hallado en la primera prueba en VM.

### Cambiado
- `LEEME_CLAUDE.md`: el arranque funciona con la frase "carga este repo de GitHub y sigue las instrucciones" aunque no haya URL; descarga del kit sin git comprobada en el PC de origen; indicaciones sobre la carpeta conectada y la carpeta de trabajo.

## [0.1.0] - 07/11/2026
Primera versión pública.

### Añadido
- `PROMPT_PRINCIPAL.md`: instrucciones del proyecto de Claude (agente de diseño 3D), con orden de ficheros de salida y comando GUARDA PROYECTO.
- `LEEME_CLAUDE.md`: pasos de Claude al recibir la URL del repo.
- Documentación (`docs/`): laminado con Anycubic Slicer Next, instalación y API de SolidCraft, lecciones, piezas orgánicas, imagen → pieza multicolor, glosario.
- Instalador (`instalar_todo.bat` / `instalar_entorno.py`): Python, SolidCraft, bloque `mcpServers.solidcraft` con simulación, copia de seguridad y comprobaciones.
- Lanzadores, ejecutor de trabajos, demonio de órdenes con autorización por hash, `build_3mf.py`.
- Licencia PolyForm Small Business 1.0.0, `COMMERCIAL.md`, `SECURITY.md`, `CONTRIBUTING.md` (con CLA), `CODE_OF_CONDUCT.md`.
- Pruebas unitarias y CI en Linux y Windows.

### Limitaciones conocidas
- Instalador no probado todavía en un Windows limpio real (ver `docs/PROBAR_EN_LIMPIO.md`).
- Secuencia de clics del laminador con control de pantalla, otros laminadores/impresoras y tolerancias: sin verificar fuera del PC de origen.
