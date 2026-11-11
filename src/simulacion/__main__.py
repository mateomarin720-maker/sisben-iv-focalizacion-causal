"""Línea de comandos del módulo de simulación.

Tres usos:

  Corrida de la tesis (hogares de la GEIH 2024 y Sisbén del banco de datos):
    python -m src.simulacion [n_jobs]
    Salidas en docs/reports/simulacion_semisintetica* y
    docs/resultados/3_simulacion/simulacion_semisintetica_convergencia.png

  Modo simulado (sin microdatos; población sintética desde los agregados
  de src/simulacion/parametros/poblacion_2024.json):
    python -m src.simulacion simulado --salida CARPETA [--hogares 300000] [--semilla 2026]
        [--procesos 3] [--repeticiones N]

  Modo de datos propios (tabla de hogares con las columnas canónicas; si
  trae Grupo y vinculo, además la estimación con datos reales):
    python -m src.simulacion propios --hogares RUTA --salida CARPETA [--registro RUTA]
        [--procesos 3] [--repeticiones N]

Los resultados de la evaluación son simulados (*). La estimación con el
grupo observado (modo de datos propios) es real y se guarda aparte, en
estimacion_datos_reales.csv.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from src.simulacion import contrato
from src.simulacion.escenarios import MAX_REPS, N_ENCUESTA

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def _leer(ruta: str, rol: str) -> pd.DataFrame:
    """Parquet o CSV con las columnas canónicas (como texto: un código
    '01' no se convierte en 1)."""
    ruta = Path(ruta)
    if ruta.suffix.lower() == ".csv":
        tabla = pd.read_csv(ruta, dtype=str)
        for c in ("ingreso_percapita", "fex"):
            if c in tabla:
                tabla[c] = pd.to_numeric(tabla[c], errors="coerce")
    else:
        tabla = pd.read_parquet(ruta)
    return contrato.validar(tabla, rol)


def _argumentos(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="python -m src.simulacion")
    sub = p.add_subparsers(dest="modo", required=True)
    for nombre in ("simulado", "propios"):
        s = sub.add_parser(nombre)
        s.add_argument("--salida", required=True, help="carpeta donde se guardan los resultados")
        s.add_argument("--procesos", type=int, default=3)
        s.add_argument("--repeticiones", type=int, default=MAX_REPS, help="tope de repeticiones; se revisa al cerrar cada lote de 24")
        s.add_argument("--encuesta", type=int, default=N_ENCUESTA, help="hogares de la encuesta por repetición")
    sim = sub.choices["simulado"]
    sim.add_argument("--hogares", type=int, default=300_000)
    sim.add_argument("--semilla", type=int, default=2026)
    pro = sub.choices["propios"]
    pro.add_argument("--hogares", required=True, help="tabla de hogares (Parquet o CSV)")
    pro.add_argument("--registro", help="registro del Sisbén para P(T | celda); si no, los agregados del modo simulado")
    return p.parse_args(argv)


def main(argv: list[str]) -> None:
    from src.simulacion import evaluacion, generador
    from src.simulacion.base import preparar_base

    if not argv or argv[0].isdigit():  # corrida de la tesis
        evaluacion.main(*[int(a) for a in argv])
        return
    a = _argumentos(argv)
    if a.modo == "simulado":
        hogares, p_t = generador.generar(generador.cargar_parametros(), a.hogares, a.semilla)
        origen = dict(modo="simulado", hogares=a.hogares, semilla=a.semilla)
    else:
        hogares = _leer(a.hogares, "hogares")
        p_t = (evaluacion.p_t_por_celda(_leer(a.registro, "registro")) if a.registro
               else pd.Series(generador.cargar_parametros()["p_t_celda"], dtype=float))
        origen = dict(modo="propios", hogares=str(Path(a.hogares).resolve()), registro=a.registro)
        if {"Grupo", "vinculo"} <= set(hogares.columns):
            from src.simulacion.datos_propios import estimacion_observada

            real = estimacion_observada(hogares, p_t)
            Path(a.salida).mkdir(parents=True, exist_ok=True)
            real.to_csv(Path(a.salida) / "estimacion_datos_reales.csv", index=False)
            print("\n=== Estimación con el grupo observado (datos reales, sin asterisco) ===")
            print(real.round(4).to_string(index=False))
    columnas = contrato.columnas("hogares") + [c for c in ("fex",) if c in hogares.columns]
    base = preparar_base(hogares[columnas], p_t)
    evaluacion.main(a.procesos, a.encuesta, base=base, salida=Path(a.salida), origen=origen, max_reps=a.repeticiones)


if __name__ == "__main__":
    main(sys.argv[1:])
