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
    (departamento + ciclo de vida del jefe + tramo de `viv_cuartos`, desde
    2026-10-21, código de `viv_cuartos` corregido 2026-10-28 — ver
    `docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`) con degradación
    jerárquica (celda_exacta → solo_depto_edad → solo_depto →
    pool_nacional). Asigna `Grupo`/`Nivel`/`Clasificacion` del Sisbén a
    los hogares GEIH. Válido solo a nivel poblacional (no identifica el
    mismo hogar). `viv_paredes`/`viv_pisos` NO están en la celda — código
    GEIH ya confirmado, pero sus categorías siguen sin homologar contra
    el Sisbén (ver `docs/insumos/DICCIONARIO_HOTDECK.md` §8).

- **`estimacion/`**
  - Pruebas exploratorias de ATE/ATT/CATE que precedieron la corrida real
    (`3_preprocesamiento.py` + `5_estimacion.py`) — ver
    `src/estimacion/README.md`. Útil para entender el razonamiento, ya no
    es la corrida vigente.
  - `cotas_frechet_manski.py` ✅: alternativa de robustez al DML — cotas
    de Fréchet-Manski sobre `P(Y|X)` (GEIH) y `P(T|X)` (Sisbén) por
    separado, sin suponer independencia condicional. Ver
    `docs/resultados/RESULTADOS_FRECHET_MANSKI.md`.

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
    `docs/resultados/RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`).

- **`/tests`** (raíz del repo)
  - Pruebas con `pytest` sobre las transformaciones críticas —
    `poetry run pytest tests/`. Hoy cubre `3_preprocesamiento.py`
    (construcción del outcome) sobre datos reales, no sintéticos.

- **`utils/`**
  - `azure_storage.py`, `publicar_banco_datos_azure.py` y
    `restaurar_banco_datos_azure.py`: banco de datos en Azure Blob Storage
    (los datos no se versionan en git).
  - `config.py`: carga `data/catalogo.yaml` y variables de entorno
    (`.env`) de forma centralizada para todos los scripts.

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

- **`4_dag_identificacion.py`** ✅ implementado 2026-10-21
  - Los dos DAG del documento de pipeline (diseño principal, diseño de una
    sola tabla) con `networkx` y chequeo formal de d-separación. Ver
    `docs/resultados/IDENTIFICACION_CAUSAL.md`.

- **`5_estimacion.py`** ✅ implementado 2026-10-21
  - DML (`LinearDML`: ATE, y ATT/ATU evaluando el mismo modelo sobre cada
    subpoblación) y Causal Forest (`CausalForestDML`: CATE) sobre
    `muestra_estimacion_2024.parquet`. Resultados interpretados:
    `docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md` y
    `docs/resultados/RESULTADOS_CAUSALFOREST_CATE.md`. Sigue siendo una
    corrida sobre un outcome que cubre 8 de 15 privaciones — no reemplaza el marco
    teórico-metodológico completo pendiente (ver Tabla 1 del documento de
    pipeline: LASSO/Ridge/SHAP, RD B/C, vecino más cercano con Gower y
    estudio de eventos Sisbén III→IV siguen sin implementar; cotas de
    Fréchet-Manski ya implementadas, ver `estimacion/` abajo).

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
