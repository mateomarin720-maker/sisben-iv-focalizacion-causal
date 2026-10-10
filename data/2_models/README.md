# data/2_models

Bases armonizadas y resultados intermedios de modelado.

**Producidos hoy**
- `geih_estandarizado_2024.parquet` — GEIH, 12 meses, una fila por hogar
  (`src/armonizacion/armonizar_geih_hogar_2024.py`).
- `sisben_estandarizado_2024.parquet` — Sisbén nacional, una fila por hogar
  (`armonizar_sisben_hogar_2024.py`).
- `sisben_bogota_estandarizado.parquet` — Sisbén Bogotá-SDP
  (`armonizar_sisben_bogota_sdp.py`).
- `sisben_estandarizado_2024_con_bogota.parquet` — donante final (Bogotá
  reemplaza al municipio 11001 del nacional).
- `geih_sisben_fusionado_2024.parquet` — resultado del Hot-Deck: hogares
  GEIH con `Grupo/Nivel/Clasificacion_hotdeck`
  (`src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py`).

**Previstos**: modelos LASSO/Ridge y SHAP (OE1), objetos DML / Causal
Forest (OE2) y simulaciones de reglas de focalización (OE3), producidos por
`src/4_dag_identificacion.py`, `src/5_estimacion.py` y `src/6_refutacion.py`.

Los nombres de columnas y su significado están en
[`docs/DICCIONARIO_HOTDECK.md`](../../docs/DICCIONARIO_HOTDECK.md).
Contenido no versionado (`.gitignore`); respaldo en Azure Blob Storage.
