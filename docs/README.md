# Carpeta: docs (documentación)

Toda la documentación del proyecto, agrupada por para qué sirve. Cada
carpeta responde a una pregunta distinta.

| Carpeta | Qué hay | Para qué sirve |
|---|---|---|
| [`insumos/`](insumos/) | Diccionarios, descripción de tablas, códigos y referencias | Consultar qué significa cada variable y de dónde sale |
| [`metodologia/`](metodologia/) | Diseño metodológico de fases nuevas (p. ej. comparación de proxies del IPM, [módulo de simulación](metodologia/DISENO_MODULO_SIMULACION.md)) | Revisar definiciones antes de construir variables |
| [`metodologia/ARQUITECTURA_Y_REPLICACION.md`](metodologia/ARQUITECTURA_Y_REPLICACION.md) | Capas de datos, controles de calidad y guía de replicación | Reproducir el proyecto o reutilizarlo |
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
- [`METODOLOGIA_INDICADOR_IPM_GEIH.md`](insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md): cómo se construyen las 8 privaciones del indicador IPM-GEIH (de las 15 oficiales), la familia de umbrales de sensibilidad, las validaciones obligatorias y las privaciones que quedan sin construir.

## `resultados/`
- [`README.md`](resultados/README.md): **índice y hallazgos consolidados** — el hilo conductor que conecta los documentos de abajo (resumen ejecutivo, no hace falta leerlos todos para entender el estado del proyecto).
- [`RESULTADOS_HOTDECK.md`](resultados/1_datos_y_enlace/RESULTADOS_HOTDECK.md): resultado del emparejamiento GEIH ← Sisbén, la verificación de los códigos de edad `PER002` y cómo leerlos.
- [`COMPARACION_FILTROS_SDP.md`](resultados/1_datos_y_enlace/COMPARACION_FILTROS_SDP.md): el SDP (Sisbén Bogotá) es un registro continuo, no un corte único — comparación lado a lado de los dos filtros posibles (vigencia vs. año exacto) y por qué se adoptó vigencia.
- [`IDENTIFICACION_CAUSAL.md`](resultados/2_diagnostico_datos_reales/IDENTIFICACION_CAUSAL.md): los dos DAG del pipeline (diseño principal y diseño de una sola tabla), con el chequeo formal de d-separación — por qué el diagrama simplificado del documento de pipeline necesita distinguir elegibilidad del donante de la del receptor para sostener su propia afirmación.
- [`RESULTADOS_DML_ATE_ATT_ATU.md`](resultados/2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md): ATE/ATT/ATU (Double Machine Learning) sobre los cuatro outcomes (IPM-GEIH y pobreza monetaria) con dos especificaciones de controles; los efectos son ≈0.
- [`RESULTADOS_CAUSALFOREST_CATE.md`](resultados/2_diagnostico_datos_reales/RESULTADOS_CAUSALFOREST_CATE.md): CATE (Causal Forest) — la heterogeneidad por zona y sexo del jefe cambia de signo entre corridas y no se toma como conclusión.
- [`RESULTADOS_FRECHET_MANSKI.md`](resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md): cotas de Fréchet-Manski (sin suponer independencia condicional) — el rango de efectos compatible con los datos crudos no fija ni el signo del efecto (ninguna celda excluye el 0); incluye pobreza monetaria.
- [`DIAGNOSTICO_W_CELDA_EXACTA.md`](resultados/2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md): especificación de los controles del DML, aproximación continua frente a la celda exacta del Hot-Deck.
- [`RESULTADOS_POBREZA_MONETARIA.md`](resultados/1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md): pobreza monetaria reconstruida (FGT0, FGT1) y su contraste con la base oficial del DANE.
- [`RESULTADOS_SELECCION_VARIABLES_OE1.md`](resultados/2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md): LASSO, Ridge y SHAP sobre el Sisbén (P1/OE1).
- [`SIMULACION_IDENTIFICACION.md`](resultados/3_simulacion/SIMULACION_IDENTIFICACION.md) y [`SIMULACION_SEMISINTETICA.md`](resultados/3_simulacion/SIMULACION_SEMISINTETICA.md): qué diseño recupera un efecto conocido, con datos sintéticos y con hogares reales de la GEIH.
- [`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`](resultados/1_datos_y_enlace/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md): la cobertura del Sisbén respecto a la población de GEIH varía 32 veces entre departamentos — el registro no es una muestra uniforme.

## `seguimiento/`
- [`README.md`](seguimiento/README.md): **seguimiento consolidado** — cambios y avances desde agosto, correcciones, resultados vigentes y pendientes; es el documento para revisar con el profesor.
- [`RESUMEN_AVANCES.md`](seguimiento/RESUMEN_AVANCES.md): estado de fuentes, pipeline y pendientes técnicos.
- [`CHANGELOG_PENDIENTES.md`](seguimiento/CHANGELOG_PENDIENTES.md): historial de cambios, más reciente primero.
- [`README_AVANCE_2026-11-02.md`](seguimiento/README_AVANCE_2026-11-02.md): corte del 2026-11-02 — commits del día, resultados de los modelos, estado y pendientes.

## `institucional/`
- [`Anteproyecto_Sisben_IV.docx`](institucional/Anteproyecto_Sisben_IV.docx): anteproyecto (abril 2026). Contiene la formulación anterior de objetivos (OE1–OE5); los vigentes son P1/OE1, P2/OE2 y P3/OE3 (ver el `README.md` de la raíz). Su actualización está a cargo del equipo.

## `reports/`
Los scripts de calidad de datos (`src/2_limpieza.py`, `src/utils/validar_geih.py`,
`src/validacion/comparar_filtros_sdp.py`), las
pruebas exploratorias (`src/diagnostico/`) y la estimación real (`src/5_estimacion.py`)
escriben aquí sus salidas crudas (CSV, TXT). Esta es la única carpeta de
reportes generados; los resultados interpretados van en `resultados/`.

## Pendiente
- Marco teórico y metodológico completo: se redacta en un documento aparte y se agregará a `insumos/` cuando esté estable (el diagrama causal ya está en `resultados/2_diagnostico_datos_reales/IDENTIFICACION_CAUSAL.md`, pero falta integrarlo al marco teórico formal).
- Resultados de determinantes y validez (P1/OE1): LASSO/Ridge/SHAP sobre el Sisbén — hecho 2026-11-02, ver `resultados/2_diagnostico_datos_reales/RESULTADOS_SELECCION_VARIABLES_OE1.md`.
- Efectos causales (P2/OE2): estimación y cotas hechas (`resultados/2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md`, `RESULTADOS_FRECHET_MANSKI.md`, `DIAGNOSTICO_W_CELDA_EXACTA.md`). Con el Hot-Deck el DML es una prueba placebo del emparejamiento y las cotas no fijan el signo; la evaluación semisintética (`resultados/3_simulacion/SIMULACION_SEMISINTETICA.md`) tiene una primera versión y falta ampliarla.
- Reglas contrafactuales (P3/OE3): no iniciado; se plantea sobre la evaluación semisintética.
- Angostar las cotas de Fréchet-Manski con supuestos de monotonía (MTS/MTR) — ver "Próximo paso" en `resultados/2_diagnostico_datos_reales/RESULTADOS_FRECHET_MANSKI.md`.
- Indicador de pobreza ampliado: resuelto 2026-10-28 (8 de 15 privaciones, antes 4) — ver `insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`. Quedan 7 privaciones sin construir (5 por alcance/tiempo, 2 retiradas por tautología con covariables de heterogeneidad).
- Pobreza monetaria (ingreso per cápita, FGT0/FGT1): construida y conectada a `5_estimacion.py` y a las cotas (`src/indicadores/pobreza_monetaria_geih.py`, ver `resultados/1_datos_y_enlace/RESULTADOS_POBREZA_MONETARIA.md`). Reconstruye 33,2 % de personas pobres frente a 31,8 % oficial y clasifica igual al 93,9 % de los hogares de la base oficial. Metodología en `metodologia/pobreza_monetaria/`.
