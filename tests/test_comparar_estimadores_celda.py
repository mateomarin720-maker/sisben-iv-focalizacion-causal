"""Comparación de estimadores con la celda exacta
(`src/diagnostico/comparar_estimadores_celda.py`)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.diagnostico import comparar_estimadores_celda as ce


def _datos(n: int = 6_000, celdas: int = 60, efecto: float = 0.0, seed: int = 0) -> pd.DataFrame:
    """T sorteado dentro de la celda con P(T | celda) distinta por celda, y
    un resultado que depende de la celda: confusión entre celdas."""
    rng = np.random.default_rng(seed)
    celda = rng.integers(0, celdas, n)
    p = np.linspace(0.2, 0.8, celdas)[celda]
    t = (rng.random(n) < p).astype(int)
    y = 2.0 * p + efecto * t + rng.normal(0, 0.3, n)
    return pd.DataFrame({"hotdeck_celda_cat": celda, "T": t, "log_ingreso_percapita": y,
                         "geo_zona_urbana": rng.integers(0, 2, n), "jefe_mujer": rng.integers(0, 2, n),
                         "viv_paredes": rng.integers(1, 4, n)})


def test_con_celdas_grandes_los_tres_estimadores_recuperan_el_efecto():
    """Con 100 hogares por celda, los tres controlan la confusión entre
    celdas y recuperan el efecto (0,1)."""
    r = ce.comparar(_datos(efecto=0.1), outcomes=["log_ingreso_percapita"]).set_index("estimador")
    assert set(r.index) == {"linear_dml", "linear_dml_casi_sin_regularizar", "regresion_efectos_fijos"}
    for est, fila in r.iterrows():
        assert fila["ic_lo"] <= 0.1 <= fila["ic_hi"], est
        assert abs(fila["ate"] - 0.1) < 0.03, est


def test_sin_controlar_la_celda_habria_sesgo():
    """Control negativo: la diferencia de medias, sin la celda, sí se
    sesga; así la prueba de arriba no pasa por falta de confusión."""
    d = _datos()
    dif = d.loc[d["T"] == 1, "log_ingreso_percapita"].mean() - d.loc[d["T"] == 0, "log_ingreso_percapita"].mean()
    assert dif > 0.1
