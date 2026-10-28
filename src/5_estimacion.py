"""Estimación de efectos causales (P2/OE2).

Corrida sobre el outcome construido en `3_preprocesamiento.py` (IPM-GEIH,
10 privaciones verificadas contra el diccionario oficial de GEIH desde
2026-10-28) y el tratamiento asignado por el Hot-Deck con vivienda sumada
a la celda (`geo_depto + jefe_edad + viv_cuartos`, este último también
corregido el 2026-10-28 — antes tomaba el código equivocado,
`docs/seguimiento/CHANGELOG_PENDIENTES.md`).

Los cuatro efectos que pide el documento de pipeline (Roncancio y Fonseca,
2026, Figura 1):
  - **ATE** (efecto promedio global) — `LinearDML` sobre toda la muestra.
  - **ATT** (efecto sobre los tratados, error de inclusión) — el MISMO
    `LinearDML`, evaluado solo sobre los hogares con `T=1`.
  - **ATU** (efecto sobre los no tratados, error de exclusión) — el mismo
    modelo, evaluado solo sobre los hogares con `T=0`.
  - **CATE** (efecto por tipo de hogar) — `CausalForestDML`.

  (Se descartó `LinearDRLearner` para ATT/ATU — daba valores absurdos por
  inestabilidad del estimador doblemente robusto; ver docstring de
  `_ate_att_atu`.)

Cada modelo controla por `W = {geo_depto, jefe_edad, viv_cuartos}` — la
celda COMPLETA del Hot-Deck tal como quedó implementada (ver
`docs/resultados/IDENTIFICACION_CAUSAL.md`: dado W, el grupo asignado
debería quedar d-separado del outcome). `X = {geo_zona, jefe_sexo,
viv_paredes, viv_pisos}` son las covariables NO usadas en la celda, para
heterogeneidad (CATE) y como chequeo de que no quede señal espuria.

⚠️ Limitaciones — las mismas de siempre, sin excepción:
  - El tratamiento es imputado por Hot-Deck, no observado.
  - El outcome es un proxy reducido (4 de 15 privaciones), NO el IPM
    oficial — ver docstring de `3_preprocesamiento.py` para qué se incluyó
    y qué no, y la limitación de `sin_cotizacion_pension_jefe`.
  - Sin ajuste por diseño muestral de GEIH ni de Sisbén.
  - El Sisbén solo cubre hogares inscritos (selección).
  - Falta DPS/RUI como confusores (canal de la Figura 2 sin datos todavía).

Uso:
    poetry run python src/5_estimacion.py
Salida: docs/reports/estimacion_ate_att_atu_cate.txt (vía redirección de
consola) y resumen interpretado en docs/resultados/.
"""
from __future__ import annotations

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression

from econml.dml import LinearDML, CausalForestDML

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA = Path("data/2_models/muestra_estimacion_2024.parquet")
SEED = 42
N_SUB_CATE = 80_000

W_COLS = ["geo_depto_cat", "jefe_edad", "viv_cuartos"]  # celda completa del Hot-Deck
X_COLS = ["geo_zona_urbana", "jefe_mujer", "viv_paredes", "viv_pisos"]  # NO usadas en la celda


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["T"] = df["Grupo_hotdeck"].isin(["A", "B"]).astype(int)
    df["jefe_edad"] = pd.to_numeric(df["jefe_edad"], errors="coerce")
    for c in ["viv_paredes", "viv_pisos", "viv_cuartos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["geo_zona_urbana"] = (df["geo_zona"] == "1").astype(int)
    df["jefe_mujer"] = (df["jefe_sexo"] == "2").astype(int)
    df["geo_depto_cat"] = df["geo_depto"].astype("category").cat.codes
    return df


def _modelo_y() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=SEED)


def _ate_att_atu(df: pd.DataFrame, y_col: str) -> None:
    """ATE, ATT y ATU con el MISMO LinearDML ya ajustado — se evalúa
    `effect()`/`ate()` sobre tres poblaciones distintas (todos, T=1, T=0).

    Se descartó `LinearDRLearner` para ATT/ATU: con las mismas covariables
    daba valores absurdos (cientos de unidades en un outcome acotado entre
    0 y 4) por inestabilidad del estimador doblemente robusto cuando hay
    poca superposición de propensión en algunas celdas — un caso real de
    "no confiar en el número solo porque el modelo corrió sin error".
    Reusar el LinearDML (ya estable para el ATE completo) evaluado en cada
    subpoblación evita ese problema y es una forma válida de reportar
    ATT/ATU bajo el mismo marco DML.
    """
    d = df.dropna(subset=[y_col, "T", *W_COLS, *X_COLS])
    W = d[W_COLS].to_numpy(dtype=float)
    X = d[X_COLS].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)

    modelo_t = LogisticRegression(max_iter=1000)
    modelo_t.fit(W, T)
    prop = modelo_t.predict_proba(W)[:, 1]
    print(f"  Propensión (T=1 | W): min={prop.min():.3f} p5={np.percentile(prop,5):.3f} "
          f"p95={np.percentile(prop,95):.3f} max={prop.max():.3f}")

    est = LinearDML(model_y=_modelo_y(), model_t=LogisticRegression(max_iter=1000),
                     discrete_treatment=True, random_state=SEED)
    est.fit(Y, T, X=X, W=W)

    for nombre, mask in [("ATE (toda la muestra)", np.ones(len(d), dtype=bool)),
                          ("ATT (tratados, error de inclusión)", T == 1),
                          ("ATU (no tratados, error de exclusión)", T == 0)]:
        efecto, (lo, hi) = est.ate(X[mask]), est.ate_interval(X[mask], alpha=0.05)
        print(f"  {nombre}: n={mask.sum():,} | {efecto:+.4f}  IC95%=({lo:+.4f}, {hi:+.4f})")


def _cate(df: pd.DataFrame, y_col: str) -> None:
    d = df.dropna(subset=[y_col, "T", *W_COLS, *X_COLS])
    if len(d) > N_SUB_CATE:
        d = d.sample(N_SUB_CATE, random_state=SEED)
    X = d[X_COLS].to_numpy(dtype=float)
    W = d[W_COLS].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)
    est = CausalForestDML(model_y=_modelo_y(), model_t=LogisticRegression(max_iter=1000),
                           discrete_treatment=True, n_estimators=400, min_samples_leaf=50, random_state=SEED)
    est.fit(Y, T, X=X, W=W)
    cate = est.effect(X)
    print(f"  CATE: n={len(d):,} | media={cate.mean():+.4f}  sd={cate.std():.4f}  "
          f"rango=({cate.min():+.4f}, {cate.max():+.4f})")
    d = d.assign(_cate=cate)
    print("  Por zona (urbana=1):", d.groupby("geo_zona_urbana")["_cate"].mean().round(4).to_dict())
    print("  Por sexo jefe (mujer=1):", d.groupby("jefe_mujer")["_cate"].mean().round(4).to_dict())
    imp = pd.Series(est.feature_importances_, index=X_COLS).sort_values(ascending=False)
    print("  Importancia de variables:", imp.round(3).to_dict())


def main() -> None:
    logger.info("Cargando %s", DATA)
    if not DATA.exists():
        raise SystemExit(f"Falta {DATA}: corra src/3_preprocesamiento.py primero")
    df = _preparar(pd.read_parquet(DATA))
    logger.info("n=%s | T=1 (Grupo A/B): %.1f%%", f"{len(df):,}", df["T"].mean() * 100)

    for y_col, etiqueta in [("ipm_geih_score", "ipm_geih_score (continuo, 0-10 privaciones)"),
                             ("POBRE_GEIH", "POBRE_GEIH (binario, score >= K_POBRE adoptado en 3_preprocesamiento.py)")]:
        print("\n" + "=" * 70)
        print(f"Outcome: {etiqueta}")
        print("=" * 70)
        _ate_att_atu(df, y_col)
        _cate(df, y_col)

    print("\n" + "=" * 70)
    print("Cómo leer esto: W = celda completa del Hot-Deck (depto+edad+cuartos).")
    print("Si el efecto no es ~0, no se puede interpretar como causal del Sisbén")
    print("sin antes descartar fuga por geografía/vivienda — ver IDENTIFICACION_CAUSAL.md.")
    print("=" * 70)


if __name__ == "__main__":
    main()
