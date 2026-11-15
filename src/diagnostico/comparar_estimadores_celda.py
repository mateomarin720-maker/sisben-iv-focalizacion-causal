"""Comparación de estimadores con la celda exacta, con datos reales.

En la simulación, con 30.000 hogares y ≈8 por celda, LinearDML se sesga
(−0,035 con efecto nulo): la regularización y el ajuste cruzado de sus
modelos auxiliares dejan confusión entre celdas
(`docs/resultados/3_simulacion/SIMULACION_SEMISINTETICA.md`, punto 8).
Este módulo comprueba si pasa lo mismo con los 290.968 hogares reales:
estima el ATE con la celda exacta de tres formas y las compara.

  - LinearDML con la regularización del proyecto (la de `5_estimacion.py`).
  - LinearDML casi sin regularizar (`CASI_SIN_REGULARIZAR`).
  - Regresión con efectos fijos de celda, sin modelos auxiliares ni ajuste
    cruzado (`simulacion.estimadores.regresion_efectos_fijos`).

Si las tres coinciden, el sesgo de la simulación no se traslada a la
estimación con datos reales.

Uso: python -m src.diagnostico.comparar_estimadores_celda
Salida: docs/reports/comparar_estimadores_celda.txt (lo que imprime)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulacion.estimadores import estimacion5, regresion_efectos_fijos

OUTCOMES = ["log_ingreso_percapita", "POBRE_MONETARIO", "POBRE_GEIH"]


def linear_dml(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, regularizado: bool) -> tuple[float, float, float]:
    from econml.dml import LinearDML

    est5 = estimacion5()
    extra = {} if regularizado else est5.CASI_SIN_REGULARIZAR
    modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA, **extra)
    X = d[est5.X_COLS].to_numpy(float)
    m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=est5.SEED)
    m.fit(y, t, X=X, W=d[est5.W_CELDA[0]].to_numpy(float))
    lo, hi = m.ate_interval(X, alpha=0.05)
    return float(m.ate(X)), float(lo), float(hi)


def efectos_fijos(d: pd.DataFrame, y: np.ndarray, t: np.ndarray) -> tuple[float, float, float]:
    """X en indicadoras (paredes es categórica sin orden) y efectos fijos de celda."""
    est5 = estimacion5()
    Z = pd.get_dummies(d[est5.X_COLS].astype(str), drop_first=True).to_numpy(float)
    celda = pd.factorize(d[est5.W_CELDA[0][0]])[0]
    return regresion_efectos_fijos(y, t, Z, celda)


def comparar(df: pd.DataFrame, outcomes: list[str] = OUTCOMES) -> pd.DataFrame:
    est5 = estimacion5()
    filas = []
    for y_col in outcomes:
        d = df.dropna(subset=[y_col, "T", est5.W_CELDA[0][0], *est5.X_COLS])
        y, t = d[y_col].to_numpy(float), d["T"].to_numpy(int)
        for nombre, (a, lo, hi) in [("linear_dml", linear_dml(d, y, t, True)),
                                     ("linear_dml_casi_sin_regularizar", linear_dml(d, y, t, False)),
                                     ("regresion_efectos_fijos", efectos_fijos(d, y, t))]:
            filas.append(dict(outcome=y_col, estimador=nombre, ate=a, ic_lo=lo, ic_hi=hi))
    return pd.DataFrame(filas)


def main() -> pd.DataFrame:
    est5 = estimacion5()
    df = est5._preparar(pd.read_parquet(est5.DATA))
    tam = df.groupby(est5.W_CELDA[0][0]).size()
    print(f"Hogares: {len(df):,} | celdas: {len(tam):,} | hogares por celda: media {tam.mean():.0f}, "
          f"mediana {tam.median():.0f}")
    r = comparar(df)
    pd.set_option("display.width", 200)
    print(r.round(4).to_string(index=False))
    rango = r.groupby("outcome")["ate"].agg(lambda x: x.max() - x.min())
    print("\nDiferencia máxima entre estimadores:", rango.round(4).to_dict())
    print("Todos los IC incluyen el 0:", bool(((r["ic_lo"] <= 0) & (r["ic_hi"] >= 0)).all()))
    return r


if __name__ == "__main__":
    main()
