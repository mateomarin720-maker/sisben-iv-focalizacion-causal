"""Estimación de efectos causales (P2/OE2).

Corrida sobre el outcome construido en `3_preprocesamiento.py` (IPM-GEIH,
8 privaciones verificadas contra el diccionario oficial de GEIH desde
2026-10-28 — empezó en 10, pero `material_pisos_inadecuado`/
`material_paredes_inadecuado` se retiraron el mismo día por ser los
MISMOS códigos que `viv_pisos`/`viv_paredes` de `X` abajo, ver docstring
de `3_preprocesamiento.py`) y el tratamiento asignado por el Hot-Deck con
vivienda sumada a la celda (`geo_depto + jefe_edad + viv_cuartos`, este
último también corregido el 2026-10-28 — antes tomaba el código
equivocado, `docs/seguimiento/CHANGELOG_PENDIENTES.md`).

Los cuatro efectos que pide el documento de pipeline (Roncancio y Fonseca,
2026, Figura 1):
  - **ATE** (efecto promedio global) — `LinearDML` sobre toda la muestra.
  - **ATT** (efecto promedio sobre los hogares tratados, `T=1`) — el
    MISMO `LinearDML`, evaluado solo sobre esa subpoblación.
  - **ATU** (efecto promedio sobre los hogares no tratados, `T=0`) — el
    mismo modelo, evaluado solo sobre esa subpoblación.
  - **CATE** (efecto por tipo de hogar) — `CausalForestDML`.

⚠️ **Rotulado corregido 2026-11-02:** ATT/ATU se venían describiendo en
este repositorio como "error de inclusión"/"error de exclusión" — son
conceptos distintos. ATT/ATU son el efecto promedio del tratamiento en
una subpoblación (tratados o no tratados); error de inclusión/exclusión
es un concepto de focalización (clasificar como pobre/no pobre a quien no
lo es) que no se calcula en este script. No había cómputo erróneo, solo
una etiqueta engañosa — corregida aquí y en
`docs/resultados/RESULTADOS_DML_ATE_ATT_ATU.md`.

  (Se descartó `LinearDRLearner` para ATT/ATU — daba valores absurdos por
  inestabilidad del estimador doblemente robusto; ver docstring de
  `_ate_att_atu`.)

Cada modelo corre con DOS especificaciones de `W`, para diagnosticar una
discrepancia detectada el 2026-11-02 (ver
`docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md`):
  - **`W_COLS_PROXY`** = `{geo_depto, jefe_edad, viv_cuartos}` (la
    especificación usada hasta ahora): `jefe_edad`/`viv_cuartos`
    CONTINUOS como proxy de los tramos discretos que el Hot-Deck usa de
    verdad para el sorteo (`geo_depto + ciclo de vida + tramo de
    cuartos`) — no es una réplica exacta de la celda.
  - **`W_COLS_CELDA`** = `hotdeck_celda_cat`, el código categórico de
    `_hotdeck_celda` (columna que ya guarda `emparejamiento_hotdeck_
    geih_sisben.py` con la celda EXACTA usada en cada sorteo — 376
    celdas, 99,999 % en celda exacta). Esta es la réplica fiel del
    mecanismo real: si el sorteo es verdaderamente aleatorio dentro de
    esa celda (confirmado — `rng.integers` sin ponderar por nada más),
    el tratamiento imputado debería ser independiente de TODO lo demás
    condicional en esta celda, por construcción del propio algoritmo
    (no por supuesto).

`X = {geo_zona, jefe_sexo, viv_paredes, viv_pisos}` son las covariables
NO usadas en la celda, para heterogeneidad (CATE) y como chequeo de que
no quede señal espuria.

⚠️ Limitaciones — las mismas de siempre, sin excepción:
  - El tratamiento es imputado por Hot-Deck, no observado.
  - El outcome es un proxy reducido (8 de 15 privaciones), NO el IPM
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
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression

from econml.dml import LinearDML, CausalForestDML

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA = Path("data/2_models/muestra_estimacion_2024.parquet")
SEED = 42
N_SUB_CATE = 80_000

W_COLS_PROXY = ["geo_depto_cat", "jefe_edad", "viv_cuartos"]  # proxy continuo (especificación anterior)
W_COLS_CELDA = ["hotdeck_celda_cat"]  # celda EXACTA del Hot-Deck (igual al sorteo real)
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
    df["hotdeck_celda_cat"] = df["_hotdeck_celda"].astype("category").cat.codes
    return df


def _modelo_y() -> GradientBoostingRegressor:
    return GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=SEED)


def _ate_att_atu(df: pd.DataFrame, y_col: str, w_cols: list[str]) -> None:
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
    d = df.dropna(subset=[y_col, "T", *w_cols, *X_COLS])
    W = d[w_cols].to_numpy(dtype=float)
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
                          ("ATT (efecto en tratados)", T == 1),
                          ("ATU (efecto en no tratados)", T == 0)]:
        efecto, (lo, hi) = est.ate(X[mask]), est.ate_interval(X[mask], alpha=0.05)
        print(f"  {nombre}: n={mask.sum():,} | {efecto:+.4f}  IC95%=({lo:+.4f}, {hi:+.4f})")


def _cate(df: pd.DataFrame, y_col: str, w_cols: list[str]) -> None:
    d = df.dropna(subset=[y_col, "T", *w_cols, *X_COLS])
    if len(d) > N_SUB_CATE:
        d = d.sample(N_SUB_CATE, random_state=SEED)
    X = d[X_COLS].to_numpy(dtype=float)
    W = d[w_cols].to_numpy(dtype=float)
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

    especificaciones = [
        ("PROXY (geo_depto + jefe_edad continua + viv_cuartos continuo)", W_COLS_PROXY),
        ("CELDA EXACTA (código categórico de _hotdeck_celda, igual al sorteo real)", W_COLS_CELDA),
    ]

    for y_col, etiqueta in [("ipm_geih_score", "ipm_geih_score (continuo, 0-8 privaciones)"),
                             ("POBRE_GEIH", "POBRE_GEIH (binario, score >= K_POBRE adoptado en 3_preprocesamiento.py)")]:
        print("\n" + "#" * 70)
        print(f"# Outcome: {etiqueta}")
        print("#" * 70)
        for w_label, w_cols in especificaciones:
            print("\n" + "=" * 70)
            print(f"W = {w_label}")
            print("=" * 70)
            _ate_att_atu(df, y_col, w_cols)
            _cate(df, y_col, w_cols)

    print("\n" + "=" * 70)
    print("Cómo leer esto: dos especificaciones de W para el mismo outcome.")
    print("Si el efecto con la celda EXACTA no se acerca a 0 frente al PROXY,")
    print("el residuo no se explica por el proxy continuo — ver")
    print("docs/resultados/DIAGNOSTICO_W_CELDA_EXACTA.md.")
    print("=" * 70)


if __name__ == "__main__":
    main()
