"""Parámetros de la evaluación semisintética: lo configurable del
framework (escenarios, vínculos, efecto verdadero, convergencia). Los
nombres de columnas no son configurables (`contrato.py`)."""
from __future__ import annotations

SEED = 2026
N_ENCUESTA = 30_000

ESCENARIOS = {
    "aleatoria": dict(celda=0.0, x=0.0, gamma=0.0, escala=1.0),
    "confusion_observada": dict(celda=1.0, x=1.0, gamma=0.0, escala=1.0),
    "efecto_nulo": dict(celda=1.0, x=1.0, gamma=0.0, escala=1.0, factor_tau=0.0),
    "confusion_no_observada_leve": dict(celda=1.0, x=1.0, gamma=0.25, escala=1.0),
    "confusion_no_observada_media": dict(celda=1.0, x=1.0, gamma=0.5, escala=1.0),
    "confusion_no_observada": dict(celda=1.0, x=1.0, gamma=1.0, escala=1.0),
    "solapamiento_debil": dict(celda=1.0, x=1.0, gamma=0.0, escala=4.0),
    # Regla del Sisbén: T por un puntaje con corte, con confusión no observada fuerte.
    "regla_corte": dict(celda=1.0, x=1.0, gamma=1.0, escala=1.0, corte=True, ruido_puntaje=0.5),
}
VINCULOS = {"oraculo": 0.0, "vinculo_parcial_50": 0.5, "hotdeck": 1.0}  # fracción con T de un donante
VINCULOS_BOSQUE = ("oraculo", "hotdeck")
OUTCOMES = ("log_ingreso", "pobre_monetario")
B_X = dict(rural=0.3, mujer=0.2, paredes_precaria=0.5)  # X en la asignación (fuera de la celda)
TAU = dict(base=0.10, rural=0.05, mujer=-0.03, paredes_precaria=0.04)  # efecto verdadero sobre log-ingreso
H_RD = 0.5  # ancho de banda de la RD, en desviaciones estándar del puntaje

# Convergencia: MCSE máximo admitido en cada celda (Morris, White y
# Crowther, 2019, Statistics in Medicine 38:2074).
UMBRAL_SESGO = {"log_ingreso": 0.003, "pobre_monetario": 0.0015}
UMBRAL_COBERTURA = 0.025
MIN_REPS, MAX_REPS, LOTE = 100, 600, 24
MIN_REPS_BOSQUE, MAX_REPS_BOSQUE = 50, 200
