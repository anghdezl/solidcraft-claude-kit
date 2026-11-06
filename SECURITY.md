# Política de seguridad

## Qué protege este kit
Este kit da a Claude control sobre tu PC (ficheros, SolidCraft, pantalla). Por eso la seguridad es parte del diseño:

- El **demonio de órdenes** solo acepta una lista cerrada de acciones y solo ejecuta `.py` cuyo hash SHA-256 hayas autorizado tú (`%APPDATA%\SolidCraftOrdenes\autorizados.txt`).
- Claude **no borra** por iniciativa propia ni inicia impresiones sin tu orden.
- El instalador pregunta antes de cada cambio, hace copia de `claude_desktop_config.json` y no toca el resto de tu configuración.

## Riesgos que debes conocer
- **Inyección de instrucciones:** un repo, fork o documento ajeno puede contener órdenes dirigidas a Claude. Carga solo `github.com/anghdezl/solidcraft-claude-kit`.
- El instalador de SolidCraft **no está firmado** (SmartScreen avisará).
- Si cambias un script del demonio, debes reautorizarlo; no autorices hashes que no entiendas.

## Cómo reportar una vulnerabilidad
**No abras un issue público.** Usa el aviso privado de GitHub: pestaña *Security* → *Report a vulnerability* (<https://github.com/anghdezl/solidcraft-claude-kit/security/advisories/new>). Indica versión del kit (`VERSION`), pasos para reproducirlo y su impacto.

No hay equipo de seguridad ni plazos garantizados: es un proyecto personal. Se intentará acusar recibo en pocos días y corregir lo grave en la siguiente versión.

## Versiones con corrección
Solo la última versión publicada recibe correcciones.
