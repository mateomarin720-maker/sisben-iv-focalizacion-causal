"""Modo de datos propios: estimación con el tratamiento observado (paso 7
del diseño).

Una institución que trae su tabla de hogares con el grupo del Sisbén
(`Grupo`) y la forma en que lo obtuvo (`vinculo`) recibe, además de la
evaluación semisintética*, la estimación con sus datos reales:

  - LinearDML con la celda exacta del Hot-Deck como controles y las X del
    proyecto, igual que `src/5_estimacion.py` (mismos modelos auxiliares);
  - la cota de Fréchet del mismo contraste, que no supone el vínculo
    (`src/diagnostico/cotas_frechet_modelos.py`).

Resultados: log-ingreso per cápita y pobreza monetaria (ingreso per
cápita por debajo de la línea de su dominio). Si `vinculo` es `hotdeck`,
el DML se rotula como placebo del emparejamiento y no como efecto: el
grupo se sorteó dentro de la celda (`IDENTIFICACION_CAUSAL.md`). Con
`llave` (cruce hogar a hogar), es la estimación del efecto bajo el
supuesto de que la celda y las X bastan como controles.

Estas cifras son reales: no llevan asterisco.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.simulacion import contrato
from src.simulacion.base import preparar_base
from src.simulacion.estimadores import estimacion5

RESULTADOS = {"log_ingreso_percapita": "log-ingreso per cápita", "pobre_monetario": "pobreza monetaria"}


def lectura(vinculo: pd.Series) -> str:
    if (vinculo == "hotdeck").any():
        return "placebo del emparejamiento (el grupo se sorteó dentro de la celda): no es el efecto"
    return "efecto con vínculo hogar a hogar, si la celda y las X bastan como controles"


def estimacion_observada(hogares: pd.DataFrame, p_t_celda: pd.Series, semilla: int | None = None) -> pd.DataFrame:
    """DML con la celda exacta y cota de Fréchet, por resultado. `hogares`
    debe cumplir el contrato y traer `Grupo` y `vinculo`."""
    from econml.dml import LinearDML

    from src.diagnostico.cotas_frechet_modelos import agregar, cotas_contraste

    faltan = [c for c in ("Grupo", "vinculo") if c not in hogares.columns]
    if faltan:
        raise contrato.ErrorContrato(f"La estimación con datos reales necesita {faltan} en la tabla de hogares")
    b = preparar_base(hogares, p_t_celda)
    if len(b) != len(hogares):
        raise RuntimeError("preparar_base descartó hogares: el grupo observado ya no está alineado")
    est5 = estimacion5()
    t = hogares["Grupo"].astype(str).isin(["A", "B"]).astype(int).to_numpy()
    fex = pd.to_numeric(hogares["fex"], errors="coerce").to_numpy(float) if "fex" in hogares else np.ones(len(b))
    ys = {"log_ingreso_percapita": b["y0"].to_numpy(float),
          "pobre_monetario": (b["y0"] < b["log_lp"]).astype(float).to_numpy()}
    X, W = b[est5.X_COLS].to_numpy(float), b[est5.W_CELDA[0]].to_numpy(float)
    filas = []
    for nombre, y in ys.items():
        modelo_y, modelo_t = est5._modelos_auxiliares(est5.W_CELDA)
        m = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True,
                      random_state=est5.SEED if semilla is None else semilla)
        m.fit(y, t, X=X, W=W)
        lo, hi = m.ate_interval(X, alpha=0.05)
        celdas = cotas_contraste(pd.DataFrame({"celda": b["celda"], "fex": fex, nombre: y}),
                                 p_t_celda, nombre)
        c_lo, c_hi = agregar(celdas, "ATE")
        filas.append(dict(resultado=RESULTADOS[nombre], hogares=len(b), tratados=float(t.mean()),
                          ate_dml=float(m.ate(X)), ic_lo=float(lo), ic_hi=float(hi),
                          cota_frechet_lo=c_lo, cota_frechet_hi=c_hi, lectura=lectura(hogares["vinculo"])))
    return pd.DataFrame(filas)
