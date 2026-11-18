"""Sincronización con el banco de datos de Azure: qué archivo se vuelve a
subir. Hasta el 2026-11-18 se comparaba solo el tamaño y la GEIH procesada
de Azure quedó en la versión del 2026-10-10. No se conecta a Azure."""
import hashlib
import os
from datetime import datetime, timezone
from types import SimpleNamespace

from src.utils.azure_storage import ya_esta_en_azure


def _blob(contenido: bytes, md5: bool = True, modificado: float = 0.0):
    return SimpleNamespace(
        size=len(contenido),
        last_modified=datetime.fromtimestamp(modificado, tz=timezone.utc),
        content_settings=SimpleNamespace(content_md5=bytearray(hashlib.md5(contenido).digest()) if md5 else None),
    )


def test_mismo_tamano_otro_contenido_se_sube(tmp_path):
    archivo = tmp_path / "a.parquet"
    archivo.write_bytes(b"version nueva")
    assert len(b"version nueva") == len(b"version vieja")
    assert not ya_esta_en_azure(archivo, _blob(b"version vieja"))


def test_mismo_contenido_no_se_sube(tmp_path):
    archivo = tmp_path / "a.parquet"
    archivo.write_bytes(b"igual")
    assert ya_esta_en_azure(archivo, _blob(b"igual"))


def test_sin_blob_se_sube(tmp_path):
    archivo = tmp_path / "a.parquet"
    archivo.write_bytes(b"x")
    assert not ya_esta_en_azure(archivo, None)


def test_sin_md5_cuenta_la_fecha(tmp_path):
    archivo = tmp_path / "a.parquet"
    archivo.write_bytes(b"version nueva")
    os.utime(archivo, (2_000_000_000, 2_000_000_000))
    assert not ya_esta_en_azure(archivo, _blob(b"version vieja", md5=False, modificado=1_000_000_000))
    assert ya_esta_en_azure(archivo, _blob(b"version vieja", md5=False, modificado=3_000_000_000))
