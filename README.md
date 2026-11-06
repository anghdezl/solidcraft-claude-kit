# solidcraft-claude-kit

Kit para que Claude diseñe piezas 3D con **SolidCraft** (CAD paramétrico de código abierto), las exporte a 3MF multicolor y las lamine en tu laminador, controlando tu PC Windows desde una sesión de Claude Desktop.

Contiene: el **prompt principal** (instrucciones del proyecto de Claude), la **documentación** que Claude consulta bajo demanda (lecciones, API, recetas) y los **scripts de arranque** (`lanzar_todo.bat`, ejecutor, demonio de órdenes, generador de 3MF).

> Origen: sale de un proyecto real con una Anycubic Kobra S1 + ACE y Anycubic Slicer Next. Lo que no es de esa máquina está marcado como "no verificado" en los docs.

## Requisitos
| Requisito | Quién lo pone |
|---|---|
| Windows 10/11 (con `winget`, incluido en las versiones actualizadas) | Tú |
| App de escritorio de **Claude** instalada y con sesión iniciada ([claude.ai/download](https://claude.ai/download)) | Tú (el instalador no la instala) |
| Python 3.8+ | El instalador, con tu confirmación (`winget install Python.Python.3.12`) |
| [SolidCraft](https://github.com/tangency-labs/solidcraft) (probado 0.27.1) | El instalador, con tu confirmación (`winget install bherbruck.SolidCraft`, o el MSI si no hay winget). No está firmado: SmartScreen > "Más información" > "Ejecutar de todos modos" |
| Bloque `solidcraft` en la configuración de Claude Desktop | El instalador, con copia de seguridad y solo tras tu confirmación |
| Laminador + impresora (probado: Anycubic Slicer Next 2.0.0.3, Kobra S1, ACE) | Tú (descarga del fabricante) |
| Un **proyecto** de Claude con el prompt pegado y la conversación abierta **en la app de escritorio de este PC** | Tú: es lo que da a Claude el control de ficheros, SolidCraft y pantalla |
| Git (opcional) | Solo para clonar/publicar el repo |

El kit solo registra un servidor MCP: `solidcraft` (viene en `solidcraft-cli`). En el PC de origen Claude Desktop tiene además un servidor `Filesystem` activo; no se ha comprobado si el flujo lo necesita (el acceso a ficheros y shell funcionó con la carpeta conectada). Si tu app pide activar el control del ordenador o conceder acceso a una carpeta, acéptalo: esos avisos no se pueden automatizar y cómo se activan en tu versión no está verificado aquí.

## Uso rápido: "carga este repo"
Si ya tienes la app de escritorio de Claude y la conversación enlazada a tu PC, basta con escribir:

> Carga este repo y prepáralo todo: https://github.com/anghdezl/solidcraft-claude-kit

Claude lee `LEEME_CLAUDE.md` y `PROMPT_PRINCIPAL.md`, trae el kit a tu carpeta conectada y te pide **una sola cosa que solo puedes hacer tú**: doble clic en `instalar_todo.bat` (instala Python/SolidCraft si faltan, registra el servidor en Claude Desktop y autoriza los scripts). Después reinicias Claude Desktop y sigues. Para que las instrucciones persistan entre conversaciones, pega el prompt en un proyecto (pasos abajo).
Solo carga repos oficiales: un fork puede contener instrucciones que no son tuyas.

## Instalación (10-15 minutos)
1. Instala Claude Desktop e inicia sesión. Clona o descarga este repo.
2. **Doble clic en `instalar_todo.bat`.** El asistente (te pregunta antes de cada cambio):
   1. Comprueba Python; si falta, ofrece instalarlo con winget (después cierra la ventana y repite el doble clic).
   2. Te pide la **carpeta de trabajo** (por defecto `C:\Users\TU_USUARIO\ClaudeSolidCraft`) y copia `solidcraft\`, `docs\` y el prompt. Esa carpeta es la que conectarás a Claude.
   3. Diagnóstico; si falta SolidCraft, lo instala.
   4. Muestra el cambio que haría en `claude_desktop_config.json` (**simulación**), y solo si aceptas lo aplica: exige Claude Desktop cerrado del todo (también en la bandeja), guarda una copia `.bak-FECHA` y conserva el resto de tu configuración.
   5. Autorización de los scripts del demonio (verás el hash y escribes SI).
   Deja el log en `solidcraft\sistema\logs\instalar_entorno.log`.
3. **Reinicia Claude Desktop** del todo.
4. En Claude, crea un **proyecto**, abre `PROMPT_PRINCIPAL.md`, copia desde la línea `---` hasta el final y pégalo en *Instrucciones del proyecto* (cambia `<CARPETA_TRABAJO>`).
5. Abre una conversación **dentro del proyecto, en la app de escritorio**, conecta la carpeta de trabajo, haz doble clic en `solidcraft\lanzar_todo.bat` y escribe: *"Empieza el arranque inicial"*.
6. Claude te hará hasta 3 preguntas y una prueba mínima (caja 40×30×20 → 24000 mm³ y un STL exportado).

Comandos útiles después: `solidcraft\instalar_entorno.bat diagnostico` (solo lee), `... configurar` (simulación) y `... configurar --aplicar`.

## Qué toca el instalador fuera de la carpeta de trabajo
| Dónde | Qué | Cómo deshacerlo |
|---|---|---|
| `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Roaming\Claude\claude_desktop_config.json` (instalación MSIX/Store/winget; en instalaciones clásicas, `%APPDATA%\Claude\`) | Añade `mcpServers.solidcraft`; copia `.bak-FECHA` al lado | Restaura la copia o borra ese bloque |
| `%APPDATA%\SolidCraftOrdenes\autorizados.txt` | Hashes de los scripts que el demonio puede lanzar | Borra el fichero |
| Programas | Python y SolidCraft (solo si faltaban y aceptaste) | `winget uninstall` |
La app de Claude Desktop en MSIX lee la copia **virtualizada** de la configuración, no `%APPDATA%\Claude`; el botón *Editar configuración* puede abrir el fichero equivocado (incidencia documentada en el repositorio de Claude Code). El instalador usa la ruta que la app realmente lee.

## Uso diario
`lanzar_todo.bat` (doble clic) → mándale a Claude una foto con las cotas → responde sus preguntas → Claude modela en la ventana de SolidCraft que ves en directo, guarda el `.sc`, exporta los STL a `salida\<pieza>\`, monta el 3MF y abre el laminador. **Claude se detiene antes de "Iniciar impresión"**: la orden de imprimir es tuya. `parar_todo.bat` para ejecutor y demonio.

## Seguridad (léelo)
- El demonio de órdenes solo acepta una lista cerrada de acciones y solo ejecuta `.py` cuyo hash hayas autorizado tú. Si cambias un script, reautoriza.
- Claude no borra por iniciativa propia: mueve a `_obsoleto\`. Borrar exige tu permiso en la sesión.
- SolidCraft es de madurez temprana. Tu carpeta de trabajo es lo único que Claude debe tocar.
- No subas a un repo público tus `salida\`, `logs\`, `resultados\` ni `ESTADO_LOCAL.md` (el `.gitignore` ya los excluye).

## Qué NO está verificado
Ver `PROMPT_PRINCIPAL.md`, sección 7. Resumen: otras rutas de instalación, otros laminadores/impresoras, la secuencia exacta de clics para abrir y laminar un 3MF con control de pantalla, y las tolerancias (validadas con una sola impresora). `joint.*` e `inspect.interference` no detectan colisiones de piezas móviles de forma fiable.

## Estructura
```
LEEME_CLAUDE.md          -> qué hace Claude al recibir la URL del repo
instalar_todo.bat        -> asistente de instalación (doble clic)
PROMPT_PRINCIPAL.md      -> instrucciones del proyecto de Claude
docs\                    -> conocimiento que Claude lee bajo demanda (índice en 00-indice.md)
kit\solidcraft\          -> se copia a tu carpeta de trabajo
  lanzar_todo.bat, parar_todo.bat
  sistema\               -> ejecutor, demonio de órdenes, build_3mf.py, batería y pruebas de API
```

## Licencia
Sin licencia todavía: por defecto, todos los derechos reservados y nadie puede reutilizarlo legalmente. Añade un `LICENSE` (por ejemplo MIT) antes de compartirlo. SolidCraft tiene su propia licencia.
