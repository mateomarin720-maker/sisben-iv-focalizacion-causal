# src/ingesta

Módulos de conexión a fuentes de datos.

- **`socrata_client.py`**: cliente genérico para portales Socrata (fuentes
  con `acceso: abierto` en `data/catalogo.yaml`, p. ej. indicadores
  agregados de IPM en datos.gov.co). Paginación automática, guardado
  directo a `data/0_raw/` en parquet.

- **`local_csv_parser.py`**: ingesta de microdatos locales (CSV) por
  chunks — para GEIH y Sisbén IV, que llegan como archivos entregados
  directamente por DANE/DNP (no vía API), a veces pesados o repartidos en
  varios archivos por departamento/mes. Adaptado del patrón real usado en
  el repo de referencia `desarrollo_social_y_economico`
  (`src/ingesta/bronze/parsers/parser_csv_secop.py` y
  `parser_csv_cnpv.py`, rama `trabajo-final`), que lee CSV de hasta ~10GB
  por lotes con PyArrow en vez de cargarlos completos en RAM.
  - `parse_csv_a_parquet(...)`: para un solo archivo.
  - `parse_carpeta_csv_a_parquet(...)`: para varios archivos en una
    carpeta (p. ej. GEIH repartida por mes).

- **Fuentes de acceso restringido** (`solicitud_institucional` o
  `registro` en `data/catalogo.yaml`: Sisbén IV, DPS, RUI, GEIH
  microdato) **no tienen cliente API** — no existe endpoint público. El
  flujo es: (1) tramitar la solicitud ante la entidad correspondiente,
  (2) depositar el archivo entregado directamente en `data/0_raw/<fuente>/`,
  (3) correr `parse_csv_a_parquet` o `parse_carpeta_csv_a_parquet` sobre
  ese archivo/carpeta, (4) documentar la fecha y el canal de obtención en
  `data/catalogo.yaml` (campo `estado` → `disponible`).

- **`geih_loader.py`** y **`sisben_loader.py`**: cargadores específicos.
  El de GEIH recorre `data/0_raw/geih/2024/<mes>/CSV/` y convierte los 8
  módulos de cada mes a Parquet (lectura `latin1`); el de Sisbén convierte
  los TXT (separador tab) de Hogares, Viviendas y Personas por lotes de
  200.000 filas.

## Estado

| Fuente | Estado |
|---|---|
| GEIH 2024 (12 meses) | ✅ Ingestada |
| IPM 2024 | ✅ Ingestado |
| Sisbén IV nacional (ANDA-DNP) | ✅ Ingestado |
| Sisbén IV Bogotá (SDP, CSV) | ✅ Armonizado directamente desde el CSV (`src/armonizacion/armonizar_sisben_bogota_sdp.py`, filtrado a hogares vigentes — el archivo es un registro continuo, no un corte único) |
| DPS | ⏳ Por gestionar; escribir el conector cuando se defina el canal de entrega |

La armonización entre fuentes y el emparejamiento no pertenecen a esta
carpeta: ver `src/armonizacion/` y `src/emparejamiento/`.
