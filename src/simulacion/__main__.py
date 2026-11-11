"""Evaluación semisintética con los hogares de la GEIH 2024 y el Sisbén
del banco de datos (`data/2_models/`), hasta la convergencia.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion [n_jobs]
Salidas:
    docs/reports/simulacion_semisintetica.csv (cada repetición)
    docs/reports/simulacion_semisintetica_resumen.csv (con MCSE)
    docs/reports/simulacion_semisintetica_convergencia.csv (traza por lote)
    docs/reports/simulacion_semisintetica_tablas.md (tablas del documento)
    docs/resultados/3_simulacion/simulacion_semisintetica_convergencia.png
"""
import logging
import sys

from src.simulacion.evaluacion import main

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
main(*[int(a) for a in sys.argv[1:]])
