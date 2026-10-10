# data/1_processed

Datos limpios y tipados, en Parquet, producto de la ingesta
(`src/1_integracion.py`, `src/ingesta/`) y la limpieza (`src/2_limpieza.py`):

- `geih/2024/<mes>/<modulo>.parquet` — 12 meses × 8 módulos.
- `sisben_iv/2024/{hogares,viviendas,personas}.parquet`.
- IPM Hogares/Personas/Viviendas limpios.

La armonización entre fuentes y el emparejamiento se guardan en
`data/2_models/` (ver su README). Pendiente: tabla unificada a nivel hogar
con tratamiento, outcomes y covariables (`src/3_preprocesamiento.py`).

Contenido no versionado (`.gitignore`); respaldo en Azure Blob Storage.
