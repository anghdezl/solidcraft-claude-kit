# SolidCraft: método, lecciones y tolerancias

## Método por pieza
Parámetros → bocetos y sólidos → `measure` contra el cálculo a mano → interferencias si hay varias piezas → guardar `.sc` → **exportar STL** en `salida\<pieza>\` con nombre identificable. Pregunta antes de `new_design` si hay trabajo sin guardar.

## Qué se ha comprobado (batería, piezas de volumen conocido)
| Nivel | Pieza | Resultado |
|---|---|---|
| 1 | Primitivas y booleanas (cohete) | OK; aviso interno de booleana ~0,0002 mm sin efecto |
| 2 | Placa 90×50×5 con ranura y 4 agujeros con rebaje | 20261,28 frente a 20261,13 calculado |
| 3 | Caja 60×40×30 pared 2 con tapa | 0 interferencias, volúmenes = cálculo |
| 4 | Pieza desde foto con 2 cotas (bisagra 40×60) | ~1 mm de error: vale para formas, **no para encajes** |
| 5 | 3MF multiparte → laminador → impresión | Llega al laminador con filamento por parte; las piezas impresas funcionaron |
La batería automática (`sistema\bateria\bateria.py`) puntúa STL contra volumen y caja calculados: 12/12 con 100 puntos, pero salió al primer intento, así que **aún no discrimina**. Volumen, caja y centro de masas no detectan todo: hace falta captura.

## Tolerancias de referencia (de UNA impresora; valídalas con la tuya)
Hueco XY 0,30 mm (validado en bisagras con capa 0,20), hueco Z 0,40 mm (2 capas), agujero para filamento de 1,75: Ø2,10. Bisagra con pasador de filamento y print-in-place con pasador en rombo (caras a 45°, sin soportes) funcionaron a 0,30. Con otra máquina o material, repite una pieza de prueba antes de fiarte.

## Lecciones de modelado
- Un boceto de ranura necesita 3 cotas extra para quedar con 0 grados de libertad. El rectángulo desde el centro queda anclado al origen.
- Las booleanas entre primitivas pueden avisar ("Boolean retry"): comprueba que el volumen coincide con el cálculo.
- El plano XZ tiene normal +Y y el eje y del boceto es −Z.
- **Rutas en formato Windows y dentro de la carpeta permitida. La carpeta de la pieza hay que crearla antes de exportar/guardar** (SolidCraft no la crea y el error es confuso).
- `rectangle.two_point` y `circle.center` solo aceptan números en los puntos; `sketch.line` acepta expresiones. Con números el boceto queda sin acotar: usa parámetros o `sketch.dimension` si debe ser paramétrico.
- Dos taladros que se cruzan: boceto + `extrude cut` por plano. Los cilindros primitivos que cortan superficies curvas pueden fallar.
- `sketch.create` acepta `offset`; `extrude` con `direction: symmetric` usa `distance` como espesor total.
- La captura iso por defecto mira desde atrás; para el frente: `camera` con yaw ≈ 2,4. `inspect.section` con la cámara desde atrás (yaw π) enseña el corte.
- Un `batch` con `rollback:false` puede llevar `new_design`, construcción, `measure`, `save` y `export` de 2-3 piezas.
- Una foto con perspectiva y pocas cotas da formas, no encajes. Método foto → pieza: `sistema\bateria\METODO_FOTO_A_PIEZA.md`.
