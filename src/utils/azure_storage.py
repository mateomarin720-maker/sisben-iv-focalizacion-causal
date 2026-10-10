"""Cliente de Azure Blob Storage — repositorio de datos fuera de GitHub.

Los archivos de datos (data/0_raw, data/1_processed, data/2_models) NO
se versionan en git (ver .gitignore) por su tamaño — este módulo es el
reemplazo: sube/baja esos archivos a un contenedor de Azure Blob
Storage compartido por el equipo, en vez de depender de que cada quien
regenere todo localmente desde cero.

Configuración necesaria (una sola vez, NO se versiona — va en .env,
que ya está en .gitignore):

    AZURE_STORAGE_CONNECTION_STRING=<cadena de conexión de su cuenta de Azure>

Convención de carpetas virtuales dentro del contenedor "datos-proyecto"
(refleja la misma estructura de data/ del repo, para que sea intuitivo):

    datos-proyecto/
        0_raw/geih/2024/01/...
        0_raw/sisben_iv/2024/...
        0_raw/ipm/...
        1_processed/geih/2024/01/...
        1_processed/sisben_iv/2024/...
        2_models/...

Uso típico:
    from utils.azure_storage import subir_archivo, descargar_archivo, listar_archivos

    # Subir lo que generó el loader localmente
    subir_archivo("data/1_processed/sisben_iv/2024/hogares.parquet",
                  "1_processed/sisben_iv/2024/hogares.parquet")

    # Bajar en otra máquina (o para un compañero de equipo)
    descargar_archivo("1_processed/sisben_iv/2024/hogares.parquet",
                       "data/1_processed/sisben_iv/2024/hogares.parquet")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()  # carga .env explícitamente, sin depender de que el editor lo inyecte a la terminal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("azure").setLevel(logging.WARNING)  # oculta el detalle de cada petición HTTP
logger = logging.getLogger(__name__)

CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "datos-inferencia-causal")


def _cliente_contenedor():
    """Crea el cliente del contenedor, leyendo la cadena de conexión
    desde la variable de entorno (nunca hardcodeada en el código)."""
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise ValueError(
            "AZURE_STORAGE_CONNECTION_STRING no está configurada. "
            "Agréguenla a su archivo .env (no se versiona en git) o "
            "expórtenla como variable de entorno del sistema."
        )
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    return blob_service_client.get_container_client(CONTAINER_NAME)


def subir_archivo(ruta_local: str | Path, ruta_azure: str, sobrescribir: bool = True) -> None:
    """Sube un archivo local (parquet, csv, txt, lo que sea) a Azure.

    ruta_local: path del archivo en el disco de quien corre el script.
    ruta_azure: ruta virtual dentro del contenedor, ej.
                "1_processed/sisben_iv/2024/hogares.parquet"
    """
    ruta_local = Path(ruta_local)
    if not ruta_local.exists():
        raise FileNotFoundError(f"No existe el archivo local: {ruta_local}")

    container = _cliente_contenedor()
    blob_client = container.get_blob_client(ruta_azure)

    logger.info(
        "Subiendo %s -> azure://%s/%s (%.2f MB)",
        ruta_local, CONTAINER_NAME, ruta_azure, ruta_local.stat().st_size / (1024**2),
    )
    # Reintentos y timeouts amplios: con conexiones domésticas, archivos de
    # decenas de MB pueden agotar el timeout de escritura por defecto.
    ultimo_error: Exception | None = None
    for intento in range(1, 4):
        try:
            with open(ruta_local, "rb") as f:
                blob_client.upload_blob(
                    f, overwrite=sobrescribir,
                    timeout=900, connection_timeout=900, max_concurrency=2,
                )
            logger.info("Subida completa: %s", ruta_azure)
            return
        except Exception as exc:  # noqa: BLE001 - se reintenta y se relanza al final
            ultimo_error = exc
            logger.warning("Intento %s/3 falló para %s: %s", intento, ruta_azure, type(exc).__name__)
    raise ultimo_error


def descargar_archivo(ruta_azure: str, ruta_local: str | Path) -> Path:
    """Descarga un archivo de Azure al disco local.

    ruta_azure: ruta virtual dentro del contenedor.
    ruta_local: dónde guardarlo localmente (se crean las carpetas
                intermedias si no existen).
    """
    ruta_local = Path(ruta_local)
    ruta_local.parent.mkdir(parents=True, exist_ok=True)

    container = _cliente_contenedor()
    blob_client = container.get_blob_client(ruta_azure)

    logger.info("Descargando azure://%s/%s -> %s", CONTAINER_NAME, ruta_azure, ruta_local)
    with open(ruta_local, "wb") as f:
        f.write(blob_client.download_blob().readall())
    logger.info("Descarga completa: %s", ruta_local)
    return ruta_local


def listar_archivos(prefijo: str = "") -> list[str]:
    """Lista los archivos disponibles en el contenedor, opcionalmente
    filtrados por una carpeta virtual (prefijo), ej. listar_archivos("1_processed/geih/")"""
    container = _cliente_contenedor()
    return [b.name for b in container.list_blobs(name_starts_with=prefijo)]


def sincronizar_carpeta_local_a_azure(
    carpeta_local: str | Path,
    prefijo_azure: str,
    excluir_extensiones: tuple[str, ...] = (),
) -> None:
    """Sube TODOS los archivos de una carpeta local (recursivo) a Azure,
    preservando la estructura de subcarpetas.

    excluir_extensiones: extensiones a saltar (ej. (".DTA", ".SAV") —
    formatos duplicados de GEIH que el pipeline nunca usa, solo CSV).
    """
    carpeta_local = Path(carpeta_local)
    archivos = list(carpeta_local.rglob("*"))
    archivos = [a for a in archivos if a.is_file()]
    if excluir_extensiones:
        antes = len(archivos)
        archivos = [a for a in archivos if a.suffix.upper() not in [e.upper() for e in excluir_extensiones]]
        omitidos = antes - len(archivos)
        if omitidos:
            logger.info("Omitiendo %s archivos con extensión en %s", omitidos, excluir_extensiones)

    logger.info("Sincronizando %s archivos de %s hacia azure://%s/%s",
                len(archivos), carpeta_local, CONTAINER_NAME, prefijo_azure)

    # Reanudable: se omiten los archivos que ya están en Azure con el mismo tamaño.
    existentes = {
        b.name: b.size
        for b in _cliente_contenedor().list_blobs(name_starts_with=f"{prefijo_azure}/")
    }
    subidos = omitidos_ya = 0
    for archivo in archivos:
        ruta_relativa = archivo.relative_to(carpeta_local)
        ruta_azure = f"{prefijo_azure}/{ruta_relativa.as_posix()}"
        if existentes.get(ruta_azure) == archivo.stat().st_size:
            omitidos_ya += 1
            continue
        subir_archivo(archivo, ruta_azure)
        subidos += 1

    logger.info("Sincronización completa: %s subidos, %s ya estaban en Azure", subidos, omitidos_ya)


def descargar_carpeta_de_azure(prefijo_azure: str, carpeta_local: str | Path) -> int:
    """Descarga TODOS los archivos bajo un prefijo de Azure hacia una
    carpeta local, preservando la estructura. Es el reverso de
    sincronizar_carpeta_local_a_azure — para que cualquiera del equipo
    (o una máquina nueva) pueda reconstruir data/ sin tener que
    regenerar todo desde los CSV/TXT crudos ni correr los loaders."""
    carpeta_local = Path(carpeta_local)
    archivos_azure = listar_archivos(prefijo_azure)

    if not archivos_azure:
        logger.warning("No se encontró ningún archivo en azure://%s/%s", CONTAINER_NAME, prefijo_azure)
        return 0

    logger.info("Descargando %s archivos de azure://%s/%s hacia %s",
                len(archivos_azure), CONTAINER_NAME, prefijo_azure, carpeta_local)

    for ruta_azure in archivos_azure:
        ruta_relativa = ruta_azure[len(prefijo_azure):].lstrip("/")
        ruta_local_destino = carpeta_local / ruta_relativa
        descargar_archivo(ruta_azure, ruta_local_destino)

    logger.info("Descarga completa: %s archivos", len(archivos_azure))
    return len(archivos_azure)


if __name__ == "__main__":
    # Prueba rápida de conexión: lista lo que ya hay en el contenedor
    print("Archivos actuales en el contenedor:")
    for nombre in listar_archivos():
        print(f"  {nombre}")
