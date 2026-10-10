"""Sincroniza TODO data/ (0_raw, 1_processed, 2_models) hacia Azure.

Azure Blob Storage es el banco de datos principal del equipo — GitHub
NUNCA guarda datos (ver .gitignore), solo código. Este script es el
punto único para subir todo lo que tengan localmente procesado, y su
contraparte (restaurar_banco_datos_azure.py) para que cualquier
integrante del equipo (o una máquina nueva) reconstruya data/ sin
tener que volver a correr todos los loaders desde los CSV/TXT crudos.

Flujo recomendado del equipo:
    1. Alguien corre los loaders localmente (geih_loader, sisben_loader,
       armonizar_*, emparejamiento_*) — esto puede tardar minutos.
    2. Esa persona corre publicar_banco_datos_azure.py UNA VEZ.
    3. El resto del equipo corre restaurar_banco_datos_azure.py y ya
       tiene todo sin tener que reprocesar nada.

Uso:
    poetry run python -m src.utils.publicar_banco_datos_azure
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.utils.azure_storage import sincronizar_carpeta_local_a_azure

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Carpeta local -> prefijo en Azure (mismo nombre, mantiene la
# estructura intuitiva y espejada entre disco local y la nube)
CARPETAS = ["0_raw", "1_processed", "2_models"]


def main() -> None:
    base = Path("data")
    if not base.exists():
        logger.error("No existe la carpeta data/ — correr desde la raíz del proyecto")
        return

    # Orden: primero lo procesado (más valioso, imposible de regenerar
    # sin volver a correr todo el pipeline; también más liviano) —
    # 0_raw va al final porque son GB de CSV/DTA/SAV redescargables
    # desde DANE/DNP si hiciera falta.
    prioridad = [
        ("2_models", ()),
        ("1_processed", ()),
        ("0_raw", (".DTA", ".SAV")),  # excluir formatos que el pipeline no usa
    ]

    for carpeta, excluir in prioridad:
        carpeta_local = base / carpeta
        if not carpeta_local.exists() or not any(carpeta_local.iterdir()):
            logger.info("%s: vacía o no existe, se omite", carpeta_local)
            continue
        sincronizar_carpeta_local_a_azure(carpeta_local, carpeta, excluir_extensiones=excluir)

    print("\n=== Sincronización a Azure completa ===")
    print("Banco de datos principal del equipo: azure://datos-inferencia-causal/")


if __name__ == "__main__":
    main()
