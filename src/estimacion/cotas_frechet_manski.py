"""Cotas de Fréchet–Manski para el ATE — alternativa al Hot-Deck que NO
supone independencia condicional (CIA).

Item "por explorar" de la Tabla 1 del documento de pipeline (Roncancio y
Fonseca, 2026): el Hot-Deck asume que, dada la celda X, el grupo Sisbén
asignado es como-si-aleatorio (ver `docs/resultados/IDENTIFICACION_CAUSAL.md`).
Si esa suposición falla, el DML (`src/5_estimacion.py`) puede estar sesgado
sin que su IC95% lo refleje — el IC mide error de muestreo, no error de la
suposición de independencia.

Las cotas de Fréchet–Manski (Manski, 2003) no imputan nada: usan
DIRECTAMENTE `P(Y|X)` calculada solo en GEIH y `P(T|X)` calculada solo en
Sisbén (sin Hot-Deck de por medio), y aplican la desigualdad de
Fréchet–Hoeffding — dadas dos marginales sin conocer su dependencia
conjunta, hay un RANGO de distribuciones conjuntas compatibles con ellas,
desde la más favorable hasta la menos favorable. El resultado no es un
punto, es un intervalo: el verdadero ATE está ahí dentro sin importar qué
tan buena sea la celda del Hot-Deck.

Por celda X (misma celda del Hot-Deck: depto + ciclo de edad + tramo de
cuartos):
    P(Y=1,T=1|X) ∈ [max(0, P(Y=1|X)+P(T=1|X)-1), min(P(Y=1|X), P(T=1|X))]
    P(Y=1,T=0|X) ∈ [max(0, P(Y=1|X)-P(T=1|X)), min(P(Y=1|X), 1-P(T=1|X))]
    CATE(X) = E[Y|T=1,X] - E[Y|T=0,X], cota = [inf(T=1)-sup(T=0), sup(T=1)-inf(T=0)]
Agregado a ATE ponderando por el peso poblacional de cada celda en GEIH
(`FEX_C18`/`fex`).

Outcomes: `POBRE_GEIH` y `POBRE_MONETARIO` (binarios). Las cotas de
Fréchet-Hoeffding para un outcome continuo (`ipm_geih_score`,
`log_ingreso_percapita`) requieren acotar la CDF conjunta completa;
quedan fuera de este corte. Los hogares sin `POBRE_MONETARIO` (sin
personas, ingreso per cápita indefinido) se excluyen de su cálculo.

Uso (requiere 3b_preprocesamiento_monetario.py):
    poetry run python -m src.estimacion.cotas_frechet_manski
Salida: detalle por celda en docs/reports/cotas_frechet_manski.csv
        (POBRE_GEIH) y cotas_frechet_manski_pobre_monetario.csv, más un
        resumen impreso en consola.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import construir_celda

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_PATH = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
SISBEN_PATH = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
OUTCOMES = {
    "POBRE_GEIH": Path("docs/reports/cotas_frechet_manski.csv"),
    "POBRE_MONETARIO": Path("docs/reports/cotas_frechet_manski_pobre_monetario.csv"),
    # Robustez: clasificación oficial DANE, sin los 9 departamentos que su base no trae
    "POBRE_MONETARIO_OFICIAL": Path("docs/reports/cotas_frechet_manski_pobre_monetario_oficial.csv"),
}
REPORT_MONOTONIA = Path("docs/reports/cotas_frechet_manski_monotonia.csv")


def _p_y_por_celda(geih: pd.DataFrame, y_col: str) -> pd.DataFrame:
    """P(Y=1|X) en GEIH, ponderado por el factor de expansión (encuesta
    compleja) — a diferencia de Sisbén, GEIH SÍ trae un diseño muestral
    real y hay que respetarlo."""
    geih = geih[geih[y_col].notna()].copy()
    geih["celda"] = construir_celda(geih, edad_en_codigos=False)
    geih["fex"] = pd.to_numeric(geih["fex"], errors="coerce").fillna(0)
    geih["y1"] = geih[y_col].astype(float) * geih["fex"]

    agg = geih.groupby("celda").agg(
        n_geih=(y_col, "size"),
        peso_fex=("fex", "sum"),
        y1_fex=("y1", "sum"),
    )
    agg["p_y"] = agg["y1_fex"] / agg["peso_fex"]
    return agg[["n_geih", "peso_fex", "p_y"]]


def _p_t_por_celda(sisben: pd.DataFrame) -> pd.DataFrame:
    """P(T=1|X) en Sisbén — sin ponderar: el Sisbén no es una encuesta con
    diseño muestral (es administrativo/censal de los hogares registrados),
    así que el conteo simple por celda es lo que hay."""
    s = sisben[sisben["Clasificacion"].notna()].copy()
    s["celda"] = construir_celda(s, edad_en_codigos=True)
    s["t1"] = s["Grupo"].isin(["A", "B"]).astype(float)

    agg = s.groupby("celda").agg(n_sisben=("t1", "size"), p_t=("t1", "mean"))
    return agg


def cotas_frechet(p_y, p_t) -> pd.DataFrame:
    """Cotas de Fréchet-Hoeffding de E[Y|T=1], E[Y|T=0] y del CATE dadas
    solo las marginales P(Y=1) y P(T=1) de una celda. Con P(T) en 0 o 1 el
    contraste no está definido (NaN)."""
    p_y, p_t = np.asarray(p_y, float), np.asarray(p_t, float)
    pyt1_lo = np.maximum(0, p_y + p_t - 1)
    pyt1_hi = np.minimum(p_y, p_t)
    pyt0_lo = np.maximum(0, p_y - p_t)
    pyt0_hi = np.minimum(p_y, 1 - p_t)

    with np.errstate(divide="ignore", invalid="ignore"):
        out = pd.DataFrame({
            "e_y_t1_lo": np.where(p_t > 0, pyt1_lo / p_t, np.nan),
            "e_y_t1_hi": np.where(p_t > 0, pyt1_hi / p_t, np.nan),
            "e_y_t0_lo": np.where((1 - p_t) > 0, pyt0_lo / (1 - p_t), np.nan),
            "e_y_t0_hi": np.where((1 - p_t) > 0, pyt0_hi / (1 - p_t), np.nan),
        })
    out["cate_lo"] = out["e_y_t1_lo"] - out["e_y_t0_hi"]
    out["cate_hi"] = out["e_y_t1_hi"] - out["e_y_t0_lo"]
    return out


def ate_agregado(df: pd.DataFrame) -> tuple[float, float]:
    """Cota del ATE: promedio de las cotas por celda ponderado por el peso
    poblacional de la celda en GEIH (`peso_fex`)."""
    w = df["peso_fex"] / df["peso_fex"].sum()
    return float((w * df["cate_lo"]).sum()), float((w * df["cate_hi"]).sum())


SUPUESTOS = [  # (nombre, ¿es el ATE causal?, dependencia positiva, MTS, MTR)
    ("contraste", False, False, False, False),
    ("contraste_dep_positiva", False, True, False, False),
    ("ate_sin_supuestos", True, False, False, False),
    ("ate_mts", True, False, True, False),
    ("ate_mtr", True, False, False, True),
    ("ate_mts_mtr", True, False, True, True),
    ("ate_mts_mtr_dep_positiva", True, True, True, True),
]


def cotas_con_supuestos(p_y, p_t) -> pd.DataFrame:
    """Cotas por celda bajo supuestos de monotonía (Manski y Pepper, 2000),
    con Y = pobreza (1 = pobre) y T = clasificado en A/B.

    Dos problemas superpuestos: (1) no se observa la conjunta de T e Y
    (fuentes sin llave): P11 = P(Y=1, T=1) ∈ [L, U] de Fréchet; (2) no se
    observan los resultados potenciales. Para cada P11 factible:
      contraste   E[Y|T=1] − E[Y|T=0] = P11/p_t − (p_y − P11)/(1 − p_t)
                  (lo que acota el script desde el inicio; es el ATE solo
                  si no hay confusión dentro de la celda)
      sin supuestos   ATE ∈ [2·P11 − p_y − p_t, 2·P11 − p_y − p_t + 1]
      MTS  (los A/B son al menos tan pobres como el resto en ambos
            resultados potenciales): cota superior = contraste
      MTR  (el programa no aumenta la pobreza de nadie): cota superior = 0
    `dep_positiva` (dentro de la celda, los A/B son al menos tan pobres:
    P11 ≥ p_y·p_t) recorta el rango de P11. Todas las cotas son monótonas
    en P11, así que la unión sobre los P11 factibles se alcanza en sus
    extremos. Ningún supuesto de estos sube la cota inferior del ATE salvo
    la dependencia positiva."""
    p_y, p_t = np.asarray(p_y, float), np.asarray(p_t, float)
    lo11, hi11 = np.maximum(0, p_y + p_t - 1), np.minimum(p_y, p_t)
    lo11_dep = np.maximum(lo11, p_y * p_t)

    def contraste(p11):
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where((p_t > 0) & (p_t < 1), p11 / p_t - (p_y - p11) / (1 - p_t), np.nan)

    out = {}
    for nombre, causal, dep, mts, mtr in SUPUESTOS:
        lo11_s = lo11_dep if dep else lo11
        if not causal:
            lo, hi = contraste(lo11_s), contraste(hi11)
        else:
            lo = 2 * lo11_s - p_y - p_t
            hi = 2 * hi11 - p_y - p_t + 1
            if mts:
                hi = np.minimum(hi, contraste(hi11))
            if mtr:
                hi = np.minimum(hi, 0.0)
            lo = np.where(np.isnan(contraste(hi11)), np.nan, lo)
        out[f"{nombre}_lo"], out[f"{nombre}_hi"] = lo, hi
    return pd.DataFrame(out)


def cotas_por_celda(geih: pd.DataFrame, sisben: pd.DataFrame, y_col: str = "POBRE_GEIH") -> pd.DataFrame:
    py = _p_y_por_celda(geih, y_col)
    pt = _p_t_por_celda(sisben)
    df = py.join(pt, how="inner")  # solo celdas con info de AMBAS fuentes
    cotas = cotas_frechet(df["p_y"], df["p_t"]).set_index(df.index)
    return pd.concat([df, cotas], axis=1).reset_index()


def main() -> None:
    logger.info("Cargando %s y %s", GEIH_PATH, SISBEN_PATH)
    geih = pd.read_parquet(GEIH_PATH, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "fex", *OUTCOMES])
    sisben = pd.read_parquet(SISBEN_PATH, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "Grupo", "Clasificacion"])
    total_geih = pd.to_numeric(geih["fex"], errors="coerce").fillna(0).sum()
    filas_monotonia = []

    for y_col, report in OUTCOMES.items():
        df = cotas_por_celda(geih, sisben, y_col)
        df = df.dropna(subset=["cate_lo", "cate_hi"])

        cobertura = df["peso_fex"].sum()
        ate_lo, ate_hi = ate_agregado(df)
        p_y = (df["peso_fex"] / cobertura * df["p_y"]).sum()

        report.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(report, index=False)

        print(f"\n=== Cotas de Fréchet-Manski — ATE sobre {y_col} ===")
        print(f"Celdas usadas: {len(df)} | cobertura poblacional GEIH: {cobertura / total_geih * 100:.1f}%")
        print(f"P(Y=1) ponderada en las celdas usadas: {p_y:.4f}")
        print(f"ATE (Fréchet-Manski, SIN suponer independencia condicional): [{ate_lo:+.4f}, {ate_hi:+.4f}]")
        print(f"Ancho de la cota: {ate_hi - ate_lo:.4f}")
        print(f"Detalle por celda: {report}")

        sup = cotas_con_supuestos(df["p_y"], df["p_t"])
        w = (df["peso_fex"] / cobertura).to_numpy()
        for nombre, *_ in SUPUESTOS:
            lo, hi = float((w * sup[f"{nombre}_lo"]).sum()), float((w * sup[f"{nombre}_hi"]).sum())
            filas_monotonia.append(dict(outcome=y_col, supuesto=nombre, cota_lo=lo, cota_hi=hi, ancho=hi - lo,
                                        celdas=len(df)))

    tabla = pd.DataFrame(filas_monotonia)
    tabla.to_csv(REPORT_MONOTONIA, index=False)
    print("\n=== Cotas con supuestos de monotonía (Manski y Pepper, 2000) ===")
    print(tabla.round(4).to_string(index=False))
    print(f"Guardado: {REPORT_MONOTONIA}")

    print(
        "\nATE puntual del DML con Hot-Deck (SÍ supone CIA): ver "
        "docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md — no se hardcodea aquí."
    )


if __name__ == "__main__":
    main()
