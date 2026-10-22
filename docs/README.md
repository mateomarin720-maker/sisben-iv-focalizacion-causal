# Carpeta: docs (documentación)

Toda la documentación del proyecto, agrupada por para qué sirve. Cada
carpeta responde a una pregunta distinta.

| Carpeta | Qué hay | Para qué sirve |
|---|---|---|
| [`insumos/`](insumos/) | Diccionarios, descripción de tablas, códigos y referencias | Consultar qué significa cada variable y de dónde sale |
| [`resultados/`](resultados/) | Documentos cortos con los resultados de cada paso | Revisar resultados sin correr los scripts ni los cuadernos |
| [`seguimiento/`](seguimiento/) | Resumen de avances y changelog | Saber en qué estado está el proyecto |
| [`institucional/`](institucional/) | Anteproyecto | Documentos formales de la maestría |
| [`reports/`](reports/) | CSV y HTML que generan los scripts de calidad de datos | Salidas automáticas; no se editan a mano |

## `insumos/`
- [`DICCIONARIO_DATOS.md`](insumos/DICCIONARIO_DATOS.md): variables en uso del IPM y GEIH, con tipo, distribución y estado por fuente.
- [`DICCIONARIO_HOTDECK.md`](insumos/DICCIONARIO_HOTDECK.md): variables, llaves de hogar y limitaciones del emparejamiento GEIH ↔ Sisbén (incluye Bogotá y los códigos de edad `PER002`).
- [`DESCRIPCION_TABLAS.md`](insumos/DESCRIPCION_TABLAS.md): las tablas de `data/2_models/`: qué es una fila, cuál es la llave, cuántas filas tiene y qué script la genera.
- [`DICCIONARIO_IPM_2025.md`](insumos/DICCIONARIO_IPM_2025.md): diccionario del IPM (nota: el proyecto trabaja con el IPM 2024).
- [`CODIGOS_LOCALIDAD_BOGOTA.md`](insumos/CODIGOS_LOCALIDAD_BOGOTA.md): códigos de localidad del Sisbén de Bogotá.
- [`referencias_teoricas.md`](insumos/referencias_teoricas.md): referencias metodológicas del proyecto.

## `resultados/`
- [`RESULTADOS_HOTDECK.md`](resultados/RESULTADOS_HOTDECK.md): resultado del emparejamiento GEIH ← Sisbén, la verificación de los códigos de edad `PER002` y cómo leerlos.
- [`COMPARACION_FILTROS_SDP.md`](resultados/COMPARACION_FILTROS_SDP.md): el SDP (Sisbén Bogotá) es un registro continuo, no un corte único — comparación lado a lado de los dos filtros posibles (vigencia vs. año exacto) y por qué se adoptó vigencia.
- [`IDENTIFICACION_CAUSAL.md`](resultados/IDENTIFICACION_CAUSAL.md): los dos DAG del pipeline (diseño principal y diseño de una sola tabla), con el chequeo formal de d-separación — por qué el diagrama simplificado del documento de pipeline necesita distinguir elegibilidad del donante de la del receptor para sostener su propia afirmación.

## `seguimiento/`
- [`RESUMEN_AVANCES.md`](seguimiento/RESUMEN_AVANCES.md): estado de fuentes, pipeline y pendientes técnicos.
- [`CHANGELOG_PENDIENTES.md`](seguimiento/CHANGELOG_PENDIENTES.md): historial de cambios, más reciente primero.

## `institucional/`
- [`Anteproyecto_Sisben_IV.docx`](institucional/Anteproyecto_Sisben_IV.docx): anteproyecto (abril 2026). Contiene la formulación anterior de objetivos (OE1–OE5); los vigentes son P1/OE1, P2/OE2 y P3/OE3 (ver el `README.md` de la raíz). Su actualización está a cargo del equipo.

## `reports/`
Los scripts de calidad de datos (`src/2_limpieza.py`, `src/utils/validar_geih.py`,
`src/utils/validar_linkage.py`, `src/validacion/comparar_filtros_sdp.py`) y las
pruebas exploratorias (`src/estimacion/`) escriben aquí sus salidas crudas
(CSV, TXT). Esta es la única carpeta de reportes generados; los resultados
interpretados van en `resultados/`.

## Pendiente
- Marco teórico y metodológico completo: se redacta en un documento aparte y se agregará a `insumos/` cuando esté estable (el diagrama causal ya está en `resultados/IDENTIFICACION_CAUSAL.md`, pero falta integrarlo al marco teórico formal).
- Resultados de determinantes y validez (P1/OE1), efectos causales (P2/OE2) y reglas contrafactuales (P3/OE3): se agregan a `resultados/` cuando se ejecuten (`5_estimacion.py` sigue sin implementar — ver `src/estimacion/README.md` para la prueba exploratoria que sí corrió).
