"""Errores de inclusión y exclusión del Sisbén con datos reales, como
cotas de Fréchet por celda.

La GEIH dice quién es pobre y el Sisbén quién es elegible, pero ningún
hogar está en las dos fuentes, así que no se puede contar cuántos pobres
quedan por fuera. En cada celda c del Hot-Deck sí se conocen la
proporción de pobres p (GEIH, con factor de expansión) y la de elegibles
e (Sisbén). Las cotas de Fréchet acotan las proporciones conjuntas sin
ningún supuesto sobre cómo se relacionan pobreza y elegibilidad dentro de
la celda:

  pobre y no elegible   max(0, p − e) ≤ P(P=1, E=0 | c) ≤ min(p, 1 − e)
  elegible y no pobre   max(0, e − p) ≤ P(P=0, E=1 | c) ≤ min(1 − p, e)

Sumando con los factores de expansión de la GEIH sale el intervalo
nacional y departamental de las dos tasas, con las mismas definiciones de
las reglas de focalización simuladas (`reglas_focalizacion.py`):

  error de exclusión = pobres no elegibles / pobres
  error de inclusión = elegibles no pobres / elegibles

Los denominadores (Σ w·p y Σ w·e) se conocen, así que las cotas de las
tasas son las de los numeradores divididas por ellos. Como referencia se
da también el valor con independencia dentro de la celda, p·(1 − e), que
es lo que produce un Hot-Deck que sortea el grupo al azar en la celda.

Supuesto que sí se mantiene: e es la proporción de elegibles entre los
hogares de la celda registrados en el Sisbén, y se toma como la de la
celda en la GEIH (el mismo supuesto del Hot-Deck; ver
`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`). Celdas de la GEIH sin hogares
del Sisbén: e del primer nivel de la cadena de respaldos del Hot-Deck que
sí los tenga (`claves_por_nivel`).

Elegible: grupos A y B (el tratamiento T del resto del proyecto); como
robustez, A, B y C.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.estimacion.errores_focalizacion_frechet
Salida: docs/reports/errores_focalizacion_frechet.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import claves_por_nivel
from src.estimacion.cotas_frechet_manski import GEIH_PATH, SISBEN_PATH

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/errores_focalizacion_frechet.csv")
POBREZA = ["POBRE_MONETARIO", "POBRE_GEIH", "POBRE_MONETARIO_OFICIAL"]
ELEGIBLE = {"A-B": ["A", "B"], "A-B-C": ["A", "B", "C"]}
CELDA = ["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos"]


def elegibles_por_hogar(geih: pd.DataFrame, sisben: pd.DataFrame, grupos: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """e de la celda de cada hogar GEIH, con la cadena de respaldos, y el
    nivel usado (0 = celda exacta)."""
    elegible = sisben["Grupo"].isin(grupos).astype(float)
    e = np.full(len(geih), np.nan)
    nivel = np.full(len(geih), -1)
    for i, ((_, clave_g), (_, clave_s)) in enumerate(zip(claves_por_nivel(geih, edad_en_codigos=False),
                                                         claves_por_nivel(sisben, edad_en_codigos=True))):
        tasa = elegible.groupby(clave_s.to_numpy()).mean()
        valores = clave_g.map(tasa).to_numpy(float)
        llena = np.isnan(e) & ~np.isnan(valores)
        e[llena], nivel[llena] = valores[llena], i
    sin_celda = np.isnan(e)  # como el Hot-Deck: al final, todo el registro
    e[sin_celda], nivel[sin_celda] = float(elegible.mean()), i + 1
    return e, nivel


def cotas_celda(p: np.ndarray, e: np.ndarray) -> dict[str, np.ndarray]:
    """Fréchet para las dos proporciones conjuntas de una celda, y su
    valor con independencia."""
    return dict(excl_lo=np.maximum(0, p - e), excl_hi=np.minimum(p, 1 - e), excl_ind=p * (1 - e),
                incl_lo=np.maximum(0, e - p), incl_hi=np.minimum(1 - p, e), incl_ind=(1 - p) * e)


def tasas(celdas: pd.DataFrame) -> dict[str, float]:
    """Agrega las cotas por celda (columnas peso, p, e) a las dos tasas."""
    w = celdas["peso"].to_numpy(float)
    c = cotas_celda(celdas["p"].to_numpy(float), celdas["e"].to_numpy(float))
    pobres, elegibles = w @ celdas["p"].to_numpy(float), w @ celdas["e"].to_numpy(float)
    out = {f"exclusion_{k[5:]}": float(w @ v) / pobres for k, v in c.items() if k.startswith("excl")}
    out |= {f"inclusion_{k[5:]}": float(w @ v) / elegibles for k, v in c.items() if k.startswith("incl")}
    return out | dict(tasa_pobreza=pobres / w.sum(), tasa_elegibles=elegibles / w.sum(), celdas=len(celdas))


def calcular(geih: pd.DataFrame, sisben: pd.DataFrame) -> pd.DataFrame:
    celda = claves_por_nivel(geih, edad_en_codigos=False)[0][1].to_numpy()
    filas = []
    for elegible, grupos in ELEGIBLE.items():
        e, nivel = elegibles_por_hogar(geih, sisben, grupos)
        logger.info("Elegible %s: %.2f %% de los hogares GEIH con e de la celda exacta", elegible,
                    100 * np.average(nivel == 0, weights=geih["fex"]))
        for pobre in POBREZA:
            d = pd.DataFrame({"celda": celda, "depto": geih["geo_depto"].astype(str).str.zfill(2).to_numpy(),
                              "w": geih["fex"].to_numpy(float), "y": geih[pobre].to_numpy(float), "e": e})
            d = d[d["y"].notna() & d["e"].notna()]
            d["wy"] = d["w"] * d["y"]
            g = d.groupby(["depto", "celda"]).agg(peso=("w", "sum"), wy=("wy", "sum"), e=("e", "first")).reset_index()
            g["p"] = g["wy"] / g["peso"]
            filas.append(dict(elegible=elegible, pobreza=pobre, ambito="nacional", depto="00", **tasas(g)))
            filas += [dict(elegible=elegible, pobreza=pobre, ambito="departamento", depto=dep, **tasas(gd))
                      for dep, gd in g.groupby("depto")]
    return pd.DataFrame(filas)


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    geih = pd.read_parquet(GEIH_PATH, columns=[*CELDA, "fex", *POBREZA])
    geih["fex"] = pd.to_numeric(geih["fex"], errors="coerce").fillna(0)
    for c in POBREZA:
        geih[c] = pd.to_numeric(geih[c], errors="coerce").astype(float)
    sisben = pd.read_parquet(SISBEN_PATH, columns=[*CELDA, "Grupo", "Clasificacion"])
    return geih, sisben[sisben["Clasificacion"].notna()].reset_index(drop=True)


def main() -> pd.DataFrame:
    geih, sisben = cargar()
    r = calcular(geih, sisben)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    cols = ["exclusion_lo", "exclusion_ind", "exclusion_hi", "inclusion_lo", "inclusion_ind", "inclusion_hi",
            "tasa_pobreza", "tasa_elegibles", "celdas"]
    print("=== Errores de focalización del Sisbén con datos reales: cotas de Fréchet por celda ===")
    print("(lo/hi: cotas sin supuestos dentro de la celda; ind: con independencia, como el Hot-Deck)")
    print(r[r["ambito"] == "nacional"].set_index(["elegible", "pobreza"])[cols].round(3).to_string())
    print("\n--- Por departamento (pobreza monetaria, elegible A-B)")
    dep = r[(r["ambito"] == "departamento") & (r["elegible"] == "A-B") & (r["pobreza"] == "POBRE_MONETARIO")]
    print(dep.set_index("depto")[cols].round(3).to_string())
    print(f"\nGuardado: {OUT}")
    return r


if __name__ == "__main__":
    main()
