"""¿Conviene sumar pisos y paredes a la celda del Hot-Deck?

Compara tres celdas sin cambiar la oficial:
  1. depto + ciclo de vida del jefe + cuartos (la actual)
  2. 1 + pisos
  3. 1 + pisos + paredes

Pisos y paredes entran por la escala común de
`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`, agrupada en tres
niveles para no fragmentar las celdas:
  pisos:   acabado (P1-P2) | cemento o madera burda (P3-P4) | tierra (P5)
  paredes: ladrillo/bloque (H1) | tapia o bahareque (H2-H3) | precarias (H4-H7)
Los códigos crudos no se comparan entre fuentes (en pisos van al revés).

Para cada celda: cobertura (cuántos hogares GEIH encuentran donante en la
celda exacta), tamaño de las celdas, distribución de grupos A-D y cuánto
varía P(T | celda), que es lo único que mueve el tratamiento imputado.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.comparar_celdas_hotdeck_vivienda
Salida: docs/reports/comparacion_celdas_hotdeck_vivienda.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import (
    SISBEN, SISBEN_BOG, _sortear, construir_celda,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RECEPTOR = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
REPORT = Path("docs/reports/comparacion_celdas_hotdeck_vivienda.csv")
SEED = 42
MIN_DONANTES = 30

PISOS = {  # código crudo -> nivel común
    "geih": {"5": "acabado", "6": "acabado", "7": "acabado", "4": "acabado",
             "2": "cemento_madera", "3": "cemento_madera", "1": "tierra"},
    "sisben": {"1": "acabado", "2": "acabado", "3": "cemento_madera", "4": "cemento_madera", "5": "tierra"},
}
PAREDES = {
    "geih": {"1": "ladrillo", "2": "ladrillo", "3": "tapia_bahareque", "4": "tapia_bahareque",
             "5": "precaria", "6": "precaria", "7": "precaria", "8": "precaria", "9": "precaria"},
    "sisben": {"1": "ladrillo", "4": "ladrillo", "2": "tapia_bahareque", "3": "tapia_bahareque",
               "5": "precaria", "6": "precaria", "7": "precaria", "0": "precaria"},
}


def _celdas(df: pd.DataFrame, fuente: str) -> dict[str, pd.Series]:
    base = construir_celda(df, edad_en_codigos=fuente == "sisben").reset_index(drop=True)
    pisos = df["viv_pisos"].astype(str).map(PISOS[fuente]).fillna("NA").reset_index(drop=True)
    paredes = df["viv_paredes"].astype(str).map(PAREDES[fuente]).fillna("NA").reset_index(drop=True)
    return {
        "1_depto_edad_cuartos": base,
        "2_mas_pisos": base + "|" + pisos,
        "3_mas_pisos_paredes": base + "|" + pisos + "|" + paredes,
    }


def _evaluar(nombre: str, cr: pd.Series, cd: pd.Series, rec: pd.DataFrame, don: pd.DataFrame) -> dict:
    rng = np.random.default_rng(SEED)
    grupos = {k: v.values for k, v in pd.Series(np.arange(len(don))).groupby(cd.values)}
    elegido = _sortear(grupos, cr, rng)
    exacta = elegido >= 0
    # Respaldo igual al del Hot-Deck: depto + edad, luego depto.
    respaldos = [
        (construir_celda(rec, incluir_vivienda=False), construir_celda(don, edad_en_codigos=True, incluir_vivienda=False)),
        (rec["geo_depto"].astype(str).str.zfill(2), don["geo_depto"].astype(str).str.zfill(2)),
    ]
    for clave_rec, clave_don in respaldos:
        falta = elegido < 0
        if not falta.any():
            break
        g = {k: v.values for k, v in pd.Series(np.arange(len(don))).groupby(clave_don.values)}
        elegido[falta] = _sortear(g, clave_rec.reset_index(drop=True)[falta].reset_index(drop=True), rng)
    elegido[elegido < 0] = rng.integers(0, len(don), size=int((elegido < 0).sum()))

    grupo = pd.Series(don["Grupo"].values[elegido])
    t = grupo.isin(["A", "B"]).astype(float)
    w = pd.to_numeric(rec["fex"], errors="coerce").fillna(0).to_numpy()
    n_don = cr.map(pd.Series({k: len(v) for k, v in grupos.items()})).fillna(0)
    celdas_rec = cr.nunique()
    p_celda = cd.to_frame("c").assign(T=don["Grupo"].isin(["A", "B"]).values).groupby("c")["T"].mean()
    p_rec = cr.map(p_celda)
    pobre = pd.to_numeric(rec["POBRE_MONETARIO"], errors="coerce").to_numpy()
    ok = ~np.isnan(pobre)
    dif_naive = (np.average(pobre[ok & (t == 1)], weights=w[ok & (t == 1)])
                 - np.average(pobre[ok & (t == 0)], weights=w[ok & (t == 0)]))
    fila = dict(
        celda=nombre, celdas_con_receptores=celdas_rec,
        pct_hogares_celda_exacta=exacta.mean() * 100,
        donantes_mediana=float(n_don[exacta].median()), donantes_p5=float(n_don[exacta].quantile(0.05)),
        pct_hogares_celda_menos_30_donantes=float((n_don < MIN_DONANTES).mean() * 100),
        sd_p_t_celda=float(p_rec.std()), p_t_p5=float(p_rec.quantile(0.05)), p_t_p95=float(p_rec.quantile(0.95)),
        corr_p_t_celda_pobre_monetario=float(pd.Series(p_rec.to_numpy()[ok]).corr(pd.Series(pobre[ok]))),
        dif_pobreza_T1_menos_T0=float(dif_naive),
    )
    for g in "ABCD":
        fila[f"pct_grupo_{g}"] = float(np.average(grupo == g, weights=w) * 100)
    return fila


def main() -> None:
    rec = pd.read_parquet(RECEPTOR).reset_index(drop=True)
    sb = SISBEN_BOG if SISBEN_BOG.exists() else SISBEN
    don = pd.read_parquet(sb, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos",
                                       "viv_paredes", "Grupo", "Clasificacion"])
    don = don[don["Clasificacion"].notna()].reset_index(drop=True)
    logger.info("Receptor GEIH: %s hogares | Donante Sisbén: %s hogares", f"{len(rec):,}", f"{len(don):,}")

    c_rec, c_don = _celdas(rec, "geih"), _celdas(don, "sisben")
    tabla = pd.DataFrame([_evaluar(n, c_rec[n], c_don[n], rec, don) for n in c_rec])

    pd.set_option("display.width", 220)
    print("\n=== Celdas Hot-Deck con y sin vivienda homologada ===")
    print(tabla.round(3).T.to_string())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT, index=False)
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
