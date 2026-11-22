"""Selección de variables sobre el Sisbén con LASSO, Ridge y SHAP (OE1).

Objetivo específico 1: "determinar grupos y subgrupos de variables para
LASSO, Ridge y SHAP" (Tabla 3 del documento de avance, Roncancio y
Fonseca, 2026). Es un ejercicio de selección/importancia de variables,
NO de inferencia causal — no estima un efecto del Sisbén, solo qué
variables del hogar predicen mejor el `Grupo` (A-D) que asigna el
Sisbén.

## Outcome y por qué NO hay circularidad

`Grupo` (A/B/C/D) es la variable a predecir. El Sisbén lo calcula
internamente a partir de `I1`-`I15`/`H_5` (privaciones ya agregadas) —
CLAUDE.md prohíbe usar esas columnas como outcome en la parte causal por
circularidad, y aquí se extiende la misma regla: tampoco se usan como
PREDICTORES, porque equivaldría a redescubrir la fórmula propia del
Sisbén, no a aportar información nueva. Los predictores que sí se usan
son características del hogar INDEPENDIENTES del cálculo interno del
índice: vivienda, demografía del jefe y geografía — el mismo esquema
canónico ya armonizado en `sisben_estandarizado_2024_con_bogota.parquet`
(usado también para el Hot-Deck).

## Variables y por qué van numéricas u one-hot

- **Cardinales/ordinales con orden establecido** (van numéricas tal
  cual): `hog_num_personas` y `hog_num_menores` (conteos; menores desde el
  2026-11-22, como en la celda del Hot-Deck), `viv_cuartos` (conteo), `jefe_edad`
  (código de ciclo de vida 3-6, orden corroborado indirectamente — ver
  `docs/insumos/DICCIONARIO_HOTDECK.md` §5).
- **Categóricas SIN dirección/orden verificado** (van one-hot, nunca
  numéricas — mismo criterio que evitó el bug de `LinearDRLearner` con
  `geo_depto_cat`, ver CLAUDE.md): `viv_paredes`, `viv_pisos` (categorías
  Sisbén no homologadas contra GEIH, dirección no confirmada),
  `viv_alcantarillado`, `viv_acueducto`, `jefe_sexo`, `geo_zona`.
- **Control geográfico, no foco del análisis**: `geo_depto` (33
  categorías, one-hot) — se incluye para no atribuirle a vivienda o
  demografía variación que en realidad es solo geografía, pero se reporta
  aparte, no en el ranking principal (mismo criterio que `W` en
  `5_estimacion.py`).

## Los tres métodos

- **LASSO** (`LogisticRegressionCV`, `l1_ratios=[1.0]`, multinomial):
  regresión logística regularizada en L1 — lleva coeficientes exactamente
  a 0, así que ADEMÁS de rankear importancia, dice qué variables quedan
  completamente eliminadas del modelo.
- **Ridge** (`LogisticRegressionCV`, `l1_ratios=[0.0]`, multinomial): la
  misma regresión con regularización L2 — no elimina variables, pero
  permite comparar el ranking de magnitud de coeficientes contra LASSO
  (¿coinciden en qué es importante, o el L1 está siendo agresivo con
  alguna variable correlacionada?).
- **SHAP** sobre `RandomForestClassifier`: importancia no lineal/no
  paramétrica, para contrastar contra los dos modelos lineales — si
  SHAP concuerda con LASSO/Ridge, la señal es robusta a la forma
  funcional; si no, hay no linealidad o interacción que los modelos
  lineales no capturan.

Uso:
    poetry run python -m src.diagnostico.seleccion_variables_lasso_shap
Salida: docs/reports/seleccion_variables_lasso_ridge_shap.csv + resumen
impreso en consola.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import shap
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegressionCV
from sklearn.metrics import accuracy_score, brier_score_loss, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import PISOS_NIVEL, peso_donante

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SISBEN_PATH = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
REPORT = Path("docs/reports/seleccion_variables_lasso_ridge_shap.csv")
REPORT_CLASES = Path("docs/reports/seleccion_variables_metricas_por_clase.csv")
REPORT_SHAP = Path("docs/reports/seleccion_variables_shap_ab.csv")
SEED = 42
N_MUESTRA = 150_000  # submuestra ponderada por fex, por costo de LogisticRegressionCV/SHAP
N_SHAP_FIGURA = 4_000  # hogares cuyo valor SHAP se guarda para la figura

NUMERICAS = ["hog_num_personas", "hog_num_menores", "viv_cuartos", "jefe_edad"]
CATEGORICAS = ["viv_paredes", "viv_pisos", "viv_alcantarillado", "viv_acueducto", "jefe_sexo", "geo_zona"]
CONTROL = ["geo_depto"]
TODAS = NUMERICAS + CATEGORICAS + CONTROL


def _preparar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[str, str]]:
    """Arma X (numéricas + dummies one-hot) y el mapa columna_dummy -> variable original."""
    d = df.dropna(subset=[*TODAS, "Grupo"]).copy()
    for c in NUMERICAS:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=NUMERICAS)

    partes = [d[NUMERICAS]]
    mapa: dict[str, str] = {c: c for c in NUMERICAS}
    for c in CATEGORICAS + CONTROL:
        dummies = pd.get_dummies(d[c].astype(str), prefix=c, dtype=float)
        partes.append(dummies)
        for col in dummies.columns:
            mapa[col] = c

    X = pd.concat(partes, axis=1)
    y = d["Grupo"].astype(str)
    return X, y, mapa


def _importancia_por_variable(pesos: np.ndarray, columnas: list[str], mapa: dict[str, str]) -> pd.Series:
    """Suma |peso| por variable original, agregando sus columnas dummy."""
    s = pd.Series(np.abs(pesos), index=columnas)
    return s.groupby([mapa[c] for c in columnas]).sum().sort_values(ascending=False)


def muestra_ponderada(peso: np.ndarray, n: int, seed: int, prueba: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """Posiciones de entrenamiento y prueba que representan a la población:
    el Sisbén nacional es una muestra con `fex` (Bogotá trae 1), así que se
    sortean hogares con probabilidad proporcional al `fex`, con reemplazo.
    Los hogares se separan antes en dos grupos disjuntos, para que un hogar
    repetido no quede en entrenamiento y en prueba a la vez. Hasta el
    2026-11-22 la submuestra se estratificaba por grupo sin ponderar."""
    rng = np.random.default_rng(seed)
    en_prueba = rng.random(len(peso)) < prueba
    salida = []
    for mascara, m in ((~en_prueba, round(n * (1 - prueba))), (en_prueba, round(n * prueba))):
        pos = np.flatnonzero(mascara)
        salida.append(rng.choice(pos, size=m, replace=True, p=peso[pos] / peso[pos].sum()))
    return salida[0], salida[1]


def _valor_ordinal(d: pd.DataFrame) -> pd.DataFrame:
    """Valor de cada variable en una escala de bajo a alto, para colorear la
    figura SHAP. Solo variables con orden verificado (pisos y paredes por la
    escala común; sexo 2 = mujer y zona 1 = cabecera en las dos fuentes);
    departamento y servicios quedan sin color."""
    pisos = d["viv_pisos"].astype(str).map(PISOS_NIVEL["sisben"]).map({"tierra": 0, "cemento_madera": 1, "acabado": 2})
    paredes = d["viv_paredes"].astype(str).map({"1": 2, "4": 2, "2": 1, "3": 1, "5": 0, "6": 0, "7": 0, "0": 0})
    return pd.DataFrame({
        "hog_num_personas": pd.to_numeric(d["hog_num_personas"], errors="coerce"),
        "hog_num_menores": pd.to_numeric(d["hog_num_menores"], errors="coerce"),
        "viv_cuartos": pd.to_numeric(d["viv_cuartos"], errors="coerce"),
        "jefe_edad": pd.to_numeric(d["jefe_edad"], errors="coerce"),
        "viv_pisos": pisos, "viv_paredes": paredes,
        "jefe_sexo": (d["jefe_sexo"].astype(str) == "2").astype(float),
        "geo_zona": (d["geo_zona"].astype(str) != "1").astype(float),
    }, index=d.index)


def _metricas_por_clase(nombre: str, modelo, X_te, y_te) -> pd.DataFrame:
    """Precisión, sensibilidad y F1 por grupo, matriz de confusión y
    calibración (probabilidad predicha media vs. tasa observada, Brier por
    clase). El modelo predice el grupo ASIGNADO por el Sisbén, no la
    pobreza real."""
    pred = modelo.predict(X_te)
    proba = modelo.predict_proba(X_te)
    clases = list(modelo.classes_)
    prec, rec, f1, sop = precision_recall_fscore_support(y_te, pred, labels=clases, zero_division=0)
    tabla = pd.DataFrame({
        "modelo": nombre, "grupo": clases, "precision": prec, "sensibilidad": rec, "f1": f1, "soporte": sop,
        "tasa_observada": [(y_te == c).mean() for c in clases],
        "prob_predicha_media": proba.mean(axis=0),
        "brier": [brier_score_loss((y_te == c).astype(int), proba[:, i]) for i, c in enumerate(clases)],
    })
    cm = pd.DataFrame(confusion_matrix(y_te, pred, labels=clases, normalize="true") * 100,
                      index=[f"real {c}" for c in clases], columns=[f"pred {c}" for c in clases])
    print(f"\n{nombre} — por grupo:")
    print(tabla.drop(columns="modelo").round(3).to_string(index=False))
    print(f"{nombre} — matriz de confusión (% de cada grupo real):")
    print(cm.round(1).to_string())
    return tabla


def _lasso(X_tr, y_tr, X_te, y_te, columnas, mapa):
    modelo = LogisticRegressionCV(
        l1_ratios=[1.0], solver="saga", Cs=8, cv=3, scoring="accuracy",
        max_iter=3000, random_state=SEED, n_jobs=-1, use_legacy_attributes=False,
    )
    modelo.fit(X_tr, y_tr)
    pred = modelo.predict(X_te)
    acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro")
    pesos_por_clase = np.abs(modelo.coef_).sum(axis=0)  # |coef| sumado sobre las 4 clases
    importancia = _importancia_por_variable(pesos_por_clase, columnas, mapa)
    eliminadas = importancia[importancia == 0].index.tolist()
    return modelo, importancia, eliminadas, acc, f1


def _ridge(X_tr, y_tr, X_te, y_te, columnas, mapa):
    modelo = LogisticRegressionCV(
        l1_ratios=[0.0], solver="saga", Cs=8, cv=3, scoring="accuracy",
        max_iter=3000, random_state=SEED, n_jobs=-1, use_legacy_attributes=False,
    )
    modelo.fit(X_tr, y_tr)
    pred = modelo.predict(X_te)
    acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro")
    pesos_por_clase = np.abs(modelo.coef_).sum(axis=0)
    importancia = _importancia_por_variable(pesos_por_clase, columnas, mapa)
    return modelo, importancia, acc, f1


def _shap_rf(X_tr, y_tr, X_te, y_te, columnas, mapa):
    modelo = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=20, random_state=SEED, n_jobs=-1,
    )
    modelo.fit(X_tr, y_tr)
    pred = modelo.predict(X_te)
    acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro")

    n_shap = min(20_000, len(X_te))
    X_shap = X_te.iloc[np.random.default_rng(SEED).choice(len(X_te), n_shap, replace=False)]
    explainer = shap.TreeExplainer(modelo)
    sv = explainer.shap_values(X_shap)
    # shap >=0.45 con RandomForestClassifier multiclase: array (n, n_features, n_clases)
    sv = np.asarray(sv)
    pesos = np.abs(sv).mean(axis=0).sum(axis=1)  # media |shap| por fila, sumado sobre clases
    importancia = _importancia_por_variable(pesos, columnas, mapa)
    # Efecto de cada variable sobre P(A) + P(B), sumando sus columnas dummy.
    clases = list(modelo.classes_)
    ab = sv[:, :, [clases.index("A"), clases.index("B")]].sum(axis=2)
    shap_ab = pd.DataFrame(ab, columns=columnas, index=X_shap.index).T.groupby([mapa[c] for c in columnas]).sum().T
    return modelo, importancia, acc, f1, shap_ab


def main() -> None:
    logger.info("Cargando %s", SISBEN_PATH)
    df = pd.read_parquet(SISBEN_PATH, columns=[*TODAS, "Grupo", "cod_mpio", "fex"])
    X, y, mapa = _preparar(df)
    municipios = df.loc[X.index, "cod_mpio"].astype(str)
    peso = peso_donante(df.loc[X.index])
    logger.info("Hogares con las %s variables completas: %s", len(TODAS), f"{len(X):,}")

    tr_pos, te_pos = muestra_ponderada(peso, N_MUESTRA, SEED)
    X_tr, y_tr = X.iloc[tr_pos].reset_index(drop=True), y.iloc[tr_pos].reset_index(drop=True)
    X_te, y_te = X.iloc[te_pos].reset_index(drop=True), y.iloc[te_pos].reset_index(drop=True)
    X_m, y_m = pd.concat([X_tr, X_te], ignore_index=True), pd.concat([y_tr, y_te], ignore_index=True)
    mpio_m = pd.concat([municipios.iloc[tr_pos], municipios.iloc[te_pos]], ignore_index=True)
    origen_te = X.index[te_pos]  # fila del Sisbén de cada hogar de prueba
    columnas = list(X.columns)
    poblacion = pd.Series(peso, index=X.index).groupby(y.values).sum() / peso.sum() * 100

    print("\n=== Selección de variables — Sisbén, outcome = Grupo (A-D) ===")
    print(f"n total con variables completas: {len(X):,} | submuestra ponderada por fex: {len(X_m):,} "
          f"(train={len(X_tr):,}, test={len(X_te):,})")
    print("Grupos en la población (fex), %: " + ", ".join(f"{g} {v:.1f}" for g, v in poblacion.items()))
    print("Grupos en la submuestra, %: " + ", ".join(f"{g} {v:.1f}" for g, v in
                                                     (y_m.value_counts(normalize=True).sort_index() * 100).items()))
    print(f"Línea base (siempre el grupo más frecuente): exactitud {y_te.value_counts(normalize=True).max():.3f}")

    m_lasso, imp_lasso, eliminadas, acc_l, f1_l = _lasso(X_tr, y_tr, X_te, y_te, columnas, mapa)
    print(f"\n--- LASSO (L1) --- accuracy={acc_l:.3f} f1_macro={f1_l:.3f}")
    print(imp_lasso.round(3).to_string())
    print(f"Variables eliminadas (coef=0 en las 4 clases): {eliminadas or 'ninguna'}")

    m_ridge, imp_ridge, acc_r, f1_r = _ridge(X_tr, y_tr, X_te, y_te, columnas, mapa)
    print(f"\n--- Ridge (L2) --- accuracy={acc_r:.3f} f1_macro={f1_r:.3f}")
    print(imp_ridge.round(3).to_string())

    m_rf, imp_shap, acc_s, f1_s, shap_ab = _shap_rf(X_tr, y_tr, X_te, y_te, columnas, mapa)
    figura = shap_ab.iloc[:N_SHAP_FIGURA]
    valores = _valor_ordinal(df.loc[origen_te[figura.index]]).reset_index(drop=True)
    figura = pd.concat([figura.reset_index(drop=True).add_prefix("shap_"), valores.add_prefix("valor_")], axis=1)
    figura.round(5).to_csv(REPORT_SHAP, index=False)
    print("Media |SHAP| sobre P(A/B): " + ", ".join(f"{k} {v:.4f}" for k, v in
                                                     shap_ab.abs().mean().sort_values(ascending=False).items()))
    print(f"\n--- SHAP sobre RandomForestClassifier --- accuracy={acc_s:.3f} f1_macro={f1_s:.3f}")
    print(imp_shap.round(4).to_string())

    print("\n=== Rendimiento por grupo y calibración (partición aleatoria) ===")
    por_clase = [_metricas_por_clase(n, m, X_te, y_te)
                 for n, m in (("LASSO", m_lasso), ("Ridge", m_ridge), ("RandomForest", m_rf))]

    # Partición por municipio: ningún municipio queda en entrenamiento y prueba a
    # la vez, para que la nota no se apoye en hogares vecinos o registros repetidos.
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=SEED)
                  .split(X_m, y_m, groups=mpio_m))
    rf_g = RandomForestClassifier(n_estimators=300, max_depth=10, min_samples_leaf=20,
                                  random_state=SEED, n_jobs=-1).fit(X_m.iloc[tr], y_m.iloc[tr])
    pred_g = rf_g.predict(X_m.iloc[te])
    print(f"\n=== Partición por municipio (RandomForest) === accuracy="
          f"{accuracy_score(y_m.iloc[te], pred_g):.3f} "
          f"f1_macro={f1_score(y_m.iloc[te], pred_g, average='macro'):.3f} (aleatoria: {acc_s:.3f} / {f1_s:.3f})")
    por_clase.append(_metricas_por_clase("RandomForest_por_municipio", rf_g, X_m.iloc[te], y_m.iloc[te]))
    REPORT_CLASES.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(por_clase).to_csv(REPORT_CLASES, index=False)

    variables = sorted(set(imp_lasso.index) | set(imp_ridge.index) | set(imp_shap.index))
    tabla = pd.DataFrame({
        "lasso_norm": imp_lasso / imp_lasso.max(),
        "ridge_norm": imp_ridge / imp_ridge.max(),
        "shap_norm": imp_shap / imp_shap.max(),
    }).reindex(variables).fillna(0)
    tabla["es_control_geografico"] = [v == "geo_depto" for v in tabla.index]
    tabla["promedio"] = tabla[["lasso_norm", "ridge_norm", "shap_norm"]].mean(axis=1)
    tabla = tabla.sort_values("promedio", ascending=False)

    print("\n=== Tabla combinada (normalizada 0-1 dentro de cada método) ===")
    print(tabla.round(3).to_string())

    r_lr, _ = spearmanr(tabla["lasso_norm"], tabla["ridge_norm"])
    r_ls, _ = spearmanr(tabla["lasso_norm"], tabla["shap_norm"])
    r_rs, _ = spearmanr(tabla["ridge_norm"], tabla["shap_norm"])
    print(f"\nCorrelación de Spearman entre rankings: LASSO-Ridge={r_lr:.3f} "
          f"LASSO-SHAP={r_ls:.3f} Ridge-SHAP={r_rs:.3f}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT, index_label="variable")
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
