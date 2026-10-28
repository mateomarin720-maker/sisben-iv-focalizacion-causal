# data/2_models

Bases armonizadas, el emparejamiento Hot-Deck y la tabla final de
estimación.

**Armonización y emparejamiento**
- `geih_estandarizado_2024.parquet` — GEIH, 12 meses, una fila por hogar
  (`src/armonizacion/armonizar_geih_hogar_2024.py`).
- `sisben_estandarizado_2024.parquet` — Sisbén nacional, una fila por hogar
  (`armonizar_sisben_hogar_2024.py`).
- `sisben_bogota_estandarizado.parquet` — Sisbén Bogotá-SDP, hogares
  vigentes al 31-dic-2024 (filtro adoptado); `_anio_exacto.parquet` es la
  variante alternativa para comparar (`armonizar_sisben_bogota_sdp.py --modo`).
- `sisben_estandarizado_2024_con_bogota.parquet` (y su variante
  `_anio_exacto`) — donante final del Hot-Deck (Bogotá reemplaza al
  municipio 11001 del nacional).
- `geih_sisben_fusionado_2024.parquet` — resultado del Hot-Deck: hogares
  GEIH con `Grupo/Nivel/Clasificacion_hotdeck`, celda
  depto+edad+cuartos de vivienda
  (`src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`).

**Preprocesamiento y estimación**
- `muestra_estimacion_2024.parquet` — tabla final a nivel hogar: outcome
  IPM-GEIH (`ipm_geih_score`/`POBRE_GEIH`, 4 de 15 privaciones),
  tratamiento (`Grupo_hotdeck`) y covariables (`src/3_preprocesamiento.py`).
  Usada por `src/5_estimacion.py` (DML, Causal Forest) y
  `src/estimacion/cotas_frechet_manski.py`.
- `muestra_estimacion_prueba.parquet` — outcome de prueba (empleo/ingreso
  del jefe) que precedió al outcome oficial; ver `src/estimacion/README.md`.

**Previsto**: modelos LASSO/Ridge y SHAP (P1/OE1), simulaciones de reglas
de focalización FGT1 (P3/OE3, `src/6_refutacion.py`, `src/7_reporte/`).

Los resultados interpretados de cada tabla están en
[`docs/resultados/`](../../docs/resultados/README.md); los nombres de
columnas y su significado en
[`docs/insumos/DICCIONARIO_HOTDECK.md`](../../docs/insumos/DICCIONARIO_HOTDECK.md)
y [`DESCRIPCION_TABLAS.md`](../../docs/insumos/DESCRIPCION_TABLAS.md).
Contenido no versionado (`.gitignore`); respaldo en Azure Blob Storage.
