# Declaración de uso de inteligencia artificial

Los autores declaran que, durante el desarrollo del repositorio (agosto a
noviembre de 2026), usaron un asistente de programación basado en modelos
de lenguaje: Claude Code, de Anthropic. Esta declaración cubre todo el
repositorio. El historial de git no distingue qué cambios se hicieron con
el asistente: todos los commits figuran a nombre de los autores, que los
revisaron y aceptaron.

## En qué se usó

| Tarea | Uso del asistente |
|---|---|
| Código | Escribir y reorganizar módulos de ingesta, armonización, Hot-Deck, estimación, cotas, simulación y focalización, a partir de instrucciones de los autores |
| Pruebas | Escribir pruebas automáticas y la prueba de mutación, que reintroduce cada error conocido y comprueba que alguna prueba falle |
| Depuración | Buscar la causa de resultados sospechosos y proponer correcciones (ver los errores corregidos en `CLAUDE.md` y en `docs/seguimiento/RESUMEN_AVANCES.md`) |
| Documentación | Redactar los documentos de resultados (`docs/resultados/`), los anexos de esta carpeta y los README |
| Verificación | Cruzar cifras entre documentos y reportes; buscar cada referencia bibliográfica en la fuente original (`BIBLIOGRAFIA_VERIFICADA.md`) |
| Figuras | Escribir el código que genera las figuras desde los reportes versionados |

## Qué no hizo

- **No generó datos ni resultados.** Toda cifra sale de ejecutar el
  código sobre las fuentes oficiales (GEIH, Sisbén IV y pobreza monetaria
  del DANE). El anexo de trazabilidad (`ANEXO_TRAZABILIDAD.md`) lee cada
  cifra de su reporte en `docs/reports/` y falla si no la encuentra.
- **No tomó las decisiones de investigación.** La pregunta, el diseño,
  las fuentes, los supuestos y la interpretación son de los autores y de
  la dirección de la tesis. Las reglas del director están en `CLAUDE.md`.
- **No es fuente bibliográfica.** Ninguna referencia se tomó de una
  respuesta del asistente sin verificarla en la editorial, la revista, el
  repositorio o una biblioteca.

## Controles

- 262 pruebas automáticas y 56 errores conocidos reintroducidos por
  mutación, en integración continua en cada cambio (`tests/README.md`).
- Validación externa de los indicadores frente a las cifras oficiales del
  DANE (93,9 % de hogares con la misma clasificación de pobreza
  monetaria).
- Cada cambio de armonización o emparejamiento se reproduce con la
  secuencia de validación de `CLAUDE.md` y se compara con los números
  documentados.

Los autores revisaron el código y los textos producidos con el asistente y
son responsables de su contenido.
