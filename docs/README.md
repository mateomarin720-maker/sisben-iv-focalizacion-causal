# Carpeta `docs/`: documentación

Toda la documentación del proyecto, agrupada por para qué sirve.

| Carpeta | Qué hay | Para qué sirve |
|---|---|---|
| [`resultados/`](resultados/README.md) | Un documento por paso, en cuatro carpetas: datos y enlace, diagnóstico con datos reales, simulación y focalización | Revisar los resultados sin correr los scripts. Empezar por su [índice](resultados/README.md) |
| [`reports/`](reports/) | Salidas crudas de cada script (CSV y TXT) | Salidas automáticas; no se editan a mano. La interpretación de cada una está en `resultados/` |
| [`metodologia/`](metodologia/) | [Arquitectura y replicación](metodologia/ARQUITECTURA_Y_REPLICACION.md), [diseño del módulo de simulación](metodologia/DISENO_MODULO_SIMULACION.md), metodología de la pobreza monetaria y comparación de proxies del IPM | Reproducir el proyecto o reutilizarlo; revisar definiciones antes de construir variables |
| [`insumos/`](insumos/) | Diccionarios oficiales, ficha del Sisbén IV, homologaciones y referencias | Consultar qué significa cada variable y de dónde sale |
| [`seguimiento/`](seguimiento/) | Guía de la tesis, resumen de avances y changelog | Saber en qué estado está el proyecto y qué cambió |
| [`anexos_tesis/`](anexos_tesis/README.md) | Anexo de trazabilidad, contrato de datos, método predictivo, bibliografía verificada y figuras del documento | Corregir el documento escrito con cifras que salen del repositorio |
| [`institucional/`](institucional/) | Anteproyecto | Documentos formales de la maestría |

## `insumos/`

- [`DICCIONARIO_GEIH_2024.xlsx`](insumos/DICCIONARIO_GEIH_2024.xlsx) y [`DICCIONARIO_SISBEN_2024.xlsx`](insumos/DICCIONARIO_SISBEN_2024.xlsx): diccionarios oficiales. Todo código de la GEIH se verifica aquí antes de usarlo.
- [`FICHA_SISBEN_IV_FCS_2017.pdf`](insumos/FICHA_SISBEN_IV_FCS_2017.pdf): ficha del Sisbén IV, con los códigos de respuesta.
- [`HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`](insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md): escala común de paredes y pisos entre las dos fuentes.
- [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md): las 8 privaciones del IPM-GEIH y las que no se construyen.
- [`DICCIONARIO_HOTDECK.md`](insumos/DICCIONARIO_HOTDECK.md): variables, llaves y limitaciones del emparejamiento.
- [`DESCRIPCION_TABLAS.md`](insumos/DESCRIPCION_TABLAS.md): las tablas de `data/2_models/`: qué es una fila, su llave y qué script la genera.
- [`DICCIONARIO_DATOS.md`](insumos/DICCIONARIO_DATOS.md), [`DICCIONARIO_IPM_2025.md`](insumos/DICCIONARIO_IPM_2025.md), [`CODIGOS_LOCALIDAD_BOGOTA.md`](insumos/CODIGOS_LOCALIDAD_BOGOTA.md), [`DANE_boletin_PM_2024.pdf`](insumos/DANE_boletin_PM_2024.pdf) y [`referencias_teoricas.md`](insumos/referencias_teoricas.md).

## `seguimiento/`

- [`SEGUIMIENTO_TESIS_2026-11-04.md`](seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md): guía de la tesis desde la tutoría del 3 de noviembre (enfoque, estado y prioridades).
- [`RESUMEN_AVANCES.md`](seguimiento/RESUMEN_AVANCES.md): estado de fuentes, pipeline y pendientes técnicos.
- [`CHANGELOG_PENDIENTES.md`](seguimiento/CHANGELOG_PENDIENTES.md): historial de cambios, más reciente primero.
- [`README.md`](seguimiento/README.md) y [`README_AVANCE_2026-11-02.md`](seguimiento/README_AVANCE_2026-11-02.md): seguimiento consolidado desde agosto y corte del 2 de noviembre (históricos).

## `institucional/`

- [`Anteproyecto_Sisben_IV.docx`](institucional/Anteproyecto_Sisben_IV.docx): anteproyecto de abril de 2026, con la formulación anterior de objetivos (OE1-OE5). La vigente está en el `README.md` de la raíz.
