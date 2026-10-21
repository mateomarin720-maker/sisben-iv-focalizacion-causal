"""Genera una URL de solo lectura, con vencimiento, para compartir los datos.

Sirve para dar acceso al profesor (o a un jurado) sin entregar la cadena de
conexión de la cuenta, que permite escribir y borrar. El token SAS solo
permite listar y leer, y vence solo.

Uso (lo corre quien tiene AZURE_STORAGE_CONNECTION_STRING en su .env):
    poetry run python -m src.utils.generar_acceso_lectura_azure
    poetry run python -m src.utils.generar_acceso_lectura_azure --dias 30

Quien recibe la URL la pega en su .env:
    AZURE_CONTAINER_SAS_URL=<url>
y ya puede correr:
    poetry run python -m src.utils.restaurar_banco_datos_azure --solo 2_models

La URL es un secreto mientras no venza: no se sube a GitHub ni se pega en chats
abiertos. Para revocarla antes de tiempo, roten la clave de la cuenta en Azure.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone

from azure.storage.blob import ContainerSasPermissions, generate_container_sas
from dotenv import load_dotenv

load_dotenv()

CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "datos-inferencia-causal")


def _partes(cadena: str) -> dict[str, str]:
    return dict(p.split("=", 1) for p in cadena.strip().split(";") if "=" in p)


def generar_url(cadena_conexion: str, contenedor: str, dias: int) -> tuple[str, datetime]:
    partes = _partes(cadena_conexion)
    cuenta, clave = partes["AccountName"], partes["AccountKey"]
    vence = datetime.now(timezone.utc) + timedelta(days=dias)
    token = generate_container_sas(
        account_name=cuenta,
        container_name=contenedor,
        account_key=clave,
        permission=ContainerSasPermissions(read=True, list=True),
        expiry=vence,
    )
    sufijo = partes.get("EndpointSuffix", "core.windows.net")
    return f"https://{cuenta}.blob.{sufijo}/{contenedor}?{token}", vence


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dias", type=int, default=14, help="días de validez (por defecto 14)")
    args = ap.parse_args()

    cadena = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not cadena:
        raise SystemExit("Falta AZURE_STORAGE_CONNECTION_STRING en su .env")

    url, vence = generar_url(cadena, CONTAINER_NAME, args.dias)
    print(f"\nURL de solo lectura (vence {vence:%Y-%m-%d %H:%M} UTC):\n")
    print(url)
    print("\nEnvíela por un canal privado. El profesor la pega en su .env como "
          "AZURE_CONTAINER_SAS_URL=<url>")


if __name__ == "__main__":
    main()
