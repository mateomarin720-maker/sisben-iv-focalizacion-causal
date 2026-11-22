"""Enlace fraccional por hogar: el paso del pipeline que guarda la FHDI.

Por cada hogar de la GEIH guarda la probabilidad de cada grupo del Sisbén
según su celda (FEFI), con la misma celda y cadena de respaldos del
Hot-Deck. Es lo que leen los módulos que usan el enlace fraccional, como
la fusionada del Hot-Deck para el sorteo.

Por qué se guarda la probabilidad y no la base expandida de 10 donantes:
con los pesos calibrados (`reglas.py`), la distribución por grupo de los
10 donantes de cada hogar es exactamente la de su celda, así que toda
cantidad que dependa del grupo da lo mismo con la base expandida que con
la probabilidad (`tests/test_fhdi.py`). La base expandida se reconstruye
con `reglas.donantes_fraccionales` y la semilla 42 si hiciera falta.

Columnas (una fila por hogar, en el orden de la muestra de estimación):
  llave_directorio, llave_secuencia_p, llave_hogar, mes   llave del hogar
  _hotdeck_celda    celda exacta (la misma de la fusionada del Hot-Deck)
  fhdi_nivel        nivel de la cadena usado (celda_exacta, …, pool_nacional)
  fhdi_p_A … fhdi_p_D  probabilidad de cada grupo (suman 1)
  fhdi_p_AB         probabilidad de A o B (el tratamiento T del proyecto)
  fhdi_donantes_celda  donantes del Sisbén en la celda usada

Uso (lee de Azure en memoria; con `--publicar` sube el resultado a Azure):
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.emparejamiento.fhdi.enlace --publicar
Salida: data/2_models/geih_sisben_fhdi_2024.parquet
"""
from __future__ import annotations

import io
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import CELDA_COLUMNAS, construir_celda
from src.emparejamiento.fhdi import reglas
from src.utils.azure_storage import leer_bytes, subir_archivo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

AZ_GEIH = "2_models/muestra_estimacion_monetaria_2024.parquet"
AZ_SISBEN = "2_models/sisben_estandarizado_2024_con_bogota.parquet"
AZ_SALIDA = "2_models/geih_sisben_fhdi_2024.parquet"
SALIDA = Path("data") / AZ_SALIDA
LLAVE = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]


def tabla_enlace(receptor: pd.DataFrame, donante: pd.DataFrame) -> pd.DataFrame:
    """Una fila por receptor, en su mismo orden, con la probabilidad de
    cada grupo de su celda y el nivel de la cadena."""
    pi, nivel = reglas.probabilidades(receptor, donante)
    _, celda, celdas_donante, total = reglas.asignar_nivel(receptor, donante)
    donantes = np.bincount(np.concatenate([*celdas_donante, np.full(len(donante), total)]), minlength=total + 1)
    out = receptor[[c for c in LLAVE if c in receptor]].copy().reset_index(drop=True)
    out["_hotdeck_celda"] = construir_celda(receptor).to_numpy()
    out["fhdi_nivel"] = nivel
    for k, g in enumerate(reglas.GRUPOS):
        out[f"fhdi_p_{g}"] = pi[:, k]
    out["fhdi_p_AB"] = pi[:, list(reglas.ELEGIBLE)].sum(axis=1)
    out["fhdi_donantes_celda"] = donantes[celda]
    return out


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    geih = pd.read_parquet(io.BytesIO(leer_bytes(AZ_GEIH)), columns=[*LLAVE, *CELDA_COLUMNAS, "_hotdeck_celda"])
    sisben = pd.read_parquet(io.BytesIO(leer_bytes(AZ_SISBEN)), columns=[*CELDA_COLUMNAS, "Grupo", "Clasificacion", "fex"])
    return geih, sisben[sisben["Clasificacion"].notna()].reset_index(drop=True)


def main(publicar: bool = False) -> pd.DataFrame:
    geih, sisben = cargar()
    out = tabla_enlace(geih, sisben)
    # La celda debe ser la misma que guardó el Hot-Deck: si no, la
    # armonización o la celda cambiaron después de la fusionada.
    distinta = (out["_hotdeck_celda"] != geih["_hotdeck_celda"].astype(str)).mean()
    if distinta > 0:
        raise SystemExit(f"La celda no coincide con la del Hot-Deck en el {distinta:.2%} de los hogares")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(SALIDA, index=False)
    print("=== Enlace fraccional (FHDI) por hogar ===")
    print(f"Hogares GEIH: {len(out):,} | donantes Sisbén: {len(sisben):,}")
    print((out["fhdi_nivel"].value_counts(normalize=True) * 100).round(2).astype(str) + " %")
    print(f"Probabilidad media de A/B (sin ponderar): {out['fhdi_p_AB'].mean():.4f} | "
          f"hogares con P(A/B) entre 0,3 y 0,7: {out['fhdi_p_AB'].between(0.3, 0.7).mean() * 100:.1f} %")
    print(f"Guardado: {SALIDA}")
    if publicar:
        subir_archivo(SALIDA, AZ_SALIDA)
        print(f"Publicado en Azure: {AZ_SALIDA}")
    return out


if __name__ == "__main__":
    main(publicar="--publicar" in sys.argv[1:])
