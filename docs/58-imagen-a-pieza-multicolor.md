# Imagen → relieve multicolor por capas (llaveros, parches)

Receta validada con un logo de 3 colores (negro, blanco, amarillo) impreso a 110 y ~80 mm: resultado "perfecto". Con texto o trazos finos falló a 80 mm (trazos ≈0,4-0,5 mm ilegibles); se pasó a 120 mm. Aplica a cualquier imagen plana con pocos colores.

## Antes de empezar: preguntar
Tamaño, nº de colores, qué filamento va en cada ranura y si quiere boceto de aprobación antes de la versión final.

## Requisitos de calidad (por defecto)
1. Contornos y letras suaves y rectos, sin dientes de sierra.
2. Sin borde exterior de otro color: el contorno es del color base (salvo que el usuario pida un aro).
3. Líneas finas en su color real, no en el de la base.
4. Sin color de base asomando bajo otro color y sin agujeritos.
5. Detalles finos del original conservados; solo se pierde lo que la boquilla no puede imprimir.

## Apilado de capas (base → medio → superior)
| Capa | Altura | Contenido |
|---|---|---|
| Base (color del contorno) | 0–0,8 mm | Silueta completa |
| Medio (p. ej. negro) | 0,8–1,6 mm | Todo el interior + blanco dilatado |
| Superior (p. ej. blanco) | 1,6–2,4 mm | Solo las zonas blancas, encima del negro |
Cada capa se apila sobre la anterior (nunca piezas de colores pegadas por el lateral): sin juntas ni huecos; solo **3 cambios de filamento**.
Alternativa sin booleanas (parche con muchos detalles): disco base macizo + una capa superior con un SVG por color (extrusión `new`).

## Procesado de la imagen (Python/OpenCV)
- Clasificar por canales (blanco = azul alto; amarillo = rojo alto y azul bajo; negro = rojo bajo). Silueta = contorno exterior cerrado de la zona clara.
- Ampliar ×4 (cúbica) + gaussiana y luego umbralizar: bordes lisos. Escala 0,1 mm/px.
- **Borde exterior forzado en color base** (~0,45 mm): erosiona los demás colores esa distancia desde la silueta.
- Piezas ≥ 15 px² (~0,15 mm²) se conservan; menores pasan al color de debajo. Líneas finas dilatadas a ≥ 0,4 mm. Motas blancas < 35 px² descartadas.
- **No apliques apertura/cierre morfológico fuerte** (redondea puntas y borra detalle). `approxPolyDP` a 0,45 px; SVG con `fill-rule evenodd`.
- Compara siempre recortes fuente vs resultado antes de pasar a SolidCraft.
- **Foto con perspectiva:** ajusta una elipse al disco principal y deshazla con una afín a círculo antes de clasificar; escala por un radio conocido; trazos finos < 0,45 mm: discos de 0,45 mm sobre su esqueleto (`skimage.skeletonize`), **no** dilatar la zona (deja bultos en las puntas).

## SolidCraft
- Por capa: `sketch.create` (plano XY, `offset` = altura de inicio) → `sketch.insert_svg` → `sketch.finish` → `solid.extrude` (`new`). `insert_svg` trata el SVG con y hacia abajo: **no voltees la y**.
- **`insert_svg` pone el origen del viewBox en (0,0) del boceto:** con `viewBox="-50 -50 100 100"` el dibujo queda en x 0…100, y −100…0. Los demás cuerpos (disco base) deben llevar ese desfase; si ya están hechos, `solid.move` con `copy:false`.
- **Sin agujero en el modelo** (se hace en el laminador, para poder escalar). Deja zona sólida donde pueda ir.
- El `batch` con `verbose:false` devuelve ~96 KB por cada `insert_svg`: no lo leas; si lo guardas en fichero, comprueba con `grep` (`completed`, `ok`, `curves`, `profiles`).
- Guarda `.sc`, exporta un STL por color (cuerpos del mismo color en un STL) y monta el 3MF con `build_3mf.py` y un manifiesto.
- Al copiar ficheros al PC usa **nombres nuevos** en cada envío (reutilizar un nombre entregó una vez contenido antiguo); verifica contando `L` en el SVG.

## Perfil de laminado de partida (valores del usuario original; compruébalos en el G-code)
Capa 0,16 (primera 0,20), relleno **98 %** (con 7 % salían puentes sobre vacío bajo el color superior y "agujeritos"), paredes Arachne × 2, pared exterior 175 mm/s, sin torre ni soportes, factor de limpieza 0,65, costura alineada atrás, planchado `top` al 5 %. Revisa siempre en la vista previa: borde, cuñas, líneas finas, puentes.

## Límites
- Detalles < 0,4-0,5 mm están al límite de la boquilla de 0,4 mm: pueden perderse aunque estén en el STL. La cuña pequeña (~0,8×0,3 mm) es el detalle más arriesgado: si no sale, pásala al color vecino.
- **Cambiar de tamaño:** abre el `.sc` y `solid.scale` a todos los cuerpos con `factors:[k,k,1]` y `origin:[0,0,0]` (el grosor y los cortes de capa no cambian). Después guarda con otro nombre, exporta y monta el 3MF. Cortar con todos los perfiles de un boceto muy denso falla con `planar tool comparison budget exceeded`.
