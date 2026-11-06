# Cómo contribuir

¡Gracias! Las mejores contribuciones ahora mismo son **informes de pruebas en máquinas distintas**: otro Windows, otro laminador, otra impresora.

## Antes de empezar
1. Mira los [issues](https://github.com/anghdezl/solidcraft-claude-kit/issues) por si ya existe.
2. Para cambios grandes, abre antes un issue con la idea.
3. Lo que no hayas probado, dilo: en este repo "no verificado" es una respuesta válida y preferida a una afirmación sin prueba.

## Cambios en el código
- Solo biblioteca estándar de Python en `kit/` (sin dependencias nuevas).
- `python -m unittest discover -s tests` debe pasar.
- No subas datos personales, rutas privadas, claves, `salida\`, `logs\` ni `ESTADO_LOCAL.md`.
- Si cambias un script del demonio, indícalo en el PR: obliga a reautorizar.

## Cambios en la documentación
- Español primero; la versión en inglés se mantendrá aparte cuando exista.
- Cualquier sigla nueva va al glosario (`docs/99-glosario.md`).

## Licencia de tus contribuciones (CLA)
El proyecto se publica bajo [PolyForm Small Business 1.0.0](LICENSE) y el titular ofrece además licencias comerciales (ver [COMMERCIAL.md](COMMERCIAL.md)). Para poder hacerlo, al enviar una contribución (PR, parche o texto):

1. declaras que eres su autor o tienes derecho a aportarla, y
2. concedes a Lito (titular del copyright) una licencia mundial, perpetua, irrevocable y gratuita para usar, copiar, modificar, distribuir y **sublicenciar** tu contribución, incluso bajo otros términos, comerciales incluidos; y
3. conservas la autoría y los derechos sobre lo que aportas.

Marcar la casilla del CLA en la plantilla del PR equivale a aceptar estos términos. Si no estás de acuerdo, no envíes código: puedes seguir ayudando con issues y pruebas.

> Nota: este texto no ha sido revisado por un abogado. Quien necesite certeza jurídica debe consultarlo.

## Conducta
Ver [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
