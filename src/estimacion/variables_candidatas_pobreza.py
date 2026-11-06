"""Qué variables podría incorporar el Sisbén para captar mejor la pobreza.

Ejercicio predictivo con datos reales de la GEIH 2024: no usa el Hot-Deck ni
la simulación y no estima efectos causales. Una variable que predice pobreza
no la causa, ni demuestra que incorporarla mejore la política. La
interpretación está en `docs/resultados/RECOMENDACION_VARIABLES_POBREZA.md`.

Se comparan modelos anidados, de menos a más información:

- `canonico`: las variables del esquema canónico del Hot-Deck.
- `ficha`: lo que la GEIH y la ficha del Sisbén IV recogen en común.
- `ficha_derivadas`: lo anterior más variables del hogar calculables con lo
  que el Sisbén ya recoge (dependencia, monoparentalidad, etc.). Es la
  referencia: un candidato solo cuenta si aporta sobre ella.
- `+grupo`: la referencia más un grupo de variables que no están en el
  diccionario del Sisbén.
- `todo` y `todo-grupo`: todos los grupos, y todos menos uno.

Códigos verificados contra `docs/insumos/DICCIONARIO_GEIH_2024.xlsx` y, donde
el diccionario no trae la lista de categorías, con los datos: en `P3373` el 3
es otro país (el código de país trae 862, Venezuela) y en `P3374` el 3 es
extranjero (`P3374S1` no trae Colombia, 170, de primero); en `P1906` el 4 es
sin dificultad (cae con la edad, de 97,6 % a 52,9 %) y 1 y 2 son no puede y
mucha dificultad. `P3092` solo se pregunta en la zona rural.

Quedan fuera las variables en dinero (arriendo, valor de la vivienda, cuota,
ingresos, subsidios), porque entran en el ingreso o lo miden directamente, e
`I1`-`I15`/`H_5` del Sisbén (circularidad).

`analisis_posterior` no participa en el criterio de decisión: se agregó después
de ver los resultados, para revisar lo que el criterio no mide (si la cuenta de
ahorros es consecuencia de las transferencias, y qué queda sin ella).

Uso:
    poetry run python -m src.estimacion.variables_candidatas_pobreza [n_jobs] [posterior]
Con `posterior` corre solo esa parte, sobre la tabla ya construida.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils.variables_canonicas import es_jefe, normalizar_llave

logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
MUESTRA = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
VICTIMAS = Path("data/0_raw/victimas_mpmd/Victimas_MPMD.csv")
TABLA = Path("data/2_models/variables_candidatas_hogar_2024.parquet")
REPORTES = Path("docs/reports")
OUT_METRICAS = REPORTES / "variables_candidatas_metricas.csv"
OUT_DELTAS = REPORTES / "variables_candidatas_deltas.csv"
OUT_SIGNIFICANCIA = REPORTES / "variables_candidatas_significancia.csv"
OUT_GRUPOS = REPORTES / "variables_candidatas_grupos.csv"
OUT_SELECCION = REPORTES / "variables_candidatas_seleccion.csv"
OUT_DECISION = REPORTES / "variables_candidatas_decision.csv"
OUT_POSTERIOR = REPORTES / "variables_candidatas_posterior.csv"
OUT_TRANSFERENCIAS = REPORTES / "variables_candidatas_transferencias.csv"
OUT_LASSO = REPORTES / "variables_candidatas_lasso_estricto.csv"
MESES = [f"{m:02d}" for m in range(1, 13)]
K3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]
SEED = 2026
LASSO_C = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
N_BOOT = 200
N_FOLDS = 5

PRINCIPAL = "POBRE_MONETARIO"
OUTCOMES = ["POBRE_MONETARIO", "POBRE_EXTREMO_MONETARIO", "POBRE_MONETARIO_OFICIAL", "POBRE_GEIH"]

# Criterio fijado antes de ver los resultados.
MIN_MEJORA_EXCLUSION = 0.005  # 0,5 puntos porcentuales menos de error de exclusión
ALFA = 0.05

SI = "1"
HOGAR_VIVIENDA = {  # código GEIH -> variable de trabajo
    "P4000": "viv_tipo", "P4030S1": "viv_energia", "P4030S2": "viv_gas", "P4030S4": "viv_basuras",
    "P70": "viv_num_hogares", "P5020": "hog_sanitario", "P5030": "hog_sanitario_exclusivo",
    "P5040": "hog_basura", "P5050": "hog_agua", "P5070": "hog_cocina", "P5080": "hog_combustible",
    "P5090": "hog_tenencia", "P4030S1A1": "estrato",
}
FINANCIEROS = {
    "P5222S2": "fin_ahorros", "P5222S4": "fin_credito_vivienda", "P5222S5": "fin_credito_vehiculo",
    "P5222S6": "fin_libre_inversion", "P5222S7": "fin_tarjeta", "P5222S8": "fin_otro", "P5222S9": "fin_ninguno",
}
FIN_CORRIENTE_CDT = ["P5222S1", "P5222S3"]
DIFICULTADES = [f"P1906S{i}" for i in range(1, 9)]

CANONICO_CAT = ["geo_depto", "geo_zona", "jefe_sexo", "viv_paredes", "viv_pisos", "viv_alcantarillado", "viv_acueducto"]
CANONICO_NUM = ["jefe_edad", "hog_num_personas", "viv_cuartos"]
FICHA_CAT = CANONICO_CAT + ["viv_tipo", "viv_energia", "viv_gas", "viv_basuras", "viv_num_hogares", "hog_sanitario",
                            "hog_sanitario_exclusivo", "hog_basura", "hog_agua", "hog_cocina", "hog_combustible",
                            "hog_tenencia", "jefe_estado_civil", "jefe_educacion", "jefe_ocupacion"]
FICHA_NUM = CANONICO_NUM + ["viv_cuartos_dormir", "analfabetismo", "bajo_logro_educativo_jefe",
                            "inasistencia_escolar_menores", "sin_aseguramiento_salud",
                            "sin_cotizacion_pension_jefe", "hacinamiento"]
DERIVADAS = ["n_menores", "n_mayores", "razon_dependencia", "monoparental", "tasa_ocupados", "adulto_educ_superior"]
GRUPOS = {
    "inclusion_financiera": ["fin_ahorros", "fin_corriente_cdt", "fin_credito_vivienda", "fin_credito_vehiculo",
                             "fin_libre_inversion", "fin_tarjeta", "fin_otro", "fin_ninguno"],
    "estrato": ["estrato"],
    "discapacidad": ["hog_discapacidad", "jefe_discapacidad"],
    "etnia": ["jefe_indigena", "jefe_afro", "jefe_otra_etnia"],
    "campesino": ["jefe_campesino", "jefe_comunidad_campesina"],
    "migracion": ["hog_nacido_exterior", "jefe_extranjero", "hog_migrante_12m", "hog_migrante_5a"],
    "victimas": ["hog_victima", "hog_desplazado"],
    "autoconsumo": ["hog_huerta", "hog_animales", "hog_trae_agua"],
}
CATEGORICAS = set(FICHA_CAT) | {"estrato"}

# El IPM-GEIH se calcula con estas columnas: para predecirlo no pueden estar en
# la referencia, o el modelo reconstruiría la fórmula y no quedaría qué aportar.
MECANICAS_IPM = {"analfabetismo", "bajo_logro_educativo_jefe", "inasistencia_escolar_menores",
                 "sin_aseguramiento_salud", "sin_cotizacion_pension_jefe", "hacinamiento", "viv_alcantarillado",
                 "viv_acueducto", "viv_cuartos", "viv_cuartos_dormir", "jefe_educacion", "adulto_educ_superior"}


# --------------------------------------------------------------------------
# Tabla de hogares
# --------------------------------------------------------------------------

def agregar_personas(p: pd.DataFrame) -> pd.DataFrame:
    """De personas a hogares: composición, condiciones de algún miembro y
    características del jefe. Espera códigos como texto ("1", no "1.0")."""
    p = p.copy()
    edad = pd.to_numeric(p["P6040"], errors="coerce")
    llaves = [p[c] for c in K3]

    def algun(mascara: pd.Series) -> pd.Series:
        return mascara.fillna(False).astype(bool).groupby(llaves).any().astype(float)

    def conteo(mascara: pd.Series) -> pd.Series:
        return mascara.fillna(False).astype(float).groupby(llaves).sum()

    n_menores, n_mayores = conteo(edad < 18), conteo(edad >= 60)
    n_activos = conteo((edad >= 18) & (edad < 60))
    dificultad = p[DIFICULTADES].isin(["1", "2"]).any(axis=1)  # no puede o mucha dificultad
    h = pd.DataFrame({
        "n_menores": n_menores,
        "n_mayores": n_mayores,
        "razon_dependencia": (n_menores + n_mayores) / n_activos.clip(lower=1),
        "tasa_ocupados": conteo(p["OCI"].eq(SI)) / conteo(edad >= 15).clip(lower=1),
        "adulto_educ_superior": algun((edad >= 18) & p["P3042"].isin([str(c) for c in range(8, 14)])),
        "hog_discapacidad": algun(dificultad),
        "hog_nacido_exterior": algun(p["P3373"].eq("3")),
        "hog_migrante_12m": algun(p["P3384"].isin(["3", "4"])),
        "hog_migrante_5a": algun(p["P3382"].isin(["3", "4"])),
        "hog_huerta": algun(p["P3094"].eq(SI)),
        "hog_animales": algun(p["P3095"].eq(SI)),
        "hog_trae_agua": algun(p["P3092"].eq(SI)),
        "hog_victima": algun(p["es_victima"].eq(SI)),
        "hog_desplazado": algun(p["es_desplazado"].eq(SI)),
    })
    jefe = p[es_jefe(p, "geih")].drop_duplicates(K3).set_index(K3)
    h["monoparental"] = ((h["n_menores"] > 0) & ~jefe["P6071"].reindex(h.index).eq(SI)).astype(float)
    h["jefe_discapacidad"] = algun(dificultad & es_jefe(p, "geih"))
    h["jefe_indigena"] = jefe["P6080"].eq("1").reindex(h.index).fillna(False).astype(float)
    h["jefe_afro"] = jefe["P6080"].eq("5").reindex(h.index).fillna(False).astype(float)
    h["jefe_otra_etnia"] = jefe["P6080"].isin(["2", "3", "4"]).reindex(h.index).fillna(False).astype(float)
    h["jefe_campesino"] = jefe["P2057"].eq(SI).reindex(h.index).fillna(False).astype(float)
    h["jefe_comunidad_campesina"] = jefe["P2061"].eq(SI).reindex(h.index).fillna(False).astype(float)
    h["jefe_extranjero"] = jefe["P3374"].eq("3").reindex(h.index).fillna(False).astype(float)
    h["jefe_estado_civil"] = jefe["P6070"].reindex(h.index)
    h["jefe_educacion"] = jefe["P3042"].reindex(h.index)
    h["jefe_ocupacion"] = jefe["P6430"].reindex(h.index).astype("object").fillna("no_ocupado")
    return h.reset_index()


def variables_vivienda(v: pd.DataFrame) -> pd.DataFrame:
    """Variables del módulo de hogar y vivienda con sus nombres de trabajo."""
    h = v[K3 + list(HOGAR_VIVIENDA)].rename(columns=HOGAR_VIVIENDA).copy()
    for codigo, nombre in FINANCIEROS.items():
        h[nombre] = v[codigo].eq(SI).astype(float)
    h["fin_corriente_cdt"] = v[FIN_CORRIENTE_CDT].eq(SI).any(axis=1).astype(float)
    return h


def _leer(mes: str, modulo: str, columnas: list[str]) -> pd.DataFrame:
    d = pd.read_parquet(GEIH_DIR / mes / f"{modulo}.parquet", columns=columnas).replace("", pd.NA)
    for c in set(K3 + ["ORDEN"]) & set(d.columns):
        d[c] = normalizar_llave(d[c])
    return d


def _hogares_mes(mes: str, victimas: pd.DataFrame) -> pd.DataFrame:
    llave = K3 + ["ORDEN"]
    p = _leer(mes, "caracteristicas_generales", llave + ["P6040", "P6050", "P6070", "P6071", "P6080", "P2057", "P2061",
                                                         "P3042", *DIFICULTADES])
    for modulo, cols in (("migracion", ["P3373", "P3374", "P3382", "P3384"]),
                         ("otras_formas_trabajo", ["P3092", "P3094", "P3095"]),
                         ("ocupados", ["OCI", "P6430"])):
        p = p.merge(_leer(mes, modulo, llave + cols), on=llave, how="left")
    p = p.merge(victimas[victimas["mes"] == mes].drop(columns="mes"), on=["DIRECTORIO", "SECUENCIA_P", "ORDEN"], how="left")
    viv = _leer(mes, "hogar_vivienda", K3 + list(HOGAR_VIVIENDA) + list(FINANCIEROS) + FIN_CORRIENTE_CDT)
    h = agregar_personas(p).merge(variables_vivienda(viv), on=K3, how="left", validate="1:1")
    h["mes"] = mes
    return h


def construir_tabla() -> pd.DataFrame:
    """Muestra de estimación más las variables de trabajo, hogar por hogar."""
    v = pd.read_csv(VICTIMAS, sep=";", dtype=str)
    victimas = pd.DataFrame({"DIRECTORIO": normalizar_llave(v["directorio"]), "SECUENCIA_P": normalizar_llave(v["secuencia_p"]),
                             "ORDEN": normalizar_llave(v["orden"]), "mes": v["CD_PERI"].str[-2:],
                             "es_victima": v["es_victima"], "es_desplazado": v["es_desplazado"]})
    extra = pd.concat([_hogares_mes(m, victimas) for m in MESES], ignore_index=True)
    columnas = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes", "fex", *OUTCOMES, *CANONICO_CAT, *CANONICO_NUM,
                *[c for c in FICHA_NUM if c not in CANONICO_NUM]]
    m = pd.read_parquet(MUESTRA, columns=columnas).rename(
        columns={"llave_directorio": "DIRECTORIO", "llave_secuencia_p": "SECUENCIA_P", "llave_hogar": "HOGAR"})
    for c in K3:
        m[c] = normalizar_llave(m[c])
    t = m.merge(extra, on=K3 + ["mes"], how="left", validate="1:1", indicator=True)
    if not (t.pop("_merge") == "both").all():
        raise RuntimeError("Hogares de la muestra sin variables candidatas: revisar las llaves")
    return t


# --------------------------------------------------------------------------
# Métricas (con pesos, para poder remuestrear sin reordenar)
# --------------------------------------------------------------------------

def auc_ponderada(y: np.ndarray, p: np.ndarray, w: np.ndarray) -> float:
    """Probabilidad de que un pobre tenga mayor predicción que un no pobre."""
    _, inv = np.unique(p, return_inverse=True)
    pos, neg = np.bincount(inv, w * y), np.bincount(inv, w * (1 - y))
    previos = np.cumsum(neg) - neg
    return float((pos * (previos + 0.5 * neg)).sum() / (pos.sum() * neg.sum()))


def seleccionados(p: np.ndarray, w: np.ndarray, presupuesto: float) -> np.ndarray:
    """Hogares de mayor predicción hasta cubrir la fracción `presupuesto` del peso."""
    orden = np.argsort(-p, kind="stable")
    elegidos = np.zeros(len(p), dtype=bool)
    elegidos[orden[np.cumsum(w[orden]) <= presupuesto * w.sum()]] = True
    return elegidos


def errores_focalizacion(y: np.ndarray, elegidos: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """(exclusión, inclusión): pobres no elegidos y elegidos no pobres."""
    pobres = (w * y).sum()
    aciertos = (w * y * elegidos).sum()
    return float(1 - aciertos / pobres), float(1 - aciertos / (w * elegidos).sum())


def metricas(y: np.ndarray, p: np.ndarray, w: np.ndarray, urbano: np.ndarray, presupuesto: float) -> dict[str, float]:
    elegidos = seleccionados(p, w, presupuesto)
    exclusion, inclusion = errores_focalizacion(y, elegidos, w)
    res = dict(auc=auc_ponderada(y, p, w), exclusion=exclusion, inclusion=inclusion,
               brier=float(np.average((p - y) ** 2, weights=w)))
    for nombre, m in (("urbano", urbano), ("rural", ~urbano)):
        res[f"auc_{nombre}"] = auc_ponderada(y[m], p[m], w[m])
        res[f"exclusion_{nombre}"] = errores_focalizacion(y[m], elegidos[m], w[m])[0]
    return res


def holm(p: pd.Series) -> pd.Series:
    """p ajustados por Holm: controla la probabilidad de algún falso hallazgo."""
    orden = p.sort_values()
    ajustados = (orden * (len(orden) - np.arange(len(orden)))).cummax().clip(upper=1)
    return ajustados.reindex(p.index)


def decidir(fila: dict) -> str:
    """Clasifica un grupo con el criterio fijado antes de ver los resultados.

    `recomendar`: asociación significativa tras Holm y, sobre la referencia,
    reduce el error de exclusión al menos `MIN_MEJORA_EXCLUSION` con IC que
    excluye el cero, y la mejora se sostiene con meses y departamentos no
    vistos, en la zona urbana y la rural, y con los demás grupos presentes.
    `considerar`: significativo con mejora de IC sin el cero (exclusión o AUC),
    pero pequeña o inestable. Lo demás, `no_recomendar`."""
    significativo = fila["wald_holm"] < ALFA
    mejora_clara = fila["d_exclusion_hi"] < 0 and fila["d_exclusion"] <= -MIN_MEJORA_EXCLUSION
    estable = all(fila[c] < 0 for c in ("d_exclusion_temporal", "d_exclusion_depto", "d_exclusion_urbano",
                                        "d_exclusion_rural", "d_exclusion_sin_grupo"))
    if significativo and mejora_clara and estable:
        return "recomendar"
    if significativo and (fila["d_exclusion_hi"] < 0 or fila["d_auc_lo"] > 0):
        return "considerar"
    return "no_recomendar"


# --------------------------------------------------------------------------
# Modelos
# --------------------------------------------------------------------------

def matriz(t: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """Numéricas estandarizadas e indicadoras (categóricas sin orden nunca como
    número) y el mapa columna -> variable original."""
    variables = FICHA_CAT + FICHA_NUM + DERIVADAS + [c for g in GRUPOS.values() for c in g]
    partes, mapa = [], {}
    for v in variables:
        if v in CATEGORICAS:
            d = pd.get_dummies(t[v].astype("object").fillna("NA").astype(str), prefix=v, dtype=np.float32)
            d = d.loc[:, d.mean() >= 2e-4]  # categorías con menos de ≈60 hogares
        else:
            x = pd.to_numeric(t[v], errors="coerce").astype(float)
            x = x.fillna(x.mean())
            if not set(x.unique()) <= {0.0, 1.0}:  # las binarias quedan 0/1
                x = (x - x.mean()) / x.std()
            d = x.astype(np.float32).to_frame(v)
        partes.append(d)
        mapa.update({c: v for c in d.columns})
    return pd.concat(partes, axis=1), mapa


def especificaciones(outcome: str) -> dict[str, list[str]]:
    """Variables de cada modelo. Con el IPM-GEIH se quitan sus componentes."""
    fuera = MECANICAS_IPM if outcome == "POBRE_GEIH" else set()
    filtrar = lambda vs: [v for v in vs if v not in fuera]  # noqa: E731
    base = filtrar(FICHA_CAT + FICHA_NUM + DERIVADAS)
    todos = [c for g in GRUPOS.values() for c in g]
    specs = {"ficha_derivadas": base, "todo": base + todos}
    specs.update({f"+{g}": base + cols for g, cols in GRUPOS.items()})
    if outcome == PRINCIPAL:
        specs["canonico"] = CANONICO_CAT + CANONICO_NUM
        specs["ficha"] = filtrar(FICHA_CAT + FICHA_NUM)
        specs.update({f"todo-{g}": base + [c for o, cs in GRUPOS.items() if o != g for c in cs] for g in GRUPOS})
    return specs


def _modelo(tipo: str):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression

    if tipo == "logistica":
        return LogisticRegression(C=1.0, max_iter=1000)
    return HistGradientBoostingClassifier(max_iter=200, learning_rate=0.1, max_leaf_nodes=31, random_state=SEED)


def _ajustar(tipo: str, X: np.ndarray, y: np.ndarray, w: np.ndarray, columnas: np.ndarray, tr: np.ndarray,
             te: np.ndarray) -> np.ndarray:
    modelo = _modelo(tipo).fit(X[np.ix_(tr, columnas)], y[tr], sample_weight=w[tr] / w[tr].mean())
    return modelo.predict_proba(X[np.ix_(te, columnas)])[:, 1]


def particion_por_grupo(grupos: np.ndarray, n: int, seed: int = SEED) -> np.ndarray:
    """Pliegue de cada fila; todas las filas de un grupo van al mismo."""
    unicos, inv = np.unique(grupos, return_inverse=True)
    return np.random.default_rng(seed).permutation(len(unicos))[inv] % n


def _columnas(specs: dict[str, list[str]], X: pd.DataFrame, mapa: dict[str, str], sin: set[str] = frozenset()) -> dict:
    return {s: np.array([i for i, c in enumerate(X.columns) if mapa[c] in set(vs) - set(sin)]) for s, vs in specs.items()}


def predecir_cv(X, y, w, columnas: dict, pliegues: np.ndarray, tipo: str, n_jobs: int) -> dict[str, np.ndarray]:
    """Predicción fuera de muestra de cada especificación (mismos pliegues)."""
    from joblib import Parallel, delayed, parallel_config

    tareas = [(s, k) for s in columnas for k in np.unique(pliegues)]
    with parallel_config(backend="loky", inner_max_num_threads=1):
        res = Parallel(n_jobs=n_jobs)(delayed(_ajustar)(tipo, X, y, w, columnas[s], np.flatnonzero(pliegues != k),
                                                        np.flatnonzero(pliegues == k)) for s, k in tareas)
    pred = {s: np.empty(len(y)) for s in columnas}
    for (s, k), p in zip(tareas, res):
        pred[s][pliegues == k] = p
    return pred


def comparar(pred: dict[str, np.ndarray], y, w, urbano, viviendas, presupuesto: float,
             pares: list[tuple[str, str]]) -> tuple:
    """Métricas y diferencias frente a la referencia, con IC 95 % por bootstrap
    bayesiano de viviendas (mismos pesos para todos los modelos: comparación
    pareada). Solo mide la incertidumbre de la muestra de evaluación."""
    puntos = {s: metricas(y, p, w, urbano, presupuesto) for s, p in pred.items()}
    _, inv = np.unique(viviendas, return_inverse=True)
    rng = np.random.default_rng(SEED)
    claves = list(next(iter(puntos.values())))
    filas = {par: [] for par in pares}
    for _ in range(N_BOOT):
        wb = w * rng.standard_exponential(inv.max() + 1)[inv]
        m = {s: metricas(y, p, wb, urbano, presupuesto) for s, p in pred.items()}
        for (s, r), lista in filas.items():
            lista.append({k: m[s][k] - m[r][k] for k in claves})
    deltas = []
    for (s, r), lista in filas.items():
        b = pd.DataFrame(lista)
        for k in claves:
            deltas.append(dict(modelo=s, referencia=r, metrica=k, delta=puntos[s][k] - puntos[r][k],
                               ic_lo=float(b[k].quantile(0.025)), ic_hi=float(b[k].quantile(0.975))))
    return pd.DataFrame(puntos).T.rename_axis("modelo").reset_index(), pd.DataFrame(deltas)


def logit_agrupado(Z: np.ndarray, y: np.ndarray, w: np.ndarray, grupos: np.ndarray,
                   C: float = 1e4) -> tuple[np.ndarray, np.ndarray, int]:
    """Logit ponderado con penalización mínima (estable con categorías raras o
    columnas colineales, donde el logit sin penalizar diverge) y covarianza
    robusta agrupada. Devuelve (coeficientes con el intercepto de primero,
    covarianza, número de grupos)."""
    from scipy.special import expit
    from sklearn.linear_model import LogisticRegression

    pesos = w / w.mean()
    m = LogisticRegression(C=C, max_iter=5000, tol=1e-6).fit(Z, y, sample_weight=pesos)
    beta = np.r_[m.intercept_, m.coef_[0]]
    D = np.column_stack([np.ones(len(y)), Z])
    prob = expit(D @ beta)
    penal = np.eye(D.shape[1]) / C
    penal[0, 0] = 0
    H_inv = np.linalg.pinv((D.T * (pesos * prob * (1 - prob))) @ D + penal, hermitian=True)
    _, g = np.unique(grupos, return_inverse=True)
    G = g.max() + 1
    S = np.zeros((G, D.shape[1]))
    np.add.at(S, g, D * (pesos * (y - prob))[:, None])
    return beta, G / (G - 1) * H_inv @ (S.T @ S) @ H_inv, G


def significancia(X: pd.DataFrame, y: np.ndarray, w: np.ndarray, deptos: np.ndarray, mapa: dict[str, str],
                  columnas: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Logit con todos los candidatos y errores agrupados por departamento (los
    microdatos no traen la unidad primaria de muestreo). Por variable: prueba t
    corregida por Holm y cambio medio en la probabilidad de ser pobre al pasar
    a la categoría; por grupo: Wald conjunta, también con Holm."""
    from scipy import stats
    from scipy.special import expit

    nombres = [X.columns[i] for i in columnas]
    # Una categoría de referencia por variable (la más frecuente): con todas, la matriz es singular.
    frecuencia = X[nombres].mul(w, axis=0).sum()
    quitar = {frecuencia[[c for c in nombres if mapa[c] == v]].idxmax() for v in CATEGORICAS & {mapa[c] for c in nombres}}
    nombres = [c for c in nombres if c not in quitar]
    Z = X[nombres].to_numpy(float)
    beta, V, G = logit_agrupado(Z, y, w, deptos)
    se = np.sqrt(np.diag(V).clip(min=0))  # colineales: varianza numéricamente 0
    eta = beta[0] + Z @ beta[1:]
    candidatos = {c: g for g, cs in GRUPOS.items() for c in cs}
    filas = []
    for k, c in enumerate(nombres):
        if mapa[c] not in candidatos:
            continue
        # Frente a la categoría de referencia (0 en las binarias).
        hermanas = [i for i, o in enumerate(nombres) if mapa[o] == mapa[c]]
        eta0 = eta - Z[:, hermanas] @ beta[1:][hermanas]
        con = Z[:, k] > 0
        b, e = beta[k + 1], se[k + 1]
        filas.append(dict(grupo=candidatos[mapa[c]], variable=c, prevalencia=float(np.average(con, weights=w)),
                          coef=b, se=e, p=float(2 * stats.t.sf(abs(b / e), G - 1)),
                          cambio_prob=float(np.average(expit(eta0 + b) - expit(eta0), weights=w)),
                          tasa_con=float(np.average(y[con], weights=w[con])),
                          tasa_sin=float(np.average(y[~con], weights=w[~con]))))
    tabla = pd.DataFrame(filas)
    tabla["p_holm"] = holm(tabla["p"])
    grupos = []
    for g in GRUPOS:
        idx = [k + 1 for k, c in enumerate(nombres) if candidatos.get(mapa[c]) == g]
        F = float(beta[idx] @ np.linalg.pinv(V[np.ix_(idx, idx)]) @ beta[idx] / len(idx))
        grupos.append(dict(grupo=g, gl=len(idx), wald_f=F, wald_p=float(stats.f.sf(F, len(idx), G - 1))))
    grupos = pd.DataFrame(grupos)
    grupos["wald_holm"] = holm(grupos["wald_p"])
    return tabla, grupos


def _lasso(X, y, w, C: float, filas: np.ndarray, semilla: int = SEED):
    from sklearn.linear_model import LogisticRegression

    return LogisticRegression(l1_ratio=1.0, solver="liblinear", C=C, max_iter=200, random_state=semilla).fit(
        X[filas], y[filas], sample_weight=w[filas] / w[filas].mean())


def _lasso_coef(X, y, w, C: float, semilla: int, viviendas: np.ndarray) -> np.ndarray:
    """Coeficientes en una mitad de las viviendas, sorteada con `semilla`."""
    elegidas = np.random.default_rng(semilla).random(viviendas.max() + 1)[viviendas] < 0.5
    return _lasso(X, y, w, C, np.flatnonzero(elegidas), semilla).coef_[0]


def elegir_c_lasso(X, y, w, viviendas: np.ndarray) -> float:
    """El C más pequeño (modelo más parsimonioso) con pérdida logarítmica a
    menos de 0,5 % de la mejor, en una partición por viviendas de 60.000 hogares."""
    from sklearn.metrics import log_loss

    rng = np.random.default_rng(SEED)
    filas = rng.choice(len(y), min(60_000, len(y)), replace=False)
    entrena = rng.random(viviendas.max() + 1)[viviendas[filas]] < 0.7
    perdida = {}
    for C in LASSO_C:
        m = _lasso(X, y, w, C, filas[entrena])
        prueba = filas[~entrena]
        perdida[C] = log_loss(y[prueba], m.predict_proba(X[prueba])[:, 1], sample_weight=w[prueba])
    mejor = min(perdida.values())
    return min(C for C, v in perdida.items() if v <= mejor * 1.005)


def seleccion(X: pd.DataFrame, y: np.ndarray, w: np.ndarray, viviendas: np.ndarray, mapa: dict[str, str],
              n_jobs: int) -> tuple[pd.DataFrame, float]:
    """LASSO (frecuencia de selección en 30 mitades de la muestra), Ridge y
    SHAP sobre el modelo completo, por variable original como en el OE1. La
    importancia de una categórica suma sus indicadoras, y `geo_depto` entra
    como control: se lee aparte."""
    import shap
    from joblib import Parallel, delayed
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression

    _, inv = np.unique(viviendas, return_inverse=True)
    Xn = X.to_numpy(np.float32)
    C = elegir_c_lasso(Xn, y, w, inv)
    betas = np.array(Parallel(n_jobs=n_jobs)(delayed(_lasso_coef)(Xn, y, w, C, s, inv) for s in range(30)))
    variable = np.array([mapa[c] for c in X.columns])
    frecuencia = pd.Series((betas != 0).mean(axis=0), index=X.columns).groupby(variable).max()
    ridge = LogisticRegression(C=1.0, max_iter=1000).fit(Xn, y, sample_weight=w / w.mean())
    ridge_imp = pd.Series(np.abs(ridge.coef_[0]), index=X.columns).groupby(variable).sum()
    rng = np.random.default_rng(SEED)
    fila = rng.choice(len(y), min(100_000, len(y)), replace=False)
    bosque = RandomForestClassifier(n_estimators=200, max_depth=10, min_samples_leaf=20, random_state=SEED, n_jobs=n_jobs)
    bosque.fit(Xn[fila], y[fila], sample_weight=w[fila] / w[fila].mean())
    sv = np.asarray(shap.TreeExplainer(bosque).shap_values(Xn[rng.choice(len(y), min(10_000, len(y)), replace=False)]))
    sv = sv[..., 1] if sv.ndim == 3 else sv
    shap_imp = pd.Series(np.abs(sv).mean(axis=0), index=X.columns).groupby(variable).sum()
    tabla = pd.DataFrame({"lasso_frecuencia": frecuencia, "ridge": ridge_imp, "shap": shap_imp})
    tabla["ridge_rango"] = tabla["ridge"].rank(ascending=False).astype(int)
    tabla["shap_rango"] = tabla["shap"].rank(ascending=False).astype(int)
    grupo = {c: g for g, cs in GRUPOS.items() for c in cs}
    tabla["grupo"] = [grupo.get(v, "referencia") for v in tabla.index]
    return tabla.rename_axis("variable").reset_index().sort_values("shap", ascending=False), C


def hogares_con_transferencia() -> pd.DataFrame:
    """Hogares donde algún miembro declara ayudas en dinero del gobierno
    (`P750S2`) o de un programa (`P1661S1`-`S3`). Es participación declarada, no
    un registro administrativo. No entra en ningún modelo: es dinero y depende de
    la propia focalización."""
    columnas = K3 + ["ORDEN", "P750S2", "P1661S1", "P1661S2", "P1661S3"]
    partes = []
    for mes in MESES:
        d = _leer(mes, "otros_ingresos", columnas)
        d["mes"] = mes
        partes.append(d)
    d = pd.concat(partes, ignore_index=True)
    llaves = [d[c] for c in K3 + ["mes"]]
    return pd.DataFrame({
        "ayuda_gobierno": d[["P750S2", "P1661S1", "P1661S2", "P1661S3"]].eq(SI).any(axis=1).groupby(llaves).any(),
        "familias_en_accion": d["P1661S1"].eq(SI).groupby(llaves).any(),
        "jovenes_en_accion": d["P1661S2"].eq(SI).groupby(llaves).any(),
        "colombia_mayor": d["P1661S3"].eq(SI).groupby(llaves).any(),
    }).reset_index()


def cuenta_segun_transferencia(t: pd.DataFrame, X: pd.DataFrame, mapa: dict[str, str], w: np.ndarray,
                               columnas: np.ndarray) -> pd.DataFrame:
    """¿Tienen más cuenta de ahorros quienes reciben transferencias? En bruto por
    condición de pobreza, y ajustado por la referencia: logit de la cuenta sobre
    la transferencia y las variables de la ficha."""
    from scipy import stats
    from scipy.special import expit

    ayuda = t["ayuda_gobierno"].eq(True).to_numpy()
    cuenta = t["fin_ahorros"].to_numpy(float)
    pobre = t[PRINCIPAL].to_numpy(float) == 1
    filas = []
    for nombre, m in (("todos", np.ones(len(t), dtype=bool)), ("pobres", pobre), ("no_pobres", ~pobre)):
        filas.append(dict(poblacion=nombre, pct_con_ayuda=float(np.average(ayuda[m], weights=w[m])) * 100,
                          cuenta_con_ayuda=float(np.average(cuenta[m & ayuda], weights=w[m & ayuda])) * 100,
                          cuenta_sin_ayuda=float(np.average(cuenta[m & ~ayuda], weights=w[m & ~ayuda])) * 100))
    Z = np.column_stack([ayuda.astype(float), X.iloc[:, columnas].to_numpy(float)])
    beta, V, G = logit_agrupado(Z, cuenta, w, t["geo_depto"].astype(str).to_numpy())
    eta0 = beta[0] + Z[:, 1:] @ beta[2:]
    cambio = float(np.average(expit(eta0 + beta[1]) - expit(eta0), weights=w))
    tabla = pd.DataFrame(filas)
    tabla["cambio_ajustado_pp"] = cambio * 100
    tabla["p_ajustado"] = float(2 * stats.t.sf(abs(beta[1] / np.sqrt(V[1, 1])), G - 1))
    return tabla


def analisis_posterior(n_jobs: int = 3) -> pd.DataFrame:
    """Lo que se revisó después de ver los resultados; no cambia la decisión."""
    t = pd.read_parquet(TABLA)
    t = t.merge(hogares_con_transferencia(), on=K3 + ["mes"], how="left", validate="1:1")
    X, mapa = matriz(t)
    Xn = X.to_numpy(np.float32)
    w = pd.to_numeric(t["fex"], errors="coerce").to_numpy(float)
    y = t[PRINCIPAL].to_numpy(float)
    urbano = t["geo_zona"].astype(str).eq("1").to_numpy()
    viviendas = t["DIRECTORIO"].astype(str).to_numpy()
    meses = t["mes"].astype(int).to_numpy()
    presupuesto = presupuesto_ab()
    ref = "ficha_derivadas"
    base = especificaciones(PRINCIPAL)[ref]
    credito = ["fin_corriente_cdt", "fin_credito_vivienda", "fin_credito_vehiculo", "fin_libre_inversion", "fin_tarjeta"]
    specs = {ref: base, "+credito": base + credito, "+cuenta": base + ["fin_ahorros", "fin_ninguno"],
             "+credito+estrato": base + credito + ["estrato"],
             "+financiero+estrato": base + GRUPOS["inclusion_financiera"] + ["estrato"]}
    columnas = _columnas(specs, X, mapa)
    pred = predecir_cv(Xn, y, w, columnas, particion_por_grupo(viviendas, N_FOLDS), "logistica", n_jobs)
    _, deltas = comparar(pred, y, w, urbano, viviendas, presupuesto, [(s, ref) for s in specs if s != ref])
    prueba = np.flatnonzero(meses > 6)
    temporal = {s: metricas(y[prueba], _ajustar("logistica", Xn, y, w, c, np.flatnonzero(meses <= 6), prueba), w[prueba],
                            urbano[prueba], presupuesto)["exclusion"] for s, c in columnas.items()}
    deltas["d_exclusion_temporal"] = deltas["modelo"].map({s: temporal[s] - temporal[ref] for s in specs})

    fichas = _columnas({ref: base}, X, mapa)[ref]
    transferencias = cuenta_segun_transferencia(t, X, mapa, w, fichas)
    programas = {c: float(np.average(t[c].eq(True), weights=w)) * 100
                 for c in ("ayuda_gobierno", "familias_en_accion", "jovenes_en_accion", "colombia_mayor")}

    # LASSO con penalización fuerte: con el C elegido por validación casi nada se elimina.
    from joblib import Parallel, delayed

    _, inv = np.unique(viviendas, return_inverse=True)
    variable = np.array([mapa[c] for c in X.columns])
    lasso = {}
    for C in (1e-3, 1e-4):
        betas = np.array(Parallel(n_jobs=n_jobs)(delayed(_lasso_coef)(Xn, y, w, C, s, inv) for s in range(30)))
        lasso[f"frecuencia_C_{C:g}"] = pd.Series((betas != 0).mean(axis=0), index=X.columns).groupby(variable).max()
    lasso = pd.DataFrame(lasso)
    grupo = {c: g for g, cs in GRUPOS.items() for c in cs}
    lasso["grupo"] = [grupo.get(v, "referencia") for v in lasso.index]
    lasso = lasso.rename_axis("variable").reset_index().sort_values(list(lasso.columns[:2])[::-1], ascending=False)

    deltas.to_csv(OUT_POSTERIOR, index=False)
    transferencias.to_csv(OUT_TRANSFERENCIAS, index=False)
    lasso.to_csv(OUT_LASSO, index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 200)
    print("\n=== Análisis posterior: aporte de cuenta y crédito (diferencias en puntos porcentuales) ===")
    d = deltas[deltas["metrica"].isin(["exclusion", "auc", "exclusion_urbano", "exclusion_rural"])].copy()
    d[["delta", "ic_lo", "ic_hi", "d_exclusion_temporal"]] *= 100
    print(d.round(3).to_string(index=False))
    print("\n=== % de hogares que declara transferencia ===")
    print({k: round(v, 2) for k, v in programas.items()})
    print("\n=== % con cuenta de ahorros según transferencia ===")
    print(transferencias.round(4).to_string(index=False))
    print("\n=== LASSO estricto: frecuencia de selección en 30 mitades de la muestra ===")
    print(lasso.round(3).to_string(index=False))
    return deltas


def presupuesto_ab() -> float:
    """Fracción de hogares (ponderada) en los grupos A y B: el presupuesto con
    el que se compara, igual para todos los modelos. Solo se usa su tamaño."""
    m = pd.read_parquet(MUESTRA, columns=["Grupo_hotdeck", "fex"])
    w = pd.to_numeric(m["fex"], errors="coerce")
    return float(w[m["Grupo_hotdeck"].isin(["A", "B"])].sum() / w.sum())


def main(n_jobs: int = 3) -> pd.DataFrame:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if TABLA.exists():
        t = pd.read_parquet(TABLA)
    else:
        t = construir_tabla()
        t.to_parquet(TABLA, index=False)
    logger.info("Tabla: %s hogares", f"{len(t):,}")
    X, mapa = matriz(t)
    Xn = X.to_numpy(np.float32)
    w_todo = pd.to_numeric(t["fex"], errors="coerce").to_numpy(float)
    viviendas_todo = t["DIRECTORIO"].astype(str).to_numpy()
    deptos_todo = t["geo_depto"].astype(str).to_numpy()
    urbano_todo = t["geo_zona"].astype(str).eq("1").to_numpy()
    meses_todo = t["mes"].astype(int).to_numpy()
    ref = "ficha_derivadas"
    presupuesto = presupuesto_ab()

    metricas_todas, deltas_todos, signif_todas, grupos_todos = [], [], [], []
    for outcome in OUTCOMES:
        ok = t[outcome].notna().to_numpy()
        y, w, viviendas = t.loc[ok, outcome].to_numpy(float), w_todo[ok], viviendas_todo[ok]
        urbano, deptos = urbano_todo[ok], deptos_todo[ok]
        Xo, Xdf = Xn[ok], X[ok]
        specs = especificaciones(outcome)
        columnas = _columnas(specs, X, mapa)
        pliegues = particion_por_grupo(viviendas, N_FOLDS)
        modelos = ["logistica", "boosting"] if outcome == PRINCIPAL else ["logistica"]
        for tipo in modelos:
            logger.info("%s, %s: %d modelos", outcome, tipo, len(columnas))
            usar = columnas if tipo == "logistica" else {s: c for s, c in columnas.items() if not s.startswith("todo-")}
            pred = predecir_cv(Xo, y, w, usar, pliegues, tipo, n_jobs)
            pares = [(s, ref) for s in usar if s != ref]
            pares += [("todo", s) for s in usar if s.startswith("todo-")]  # aporte con los demás grupos presentes
            met, delt = comparar(pred, y, w, urbano, viviendas, presupuesto, pares)
            metricas_todas.append(met.assign(outcome=outcome, tipo=tipo))
            deltas_todos.append(delt.assign(outcome=outcome, tipo=tipo))
        logger.info("%s: significancia", outcome)
        s, g = significancia(Xdf, y, w, deptos, mapa, columnas["todo"])
        signif_todas.append(s.assign(outcome=outcome))
        grupos_todos.append(g.assign(outcome=outcome))

    metricas_t = pd.concat(metricas_todas, ignore_index=True)
    deltas_t = pd.concat(deltas_todos, ignore_index=True)
    signif_t = pd.concat(signif_todas, ignore_index=True)
    grupos_t = pd.concat(grupos_todos, ignore_index=True)

    # Robustez, solo con el resultado principal: meses y departamentos no vistos.
    y, w = t[PRINCIPAL].to_numpy(float), w_todo
    specs = {k: v for k, v in especificaciones(PRINCIPAL).items() if k == ref or k.startswith("+") or k == "todo"}
    columnas = _columnas(specs, X, mapa)
    logger.info("Robustez: meses y departamentos no vistos")
    prueba = np.flatnonzero(meses_todo > 6)
    pred_t = {s: _ajustar("logistica", Xn, y, w, c, np.flatnonzero(meses_todo <= 6), prueba) for s, c in columnas.items()}
    temporal = pd.DataFrame({s: metricas(y[prueba], p, w[prueba], urbano_todo[prueba], presupuesto)
                             for s, p in pred_t.items()}).T
    pred_d = predecir_cv(Xn, y, w, _columnas(specs, X, mapa, sin={"geo_depto"}), particion_por_grupo(deptos_todo, N_FOLDS),
                         "logistica", n_jobs)
    por_depto = pd.DataFrame({s: metricas(y, p, w, urbano_todo, presupuesto) for s, p in pred_d.items()}).T

    logger.info("LASSO, Ridge y SHAP")
    sel, c_lasso = seleccion(X, y, w, viviendas_todo, mapa, n_jobs)

    principal = deltas_t[(deltas_t["outcome"] == PRINCIPAL) & (deltas_t["tipo"] == "logistica")]

    def delta(modelo: str, metrica: str, referencia: str = ref) -> pd.Series:
        return principal[(principal["modelo"] == modelo) & (principal["referencia"] == referencia)
                         & (principal["metrica"] == metrica)].iloc[0]

    grupos_p = grupos_t[grupos_t["outcome"] == PRINCIPAL].set_index("grupo")
    decisiones = []
    for g in GRUPOS:
        modelo = f"+{g}"
        ex, au = delta(modelo, "exclusion"), delta(modelo, "auc")
        fila = dict(grupo=g, wald_holm=grupos_p.loc[g, "wald_holm"], d_exclusion=ex["delta"], d_exclusion_lo=ex["ic_lo"],
                    d_exclusion_hi=ex["ic_hi"], d_auc=au["delta"], d_auc_lo=au["ic_lo"], d_auc_hi=au["ic_hi"],
                    d_inclusion=delta(modelo, "inclusion")["delta"],
                    d_exclusion_urbano=delta(modelo, "exclusion_urbano")["delta"],
                    d_exclusion_rural=delta(modelo, "exclusion_rural")["delta"],
                    d_exclusion_temporal=temporal.loc[modelo, "exclusion"] - temporal.loc[ref, "exclusion"],
                    d_exclusion_depto=por_depto.loc[modelo, "exclusion"] - por_depto.loc[ref, "exclusion"],
                    d_exclusion_sin_grupo=delta("todo", "exclusion", f"todo-{g}")["delta"])
        fila["decision"] = decidir(fila)
        decisiones.append(fila)
    decision = pd.DataFrame(decisiones).sort_values("d_exclusion")

    REPORTES.mkdir(parents=True, exist_ok=True)
    metricas_t.to_csv(OUT_METRICAS, index=False)
    deltas_t.to_csv(OUT_DELTAS, index=False)
    signif_t.to_csv(OUT_SIGNIFICANCIA, index=False)
    grupos_t.to_csv(OUT_GRUPOS, index=False)
    sel.to_csv(OUT_SELECCION, index=False)
    decision.to_csv(OUT_DECISION, index=False)

    pd.set_option("display.width", 250, "display.max_columns", 40, "display.max_rows", 200)
    print(f"\n=== Variables candidatas: {len(t):,} hogares, presupuesto {presupuesto:.1%}, C del LASSO {c_lasso} ===")
    print(metricas_t.round(4).to_string(index=False))
    print("\n=== Decisión por grupo (resultado principal) ===")
    print(decision.round(4).to_string(index=False))
    print("\n=== Significancia por variable ===")
    print(signif_t.round(4).to_string(index=False))
    print("\n=== Wald por grupo ===")
    print(grupos_t.round(4).to_string(index=False))
    print("\n=== LASSO, Ridge y SHAP ===")
    print(sel.round(4).to_string(index=False))
    return decision


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if "posterior" not in sys.argv:
        main(n)
    analisis_posterior(n)
