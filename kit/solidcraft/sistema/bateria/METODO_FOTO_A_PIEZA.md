# Método foto → pieza en SolidCraft (v0.1, 31/10/2026)

Hecho a partir de la batería (`bateria.py`, 12 casos, 12/12 con 100 puntos) y de las dos fotos reales (escuadra con cuna, bloque con rampa).

## Procedimiento
1. **Leer la foto**: ejes (X, Y, Z), vistas y sentido de cada cota. Tabla de cotas con su legibilidad (alta/media/baja).
2. **No inventar**: lo ilegible o ausente (espesores, posición de agujeros) se pregunta o se marca como supuesto en un parámetro.
3. **Interpretar la forma** en palabras (qué es base, pared, cuna, nervadura) y confirmar lo dudoso con el usuario.
4. **Geometría explícita**: perfil como lista de puntos (x,z) y centros de agujeros como coordenadas. Evita errores de plano de boceto (XZ: y del boceto = −Z).
5. **Calcular a mano** volumen y centro de masas esperados antes de construir.
6. **Construir por etapas** en `batch`: parámetros → cuerpo base → cortes → agujeros/patrones.
7. **Verificar**: `measure` frente al cálculo, caja envolvente, centro de masas y dos capturas desde ángulos distintos (la vista iso por defecto mira desde atrás: usar `camera` con yaw ≈ 2,4 para ver el frente).
8. **Guardar `.sc` y exportar STL** con nombre identificable; puntuar con `python3 bateria.py`.

## Lecciones técnicas (comprobadas)
| Tema | Lección |
|---|---|
| Puntos de boceto | `rectangle.two_point` y `circle.center` solo admiten números en los puntos; `sketch.line` admite expresiones con parámetros |
| Grados de libertad | `sketch.line` con puntos numéricos deja el boceto sin acotar (dof 10-16); la extrusión funciona igual, pero no es paramétrico. Usar parámetros o `sketch.dimension` |
| Cortes cruzados | Dos taladros que se cruzan: hacerlos con boceto + `extrude cut`, no con cilindros primitivos (límite de booleanas curvas). Volumen exacto al cálculo (Steinmetz) |
| Plano desplazado | `sketch.create` acepta `offset` (p. ej. nervadura en y=12,5); comprobado con el centro de masas |
| Agujeros | `solid.hole` con `type: counterbore`, `depth` para ciegos y `pattern.circular` / `pattern.rectangular` funcionan |
| `solid.shell` | Una cara abierta + espesor: volumen exacto con esquinas vivas |
| Simetría | `extrude` con `direction: symmetric` usa `distance` como espesor total |
| Tolerancias medidas | B-rep frente a cálculo ≤0,009 %; STL frente a cálculo ≤0,071 % (revolución); caja ≤0,015 mm |
| Eficiencia | Un `batch` con `rollback:false` puede llevar new_design, construcción, `measure`, `save` y `export` de 2-3 piezas |

## Límites de la puntuación
- Volumen, caja y centro de masas no detectan todo (un agujero a otra altura puede dar el mismo volumen). Por eso se añade la captura.
- Los 12 casos salieron al primer intento: la batería aún no discrimina. Faltan casos que hayan fallado antes (revolución con perfil curvo, chaflanes, barrido, 3MF multiparte, ensamblaje con holguras).
- Los casos parten de enunciados con cotas, no de fotos: la lectura de la foto sigue siendo el punto débil y necesita confirmación del usuario.

## Qué dice la investigación (moderada)
- Vision2CAD (arXiv 2609.22688): referenciar caras/aristas por ID explícito y verificar con una vista renderizada, con corrección y máximo 2 reintentos. Sin referencia explícita la métrica baja de 0,473 a 0,419; sin verificación, a 0,448. Límites que cita: una sola vista de entrada y piezas con muchas etiquetas.
- Aplicado aquí: tabla de puntos/cotas explícita (paso 4) y comparación de capturas (paso 7).
- El artículo de AAAI sobre dibujos 2D → 3D paramétrico no se pudo leer (acceso bloqueado).

## Siguiente (sin imprimir)
1. Casos N5: revolución con perfil curvo, chaflanes, 3MF multiparte a Slicer Next (cierra la duda de `20`).
2. Pasarme fotos reales y puntuarlas con la lectura de cotas confirmada.
3. Añadir centro de masas esperado a los casos que faltan.
