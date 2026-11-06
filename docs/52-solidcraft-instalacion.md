# SolidCraft: instalación, arranque y seguridad

## Qué es
CAD paramétrico de código abierto en Rust: github.com/tangency-labs/solidcraft. Escritorio (`solidcraft.exe`), CLI (`solidcraft-cli.exe`), web y **servidor MCP** (`solidcraft-cli mcp`). Madurez temprana; instaladores de Windows sin firmar (aviso de SmartScreen). Probado con la **versión 0.27.1** en `C:\Program Files\SolidCraft\`: 542 comandos; caja 40×30×20 → 24000 mm³ exacto. Importa 3MF/STL/OBJ solo como malla; exporta STEP, 3MF, STL, OBJ, IGES. El MCP solo lee/escribe en la carpeta del diseño abierto, la de recuperación, la temporal y las de `--allow-path`.

## Carpeta `solidcraft\` (copiada desde `kit\solidcraft\`)
- **Raíz:** `lanzar_todo.bat` (único arranque), `parar_todo.bat`, `salida\` (una carpeta por pieza), `sistema\` (técnico).
- `lanzar_todo.bat` abre la ventana con `--control 27878`, el ejecutor y el demonio de órdenes sin duplicarlos, y deja `sistema\logs\lanzar_todo.log` (se sobrescribe cada vez) con una línea **`RESULTADO: OK|FALLO`**. Claude: tras pedir que lo ejecute, **leer solo ese log**. Ejecutor y demonio arrancan sin ventana: su estado está en `ejecutor_status.json` y `ordenes_status.json` (latido < 8 s = vivo).
- Si usas otra ruta de SolidCraft, edita `EXE` en `sistema\lanzar_solidcraft_ventana.bat` y la ruta de `solidcraft-cli` en `instalar_solidcraft.py`.

## Ficheros de `sistema\`
| Fichero | Para qué |
|---|---|
| `instalar_entorno.py` (+ `..\instalar_entorno.bat`) | Asistente: diagnóstico, instalación de SolidCraft (winget `bherbruck.SolidCraft` o MSI), configuración de Claude Desktop, autorización. Log `logs\instalar_entorno.log`. Sin probar en Windows limpio |
| `instalar_solidcraft.py` | Instala (winget) si falta, hace comprobaciones y escribe log. Solo librería estándar |
| `ejecutor_trabajos.py` | Vigila `trabajos\`, ejecuta con `solidcraft-cli`, escribe `resultados\` |
| `demonio_ordenes.py` | Acciones de lista cerrada desde `ordenes.txt` (abajo) |
| `comprobar_todo.py` | Comprobaciones de `lanzar_todo.bat` (`vivo ventana|ejecutor|ordenes`, `final`, `log`) |
| `gen_secciones.py` | Trabajo compacto de lofts → comandos (`54`) |
| `build_3mf.py` + `manifiestos_3mf\*.json` | 3MF multiparte desde un manifiesto: `python build_3mf.py manifiestos_3mf\PIEZA.json [--juego N] [--dir CARPETA_STL] [--out F.3mf]`. Manifiesto: `titulo`, `descripcion`, `carpeta_stl`, `prefijo`, `salida`, `partes [[stl, nombre, ranura]]` |
| `bateria\`, `pruebas_api\` | Batería de piezas con volumen conocido y regresión de la API (`53`, `56`) |

## Demonio de órdenes
- Claude escribe **una línea** `ACCION [arg]` en `sistema\ordenes.txt`; el demonio la ejecuta, la **borra** y deja el resultado en `logs\ordenes.log` y `resultados\ordenes_ultimo.json`.
- Acciones: `estado`, `probar`, `comprobar_sintaxis X.py`, `solidcraft_abrir`, `solidcraft_cerrar` (no guarda: guardar antes), `solidcraft_matar` (forzado), `ejecutor_arrancar|parar|reiniciar`, `ordenes_reiniciar|parar`, `python_script X.py`. **No ejecuta comandos libres.**
- **Seguridad:** un `.py` solo corre si su SHA-256 está en `%APPDATA%\SolidCraftOrdenes\autorizados.txt`, carpeta a la que Claude no accede. El usuario autoriza con `lanzar_ordenes.bat autorizar [fichero.py]` (muestra el hash y pide escribir SI; sin nombre, los tres scripts básicos). **Tras cualquier cambio de un script hay que reautorizar.** No intentes saltarte esto.

## Conexión con Claude
- Con la sesión de Claude enlazada al PC y la ventana abierta por `lanzar_todo.bat`, Claude se conecta a la ventana (modelado en vivo, captura, guardar, exportar). Una ventana abierta desde el icono **no escucha** el puerto: ciérrala y usa el `.bat`.
- **Registro del servidor MCP en Claude Desktop:** bloque `mcpServers.solidcraft` con `command` = ruta de `solidcraft-cli.exe` y `args` = `["mcp","--allow-path","<carpeta de trabajo>"]` (ver `claude_desktop_config.snippet.json`). Lo aplica `instalar_entorno.py configurar --aplicar` (simulación por defecto, copia de seguridad, conserva el resto del fichero, rechaza JSON corrupto).
- **Ruta del fichero:** en instalaciones MSIX/Store/winget de Claude Desktop la app lee `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`, **no** `%APPDATA%\Claude\...`, y el botón *Editar configuración* puede abrir el equivocado (fuente: incidencia anthropics/claude-code#26073). Edítalo con Claude Desktop **cerrado del todo** (también la bandeja). Claude no debe editarlo.
- Con el servidor registrado y la sesión enlazada al PC, el servidor `solidcraft` aparece como anunciado en `get_device_info` (comprobado en el PC de origen).
- Las banderas `--control` y `--allow-path` no aparecen en el README público de SolidCraft; se usan y funcionan en 0.27.1, pero pueden cambiar en versiones nuevas (la 0.10 ya añadió un token por arranque al puerto de control). Tras actualizar SolidCraft, repite la prueba de la caja.
- Ventana colgada: `solidcraft_cerrar`; si no, `solidcraft_matar`; luego `solidcraft_abrir`. La conexión vuelve sola.
- Si SolidCraft se cierra solo y `running` queda vacío: reabrir la aplicación y `new_design` reconecta.
- Los `.~*.sc.lock` junto a cada `.sc` son del programa con la pieza abierta: no moverlos ni borrarlos con la app abierta.
