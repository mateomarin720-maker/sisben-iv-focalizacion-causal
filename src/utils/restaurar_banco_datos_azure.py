"""Descarga TODO data/ desde Azure — reconstruye data/ sin reprocesar.

Contraparte de publicar_banco_datos_azure.py. Cualquier integrante del equipo,
o una máquina nueva con el repo recién clonado, corre esto UNA VEZ para
tener toda la data ya procesada (GEIH, Sisbén, IPM, estandarizados,
Hot-Deck) sin tener que volver a correr los loaders ni esperar los
minutos que toma procesar los archivos crudos.

Uso:
    poetry run python -m src.utils.restaurar_banco_datos_azure
    poetry run python -m src.utils.restaurar_banco_datos_azure --solo 2_models
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.utils.azure_storage import descargar_carpeta_de_azure

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CARPETAS = ["0_raw", "1_processed", "2_models"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", choices=CARPETAS, help="descargar solo esta carpeta (ej. 2_models)")
    args = ap.parse_args()
    base = Path("data")
    total = 0
    for carpeta in ([args.solo] if args.solo else CARPETAS):
        n = descargar_carpeta_de_azure(carpeta, base / carpeta)
        total += n

    print(f"\n=== Descarga desde Azure completa: {total} archivos ===")
    if total == 0:
        print("No se encontró nada en Azure todavía — alguien del equipo debe correr "
              "primero publicar_banco_datos_azure.py")


if __name__ == "__main__":
    main()
