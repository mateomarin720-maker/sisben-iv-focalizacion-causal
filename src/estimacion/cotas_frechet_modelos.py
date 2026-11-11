"""Cotas de Fréchet para cada parámetro de los modelos: el mismo número
que reporta el DML o el Causal Forest, sin suponer el vínculo del Hot-Deck.

El DML (`src/5_estimacion.py`) da un punto con IC porque supone que el
grupo sorteado por el Hot-Deck reproduce la relación real entre grupo y
resultado dentro de la celda. Este script acota los mismos parámetros sin
ese supuesto: usa la distribución de Y en la celda (GEIH) y la proporción
A/B en la celda (Sisbén), y recorre todos los acoples compatibles con
esas dos marginales (Fréchet-Hoeffding). Mantiene el otro supuesto del
DML, que dentro de la celda no hay confusión, así que lo que se acota es
el contraste E[Y | T=1, celda] − E[Y | T=0, celda] en cada celda,
agregado como cada parámetro:

  ATE   ponderado por el peso de la celda en GEIH (fex)
  ATT   ponderado por peso · P(T=1 | celda): los hogares A/B de la celda
  ATU   ponderado por peso · P(T=0 | celda)
  CATE  por subgrupo de las X del Causal Forest (zona, sexo del jefe,
        paredes en la escala común): celda × subgrupo, con P(T) del
        Sisbén en esa misma celda × subgrupo

Cota del contraste en una celda con P(T=1) = p (sirve para Y binaria o
continua, con pesos): el acople extremo pone a los A/B en una cola de la
distribución de Y y al resto en la otra,
  mínimo = media de la fracción p más baja − media de la fracción 1−p más alta
  máximo = media de la fracción p más alta − media de la fracción 1−p más baja
Con Y binaria coincide con `cotas_frechet` de `cotas_frechet_manski.py`.

Celdas pequeñas: con pocos hogares GEIH, P(Y) sale 0 o 1 y la cota se
cierra en [0; 0] por azar de muestreo, no por los datos. Por eso se
reporta también la cota solo con celdas de al menos `N_MINIMO` hogares en
cada fuente.

Outcomes: los cinco de `5_estimacion.py` (IPM continuo y binario,
log-ingreso per cápita, pobreza monetaria reconstruida y oficial).

Uso (requiere 3b_preprocesamiento_monetario.py):
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.estimacion.cotas_frechet_modelos
Salida: docs/reports/cotas_frechet_modelos.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda
from src.estimacion.cotas_frechet_manski import GEIH_PATH, SISBEN_PATH
from src.validacion.comparar_celdas_hotdeck_vivienda import PAREDES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/cotas_frechet_modelos.csv")
OUTCOMES = ["ipm_geih_score", "POBRE_GEIH", "log_ingreso_percapita", "POBRE_MONETARIO", "POBRE_MONETARIO_OFICIAL"]
N_MINIMO = 30
SUBGRUPOS = ("zona", "sexo_jefe", "paredes")  # las X del Causal Forest
COLUMNAS = ["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "viv_paredes", "geo_zona", "jefe_sexo"]


def subgrupos(df: pd.DataFrame, fuente: str) -> pd.DataFrame:
    """Las X del Causal Forest con el mismo código en las dos fuentes:
    zona (1 = urbano en ambas), sexo del jefe (1 = hombre, 2 = mujer: ficha
    del Sisbén IV, pregunta 47, y GEIH `P3271`) y paredes en la escala
    común de `HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`."""
    return pd.DataFrame({
        "zona": np.where(df["geo_zona"].astype(str) == "1", "urbana", "rural"),
        "sexo_jefe": df["jefe_sexo"].astype(str).map({"1": "hombre", "2": "mujer"}),
        "paredes": df["viv_paredes"].astype(str).map(PAREDES[fuente]),
    }, index=df.index)


def suma_cola_baja(y: np.ndarray, w: np.ndarray, celda: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Por hogar ordenado: lo que aporta a Σ w·y de la fracción q (en peso)
    más baja de Y en su celda. `y`, `w` y `celda` deben venir ordenados por
    (celda, y); `q` es la fracción de la celda de cada hogar."""
    total = pd.Series(w).groupby(celda).transform("sum").to_numpy()
    previo = pd.Series(w).groupby(celda).cumsum().to_numpy() - w
    parte = np.clip(q * total - previo, 0, w)  # peso del hogar que cae en la cola
    return parte * y


def cotas_contraste(geih: pd.DataFrame, p_t: pd.Series, y_col: str) -> pd.DataFrame:
    """Por celda: P(T), peso, n y la cota del contraste E[Y|T=1] − E[Y|T=0].
    `geih` trae `celda`, `fex` y el outcome; `p_t` va indexada por celda."""
    d = geih.loc[geih[y_col].notna(), ["celda", "fex", y_col]].copy()
    d = d[d["celda"].isin(p_t.index)]
    d["p"] = d["celda"].map(p_t).astype(float)
    d = d.sort_values(["celda", y_col], kind="mergesort")
    y, w, celda, p = (d[y_col].to_numpy(float), d["fex"].to_numpy(float), d["celda"].to_numpy(), d["p"].to_numpy())
    d["baja_p"] = suma_cola_baja(y, w, celda, p)
    d["baja_1p"] = suma_cola_baja(y, w, celda, 1 - p)
    d["wy"] = w * y
    g = d.groupby("celda").agg(peso=("fex", "sum"), n_geih=("fex", "size"), p_t=("p", "first"), s=("wy", "sum"),
                               baja_p=("baja_p", "sum"), baja_1p=("baja_1p", "sum"))
    g = g[(g["p_t"] > 0) & (g["p_t"] < 1) & (g["peso"] > 0)]
    tw, p = g["peso"], g["p_t"]
    t1_lo, t0_hi = g["baja_p"] / (p * tw), (g["s"] - g["baja_p"]) / ((1 - p) * tw)
    t0_lo, t1_hi = g["baja_1p"] / ((1 - p) * tw), (g["s"] - g["baja_1p"]) / (p * tw)
    g["cota_lo"], g["cota_hi"] = t1_lo - t0_hi, t1_hi - t0_lo
    return g


def p_t_por_celda(sisben: pd.DataFrame) -> pd.DataFrame:
    t1 = sisben["Grupo"].isin(["A", "B"]).astype(float)
    return t1.groupby(sisben["celda"]).agg(["mean", "size"]).rename(columns={"mean": "p_t", "size": "n_sisben"})


def agregar(g: pd.DataFrame, parametro: str) -> tuple[float, float]:
    peso = {"ATE": g["peso"], "ATT": g["peso"] * g["p_t"], "ATU": g["peso"] * (1 - g["p_t"])}[parametro]
    w = peso / peso.sum()
    return float(w @ g["cota_lo"]), float(w @ g["cota_hi"])


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    geih = pd.read_parquet(GEIH_PATH, columns=[*COLUMNAS, "fex", "ingreso_percapita",
                                               *[o for o in OUTCOMES if o != "log_ingreso_percapita"]])
    geih["log_ingreso_percapita"] = np.log1p(pd.to_numeric(geih["ingreso_percapita"], errors="coerce"))
    geih["fex"] = pd.to_numeric(geih["fex"], errors="coerce").fillna(0)
    for o in OUTCOMES:
        geih[o] = pd.to_numeric(geih[o], errors="coerce").astype(float)
    sisben = pd.read_parquet(SISBEN_PATH, columns=[*COLUMNAS, "Grupo", "Clasificacion"])
    sisben = sisben[sisben["Clasificacion"].notna()]
    geih["celda"] = construir_celda(geih, edad_en_codigos=False).to_numpy()
    sisben["celda"] = construir_celda(sisben, edad_en_codigos=True).to_numpy()
    return (pd.concat([geih, subgrupos(geih, "geih")], axis=1),
            pd.concat([sisben, subgrupos(sisben, "sisben")], axis=1))


def calcular(geih: pd.DataFrame, sisben: pd.DataFrame) -> pd.DataFrame:
    filas = []
    # (subgrupo, nivel): None = toda la población (ATE, ATT, ATU)
    cortes = [(None, None)] + [(s, nivel) for s in SUBGRUPOS for nivel in sorted(geih[s].dropna().unique())]
    for subgrupo, nivel in cortes:
        if subgrupo is None:
            ge, si = geih, sisben
        else:  # celda × subgrupo: P(T) del Sisbén dentro del mismo subgrupo
            ge, si = geih[geih[subgrupo] == nivel], sisben[sisben[subgrupo] == nivel]
        pt, total = p_t_por_celda(si), ge["fex"].sum()
        for y_col in OUTCOMES:
            g = cotas_contraste(ge, pt["p_t"], y_col).join(pt["n_sisben"])
            for muestra, gm in [("todas", g), (f"n>={N_MINIMO}", g[(g["n_geih"] >= N_MINIMO) & (g["n_sisben"] >= N_MINIMO)])]:
                for parametro in (["ATE", "ATT", "ATU"] if subgrupo is None else ["CATE"]):
                    lo, hi = agregar(gm, "ATE" if parametro == "CATE" else parametro)
                    filas.append(dict(outcome=y_col, parametro=parametro, subgrupo=subgrupo or "todos",
                                      nivel=nivel or "todos", muestra=muestra, cota_lo=lo, cota_hi=hi, ancho=hi - lo,
                                      excluye_0=bool(lo > 0 or hi < 0), celdas=len(gm),
                                      cobertura=float(gm["peso"].sum() / total)))
    return pd.DataFrame(filas)


def main() -> pd.DataFrame:
    geih, sisben = cargar()
    logger.info("GEIH %s hogares | Sisbén %s hogares clasificados", f"{len(geih):,}", f"{len(sisben):,}")
    r = calcular(geih, sisben)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    r.to_csv(OUT, index=False)
    pd.set_option("display.width", 250)
    for muestra, g in r.groupby("muestra", sort=False):
        print(f"\n=== Cotas de Fréchet por parámetro de los modelos (celdas: {muestra}) ===")
        print(g.drop(columns="muestra").round(4).to_string(index=False))
    print(f"\nGuardado: {OUT}")
    return r


if __name__ == "__main__":
    main()
