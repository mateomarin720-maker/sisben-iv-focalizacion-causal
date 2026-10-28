"""Simulación Monte Carlo: ¿qué diseño puede recuperar el efecto causal de la
elegibilidad del Sisbén sobre el bienestar? (objetivo P2/OE2 del proyecto)

Mundo simulado con efecto verdadero CONOCIDO (`efecto`, sobre la privación). Se comparan estimadores:

  A. Hot-Deck + contraste dentro de la celda  -> lo que hace hoy el pipeline
     (GEIH recibe el grupo de un donante Sisbén sorteado dentro de la celda).
  A'. Hot-Deck sin controlar por la celda     -> asociación espuria por geografía.
  B. Vinculación ORACLE (se observa T real) + control por la celda (CIA)
     -> ¿bastaría con tener una llave común? (no: T está confundido por pobreza).
  C. Vinculación oracle + discontinuidad de regresión con puntaje continuo
     (frontera de elegibilidad). Requiere puntaje continuo y vínculo con Y.
  D. Vinculación oracle + "RD" con solo grupos ordinales (A-D) -> comparar
     grupos vecinos sin puntaje continuo.

Diseño del mundo: el Sisbén es un índice ruidoso de necesidad. Elegible = índice
de necesidad por encima de un corte. La necesidad depende de la celda (depto x
ciclo de vida) y de un factor NO observable en la celda (U, p. ej. calidad de
la vivienda). El resultado Y es el nivel de privación del hogar (mayor = peor):
sube con la
necesidad y cambia `efecto` unidades si el hogar es elegible (efecto < 0 = la
elegibilidad REDUCE la privación).

Uso:
    poetry run python -m src.validacion.simulacion_identificacion [reps] [n_pob]
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd

N_DEPTO, N_CICLO = 20, 3
K = N_DEPTO * N_CICLO


def _fe_slope(y: np.ndarray, t: np.ndarray, celda: np.ndarray | None) -> float:
    """Pendiente de y sobre t con efectos fijos de celda (o sin ellos)."""
    if celda is not None:
        for v in (y, t):
            m = np.bincount(celda, v, minlength=K) / np.maximum(np.bincount(celda, minlength=K), 1)
            v -= m[celda]
    else:
        y = y - y.mean(); t = t - t.mean()
    return float((t * y).sum() / (t * t).sum()) if (t * t).sum() > 0 else np.nan


def _rd(y, score, corte, h) -> float:
    """RD local lineal (kernel triangular) en `corte` con ancho de banda h."""
    d = score - corte
    m = np.abs(d) < h
    d, yy = d[m], y[m]
    t = (d >= 0).astype(float)
    w = 1 - np.abs(d) / h
    X = np.column_stack([np.ones_like(d), t, d, t * d])
    sw = np.sqrt(w)
    beta = np.linalg.lstsq(X * sw[:, None], yy * sw, rcond=None)[0]
    return float(beta[1])


def poblacion(n, sd_celda, efecto, rng):
    depto = rng.integers(0, N_DEPTO, n); ciclo = rng.integers(0, N_CICLO, n)
    celda = depto * N_CICLO + ciclo
    a = rng.normal(0, sd_celda, K)                      # nivel de necesidad por celda
    u = 0.5 * a[celda] / max(sd_celda, 1e-9) * 0.3 + rng.normal(0, 1, n)  # factor no observable en la celda
    need = a[celda] + 0.8 * u + rng.normal(0, 0.5, n)   # necesidad verdadera
    score = need + rng.normal(0, 0.4, n)                # índice Sisbén: necesidad medida con ruido
    corte = np.quantile(score, 0.5)
    T = (score >= corte).astype(int)                    # elegible (A/B)
    Y = need + efecto * T + rng.normal(0, 0.5, n)       # privación; efecto<0 = la elegibilidad la reduce
    return dict(celda=celda, need=need, score=score, T=T, Y=Y, corte=corte)


def una_corrida(n_pob, sd_celda, efecto, rng, n_geih=30_000, h_rd=0.3):
    P = poblacion(n_pob, sd_celda, efecto, rng)
    idx = rng.permutation(n_pob)
    g, s = idx[:n_geih], idx[n_geih:n_geih + n_pob // 2]      # muestras independientes GEIH / Sisbén
    cel_g, y_g = P["celda"][g], P["Y"][g].copy()

    # A. Hot-Deck: T del donante sorteado dentro de la celda
    donantes = {c: P["T"][s][P["celda"][s] == c] for c in range(K)}
    t_imp = np.array([rng.choice(donantes[c]) if len(donantes[c]) else 0 for c in cel_g], float)
    est_A = _fe_slope(y_g.copy(), t_imp.copy(), cel_g)
    est_A2 = _fe_slope(y_g.copy(), t_imp.copy(), None)

    # B. Oracle: T real observado junto con Y, control por celda
    t_real = P["T"][g].astype(float)
    est_B = _fe_slope(y_g.copy(), t_real.copy(), cel_g)

    # C. Oracle + RD con puntaje continuo (frontera de elegibilidad)
    est_C = _rd(P["Y"][g], P["score"][g], P["corte"], h_rd)

    # D. Oracle + solo grupos ordinales: comparar los dos grupos vecinos a la frontera
    q = np.quantile(P["score"], [0.25, 0.5, 0.75]); grupo = np.digitize(P["score"][g], q)  # 0..3
    y_gr = P["Y"][g]
    est_D = y_gr[grupo == 2].mean() - y_gr[grupo == 1].mean()   # grupo "B" (elegible) vs "C" (no)
    return est_A, est_A2, est_B, est_C, est_D


def main(reps: int = 30, n_pob: int = 200_000) -> pd.DataFrame:
    filas = []
    for sd_celda in (0.3, 0.8):
        for efecto in (0.0, -0.15, -0.30):
            rng = np.random.default_rng(1000 * int(sd_celda * 10) + int(-efecto * 100))
            r = np.array([una_corrida(n_pob, sd_celda, efecto, rng) for _ in range(reps)])
            for nombre, col in zip(["A Hot-Deck + celda", "A' Hot-Deck sin celda", "B Oracle + celda (CIA)",
                                    "C Oracle + RD continuo", "D Oracle + RD ordinal"], r.T):
                filas.append(dict(sd_celda=sd_celda, efecto_verdadero=efecto, estimador=nombre,
                                  media=col.mean(), sd=col.std(ddof=1), sesgo=col.mean() - efecto))
    out = pd.DataFrame(filas)
    return out


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    n_pob = int(sys.argv[2]) if len(sys.argv) > 2 else 200_000
    res = main(reps, n_pob)
    pd.set_option("display.width", 200)
    print(f"Repeticiones={reps}, población={n_pob:,}. efecto<0 = la elegibilidad REDUCE la privación.\n")
    for sd, g in res.groupby("sd_celda"):
        print(f"--- Poder de la celda sobre la necesidad: sd_celda={sd}")
        print(g.pivot(index="estimador", columns="efecto_verdadero", values="media").round(3).to_string())
        print()
