"""Asignación del tratamiento verdadero en el mundo semisintético."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulacion.escenarios import B_X


def sigmoide(z):
    return 1 / (1 + np.exp(-z))


def asignar(b: pd.DataFrame, escenario: dict, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, float]:
    """T verdadero, puntaje y corte. score = logit P_Sisbén(T | celda) +
    X·b + gamma·U. La tasa de tratados es la del Sisbén real (media de
    P(T | celda)) en todos los escenarios: el intercepto se calibra en los
    de Bernoulli y el corte es un cuantil en la regla."""
    pbar = float(sigmoide(b["logit_p_celda"]).mean())
    precaria = (b["viv_paredes"] != 1).astype(float)
    x = (B_X["rural"] * (1 - b["geo_zona_urbana"]) + B_X["mujer"] * b["jefe_mujer"]
         + B_X["paredes_precaria"] * precaria)
    s = (escenario["celda"] * b["logit_p_celda"] + escenario["x"] * x
         + escenario["gamma"] * b["u"]).to_numpy(float)
    s = escenario["escala"] * (s - s.mean())
    if escenario.get("corte"):
        puntaje = s + rng.normal(0, escenario["ruido_puntaje"], len(s))
        corte = float(np.quantile(puntaje, 1 - pbar))
        return (puntaje >= corte).astype(int), puntaje, corte
    lo, hi = -20.0, 20.0
    for _ in range(60):  # bisección: media de la propensión = pbar
        c = (lo + hi) / 2
        lo, hi = (c, hi) if sigmoide(c + s).mean() < pbar else (lo, c)
    return (rng.random(len(b)) < sigmoide(c + s)).astype(int), s, np.nan
