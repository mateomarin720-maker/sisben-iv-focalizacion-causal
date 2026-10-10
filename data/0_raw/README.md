# data/0_raw

Datos originales sin modificación alguna, tal como se obtienen de cada
fuente: GEIH 2024 (12 meses), IPM 2024, Sisbén IV nacional (TXT) y Sisbén
Bogotá (CSV de la SDP). Ver [`../catalogo.yaml`](../catalogo.yaml) para el
detalle de cada fuente y su método de obtención.

**Regla de oro**: esta carpeta es de solo lectura. Ningún script debe
escribir aquí salvo los ingestores (`src/1_integracion.py`, `src/ingesta/`).
Toda transformación parte de una copia en `data/1_processed/`.

Contenido no versionado (`.gitignore`); el respaldo vive en Azure Blob
Storage (`src/utils/publicar_banco_datos_azure.py`). Los archivos `.DTA` y
`.SAV` no se suben a Azure (formatos redundantes).
