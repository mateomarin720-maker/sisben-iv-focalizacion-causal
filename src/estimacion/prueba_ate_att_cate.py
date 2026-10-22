"""PRUEBA EXPLORATORIA de ATE/ATT/CATE — no es la implementación de 5_estimacion.py
(esa sigue pendiente de Fase 4; requiere outcomes oficiales y el DAG de
4_dag_identificacion.py, ninguno de los dos existe todavía).

Objetivo de este script: ver cómo se comportan los estimadores con las
variables que YA tenemos, y de paso usarlo como chequeo de validez del
Hot-Deck: la celda de emparejamiento es `geo_depto + jefe_edad` (ciclo de
vida) — dado que el donante se sortea AL AZAR dentro de esa celda, el
tratamiento asignado (`Grupo_hotdeck`) debería ser independiente del
outcome UNA VEZ que se controla por `geo_depto` y `jefe_edad`. Por eso se
corre cada modelo dos veces:
  (a) controlando solo por covariables NO usadas en el matching (geo_zona,
      jefe_sexo, vivienda) -> si aparece un "efecto", es geografía/edad
      colándose por una puerta de atrás, no señal real del Hot-Deck.
  (b) agregando geo_depto + jefe_edad como controles -> si el efecto de (a)
      colapsa hacia 0 aquí, confirma que el Hot-Deck no está inventando
      heterogeneidad espuria más allá de su propia celda.

Tratamiento: T = 1 si Grupo_hotdeck ∈ {A,B} (grupos prioritarios de
focalización), 0 si ∈ {C,D}. Es una definición de prueba, no la variable de
tratamiento final del anteproyecto (que usa el puntaje/grupo completo).

Outcomes de prueba (derivados en preparar_outcome_prueba_empleo.py, NO son
los outcomes oficiales de ingreso per cápita / IPM / seguridad alimentaria):
  Y1 = jefe_ocupado (0/1), muestra completa.
  Y2 = log(jefe_ingreso_laboral), solo jefes ocupados.

⚠️ Limitaciones que aplican a TODO lo que imprime este script (no son solo
una nota al final): el tratamiento es imputado por Hot-Deck, no observado;
no hay ajuste por diseño muestral de GEIH ni por el de Sisbén; el Sisbén
solo cubre hogares inscritos (selección); faltan RUI/DPS como confusores;
zona/paredes/pisos no están verificados contra la ficha oficial. Esto sirve
para ver que el pipeline corre y se comporta de forma sensata — no para
reportar un efecto causal del Sisbén todavía.

Uso:
    poetry run python -m src.estimacion.prueba_ate_att_cate
"""
from __future__ import annotations

import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression

from econml.dml import LinearDML, CausalForestDML
from econml.dr import LinearDRLearner

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA = Path("data/2_models/muestra_estimacion_prueba.parquet")
SEED = 42
N_SUB_CATE = 80_000  # submuestra para CausalForestDML (velocidad)


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["T"] = df["Grupo_hotdeck"].isin(["A", "B"]).astype(int)
    df["jefe_edad"] = pd.to_numeric(df["jefe_edad"], errors="coerce")
    for c in ["viv_paredes", "viv_pisos", "viv_cuartos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["geo_zona_urbana"] = (df["geo_zona"] == "1").astype(int)
    df["jefe_mujer"] = (df["jefe_sexo"] == "2").astype(int)
    df["geo_depto_cat"] = df["geo_depto"].astype("category").cat.codes
    df["jefe_ocupado"] = pd.to_numeric(df["jefe_ocupado"], errors="coerce")
    return df


X_OTHER = ["geo_zona_urbana", "jefe_mujer", "viv_paredes", "viv_pisos", "viv_cuartos"]
W_MATCHING = ["geo_depto_cat", "jefe_edad"]


def _ate_dml(df: pd.DataFrame, y_col: str, x_cols: list[str], etiqueta: str) -> float:
    d = df.dropna(subset=[y_col, "T", *x_cols])
    X = d[x_cols].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)
    est = LinearDML(
        model_y=GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=SEED),
        model_t=LogisticRegression(max_iter=1000),
        discrete_treatment=True,
        random_state=SEED,
    )
    est.fit(Y, T, X=X)
    ate = est.ate(X)
    lo, hi = est.ate_interval(X, alpha=0.05)
    print(f"  [{etiqueta}] n={len(d):,} | ATE={ate:+.4f}  IC95%=({lo:+.4f}, {hi:+.4f})")
    return ate


def _att_dr(df: pd.DataFrame, y_col: str, x_cols: list[str], etiqueta: str) -> None:
    d = df.dropna(subset=[y_col, "T", *x_cols])
    X = d[x_cols].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)
    est = LinearDRLearner(
        model_propensity=LogisticRegression(max_iter=1000),
        model_regression=GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=SEED),
        random_state=SEED,
    )
    est.fit(Y, T, X=X)
    X_tratados = X[T == 1]
    att = est.ate(X_tratados)
    lo, hi = est.ate_interval(X_tratados, alpha=0.05)
    print(f"  [{etiqueta}] n_tratados={T.sum():,} | ATT={att:+.4f}  IC95%=({lo:+.4f}, {hi:+.4f})")


def _cate_forest(df: pd.DataFrame, y_col: str, x_het: list[str], w_cols: list[str], etiqueta: str) -> None:
    d = df.dropna(subset=[y_col, "T", *x_het, *w_cols])
    if len(d) > N_SUB_CATE:
        d = d.sample(N_SUB_CATE, random_state=SEED)
    X = d[x_het].to_numpy(dtype=float)
    W = d[w_cols].to_numpy(dtype=float) if w_cols else None
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)
    est = CausalForestDML(
        model_y=GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=SEED),
        model_t=LogisticRegression(max_iter=1000),
        discrete_treatment=True,
        n_estimators=400,
        min_samples_leaf=50,
        random_state=SEED,
    )
    est.fit(Y, T, X=X, W=W)
    cate = est.effect(X)
    print(f"  [{etiqueta}] n={len(d):,} | CATE media={cate.mean():+.4f}  sd={cate.std():.4f}  "
          f"rango=({cate.min():+.4f}, {cate.max():+.4f})")
    d = d.assign(_cate=cate)
    print("  Heterogeneidad por subgrupo (media de CATE):")
    print("    por zona (urbana=1):", d.groupby(d["geo_zona_urbana"])["_cate"].mean().round(4).to_dict())
    print("    por sexo jefe (mujer=1):", d.groupby(d["jefe_mujer"])["_cate"].mean().round(4).to_dict())
    try:
        imp = pd.Series(est.feature_importances_, index=x_het).sort_values(ascending=False)
        print("    importancia de variables (forest):", imp.round(3).to_dict())
    except Exception as e:  # noqa: BLE001
        logger.warning("No se pudo calcular feature_importances_: %s", e)


def main() -> None:
    logger.info("Cargando %s", DATA)
    df = _preparar(pd.read_parquet(DATA))
    logger.info("n=%s | T=1 (Grupo A/B): %.1f%%", f"{len(df):,}", df["T"].mean() * 100)

    print("\n" + "=" * 70)
    print("DIFERENCIA NAÍVE EN MEDIAS (sin controles) — referencia")
    print("=" * 70)
    for y in ["jefe_ocupado", "jefe_ingreso_laboral"]:
        d = df.dropna(subset=[y])
        m1, m0 = d.loc[d["T"] == 1, y].mean(), d.loc[d["T"] == 0, y].mean()
        print(f"  {y}: media T=1 -> {m1:.3f} | media T=0 -> {m0:.3f} | diferencia = {m1 - m0:+.3f}")

    print("\n" + "=" * 70)
    print("Y1 = jefe_ocupado (0/1) — muestra completa")
    print("=" * 70)
    print("ATE:")
    _ate_dml(df, "jefe_ocupado", X_OTHER, "(a) sin depto/edad")
    _ate_dml(df, "jefe_ocupado", X_OTHER + W_MATCHING, "(b) con depto/edad")
    print("ATT:")
    _att_dr(df, "jefe_ocupado", X_OTHER, "(a) sin depto/edad")
    _att_dr(df, "jefe_ocupado", X_OTHER + W_MATCHING, "(b) con depto/edad")
    print("CATE (Causal Forest, heterogeneidad en zona/sexo/vivienda):")
    _cate_forest(df, "jefe_ocupado", X_OTHER, [], "(a) sin depto/edad como control")
    _cate_forest(df, "jefe_ocupado", X_OTHER, W_MATCHING, "(b) con depto/edad como control")

    print("\n" + "=" * 70)
    print("Y2 = log(jefe_ingreso_laboral) — solo jefes ocupados")
    print("=" * 70)
    df2 = df.copy()
    df2["log_ingreso"] = np.log1p(df2["jefe_ingreso_laboral"])
    print("ATE:")
    _ate_dml(df2, "log_ingreso", X_OTHER, "(a) sin depto/edad")
    _ate_dml(df2, "log_ingreso", X_OTHER + W_MATCHING, "(b) con depto/edad")

    print("\n" + "=" * 70)
    print("Lectura esperada (chequeo de validez del Hot-Deck):")
    print("  Si el ATE/CATE de (a) es distinto de 0 pero el de (b) colapsa hacia 0,")
    print("  es evidencia de que el 'efecto' de (a) es geografía/edad colándose por")
    print("  la puerta de atrás (depto+edad correlacionan con Grupo_hotdeck por el")
    print("  diseño de la celda, y con el outcome por economía regional/ciclo de vida)")
    print("  — NO una heterogeneidad real que el Hot-Deck esté capturando.")
    print("=" * 70)


if __name__ == "__main__":
    main()
