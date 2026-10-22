"""Compara el Hot-Deck usando los DOS filtros posibles del SDP (Sisbén
Bogotá) sobre el mismo receptor GEIH, para decidir con evidencia cuál usar
— ver la duda original en docs/seguimiento/CHANGELOG_PENDIENTES.md
(2026-10-10) y la justificación completa en
docs/insumos/DICCIONARIO_HOTDECK.md §8.

Requiere haber corrido antes (ambos modos):
    poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV --modo vigencia
    poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV --modo anio_exacto

Uso:
    poetry run python -m src.validacion.comparar_filtros_sdp
Salida: docs/reports/comparacion_filtros_sdp.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import TRAT, hotdeck

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DIR = Path("data/2_models")
GEIH = DIR / "geih_estandarizado_2024.parquet"
REPORT = Path("docs/reports/comparacion_filtros_sdp.csv")

DONANTES = {
    "vigencia_31dic2024": DIR / "sisben_estandarizado_2024_con_bogota.parquet",
    "anio_exacto_2024": DIR / "sisben_estandarizado_2024_con_bogota_anio_exacto.parquet",
}


def _resumen(nombre: str, out: pd.DataFrame, n_donantes: int) -> dict:
    n = len(out)
    w = pd.to_numeric(out["fex"], errors="coerce").fillna(0)
    grupo_nal = (w.groupby(out["Grupo_hotdeck"]).sum() / w.sum() * 100).round(2)
    pct_exacta = (out["_hotdeck_nivel"] == "celda_exacta").mean() * 100

    bog = out[out["geo_depto"].astype(str).str.zfill(2) == "11"]
    wb = pd.to_numeric(bog["fex"], errors="coerce").fillna(1.0)
    grupo_bog = (wb.groupby(bog["Grupo_hotdeck"]).sum() / wb.sum() * 100).round(2) if len(bog) else pd.Series(dtype=float)

    fila = {
        "filtro": nombre,
        "donantes_totales": n_donantes,
        "receptores_geih": n,
        "pct_celda_exacta": round(pct_exacta, 2),
        "hogares_geih_bogota": len(bog),
    }
    for g in ["A", "B", "C", "D"]:
        fila[f"grupo_nacional_{g}_pct"] = grupo_nal.get(g, 0.0)
    for g in ["A", "B", "C", "D"]:
        fila[f"grupo_bogota_{g}_pct"] = grupo_bog.get(g, 0.0)
    return fila


def main() -> None:
    rec = pd.read_parquet(GEIH)
    filas = []
    for nombre, path in DONANTES.items():
        if not path.exists():
            logger.warning("Falta %s — corra armonizar_sisben_bogota_sdp.py con --modo correspondiente", path)
            continue
        don = pd.read_parquet(path, columns=["geo_depto", "jefe_edad", "viv_cuartos", *TRAT])
        logger.info("[%s] Donante: %s hogares", nombre, f"{len(don):,}")
        out = hotdeck(rec, don)
        filas.append(_resumen(nombre, out, len(don)))

    resultado = pd.DataFrame(filas)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    resultado.to_csv(REPORT, index=False)

    print("\n=== Comparación de filtros del SDP (Sisbén Bogotá) ===\n")
    print(resultado.to_string(index=False))
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
