"""Modelos auxiliares del DML (`src/5_estimacion.py`).

Hasta el 2026-11-02 la celda del Hot-Deck entraba a la propensión como su
código numérico: la propensión salía ≈0,64 para todos los hogares y los
ATE (+0,02 con IC sin el 0) eran un artefacto. No daba error. Estas
pruebas fijan que las categóricas entren como indicadoras y que la
propensión reproduzca P(T | celda)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("estimacion_5", ROOT / "src" / "5_estimacion.py")
est5 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(est5)

N_CELDAS = 40


def _datos(seed: int, n: int = 8000, efecto: float = 0.0) -> pd.DataFrame:
    """Celdas con P(T | celda) sin orden respecto al código (como el
    código de celda real), X como en el pipeline, y un nivel de Y por celda
    correlacionado con P(T) (confusión entre celdas)."""
    rng = np.random.default_rng(seed)
    p_celda = rng.permutation(np.linspace(0.15, 0.85, N_CELDAS))
    celda = rng.integers(0, N_CELDAS, n)
    t = (rng.random(n) < p_celda[celda]).astype(int)
    d = pd.DataFrame({
        "hotdeck_celda_cat": celda,
        "geo_zona_urbana": rng.integers(0, 2, n),
        "jefe_mujer": rng.integers(0, 2, n),
        "viv_paredes": rng.choice([1, 1, 1, 2, 5], n),
        "T": t,
    })
    d["Y"] = -2.0 * p_celda[celda] + 0.3 * d["geo_zona_urbana"] + efecto * t + rng.normal(0, 0.5, n)
    d["p_empirica"] = d.groupby("hotdeck_celda_cat")["T"].transform("mean")
    return d


def test_codificador_convierte_las_categoricas_en_indicadoras():
    cols = ["geo_zona_urbana", "jefe_mujer", "viv_paredes", "hotdeck_celda_cat"]
    cod = est5._codificador(cols, ["viv_paredes", "hotdeck_celda_cat"], [])
    d = _datos(0, n=500)
    Z = cod.fit_transform(d[cols].to_numpy(float))
    n_ind = d["viv_paredes"].nunique() + d["hotdeck_celda_cat"].nunique()
    assert Z.shape[1] == n_ind + 2  # indicadoras + las dos binarias tal cual


@pytest.mark.parametrize("seed", range(5))
def test_propension_reproduce_p_t_por_celda(seed):
    d = _datos(seed)
    _, modelo_t = est5._modelos_auxiliares(est5.W_CELDA, con_x=False)
    W = d[est5.W_CELDA[0]].to_numpy(float)
    prop = modelo_t.fit(W, d["T"]).predict_proba(W)[:, 1]
    assert np.corrcoef(prop, d["p_empirica"])[0, 1] > 0.99
    assert np.abs(prop - d["p_empirica"]).mean() < 0.01


@pytest.mark.parametrize("seed", range(5))
def test_el_error_anterior_no_reproduce_p_t(seed):
    """Con la celda como número (el error anterior), la propensión no
    sigue a P(T | celda): esta prueba documenta por qué la de arriba
    importa."""
    d = _datos(seed)
    prop = LogisticRegression(C=10.0, max_iter=2000).fit(d[["hotdeck_celda_cat"]], d["T"]).predict_proba(
        d[["hotdeck_celda_cat"]])[:, 1]
    assert np.corrcoef(prop, d["p_empirica"])[0, 1] < 0.6


def _ate(d: pd.DataFrame) -> tuple[float, float, float]:
    from econml.dml import LinearDML

    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA)
    m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=est5.SEED)
    X, W = d[est5.X_COLS].to_numpy(float), d[est5.W_CELDA[0]].to_numpy(float)
    m.fit(d["Y"].to_numpy(), d["T"].to_numpy(), X=X, W=W)
    lo, hi = m.ate_interval(X, alpha=0.05)
    return float(m.ate(X)), float(lo), float(hi)


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("efecto", [0.0, 0.5])
def test_linear_dml_con_la_celda_recupera_el_efecto(seed, efecto):
    """Con T asignado dentro de la celda y confusión entre celdas, el DML
    con indicadoras de celda recupera el efecto (0 o 0,5): la confusión
    entre celdas (−2 · P(T | celda)) no se cuela."""
    ate, lo, hi = _ate(_datos(seed, efecto=efecto))
    assert abs(ate - efecto) < 0.06
    assert lo - 0.02 <= efecto <= hi + 0.02


def test_regularizacion_vigente_y_la_de_sensibilidad():
    """Las cifras publicadas salen de alpha 1 y C 10; la versión casi sin
    regularizar (sensibilidad) se pide explícitamente."""
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA)
    assert (modelo_y[-1].alpha, modelo_t[-1].C) == (1.0, 10.0)
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA, **est5.CASI_SIN_REGULARIZAR)
    assert modelo_y[-1].alpha <= 1e-4 and modelo_t[-1].C >= 1e4
