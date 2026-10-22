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
    (departamento + ciclo de vida del jefe) con degradación jerárquica.
    Asigna `Grupo`/`Nivel`/`Clasificacion` del Sisbén a los hogares GEIH.
    Válido solo a nivel poblacional (no identifica el mismo hogar).

- **`estimacion/`**
  - Pruebas exploratorias de ATE/ATT/CATE — ver
    `src/estimacion/README.md` para el detalle. **No es la Fase 4**
    (`5_estimacion.py` sigue sin implementar): es la corrida previa para
    ver cómo se comportan los estimadores con las variables que ya hay, y
    sirve de chequeo de validez del Hot-Deck (sección 1 de
    `docs/resultados/IDENTIFICACION_CAUSAL.md`).

- **`validacion/`**
  - Chequeos de calidad: `validar_cobertura_celdas_hotdeck.py`,
    `verificar_esquema_armonizado.py`, `revisar_faltantes_modulos_geih.py`,
    `verificar_codigos_edad_sisben.py` (corrobora los códigos de ciclo de
    vida de `PER002` contra variables de comportamiento), y
    `comparar_filtros_sdp.py` (corre el Hot-Deck con los dos filtros del
    SDP — vigencia vs. año exacto — y deja el resultado lado a lado en
    `docs/reports/comparacion_filtros_sdp.csv`).

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

- **`3_preprocesamiento.py`**
  - Construcción de variables: define explícitamente **tratamiento**
    (elegibilidad A/B del Sisbén IV y participación en programas DPS),
    **outcomes** de bienestar (IPM/GEIH; nunca `I1`–`I15` ni `H_5` del
    Sisbén) y **confusores**; codificación, escalado e imputación.

- **`4_dag_identificacion.py`**
  - Especificación del DAG causal y análisis de identificabilidad
    (cadena elegibilidad → participación → bienestar; backdoor;
    discontinuidad sobre la frontera ordinal B/C, pues el extracto no trae
    puntaje continuo).

- **`5_estimacion.py`**
  - Estimación de efectos causales: DML (ATE/ATT) y Causal Forest
    (CATE), test BLP de heterogeneidad (OE2).

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
