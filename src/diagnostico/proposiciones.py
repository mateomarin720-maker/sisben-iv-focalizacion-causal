"""Comprobación numérica de las proposiciones del enlace por celdas.

Las pruebas están en `docs/anexos_tesis/PROPOSICIONES.md`; este módulo las
comprueba por Monte Carlo con una población sintética (no usa microdatos) y
verifica la descomposición del ancho de la cota con el archivo publicado de
cotas por celda.

  Proposición 1. Con T imputado por celdas, el contraste con efectos fijos
                 de celda tiene esperanza cero, sea cual sea el efecto real.
  Proposición 2. Con una fracción L de hogares enlazados al azar y el resto
                 imputado en su celda, el contraste tiende a L × efecto.
                 Con enlaces falsos (pareja al azar de toda la población) la
                 atenuación sigue la fórmula de `atenuacion_enlace_falso`.
  Proposición 3. Con imputación total, la varianza entre sorteos iguala la
                 varianza dentro de cada sorteo: la fracción de información
                 perdida de Rubin es (1 + 1/M) / (2 + 1/M) ≈ 0,5.
  Cota del ATE.  Sin supuestos y con fuentes no enlazadas, el ancho de la
                 cota en cada celda es 1 + 2Δ, con Δ el ancho del intervalo
                 de Fréchet de P(Y=1, T=1).

Uso: python -m src.diagnostico.proposiciones
Salida: docs/reports/proposiciones.txt
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.diagnostico.cotas_frechet_manski import cotas_con_supuestos
from src.diagnostico.variabilidad_hotdeck import contraste_placebo, reglas_de_rubin

R = Path(__file__).resolve().parents[2]
REPORTE = R / "docs" / "reports" / "proposiciones.txt"
COTAS_POR_CELDA = R / "docs" / "reports" / "cotas_frechet_manski_pobre_monetario.csv"
EFECTO = 0.10


@dataclass
class Poblacion:
    celda: np.ndarray      # código de celda de cada hogar (0..K-1)
    p: np.ndarray          # P(T=1 | celda), por celda
    t: np.ndarray          # tratamiento verdadero
    y: np.ndarray          # resultado
    donante_t: np.ndarray  # tratamientos de la fuente donante
    donante_celda: np.ndarray


def poblacion(n: int = 20_000, celdas: int = 150, efecto: float = EFECTO, confusion: float = 0.0,
              semilla: int = 0) -> Poblacion:
    """Receptor y donante con la misma P(T | celda). Entre celdas, las de
    mayor P(T) son más pobres (la focalización funciona entre celdas).
    `confusion` > 0 hace que, dentro de la celda, T dependa del ruido de Y:
    el contraste con T verdadero queda sesgado, el imputado no."""
    rng = np.random.default_rng(semilla)
    p = rng.beta(2, 2, celdas)
    celda = rng.integers(0, celdas, n)
    u = rng.normal(size=n)
    t = (rng.random(n) < np.clip(p[celda] + confusion * u, 0.01, 0.99)).astype(float)
    y = 1.5 * p[celda] + efecto * t + u
    donante_celda = rng.integers(0, celdas, 4 * n)
    donante_t = (rng.random(4 * n) < p[donante_celda]).astype(float)
    return Poblacion(celda, p, t, y, donante_t, donante_celda)


def hot_deck(pob: Poblacion, rng: np.random.Generator) -> np.ndarray:
    """T de un donante al azar de la misma celda."""
    orden = np.argsort(pob.donante_celda, kind="stable")
    inicio = np.searchsorted(pob.donante_celda[orden], np.arange(len(pob.p)))
    fin = np.searchsorted(pob.donante_celda[orden], np.arange(len(pob.p)), side="right")
    a, b = inicio[pob.celda], fin[pob.celda]
    return pob.donante_t[orden[a + (rng.random(len(a)) * (b - a)).astype(int)]]


def observado(pob: Poblacion, enlazados: float, rng: np.random.Generator, falso: bool = False) -> np.ndarray:
    """T que ve el analista: el verdadero en una fracción `enlazados` al azar;
    en el resto, imputado en la celda (Hot-Deck) o, con `falso`, el T de un
    hogar cualquiera de la población (enlace equivocado)."""
    otro = pob.t[rng.integers(0, len(pob.t), len(pob.t))] if falso else hot_deck(pob, rng)
    return np.where(rng.random(len(pob.t)) < enlazados, pob.t, otro)


def atenuacion_enlace_falso(pob: Poblacion, enlazados: float) -> float:
    """Factor esperado con enlaces falsos. En la celda c, T observado es
    Bernoulli(m_c) con m_c = L·p_c + (1−L)·p̄; su covarianza con Y es la de
    los enlazados, L·p_c(1−p_c)·efecto. El contraste con efectos fijos tiende a
    Σ n_c·L·p_c(1−p_c) / Σ n_c·m_c(1−m_c). Con imputación en la celda,
    m_c = p_c y el factor es exactamente L."""
    n = np.bincount(pob.celda, minlength=len(pob.p))
    m = enlazados * pob.p + (1 - enlazados) * pob.t.mean()
    return float((n * enlazados * pob.p * (1 - pob.p)).sum() / (n * m * (1 - m)).sum())


def proposicion_1(reps: int = 200, semilla: int = 1) -> pd.DataFrame:
    filas = []
    for confusion in (0.0, 0.15):
        pob = poblacion(confusion=confusion, semilla=semilla)
        rng = np.random.default_rng(semilla)
        verdadero = contraste_placebo(pob.y, pob.t, pob.celda)[0]
        imputados = np.array([contraste_placebo(pob.y, hot_deck(pob, rng), pob.celda)[0] for _ in range(reps)])
        filas.append(dict(confusion=confusion, efecto=EFECTO, contraste_t_verdadero=verdadero,
                          media_imputado=imputados.mean(), error_mc=imputados.std(ddof=1) / np.sqrt(reps)))
    return pd.DataFrame(filas)


def proposicion_2(reps: int = 100, semilla: int = 2) -> pd.DataFrame:
    """Una población nueva por réplica: el factor se mide contra el efecto
    verdadero, no contra la estimación de una sola muestra."""
    filas = []
    for falso in (False, True):
        for enlazados in (0.0, 0.25, 0.5, 0.75, 1.0):
            est, esperado = [], []
            for r in range(reps):
                pob = poblacion(semilla=semilla * 1000 + r)
                rng = np.random.default_rng(semilla * 1000 + r)
                est.append(contraste_placebo(pob.y, observado(pob, enlazados, rng, falso), pob.celda)[0])
                esperado.append(atenuacion_enlace_falso(pob, enlazados) if falso else enlazados)
            est = np.array(est)
            filas.append(dict(resto=("enlace falso" if falso else "imputado en la celda"), enlazados=enlazados,
                              factor_simulado=est.mean() / EFECTO, factor_esperado=float(np.mean(esperado)),
                              error_mc=est.std(ddof=1) / np.sqrt(reps) / EFECTO))
    return pd.DataFrame(filas)


def proposicion_3(sorteos: int = 100, poblaciones: int = 20, semilla: int = 3) -> pd.DataFrame:
    """Fracción de Rubin en varias poblaciones: con M sorteos, la varianza
    entre sorteos se estima con error relativo ≈ √(2/(M−1)), así que la
    fracción de una sola corrida varía unos ±3 puntos alrededor de 0,5."""
    filas = []
    for efecto in (0.0, EFECTO):
        razon, fraccion = [], []
        for r in range(poblaciones):
            pob = poblacion(efecto=efecto, semilla=semilla * 1000 + r)
            rng = np.random.default_rng(semilla * 1000 + r)
            res = [contraste_placebo(pob.y, hot_deck(pob, rng), pob.celda) for _ in range(sorteos)]
            rubin = reglas_de_rubin(np.array([x[0] for x in res]), np.array([x[1] for x in res]))
            razon.append(rubin["var_entre"] / rubin["var_dentro"])
            fraccion.append(rubin["fraccion_info_imputacion"])
        filas.append(dict(efecto=efecto, m=sorteos, poblaciones=poblaciones,
                          razon_entre_dentro=float(np.mean(razon)), fraccion_media=float(np.mean(fraccion)),
                          fraccion_min=float(np.min(fraccion)), fraccion_max=float(np.max(fraccion)),
                          fraccion_teorica=(1 + 1 / sorteos) / (2 + 1 / sorteos)))
    return pd.DataFrame(filas)


def ancho_cota(p_y, p_t) -> pd.DataFrame:
    """Ancho de la cota del ATE sin supuestos frente a 1 + 2Δ, celda por celda."""
    p_y, p_t = np.asarray(p_y, float), np.asarray(p_t, float)
    sup = cotas_con_supuestos(p_y, p_t)
    delta = np.minimum(p_y, p_t) - np.maximum(0, p_y + p_t - 1)
    return pd.DataFrame(dict(ancho=sup["ate_sin_supuestos_hi"] - sup["ate_sin_supuestos_lo"], delta=delta,
                             uno_mas_dos_delta=1 + 2 * delta))


def ancho_cota_publicada() -> dict | None:
    """Descompone el ancho nacional publicado (pobreza monetaria) con las
    marginales por celda del reporte versionado."""
    if not COTAS_POR_CELDA.exists():
        return None
    df = pd.read_csv(COTAS_POR_CELDA)
    w = df["peso_fex"] / df["peso_fex"].sum()
    a = ancho_cota(df["p_y"], df["p_t"])
    return dict(celdas=len(df), delta_medio=float((w * a["delta"]).sum()), ancho=float((w * a["ancho"]).sum()))


def main() -> None:
    pd.set_option("display.width", 200)
    partes = ["=== Comprobación numérica de las proposiciones (población sintética) ===",
              f"Efecto verdadero: {EFECTO}. Ver docs/anexos_tesis/PROPOSICIONES.md\n",
              "Proposición 1. Contraste con efectos fijos de celda: T verdadero frente a T imputado (media de 200 sorteos)",
              proposicion_1().round(4).to_string(index=False),
              "\nProposición 2. Factor de atenuación (contraste / efecto) según la fracción enlazada (100 réplicas)",
              proposicion_2().round(3).to_string(index=False),
              "\nProposición 3. Rubin con imputación total (100 sorteos en cada una de 20 poblaciones)",
              proposicion_3().round(4).to_string(index=False)]
    pub = ancho_cota_publicada()
    if pub:
        partes += ["\nCota del ATE sin supuestos, pobreza monetaria (cotas_frechet_manski_pobre_monetario.csv)",
                   f"celdas {pub['celdas']} | Δ medio ponderado {pub['delta_medio']:.4f} | "
                   f"1 + 2Δ = {1 + 2 * pub['delta_medio']:.4f} | ancho publicado {pub['ancho']:.4f}"]
    texto = "\n".join(partes)
    print(texto)
    REPORTE.write_text(texto + "\n", encoding="utf-8")
    print(f"\nGuardado: {REPORTE}")


if __name__ == "__main__":
    main()
