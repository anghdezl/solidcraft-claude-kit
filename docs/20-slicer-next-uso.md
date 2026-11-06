# Anycubic Slicer Next: uso

Probado con **Anycubic Slicer Next 2.0.0.3** (derivado de OrcaSlicer, interfaz en castellano) y una Kobra S1 con caja ACE de 4 ranuras. Con otro laminador o impresora, los nombres de menú pueden cambiar: **verifica con captura antes de pulsar**.

## Antes de lanzar cualquier impresión
1. **Sincronizar filamentos con el ACE** (botón junto al bloque Filamento).
2. Revisar los perfiles de filamento y de proceso.
3. Multicolor: *Volúmenes de limpieza* → multiplicador (en el PC de origen se usó **0,65**; es un valor de ese usuario, no una regla).
4. ⚠️ **Diálogo "Iniciar impresión":** el mapeo colores → ranuras físicas es aparte. Si dos colores van a la misma ranura, la pieza sale de un solo color y el único aviso es un texto amarillo poco visible. **Revísalo siempre** y pídele confirmación al usuario antes de iniciar.

## Cambio de color a partir de una capa
1. Laminar → vista previa. 2. Slider vertical: capa donde **empieza** el color nuevo. 3. Clic derecho en el "+" → **"Cambiar filamento"** → ranura nueva (**no** "Añadir cambio de color": es una pausa manual M600). 4. Relaminar y comprobar las capas anterior y siguiente.
- Alternativa: clic derecho en el objeto → *Modificador de rango de altura*.
- Con pocos cambios se puede quitar la torre de purga: la impresora purga igual.

## 3MF multiparte (el que genera `build_3mf.py`)
- Formato Bambu/Orca: una parte por filamento; el laminador conserva el filamento de cada parte (comprobado con 3MF de 3 colores).
- Los 3MF descargados de MakerWorld/Bambu pierden los colores: repintar.
- Al importar varios STL a la vez, pregunta si cargarlos como un objeto con varias partes: responde que sí.

## Vista previa
- La leyenda puede mostrar la velocidad volumétrica (mm³/s) para comprobar el tope del filamento.
- Panel de filamento: Modelo / Soportes / Descargado (purga) / Torre / Total.

## Dónde está cada ajuste (comprobado en 2.0.0.3)
| Ajuste | Dónde |
|---|---|
| Desplazamiento de Z | Impresora (lápiz) → Información básica |
| Capas superiores / inferiores | Proceso → Fuerza → Cubiertas superiores/inferiores |
| Tipo de borde | Proceso → Otros |
| Torre de purga | Proceso → Multimaterial |
| Pata de elefante | Proceso → Calidad → Precisión (modo avanzado) |
| Tabla de purgas y multiplicador | Botón **"Volúmenes de limpieza"** del bloque Filamento |

## Agujero con pieza negativa y exportar el G-code
- **Agujero:** clic derecho en el objeto (lista) → *Añadir pieza negativa* → *Cilindro*. Se coloca fuera del objeto: *Escalar* (S) con "Escala uniforme" desactivada (campo: Ctrl+A, escribir, Tab) y *Mover* (M); las coordenadas son las del objeto (origen = el del STL). Altura mayor que el grosor y Z = mitad de la altura. Elegir un sitio con pared ≥ 2 mm hasta el borde.
- **Exportar G-code:** Ctrl+G; el tipo disponible es `.gcode.3mf` (zip con `Metadata/plate_1.gcode`, legible con `unzip -p`). Guardar proyecto: Ctrl+S.
- **Verificar, no suponer:** lee los valores reales del G-code (relleno, velocidades, flujo), no el nombre del perfil.

## Control desde Claude (`computer_*`)
- Traer la ventana al frente con `computer_open_application` puede abrir **otra instancia** del laminador. El proyecto vigente es el último guardado: cierra las demás sin guardar.
- **No documentado en el origen:** la secuencia exacta para abrir un 3MF desde Claude (¿arrastrar, Ctrl+O, abrir con el programa asociado?). Pruébala con capturas y anótala en `ESTADO_LOCAL.md`.
