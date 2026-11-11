"""Estimación de efectos causales (P2/OE2).

Corre sobre `data/2_models/muestra_estimacion_monetaria_2024.parquet`
(superconjunto de `muestra_estimacion_2024.parquet` — mismas filas y
columnas de siempre, más `ingreso_percapita`/`POBRE_MONETARIO` de
`3b_preprocesamiento_monetario.py`), con CUATRO outcomes:
  - `ipm_geih_score`/`POBRE_GEIH`: IPM-GEIH, 8 privaciones verificadas
    contra el diccionario oficial de GEIH desde 2026-10-28 — empezó en
    10, pero `material_pisos_inadecuado`/`material_paredes_inadecuado`
    se retiraron el mismo día por ser los MISMOS códigos que
    `viv_pisos`/`viv_paredes` de `X` abajo, ver docstring de
    `3_preprocesamiento.py`.
  - `log_ingreso_percapita`/`POBRE_MONETARIO`: pobreza monetaria
    (2026-11-02, nuevo outcome principal según el giro del tutor del
    2026-10-27) — ver docstring de `3b_preprocesamiento_monetario.py`.
    `log_ingreso_percapita = log1p(ingreso_percapita)`: el ingreso crudo
    tiene cola derecha extrema que dominaría el ajuste por error
    cuadrático; log-ingreso es la transformación estándar para esta
    variable.
  - `POBRE_MONETARIO_OFICIAL` (robustez, 2026-11-02): la clasificación
    oficial del DANE (catálogo 874) en vez de la reconstruida. Solo
    existe para 24 departamentos y Bogotá; los 9 que la base no trae
    (Orinoquía, Amazonía, San Andrés) salen de esta corrida. La
    reconstrucción sigue siendo el outcome principal porque cubre todo el
    país.

El tratamiento es el mismo en los cuatro: Hot-Deck con vivienda sumada a
la celda (`geo_depto + jefe_edad + viv_cuartos`, corregido 2026-10-28 —
antes tomaba el código equivocado,
`docs/seguimiento/CHANGELOG_PENDIENTES.md`).

Los cuatro efectos que pide el documento de pipeline (Roncancio y Fonseca,
2026, Figura 1):
  - **ATE** (efecto promedio global) — `LinearDML` sobre toda la muestra.
  - **ATT** (efecto promedio sobre los hogares tratados, `T=1`) — el
    MISMO `LinearDML`, evaluado solo sobre esa subpoblación.
  - **ATU** (efecto promedio sobre los hogares no tratados, `T=0`) — el
    mismo modelo, evaluado solo sobre esa subpoblación.
  - **CATE** (efecto por tipo de hogar) — `CausalForestDML`.

⚠️ **Rotulado corregido 2026-11-02:** ATT/ATU se venían describiendo en
este repositorio como "error de inclusión"/"error de exclusión" — son
conceptos distintos. ATT/ATU son el efecto promedio del tratamiento en
una subpoblación (tratados o no tratados); error de inclusión/exclusión
es un concepto de focalización (clasificar como pobre/no pobre a quien no
lo es) que no se calcula en este script. No había cómputo erróneo, solo
una etiqueta engañosa — corregida aquí y en
`docs/resultados/2_diagnostico_datos_reales/RESULTADOS_DML_ATE_ATT_ATU.md`.

  (Se descartó `LinearDRLearner` para ATT/ATU — daba valores absurdos por
  inestabilidad del estimador doblemente robusto; ver docstring de
  `_ate_att_atu`.)

Cada modelo corre con DOS especificaciones de `W`, para diagnosticar una
discrepancia detectada el 2026-11-02 (ver
`docs/resultados/2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md`):
  - **`W_PROXY`** = `{geo_depto, nivel de pisos, jefe_edad,
    viv_cuartos}`: `jefe_edad`/`viv_cuartos` CONTINUOS como proxy de los
    tramos discretos que el Hot-Deck usa de verdad para el sorteo
    (`geo_depto + ciclo de vida + tramo de cuartos + nivel de pisos`) —
    no es una réplica exacta de la celda.
  - **`W_CELDA`** = `hotdeck_celda_cat`, el código categórico de
    `_hotdeck_celda` (columna que ya guarda `emparejamiento_hotdeck_
    geih_sisben.py` con la celda EXACTA usada en cada sorteo; desde el
    2026-11-02 incluye el nivel de pisos). Esta es la réplica fiel del
    mecanismo real: si el sorteo es verdaderamente aleatorio dentro de
    esa celda (confirmado — `rng.integers` sin ponderar por nada más),
    el tratamiento imputado debería ser independiente de TODO lo demás
    condicional en esta celda, por construcción del propio algoritmo
    (no por supuesto).

`X = {geo_zona, jefe_sexo, viv_paredes}` son las covariables NO usadas
en la celda, para heterogeneidad (CATE) y como chequeo de que no quede
señal espuria. `viv_pisos` salió de `X` el 2026-11-02 al entrar a la
celda.

Modelos auxiliares (corregido 2026-11-02, ver `_codificador`): las
categóricas sin orden (celda, departamento, material de paredes y pisos)
entran como variables indicadoras; `model_t` es una logística sobre ellas
y `model_y` una regresión con efectos fijos más splines de las continuas.
Antes entraban como su código numérico y la "celda exacta" no controlaba
la celda.

⚠️ Cómo leer los resultados: son un **diagnóstico de sensibilidad**, no
efectos causales. El tratamiento se sortea al azar dentro de la celda,
así que dentro de la celda T no depende de nada del hogar receptor; la
simulación (`docs/resultados/3_simulacion/SIMULACION_IDENTIFICACION.md`) muestra que
este contraste da ≈0 sea cual sea el efecto verdadero.

⚠️ Limitaciones — las mismas de siempre, sin excepción:
  - El tratamiento es imputado por Hot-Deck, no observado.
  - `ipm_geih_score`/`POBRE_GEIH` son un proxy reducido (8 de 15
    privaciones), NO el IPM oficial — ver docstring de
    `3_preprocesamiento.py` para qué se incluyó y qué no.
  - `log_ingreso_percapita`/`POBRE_MONETARIO` son una reconstrucción con
    microdatos públicos (33,2 % de personas pobres frente a 31,8 %
    oficial): sin el cruce del DANE con registros administrativos.
  - Sin ajuste por diseño muestral de GEIH ni de Sisbén.
  - El Sisbén solo cubre hogares inscritos (selección).
  - Falta DPS/RUI como confusores (canal de la Figura 2 sin datos todavía).

Uso (requiere correr primero 3_preprocesamiento.py y
3b_preprocesamiento_monetario.py, en ese orden):
    poetry run python src/3_preprocesamiento.py
    poetry run python src/3b_preprocesamiento_monetario.py
    poetry run python src/5_estimacion.py
Salida: docs/reports/estimacion_ate_att_atu_cate.txt (vía redirección de
consola) y resumen interpretado en docs/resultados/.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer

from econml.dml import LinearDML, CausalForestDML

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
SEED = 42
N_SUB_CATE = 80_000

# Cada W: (categóricas sin orden, continuas). Las categóricas entran a los
# modelos auxiliares como variables indicadoras, nunca como su código.
W_PROXY = (["geo_depto_cat", "pisos_nivel_cat"], ["jefe_edad", "viv_cuartos"])  # proxy de la celda
W_CELDA = (["hotdeck_celda_cat"], [])  # celda EXACTA del Hot-Deck (igual al sorteo real)
X_COLS = ["geo_zona_urbana", "jefe_mujer", "viv_paredes"]  # NO usadas en la celda
X_CATEGORICAS = ["viv_paredes"]  # código de material: indicadoras en los modelos auxiliares
# Regularización de los modelos auxiliares: Ridge alpha = 1 y logística
# C = 10. Encoge un poco los efectos de las ~1.000 indicadoras de celda y
# deja un sesgo pequeño en LinearDML (−0,006 con efecto nulo en la
# simulación); casi sin regularizar cae a la mitad o menos
# (`SIMULACION_SEMISINTETICA.md`, sensibilidad 3). Se conserva la vigente
# porque las cifras publicadas salen de ella; la otra es la sensibilidad.
ALPHA_Y, C_T = 1.0, 10.0
CASI_SIN_REGULARIZAR = dict(alpha=1e-6, c=1e6, max_iter=5000)


def _preparar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["T"] = df["Grupo_hotdeck"].isin(["A", "B"]).astype(int)
    df["jefe_edad"] = pd.to_numeric(df["jefe_edad"], errors="coerce")
    for c in ["viv_paredes", "viv_pisos", "viv_cuartos"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["geo_zona_urbana"] = (df["geo_zona"] == "1").astype(int)
    df["jefe_mujer"] = (df["jefe_sexo"] == "2").astype(int)
    df["geo_depto_cat"] = df["geo_depto"].astype("category").cat.codes
    df["pisos_nivel_cat"] = df["viv_pisos_nivel"].astype("category").cat.codes
    df["hotdeck_celda_cat"] = df["_hotdeck_celda"].astype("category").cat.codes
    df["log_ingreso_percapita"] = np.log1p(pd.to_numeric(df["ingreso_percapita"], errors="coerce"))
    return df


def _codificador(columnas: list[str], categoricas: list[str], continuas: list[str]) -> ColumnTransformer:
    """Indicadoras para las categóricas sin orden y splines para las
    continuas, sobre la matriz que econml pasa a los modelos auxiliares
    (`[X, W]`, en ese orden).

    Hasta el 2026-11-02 el código de celda (0..375) y el de departamento
    (0..32) entraban a una LogisticRegression como si fueran números: la
    propensión con la celda exacta salía ≈0,64 para todos los hogares,
    cuando P(T | celda) va de 0,36 a 0,87 (p5-p95). Ver CLAUDE.md."""
    idx = {c: i for i, c in enumerate(columnas)}
    partes = [("cat", OneHotEncoder(handle_unknown="ignore"), [idx[c] for c in categoricas])]
    if continuas:
        partes.append(("num", SplineTransformer(n_knots=5, degree=3), [idx[c] for c in continuas]))
    resto = [i for c, i in idx.items() if c not in categoricas and c not in continuas]
    if resto:
        partes.append(("resto", "passthrough", resto))
    return ColumnTransformer(partes, sparse_threshold=1.0)


def _modelos_auxiliares(w_spec: tuple[list[str], list[str]], con_x: bool = True, alpha: float | None = None,
                        c: float | None = None, max_iter: int = 2000):
    """model_y: regresión con efectos fijos (celda o departamento) + splines;
    model_t: logística sobre las mismas indicadoras. Con indicadoras de la
    celda, la propensión es P(T | celda), que es lo que fija el sorteo.
    `alpha` y `c`: regularización (por defecto la vigente; la de la
    sensibilidad está en `CASI_SIN_REGULARIZAR`)."""
    alpha = ALPHA_Y if alpha is None else alpha
    c = C_T if c is None else c
    w_cat, w_num = w_spec
    columnas = (X_COLS if con_x else []) + w_cat + w_num
    categoricas = (X_CATEGORICAS if con_x else []) + w_cat
    modelo_y = make_pipeline(_codificador(columnas, categoricas, w_num), Ridge(alpha=alpha))
    modelo_t = make_pipeline(_codificador(columnas, categoricas, w_num),
                             LogisticRegression(C=c, max_iter=max_iter))
    return modelo_y, modelo_t


def _ate_att_atu(df: pd.DataFrame, y_col: str, w_spec: tuple[list[str], list[str]]) -> None:
    """ATE, ATT y ATU con el MISMO LinearDML ya ajustado — se evalúa
    `effect()`/`ate()` sobre tres poblaciones distintas (todos, T=1, T=0).

    Se descartó `LinearDRLearner` para ATT/ATU: con las mismas covariables
    daba valores absurdos (cientos de unidades en un outcome acotado entre
    0 y 4) por inestabilidad del estimador doblemente robusto cuando hay
    poca superposición de propensión en algunas celdas — un caso real de
    "no confiar en el número solo porque el modelo corrió sin error".
    Reusar el LinearDML (ya estable para el ATE completo) evaluado en cada
    subpoblación evita ese problema y es una forma válida de reportar
    ATT/ATU bajo el mismo marco DML.
    """
    w_cols = w_spec[0] + w_spec[1]
    d = df.dropna(subset=[y_col, "T", *w_cols, *X_COLS])
    W = d[w_cols].to_numpy(dtype=float)
    X = d[X_COLS].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)

    _, modelo_t = _modelos_auxiliares(w_spec, con_x=False)
    prop = modelo_t.fit(W, T).predict_proba(W)[:, 1]
    print(f"  Propensión (T=1 | W): min={prop.min():.3f} p5={np.percentile(prop,5):.3f} "
          f"p50={np.percentile(prop,50):.3f} p95={np.percentile(prop,95):.3f} max={prop.max():.3f}")
    empirica = d.groupby(w_cols)["T"].transform("mean").to_numpy() if not w_spec[1] else None
    if empirica is not None:
        print(f"  vs. P(T | W) empírica: corr={np.corrcoef(prop, empirica)[0, 1]:.3f} "
              f"| dif. absoluta media={np.abs(prop - empirica).mean():.4f}")

    modelo_y, modelo_t = _modelos_auxiliares(w_spec)
    est = LinearDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, random_state=SEED)
    est.fit(Y, T, X=X, W=W)

    for nombre, mask in [("ATE (toda la muestra)", np.ones(len(d), dtype=bool)),
                          ("ATT (efecto en tratados)", T == 1),
                          ("ATU (efecto en no tratados)", T == 0)]:
        efecto, (lo, hi) = est.ate(X[mask]), est.ate_interval(X[mask], alpha=0.05)
        print(f"  {nombre}: n={mask.sum():,} | {efecto:+.4f}  IC95%=({lo:+.4f}, {hi:+.4f})")


def _cate(df: pd.DataFrame, y_col: str, w_spec: tuple[list[str], list[str]]) -> None:
    w_cols = w_spec[0] + w_spec[1]
    d = df.dropna(subset=[y_col, "T", *w_cols, *X_COLS])
    if len(d) > N_SUB_CATE:
        d = d.sample(N_SUB_CATE, random_state=SEED)
    X = d[X_COLS].to_numpy(dtype=float)
    W = d[w_cols].to_numpy(dtype=float)
    Y = d[y_col].to_numpy(dtype=float)
    T = d["T"].to_numpy(dtype=int)
    modelo_y, modelo_t = _modelos_auxiliares(w_spec)
    est = CausalForestDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, n_estimators=400, min_samples_leaf=50, random_state=SEED)
    est.fit(Y, T, X=X, W=W)
    cate = est.effect(X)
    print(f"  CATE: n={len(d):,} | media={cate.mean():+.4f}  sd={cate.std():.4f}  "
          f"rango=({cate.min():+.4f}, {cate.max():+.4f})")
    d = d.assign(_cate=cate)
    print("  Por zona (urbana=1):", d.groupby("geo_zona_urbana")["_cate"].mean().round(4).to_dict())
    print("  Por sexo jefe (mujer=1):", d.groupby("jefe_mujer")["_cate"].mean().round(4).to_dict())
    imp = pd.Series(est.feature_importances_, index=X_COLS).sort_values(ascending=False)
    print("  Importancia de variables:", imp.round(3).to_dict())


def main() -> None:
    logger.info("Cargando %s", DATA)
    if not DATA.exists():
        raise SystemExit(f"Falta {DATA}: corra src/3_preprocesamiento.py primero")
    df = _preparar(pd.read_parquet(DATA))
    logger.info("n=%s | T=1 (Grupo A/B): %.1f%%", f"{len(df):,}", df["T"].mean() * 100)

    especificaciones = [
        ("PROXY (indicadoras de geo_depto y nivel de pisos + splines de jefe_edad y viv_cuartos)", W_PROXY),
        ("CELDA EXACTA (indicadoras de _hotdeck_celda, igual al sorteo real)", W_CELDA),
    ]

    for y_col, etiqueta in [("ipm_geih_score", "ipm_geih_score (continuo, 0-8 privaciones)"),
                             ("POBRE_GEIH", "POBRE_GEIH (binario, score >= K_POBRE adoptado en 3_preprocesamiento.py)"),
                             ("log_ingreso_percapita", "log_ingreso_percapita (continuo, log1p(ingreso_percapita))"),
                             ("POBRE_MONETARIO", "POBRE_MONETARIO (binario, reconstrucción GEIH con líneas DANE 2024 por dominio)"),
                             ("POBRE_MONETARIO_OFICIAL", "POBRE_MONETARIO_OFICIAL (robustez: clasificación oficial DANE, "
                                                         "24 departamentos y Bogotá; sin los 9 que la base no trae)")]:
        print("\n" + "#" * 70)
        print(f"# Outcome: {etiqueta}")
        print("#" * 70)
        for w_label, w_spec in especificaciones:
            print("\n" + "=" * 70)
            print(f"W = {w_label}")
            print("=" * 70)
            _ate_att_atu(df, y_col, w_spec)
            _cate(df, y_col, w_spec)

    print("\n" + "=" * 70)
    print("Cómo leer esto: el grupo imputado se sortea al azar dentro de la celda,")
    print("así que con la celda controlada el efecto esperado es ≈0 (placebo del")
    print("emparejamiento, no efecto del Sisbén) — ver")
    print("docs/resultados/2_diagnostico_datos_reales/DIAGNOSTICO_W_CELDA_EXACTA.md.")
    print("=" * 70)


if __name__ == "__main__":
    main()
