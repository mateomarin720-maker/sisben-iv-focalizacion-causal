"""Valida el estimador de src/5_estimacion.py con datos sintéticos de efecto conocido (= 0).

Uso: poetry run python -m src.validacion.simulacion_estimador_dml 30000 8

Simulación consistente con el Hot-Deck real: celda = depto | ciclo de vida (4) | cuartos agrupados (1, 2, 3+).
T se sortea según la celda e independiente de todo lo demás. Efecto verdadero = 0.
Y depende de la celda y de covariables, incluido el conteo EXACTO de cuartos (como el hacinamiento)."""
import sys, time, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from econml.dml import LinearDML
X_COLS = ["zona", "mujer", "pared", "piso"]

def simular(n, seed):
    r = np.random.default_rng(seed); nd = 33
    depto = r.integers(0, nd, n); code = r.permutation(nd)[depto]
    edad_anios = r.integers(18, 90, n)
    ciclo = np.digitize(edad_anios, [29, 60])  # 0: 18-28, 1: 29-59, 2: 60+
    cuartos = np.clip(r.poisson(2.8, n), 1, 8); ctr = np.minimum(cuartos, 3)
    celda = pd.Series(depto.astype(str) + "|" + ciclo.astype(str) + "|" + ctr.astype(str))
    cod, uniq = pd.factorize(celda)
    pc = 1/(1+np.exp(-(0.9 + r.normal(0, 1.1, nd)[depto] + 0.3*ciclo - 0.3*ctr + r.normal(0, .6, len(uniq))[cod])))
    T = (r.random(n) < pc).astype(int)
    zona = (r.random(n) < 0.5 + 0.3*np.sin(depto)).astype(int); mujer = (r.random(n) < .35).astype(int)
    pared = r.integers(1, 7, n); piso = r.integers(1, 7, n)
    y = np.clip(1.5 + r.normal(0, .5, nd)[depto] + 0.3*ciclo - 0.15*cuartos - 0.4*zona + 0.3*mujer
                + 0.05*pared + 0.03*piso + r.normal(0, .9, n), 0, 4)
    return pd.DataFrame(dict(T=T, depto_code=code, edad=edad_anios, cuartos=cuartos, celda=celda,
                             zona=zona, mujer=mujer, pared=pared, piso=piso, y=y))

def fit(d, W, model_y, C=5.0):
    X = d[X_COLS].to_numpy(float)
    m = LinearDML(model_y=model_y, model_t=LogisticRegression(max_iter=3000, C=C), discrete_treatment=True, random_state=0)
    m.fit(d["y"].to_numpy(float), d["T"].to_numpy(int), X=X, W=W)
    return float(m.ate(X)), [float(v) for v in m.ate_interval(X, alpha=.05)]

def gbm(): return GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)

VARIANTES = {
 "1 original: depto como código + edad en años + cuartos exactos, logit lineal":
    lambda d: fit(d, d[["depto_code", "edad", "cuartos"]].to_numpy(float), gbm(), C=1.0),
 "2 celda del Hot-Deck (one-hot de `_hotdeck_celda`), logit + GBM":
    lambda d: fit(d, pd.get_dummies(d["celda"], dtype=float).to_numpy(), gbm()),
 "3 celda one-hot + HistGB para Y (más rápido)":
    lambda d: fit(d, pd.get_dummies(d["celda"], dtype=float).to_numpy(), HistGradientBoostingRegressor(max_iter=150, random_state=0)),
}
if __name__ == "__main__":
    n, reps = int(sys.argv[1]), int(sys.argv[2]); filas = []; t0 = time.time()
    for s in range(reps):
        d = simular(n, s)
        for k, f in VARIANTES.items():
            e, (lo, hi) = f(d); filas.append((k, e, lo, hi))
    r = pd.DataFrame(filas, columns=["modelo", "ate", "lo", "hi"]); r["cubre0"] = (r.lo <= 0) & (r.hi >= 0)
    print(f"n={n:,}, {reps} repeticiones, efecto verdadero = 0, tiempo {time.time()-t0:.0f}s\n")
    print(r.groupby("modelo").agg(ate_medio=("ate", "mean"), sesgo_abs=("ate", lambda v: v.abs().mean()),
          rango=("ate", lambda v: f"{v.min():+.3f}..{v.max():+.3f}"), cobertura_ic95=("cubre0", "mean")).round(4).to_string())
