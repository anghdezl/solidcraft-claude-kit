# SolidCraft: piezas orgánicas (lofts) y ejecutor local

SolidCraft es CAD paramétrico: va bien en piezas técnicas; en orgánicas se atasca al acumular superficies lofteadas. Para realismo, usa escultura de mallas o un STL externo (con licencia adecuada). Prueba hecha: caballo encabritado estilizado (3 cuerpos, ≈218×92×246 mm, 425 cm³), dado por cerrado porque sirvió para ver los límites.

## Receta que funcionó
| Parte | Método |
|---|---|
| Torso, cuello, cabeza | 1 loft por parte, 5-7 secciones elípticas en planos inclinados |
| Patas | Segmentos de 2 secciones + esferas en las articulaciones; una pata = 1 cuerpo; se espeja el cuerpo ya unido (`solid.mirror`, plano `XZ`) |
| Cola, crin, orejas, peana | Loft de 2-6 secciones; peana = elipse extruida 6 mm; cascos 1 mm dentro de la peana |
- Sección en el plano `{origin:[x,y0,z], x_dir:[0,1,0], y_dir:[-sen,0,cos]}` (`ang` en grados desde +X hacia +Z); elipse con `center:[0,cy]`, `major:[a,cy]` y `minor_radius:b`. +y del boceto = lado dorsal.
- Se define con una **tabla de estaciones** `(x, z, ang, a, b, cy)`; cada sección son 3 pasos (`sketch.create`, `sketch.ellipse`, `sketch.finish`). `gen_secciones.py` convierte un trabajo compacto en el lote de comandos.

## Límites medidos
- Unir 37 piezas de golpe: >10 min y la app quedó "No responde". **Unir por tramos pequeños, lo pequeño primero y lo grande al final.**
- Uniones: 0,3-3,4 s al principio; 6-41 s con el cuerpo ya grande; esferas tangentes a lofts: 26-29 s por pata. Las piezas deben **solapar** claramente, no rozar. Superficies casi tangentes = lentas (una unión superó 60 s y colgó la ventana, aunque terminó después).
- Patas finas (8-10 mm) son frágiles al imprimir.

## Ahorro de tokens
1. **Guarda el `.sc` tras cada fase.** Un cuelgue sin guardar obliga a reenviar todo.
2. Envía tablas de estaciones, no JSON redactado a mano; un lote por extremidad y los `combine` sueltos (cada uno < 60 s).
3. Cada paso de un lote devuelve su eco aunque `verbose:false`: menos pasos = menos tokens → usa el **ejecutor local**.

## Ejecutor local
- Flujo: Claude deja un trabajo en `sistema\trabajos\NOMBRE.json` → `ejecutor_trabajos.py` lo convierte en comandos, ejecuta `solidcraft-cli eval` (medidas) y, si hay `"salida"`, `run --out` (STL en `sistema\salida\`) → deja `resultados\NOMBRE.json` (estado, tiempos, errores) y mueve el trabajo a `trabajos\hechos\`. Claude solo lee el resultado. Sin ventana abierta, sin límite de 60 s, pero sin captura. Serie, timeout 1800 s por trabajo.
- Formato: `{"salida":"x.stl","pasos":[...]}`. Pasos: `["loft",nombre,y0,[[x,z,ang,a,b,cy],...]]`, `["seg",nombre,y0,[x0,z0],[x1,z1],a0,b0,a1,b1]`, `["esfera",nombre,[x,y,z],r]`, `["elipse_extruida",nombre,[cx,cy],semieje_a,b,altura]`, `["union",destino,[herramientas]]`, `["espejo",[cuerpos]]`, `["cmd",{comando en bruto}]`.
- Ejemplo: `sistema\trabajos_ejemplo\prueba_ejecutor.json` (21 comandos; volumen total 151 838,14 mm³; `run --out` exporta **todos** los cuerpos a un solo STL).
