# SolidCraft: API, fallos conocidos y coste en tokens

Auditoría hecha con SolidCraft 0.27.1: 542 comandos, **109 probados** con ~140 trabajos sueltos sobre una caja 40×30×20. "Sin error" **no** es "correcto": los sólidos se contrastaron con el volumen calculado a mano (35 de 35 coinciden, ≤0,01 %); los bocetos solo se comprobó que el comando se acepta.
**No probado:** `surface.*`, `sheet.*`, `render.*`, `view.*`, `solid.web`, `boundary_fill`, `pattern.path`, `component.move_*`, `occurrence.*`, `config.*`, `file.send_to_slicer`.

## Comportamientos que hay que conocer
| Hallazgo | Qué hacer |
|---|---|
| **Un parámetro con nombre desconocido se ignora sin error** | Comprueba el efecto (volumen/`measure`); copia el nombre exacto de `describe_command` |
| Un comando inexistente falla y sugiere el parecido | Sin riesgo |
| Un parámetro obligatorio mal formado falla con paso y motivo en una línea; el eval **para en el primer error** | Lee solo esa línea |
| `file.export` / `file.save_mesh` / `save` **no crean la carpeta** | Créala antes |
| `solid.bounding_solid` **añade un cuerpo** (volumen ×2) | Quítalo antes de medir o exportar |
| `solid.thread` es cosmético | Para rosca real, `modeled:true` (sin probar) |
| Cortar con un plano que toca la cara falla ("does not split the body") | Plano `{origin, normal}` dentro del cuerpo |
| `solid.rib` sin `depth` falla | Da `depth` |
| `edit.restore_checkpoint` pide `checkpoint:` (id de `edit.checkpoint`) | Guarda el id |
| El `eval` del CLI devuelve el diseño, **no** el resultado de `inspect.*` | Para `inspect.*`, MCP con ventana, o `measure` por cuerpo |
| `solid.combine join` de 5 cuerpos a la vez falló (esfera tangente a cilindro) | Une de una en una; evita tangencias |
| Las copias de `solid.pattern.*`/`solid.mirror` se llaman `B (2)`, `B (3)`… | Mide una vez para conocer los nombres |
| `solidcraft_open` sobre un fichero ya abierto no recarga | Cierra la pestaña o reinicia con `cerrar`/`abrir` |
| `batch` hace **rollback completo** si un paso falla | `rollback:false` y `verbose:false`; guarda tras cada fase |
| `component.from_bodies` nombra la ocurrencia `NOMBRE:1` | `joint.origin` pide `A:1`, no `A` |
| `joint.sweep` sin `step` devuelve ~90 entradas | Da siempre `step` (15 o más) |
| `joint.create` pone B opuesto a A si ambos orígenes tienen la misma `z` | Da a B la `z` contraria (`[0,-1,0]` frente a `[0,1,0]`) |
| `component.list` con 2 piezas ≈ 1,2 mil tokens | Evítalo |
| `screenshot` ≈ 1 MB (1680×1002) | Solo al cerrar una fase |
| Un `batch` con SVG grandes (~9 000 puntos) tarda >60 s: el puente dice "no respondió" **aunque el lote termina** | No repetir: espera, `screenshot`/recuento de cuerpos y guarda |

## Nombres de parámetros que fallaron al primer intento
`sketch.constraint.*` → `a`, `b` · `sketch.text` → `at` · `sketch.trim`/`extend` → `curve`, `at` · `sketch.slot.center_point` → `end` · `sketch.pattern.rectangular` → `count`, `spacing` · `sketch.project` → `refs: [{edge:[x,y,z]}]` · `construct.axis.two_points` → `a`/`b` como `{vertex:[x,y,z]}` · `timeline.inspect` → `feature` · `document.metadata.set` → claves `project, part_number, revision, author, organization, description, license` · `parts.fastener` → `family`, `size` · `component.create` → omitir `parent` si es la raíz.

## Tokens
| Medida | Coste | Regla |
|---|---|---|
| `list_commands` sin filtro | **302 181 caracteres** | **Nunca sin filtro.** `describe_command ID` |
| Error del CLI | ~150 caracteres | Prefiere el ejecutor para probar |
| `measure` de una caja (JSON) | ~1 500 caracteres | Lee solo `total.volume_mm3` |
| `inspect_design` por MCP | miles de tokens (todo el historial) | Usa `measure` |
- El ejecutor corre ~100 trabajos de 2-20 comandos en ~3 min sin pasar el JSON por la conversación: **probar y regresionar por el ejecutor**; el MCP para la ventana e `inspect.*`.
- No copies base64 a mano al PC (CRC erróneo): genera el fichero en el PC con un script.

## Regla de diseño: volumen correcto no demuestra que funcione
Un modelo con todos los volúmenes bien tenía dos fallos de diseño (ruedas sin tocar el chasis; chasis a ras de suelo) que solo vio una persona. **Antes de enseñar un diseño con piezas móviles o ensambladas:**
1. **Filtro de geometría:** `python sistema\pruebas_api\comprobar_geometria.py resultados\TRABAJO_medidas.json --exige PIEZA SOPORTE MAXGAP ...` (cabe en la cama, piezas sueltas, solapes, que cada pieza llegue a su soporte). Límite: usa cajas, no geometría real.
2. **Lista por pieza que gira o desliza:** eje y qué lo guía; holgura radial y axial; qué la apoya parada; qué la bloquea al moverla; cómo se imprime (soporte, orientación, gotas al aire).
3. **Cotas de conjunto** siempre con la peana incluida.
4. **`joint.sweep`, `inspect.interference` e `inspect.clearance` NO detectaron** colisiones claras ni holguras de 0,3-0,4 mm en las pruebas. No valides articulaciones con ellos: calcula las holguras en el diseño y valida imprimiendo.

## Regresión barata tras actualizar SolidCraft
`python pruebas_api\gen2.py PREFIJO` y `gen3.py PREFIJO` copian los trabajos a `trabajos\`; espera ~1 min y `python pruebas_api\resumen.py PREFIJO_api_`. Un cambio de nombre de parámetro aparece como línea `error`; diferencias de volumen delatan cambios de comportamiento.
