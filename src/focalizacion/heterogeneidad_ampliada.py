"""¿Sirven los efectos heterogéneos para focalizar si la heterogeneidad
es más amplia o más compleja que la del generador base?

Las reglas de focalización (`reglas_focalizacion.py`) concluyen que
ordenar por el CATE estimado empeora la focalización, pero con un efecto
que varía poco entre hogares (desviación ≈0,028) y solo por tres
variables. Este script repite las mismas reglas, con los mismos hogares,
la misma asignación y los mismos dos presupuestos, cambiando solo el
efecto verdadero tau(X):

  basico     el del generador (zona, jefatura femenina, paredes): son las
             cifras de `reglas_focalizacion.py`, no se repiten aquí
  ampliado   más modificadores con sentido socioeconómico: logro educativo
             y cotización a pensión del jefe, hogar de 5 o más personas,
             jefe de 60 años o más y piso de tierra
  complejo   el ampliado más una interacción (rural × bajo logro), un
             efecto no lineal del tamaño del hogar y diferencias entre
             departamentos

En los niveles nuevos, tau = 0,095 + 0,06 · h estandarizado (media igual
a la del generador, desviación más del doble), con un piso de 0,005, y el
Causal Forest ve todos los modificadores (X): es el caso favorable al
CATE. Papel de cada variable: modificadora del efecto; la asignación y la
confusión no cambian (`docs/resultados/3_simulacion/SIMULACION_SEMISINTETICA.md`).

Las cifras son simuladas (*).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.heterogeneidad_ampliada [n_jobs] [nivel]
Salidas (por nivel):
    docs/reports/heterogeneidad_<nivel>{.csv,_resumen.csv,_config.json}
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.simulacion.escenarios import TAU
from src.focalizacion import reglas_focalizacion as rf

NIVELES = ("ampliado", "complejo")
TAU_MEDIA, TAU_DESVIACION, TAU_PISO = 0.095, 0.06, 0.005
SEMILLA_DEPTO = 7
# Coeficientes antes de estandarizar (definen la forma, no la escala).
COEF_AMPLIADO = dict(rural=TAU["rural"], mujer=TAU["mujer"], paredes_precaria=TAU["paredes_precaria"],
                     bajo_logro=0.05, sin_pension=0.04, hogar_grande=0.03, jefe_mayor=0.04, piso_tierra=0.05)
COEF_COMPLEJO = dict(rural_x_bajo_logro=0.06, tamano_no_lineal=0.06, depto_desviacion=0.05)
X_BASE = ["geo_zona_urbana", "jefe_mujer", "viv_paredes"]
X_AMPLIADO = X_BASE + ["het_bajo_logro", "het_sin_pension", "het_personas", "het_jefe_mayor", "het_piso_tierra"]
X_POR_NIVEL = {"ampliado": X_AMPLIADO, "complejo": X_AMPLIADO + ["het_depto"]}


def modificadores(b: pd.DataFrame, hogares: pd.DataFrame) -> pd.DataFrame:
    """Agrega a la tabla de trabajo las variables que modifican el efecto
    (0/1 o conteos). `hogares` es la tabla de origen, fila por fila."""
    b = b.copy()
    b["het_bajo_logro"] = (b["bajo_logro_educativo_jefe"] > 0).astype(float)
    b["het_sin_pension"] = (b["sin_cotizacion_pension_jefe"] > 0).astype(float)
    b["het_personas"] = b["hog_num_personas"].astype(float)
    b["het_jefe_mayor"] = (pd.to_numeric(hogares["jefe_edad"], errors="coerce").to_numpy() >= 60).astype(float)
    b["het_piso_tierra"] = (hogares["viv_pisos"].astype(str).to_numpy() == "1").astype(float)  # GEIH P4020: 1 = tierra
    b["het_depto"] = b["depto"].astype("category").cat.codes.astype(float)  # en X de un bosque (no lineal): seguro
    return b


def forma(b: pd.DataFrame, nivel: str) -> np.ndarray:
    """h(X) del nivel, antes de estandarizar."""
    c = COEF_AMPLIADO
    rural = 1 - b["geo_zona_urbana"].to_numpy(float)
    h = (c["rural"] * rural + c["mujer"] * b["jefe_mujer"].to_numpy(float)
         + c["paredes_precaria"] * (b["viv_paredes"] != 1).to_numpy(float)
         + c["bajo_logro"] * b["het_bajo_logro"].to_numpy() + c["sin_pension"] * b["het_sin_pension"].to_numpy()
         + c["hogar_grande"] * (b["het_personas"].to_numpy() >= 5) + c["jefe_mayor"] * b["het_jefe_mayor"].to_numpy()
         + c["piso_tierra"] * b["het_piso_tierra"].to_numpy())
    if nivel == "complejo":
        k = COEF_COMPLEJO
        deptos = np.sort(b["depto"].unique())
        efecto_depto = dict(zip(deptos, np.random.default_rng(SEMILLA_DEPTO).normal(0, k["depto_desviacion"], len(deptos))))
        h = (h + k["rural_x_bajo_logro"] * rural * b["het_bajo_logro"].to_numpy()
             + k["tamano_no_lineal"] * np.exp(-((b["het_personas"].to_numpy() - 4) ** 2) / 2)
             + b["depto"].map(efecto_depto).to_numpy(float))
    elif nivel != "ampliado":
        raise ValueError(f"Nivel desconocido: {nivel!r}; use uno de {NIVELES}")
    return h


def efecto_por_nivel(b: pd.DataFrame, nivel: str) -> np.ndarray:
    """tau del nivel: media 0,095 y desviación 0,06 (antes del piso)."""
    h = forma(b, nivel)
    return np.maximum(TAU_MEDIA + TAU_DESVIACION * (h - h.mean()) / h.std(), TAU_PISO)


def rutas(nivel: str) -> tuple[Path, Path, Path]:
    base = Path("docs/reports") / f"heterogeneidad_{nivel}"
    return base.with_suffix(".csv"), Path(f"{base}_resumen.csv"), Path(f"{base}_config.json")


def main(n_jobs: int = 3, *niveles: str) -> None:
    b, hogares = rf.cargar_base()
    b = modificadores(b, hogares)
    for nivel in niveles or NIVELES:
        bn = b.copy()
        bn["tau"] = efecto_por_nivel(bn, nivel)
        rf.logger.info("Nivel %s: tau media %.4f, desviación %.4f", nivel, bn["tau"].mean(), bn["tau"].std())
        salida, resumen, cfg = rutas(nivel)
        firma = rf.firma(nivel=nivel, COEF_AMPLIADO=COEF_AMPLIADO, COEF_COMPLEJO=COEF_COMPLEJO, X=X_POR_NIVEL[nivel],
                         TAU_NIVEL=[TAU_MEDIA, TAU_DESVIACION, TAU_PISO, SEMILLA_DEPTO])
        r = rf.correr(bn, salida, resumen, cfg, firma, n_jobs, X_POR_NIVEL[nivel])
        rf.imprimir(r, f"Reglas de focalización con heterogeneidad {nivel}")
        print(f"Guardado: {salida}\nGuardado: {resumen}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(int(args[0]) if args else 3, *args[1:])
