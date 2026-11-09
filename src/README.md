# Carpeta: src (Código fuente)
---
Contiene el código de producción del proyecto. A diferencia de los
notebooks, el código de esta carpeta debe ser modular, reutilizable,
documentado y preferiblemente cubierto por pruebas.

## Estructura y artefactos

- **`ingesta/`**
  - Módulos reutilizables de conexión a fuentes. `socrata_client.py`
    implementa un cliente genérico para portales Socrata (usado por
    `datos.gov.co` y `microdatos.dane.gov.co` para datasets abiertos como
    IPM agregado), siguiendo el mismo patrón de parsers Socrata + CSV del
    proyecto hermano `desarrollo_social_y_economico`.
  - `geih_loader.py`: recorre automáticamente los meses de GEIH
    depositados en `data/0_raw/geih/2024/<mes>/CSV/` (01..12) y convierte
    cada uno de los 8 módulos a Parquet en `data/1_processed/geih/2024/<mes>/`.
    No requiere tener los 12 meses — procesa los que encuentre. GEIH es
    de acceso abierto (no requiere solicitud institucional como Sisbén),
    pero **nunca se versiona el CSV/DTA/SAV crudo en git** — solo el
    código que lo procesa (ver `.gitignore`, `data/0_raw/*`).
  - Las fuentes de acceso restringido (Sisbén IV, DPS, RUI) no tienen
    cliente API — se documentan en `data/catalogo.yaml` como
    `solicitud_institucional` y se ingieren manualmente en `0_raw/` una
    vez obtenido el microdato.

- **`armonizacion/`**
  - Lleva cada fuente a un esquema canónico por hogar (jefe de hogar):
    `armonizar_geih_hogar_2024.py` (12 meses GEIH),
    `armonizar_sisben_hogar_2024.py` (Sisbén nacional) y
    `armonizar_sisben_bogota_sdp.py` (Sisbén Bogotá, entrega SDP; también
    fusiona con el nacional reemplazando el municipio 11001). Salidas en
    `data/2_models/`.

- **`emparejamiento/`**
  - `emparejamiento_hotdeck_geih_sisben.py`: Hot-Deck por celdas
    (departamento + ciclo de vida del jefe + tramo de `viv_cuartos` + nivel
    de pisos homologado, este último desde el 2026-11-02 — ver
    `docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`) con degradación
    jerárquica (celda_exacta → sin_pisos → solo_depto_edad → solo_depto →
    pool_nacional). Asigna `Grupo`/`Nivel`/`Clasificacion` del Sisbén a
    los hogares GEIH. Válido solo a nivel poblacional (no identifica el
    mismo hogar). `incluir_pisos=False` reproduce la celda anterior.
    Paredes no entra (no mejora la celda, ver
    `comparar_celdas_hotdeck_vivienda.py`).

- **`estimacion/`**
  - Selección de variables, recomendación de variables e incidencia de las
    ayudas declaradas — ver `src/estimacion/README.md`.
  - `cotas_frechet_manski.py` ✅: alternativa de robustez al DML — cotas
    de Fréchet-Manski sobre `P(Y|X)` (GEIH) y `P(T|X)` (Sisbén) por
    separado, sin suponer independencia condicional. Ver
    `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

- **`simulacion/`** (módulo del framework, 2026-11-04)
  - Evaluación semisintética reutilizable: qué estimador recupera un
    efecto conocido y cuánto se pierde según el vínculo entre fuentes.
    Exige las columnas canónicas (`contrato.py`, sin alias) y calcula la
    celda y lo derivado. `python -m src.simulacion [n_jobs]`. Diseño en
    `docs/metodologia/DISENO_MODULO_SIMULACION.md`.

- **`validacion/`**
  - Chequeos de calidad: `validar_cobertura_celdas_hotdeck.py`,
    `verificar_esquema_armonizado.py`, `revisar_faltantes_modulos_geih.py`,
    `verificar_codigos_edad_sisben.py` (corrobora los códigos de ciclo de
    vida de `PER002` contra variables de comportamiento), y
    `comparar_filtros_sdp.py` (corre el Hot-Deck con los dos filtros del
    SDP — vigencia vs. año exacto — y deja el resultado lado a lado en
    `docs/reports/comparacion_filtros_sdp.csv`), y
    `verificar_representatividad_sisben.py` (cobertura del Sisbén frente a
    la población de GEIH, por departamento — ver
    `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`), y
    `comparar_pobreza_monetaria_oficial.py` (reconstrucción de la pobreza
    monetaria frente a la base oficial del DANE, hogar por hogar — ver
    `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`).

- **`/tests`** (raíz del repo)
  - Pruebas con `pytest` sobre las transformaciones críticas —
    `poetry run pytest tests/`. Cubre `3_preprocesamiento.py` (outcome
    IPM-GEIH) sobre datos reales, no sintéticos, y
    `3b_preprocesamiento_monetario.py` (outcome de pobreza monetaria) con
    datos reales para `_ingreso_mes` y casos de borde sintéticos para la
    clasificación de pobreza (lógica pura, sin I/O).

- **`utils/`**
  - `azure_storage.py`, `publicar_banco_datos_azure.py` y
    `restaurar_banco_datos_azure.py`: banco de datos en Azure Blob Storage
    (los datos no se versionan en git).
  - `config.py`: carga `data/catalogo.yaml` y variables de entorno
    (`.env`) de forma centralizada para todos los scripts.
  - `variables_canonicas.py`: reglas compartidas entre fuentes, en un
    solo lugar (2026-11-04): `normalizar_llave`, `es_jefe` (jefe de hogar
    por fuente) y `edad_a_ciclo` (edad en años → código de ciclo de vida
    de `PER002`). Los módulos de armonización, el Hot-Deck, los
    preprocesamientos y el contraste oficial lo usan en vez de copiar la
    regla.

- **`1_integracion.py`**
  - Script de integración de fuentes (ETL). Orquesta la ingesta de las
    fuentes abiertas vía `ingesta/socrata_client.py` y deja el resto de
    fuentes como placeholders documentados hasta que se resuelva el
    acceso institucional.

- **`2_limpieza.py`**
  - Limpieza y armonización: manejo de nulos, corrección de tipos,
    eliminación de duplicados, armonización de categorías entre fuentes.

- **`3_preprocesamiento.py`** ✅ implementado 2026-10-21, ampliado 2026-10-28
  - Construye el outcome real: `ipm_geih_score`/`POBRE_GEIH`, un IPM-GEIH
    que cubre **8 de 15 privaciones** oficiales (las 5 dimensiones del
    IPM, antes solo 2 — analfabetismo, logro educativo del jefe,
    asistencia escolar de menores, aseguramiento de salud, cotización a
    pensión del jefe, hacinamiento, alcantarillado, acueducto; dos
    privaciones de vivienda construidas y retiradas el mismo día por
    tautología con `viv_paredes`/`viv_pisos` de `X` en
    `5_estimacion.py` — ver docstring del script para qué se incluyó,
    qué no, y por qué). Tratamiento:
    `Grupo_hotdeck`/`Clasificacion_hotdeck` (ya en el parquet fusionado del
    Hot-Deck). Salida: `data/2_models/muestra_estimacion_2024.parquet`.

- **`indicadores/pobreza_monetaria_geih.py`** ✅ 2026-11-02
  - Pobreza monetaria reconstruida con la metodología del DANE (unidad
    de gasto, `INGLABO` más componentes no incluidos, hot-deck de no
    respuesta laboral, arriendo imputado, líneas por dominio, tasas por
    persona) y 8 escenarios de sensibilidad. FGT0 33,2 % frente a 31,8 %
    oficial. Ver `docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md`
    y `docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

- **`3b_preprocesamiento_monetario.py`** ✅
  - Pega el resultado anterior (escenario base) a la muestra de
    estimación: `ingreso_percapita`, `POBRE_MONETARIO`,
    `POBRE_EXTREMO_MONETARIO` y brechas. Salida:
    `data/2_models/muestra_estimacion_monetaria_2024.parquet`.

- **`4_dag_identificacion.py`** ✅ implementado 2026-10-21
  - Los dos DAG del documento de pipeline (diseño principal, diseño de una
    sola tabla) con `networkx` y chequeo formal de d-separación. Ver
    `docs/resultados/IDENTIFICACION_CAUSAL.md`.

- **`5_estimacion.py`** ✅ corregido 2026-11-02
  - DML (`LinearDML`: ATE, ATT y ATU) y Causal Forest (`CausalForestDML`:
    CATE), 4 outcomes × 2 especificaciones de `W` (proxy y celda exacta
    del Hot-Deck). Las categóricas sin orden entran a los modelos
    auxiliares como indicadoras. Con el grupo imputado por Hot-Deck el
    resultado es un **diagnóstico placebo** (ATE ≈0 esperado), no el
    efecto del Sisbén: ver `docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`.

- **`6_refutacion.py`**
  - Pruebas de refutación y sensibilidad: placebo, random common cause,
    data subset refuter, sensibilidad a confusores no observados.

- **`7_reporte/`**
  - Generación de reportes y visualizaciones reproducibles para
    `docs/reports/`, incluyendo la comparación FGT1 (OE3).

## Estándares de código

- **Modularidad**: funciones pequeñas con una única responsabilidad.
- **Documentación**: docstrings estilo Google o NumPy.
- **No hardcoding**: rutas y parámetros vienen de `data/catalogo.yaml`,
  `.env` o argumentos de CLI — nunca hardcodeados en el script.
- **Reproducibilidad**: fijar semillas aleatorias y registrar versiones
  de dependencias (`poetry.lock`).
