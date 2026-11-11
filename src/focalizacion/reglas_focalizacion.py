"""P3/OE3: ¿cuánto se reducirían los errores de inclusión y exclusión y la
brecha de pobreza (FGT1) con reglas de focalización informadas por los
efectos heterogéneos, frente a la clasificación vigente?

Con los datos actuales el efecto del Sisbén no está identificado (P2,
`docs/resultados/3_simulacion/SIMULACION_SEMISINTETICA.md`), así que el OE3 se responde
sobre el mismo mundo semisintético: **hogares, ingresos y líneas de
pobreza reales** de GEIH 2024 y un programa con efecto conocido tau(X)
(el de `src/simulacion/`). Las cifras son simuladas: dicen
qué regla funcionaría mejor si el efecto fuera ese, no cuánto reduce hoy
la pobreza el Sisbén.

Dos modelos del efecto, porque cambian qué hogares conviene tratar:
  proporcional   +tau en log-ingreso (el de P2): da más pesos a quien más
                 tiene, y nada a un hogar sin ingreso
  monto_fijo     una transferencia de tau líneas de pobreza por persona
                 (≈9,5 % de la línea en promedio), como un subsidio en
                 dinero

Dos presupuestos (columna `presupuesto`):
  hogares   todas las reglas tratan el mismo número de hogares: los que la
            clasificación vigente imputada deja en A/B en la muestra
  dinero    solo con monto fijo: todas gastan lo mismo que la vigente
            (transferencia × línea × personas, expandida con `fex`). Las
            reglas que ordenan por reducción esperada de la brecha ordenan
            por reducción por peso; la ideal también (aproximación voraz,
            no la óptima exacta). Usa su propio generador aleatorio: las
            cifras del presupuesto en hogares no cambian al agregarlo.
`gasto_rel` = dinero de la regla / dinero de la vigente; con efecto
proporcional el gasto es el aumento del ingreso de la unidad de gasto.

  vigente_hotdeck        grupos A/B imputados por Hot-Deck (información de
                         celda; el Sisbén real usa datos del hogar, ver
                         la limitación en el documento de resultados)
  aleatoria              referencia
  pmt_ingreso            proxy de medios: menor ingreso predicho con
                         variables observables del hogar (la lógica del
                         Sisbén IV)
  pmt_brecha             mayor reducción esperada de la brecha con efecto
                         constante (ATE)
  pmt_brecha_cate        mayor reducción esperada con el CATE de un
                         Causal Forest entrenado con el tratamiento
                         verdadero (vínculo hogar por hogar)
  pmt_brecha_cate_hd     igual, con el Causal Forest entrenado con el
                         tratamiento imputado por Hot-Deck (lo que se
                         puede hacer hoy)
  ideal                  ingreso y efecto verdaderos (no factible: techo)

La reducción esperada de la brecha de un hogar es E[g(Y) − g(Y después)],
con Y = log-ingreso predicho por el proxy de medios + su residuo,
g = max(0, 1 − ingreso/línea). Se promedia sobre los cuantiles empíricos
del residuo, no sobre una normal: los hogares con ingreso 0 dan
residuos extremos que inflarían una desviación estándar.

Métricas sobre personas (`fex` × personas de la unidad de gasto),
pobreza medida antes de la transferencia:
  error de inclusión = tratados no pobres / tratados
  error de exclusión = pobres no tratados / pobres
  FGT0 y FGT1 después de la transferencia
  % del ideal = reducción de FGT1 de la regla / reducción de la ideal

Las repeticiones corren en lotes hasta que el error estándar Monte
Carlo de cada métrica queda bajo el umbral (como en la evaluación
semisintética) y se reanudan si se interrumpen.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.reglas_focalizacion [n_jobs]
Salidas:
    docs/reports/reglas_focalizacion.csv (cada repetición)
    docs/reports/reglas_focalizacion_resumen.csv
"""
from __future__ import annotations

import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from src.simulacion import contrato
from src.simulacion.asignacion import asignar
from src.simulacion.base import celdas_por_nivel, preparar_base
from src.simulacion.escenarios import ESCENARIOS, TAU
from src.simulacion.estimadores import estimacion5
from src.simulacion.evaluacion import HOGARES, REGISTRO, p_t_por_celda
from src.simulacion.reportes import NOTA_SIMULADO, marcar_simulado, sin_marca
from src.simulacion.vinculo import sortear_donante

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/reglas_focalizacion.csv")
OUT_RESUMEN = Path("docs/reports/reglas_focalizacion_resumen.csv")
OUT_FIRMA = Path("docs/reports/reglas_focalizacion_config.json")
SEED = 2027
N_EVAL, N_ENTRENA = 30_000, 30_000
ESCENARIO = "confusion_observada"  # asignación del mundo donde se entrena el Causal Forest

# Proxy de medios: variables observables del hogar, nunca el ingreso.
PMT_CATEGORICAS = ["celda", "viv_paredes", "viv_acueducto", "viv_alcantarillado", "jefe_sexo", "geo_zona"]
PMT_NUMERICAS = ["hog_num_personas", "viv_cuartos", "analfabetismo", "bajo_logro_educativo_jefe",
                 "inasistencia_escolar_menores", "sin_aseguramiento_salud", "sin_cotizacion_pension_jefe",
                 "hacinamiento"]
REGLAS = ["vigente_hotdeck", "aleatoria", "pmt_ingreso", "pmt_brecha", "pmt_brecha_cate", "pmt_brecha_cate_hd", "ideal"]
METRICAS = ["error_inclusion", "error_exclusion", "fgt0_post", "fgt1_post", "reduccion_fgt1", "pct_ideal", "gasto_rel"]
UMBRAL_MCSE = {"error_inclusion": 0.002, "error_exclusion": 0.002, "fgt0_post": 0.001, "fgt1_post": 0.0005,
               "reduccion_fgt1": 0.0002, "pct_ideal": 0.5, "gasto_rel": 0.005}
MIN_REPS, MAX_REPS, LOTE = 30, 300, 12
TIPOS_EFECTO = ("proporcional", "monto_fijo")
PRESUPUESTOS = ("hogares", "dinero")  # dinero: solo con monto fijo (el costo se conoce antes de asignar)
REGLAS_POR_REDUCCION = ("pmt_brecha", "pmt_brecha_cate", "pmt_brecha_cate_hd", "ideal")
# Modificadores sin orden que pueden llegar en `x_cols`: indicadoras en los modelos auxiliares.
X_CATEGORICAS_EXTRA = ("het_depto",)


# --------------------------------------------------------------------------
# Base
# --------------------------------------------------------------------------

def preparar(df: pd.DataFrame, p_t_celda: pd.Series) -> pd.DataFrame:
    """La base del generador semisintético más las variables del proxy de
    medios, el grupo vigente imputado y el peso por personas."""
    df = df.reset_index(drop=True)  # faltantes en columnas canónicas: los rechaza el contrato
    b = preparar_base(df, p_t_celda)
    assert len(b) == len(df), "preparar_base descartó filas: los índices dejarían de coincidir"
    for c in PMT_NUMERICAS:
        b[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(float)
    for c in ["viv_acueducto", "viv_alcantarillado", "jefe_sexo", "geo_zona"]:
        b[c] = df[c].astype(str)
    b["vigente_ab"] = df["Grupo_hotdeck"].isin(["A", "B"]).astype(int).to_numpy()
    b["fex"] = pd.to_numeric(df["fex"], errors="coerce").fillna(0).to_numpy(float)
    b["personas"] = pd.to_numeric(df["personas_ug"], errors="coerce").fillna(1).to_numpy(float)
    b["peso"] = b["fex"] * b["personas"]
    b["lp"] = np.expm1(b["log_lp"])  # línea de pobreza del dominio, en pesos
    return b


# --------------------------------------------------------------------------
# Piezas de las reglas
# --------------------------------------------------------------------------

def ingreso_relativo(y: np.ndarray, lp: np.ndarray) -> np.ndarray:
    """Ingreso per cápita en líneas de pobreza: x = (e^y − 1) / línea."""
    return np.expm1(y) / lp


def brecha(x: np.ndarray) -> np.ndarray:
    """Brecha de pobreza normalizada: max(0, 1 − x)."""
    return np.clip(1 - x, 0, None)


def despues(y0: np.ndarray, efecto: np.ndarray, lp: np.ndarray, tipo: str) -> np.ndarray:
    """Ingreso relativo después del programa. `proporcional`: el efecto de
    P2, +tau en log-ingreso (más pesos a quien más tiene; un hogar sin
    ingreso no gana nada). `monto_fijo`: una transferencia de tau líneas
    de pobreza por persona (≈9,5 % de la línea en promedio)."""
    if tipo == "proporcional":
        return ingreso_relativo(y0 + efecto, lp)
    return ingreso_relativo(y0, lp) + efecto


def reduccion_esperada(media: np.ndarray, residuos: np.ndarray, efecto: np.ndarray, lp: np.ndarray,
                       tipo: str) -> np.ndarray:
    """E[g(Y) − g(Y después)] con Y = media + residuo, promediando sobre la
    distribución empírica de los residuos del proxy de medios (no se supone
    normalidad: hay hogares con ingreso 0 que dan residuos extremos)."""
    y = media[:, None] + residuos[None, :]
    lp2, ef2 = lp[:, None], np.asarray(efecto, float)[:, None]
    return (brecha(ingreso_relativo(y, lp2)) - brecha(despues(y, ef2, lp2, tipo))).mean(axis=1)


def ajustar_pmt(entrena: pd.DataFrame, n_cuantiles: int = 41):
    """Ridge del log-ingreso sobre las variables observables; devuelve el
    modelo y los cuantiles de su residuo en la muestra de entrenamiento."""
    cod = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), PMT_CATEGORICAS),
                             ("num", "passthrough", PMT_NUMERICAS)])
    modelo = make_pipeline(cod, Ridge(alpha=1.0))
    modelo.fit(entrena[PMT_CATEGORICAS + PMT_NUMERICAS], entrena["y0"])
    resid = entrena["y0"] - modelo.predict(entrena[PMT_CATEGORICAS + PMT_NUMERICAS])
    return modelo, np.quantile(resid, (np.arange(n_cuantiles) + 0.5) / n_cuantiles)


def ajustar_bosque(d: pd.DataFrame, y: np.ndarray, t: np.ndarray, x_cols: list[str] | None = None):
    """CausalForestDML con los modelos auxiliares de `5_estimacion.py`
    (W = celda exacta; X = zona, sexo del jefe y paredes, o `x_cols`),
    como en la evaluación semisintética. Devuelve el modelo ajustado."""
    from econml.dml import CausalForestDML
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.pipeline import make_pipeline

    est5 = estimacion5()
    x_cols = list(x_cols or est5.X_COLS)
    w_cols = est5.W_CELDA[0]
    # econml pasa [X, W] a los modelos auxiliares y el codificador ubica las
    # columnas por posición: se arma con las X que de verdad se pasan. Con
    # el codificador de `5_estimacion.py` (pensado para sus 3 X), un X más
    # largo dejaba la celda (el confusor) fuera de los modelos auxiliares.
    columnas = x_cols + w_cols
    categoricas = [c for c in x_cols if c in {*est5.X_CATEGORICAS, *X_CATEGORICAS_EXTRA}] + w_cols
    modelo_y = make_pipeline(est5._codificador(columnas, categoricas, []), Ridge(alpha=est5.ALPHA_Y))
    modelo_t = make_pipeline(est5._codificador(columnas, categoricas, []), LogisticRegression(C=est5.C_T, max_iter=2000))
    m = CausalForestDML(model_y=modelo_y, model_t=modelo_t, discrete_treatment=True, n_estimators=200,
                        min_samples_leaf=50, random_state=SEED, n_jobs=1)
    m.fit(y, t, X=d[x_cols].to_numpy(float), W=d[w_cols].to_numpy(float))
    return m


def elegir(puntaje: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Trata a los k hogares de mayor puntaje (empates al azar)."""
    orden = np.lexsort((rng.random(len(puntaje)), -np.asarray(puntaje, float)))
    t = np.zeros(len(puntaje), dtype=int)
    t[orden[:k]] = 1
    return t


def costo(d: pd.DataFrame, tipo: str) -> np.ndarray:
    """Pesos al mes que recibe cada hogar si se trata. Monto fijo: tau
    líneas por persona. Proporcional: lo que sube el ingreso de la unidad
    de gasto (solo se conoce después: sirve para medir, no para asignar)."""
    tau, lp, personas = d["tau"].to_numpy(), d["lp"].to_numpy(), d["personas"].to_numpy()
    if tipo == "monto_fijo":
        return tau * lp * personas
    return np.expm1(d["y0"].to_numpy()) * personas * np.expm1(tau)


def elegir_por_dinero(puntaje: np.ndarray, costo_hogar: np.ndarray, presupuesto: float,
                      rng: np.random.Generator) -> np.ndarray:
    """Trata en orden de puntaje (empates al azar) mientras el gasto
    acumulado no pase del presupuesto. `costo_hogar` ya va expandido."""
    orden = np.lexsort((rng.random(len(puntaje)), -np.asarray(puntaje, float)))
    t = np.zeros(len(puntaje), dtype=int)
    t[orden[np.cumsum(costo_hogar[orden]) <= presupuesto * (1 + 1e-9)]] = 1  # tolera el redondeo de la suma
    return t


def metricas(d: pd.DataFrame, t: np.ndarray, tipo: str) -> dict:
    """Errores de focalización y pobreza después del programa, sobre
    personas; la pobreza se mide antes del programa."""
    w = d["peso"].to_numpy()
    lp = d["lp"].to_numpy()
    y0 = d["y0"].to_numpy()
    pobre = (ingreso_relativo(y0, lp) < 1).astype(float)
    x1 = despues(y0, d["tau"].to_numpy() * t, lp, tipo)
    return dict(
        error_inclusion=float(np.sum(w * t * (1 - pobre)) / max(np.sum(w * t), 1e-12)),
        error_exclusion=float(np.sum(w * pobre * (1 - t)) / max(np.sum(w * pobre), 1e-12)),
        fgt0_post=float(np.average(x1 < 1, weights=w)),
        fgt1_post=float(np.average(brecha(x1), weights=w)),
    )


# --------------------------------------------------------------------------
# Una repetición
# --------------------------------------------------------------------------

def una_repeticion(b: pd.DataFrame, rep: int, x_cols: list[str] | None = None) -> list[dict]:
    """Una repetición: reglas con presupuesto en hogares (los dos modelos
    del efecto) y en dinero (monto fijo). `x_cols`: modificadores del
    efecto que ve el Causal Forest (por defecto, los de `5_estimacion.py`)."""
    rng = np.random.default_rng([SEED, rep])
    rng_dinero = np.random.default_rng([SEED, rep, 1])  # aparte: no altera el presupuesto en hogares
    idx = rng.permutation(len(b))
    ev = b.iloc[idx[:N_EVAL]].reset_index(drop=True)                      # donde se aplican las reglas
    en = b.iloc[idx[N_EVAL:N_EVAL + N_ENTRENA]].reset_index(drop=True)    # encuesta de entrenamiento (X, Y)
    reg = idx[N_EVAL + N_ENTRENA:]                                         # registro (X, T), sin llave común
    k = int(ev["vigente_ab"].sum())

    # Proxy de medios, entrenado fuera de la muestra de evaluación.
    pmt, residuos = ajustar_pmt(en)
    media = pmt.predict(ev[PMT_CATEGORICAS + PMT_NUMERICAS])

    # El mundo semisintético: T verdadero y T por Hot-Deck (donante de la celda).
    t_mundo, _, _ = asignar(b, ESCENARIOS[ESCENARIO], rng)
    t_en = t_mundo[idx[N_EVAL:N_EVAL + N_ENTRENA]]
    niveles = celdas_por_nivel(b)
    donante = reg[sortear_donante(niveles[idx[N_EVAL:N_EVAL + N_ENTRENA]], niveles[reg], rng)]
    x_cols = x_cols or estimacion5().X_COLS
    y0_en, tau_en, lp_en = en["y0"].to_numpy(), en["tau"].to_numpy(), en["lp"].to_numpy()
    w_hogar = ev["fex"].to_numpy()

    filas = []
    for tipo in TIPOS_EFECTO:
        # Resultado observado en las unidades del efecto: log-ingreso, o
        # ingreso en líneas (recortado en 10 líneas solo para entrenar).
        if tipo == "proporcional":
            y_en = y0_en + tau_en * t_en
        else:
            y_en = np.minimum(ingreso_relativo(y0_en, lp_en), 10) + tau_en * t_en
        cate = {}
        for nombre, t in [("verdadero", t_en), ("hotdeck", t_mundo[donante])]:
            bosque = ajustar_bosque(en, y_en, t, x_cols)
            cate[nombre] = (float(bosque.ate(en[x_cols].to_numpy(float))),
                            np.ravel(bosque.effect(ev[x_cols].to_numpy(float))))

        lp, y0, tau = ev["lp"].to_numpy(), ev["y0"].to_numpy(), ev["tau"].to_numpy()

        def esperada(ef):
            return reduccion_esperada(media, residuos, ef, lp, tipo)

        puntajes = {
            "vigente_hotdeck": ev["vigente_ab"].to_numpy(float),
            "aleatoria": rng.random(len(ev)),
            "pmt_ingreso": -media,
            "pmt_brecha": esperada(np.full(len(ev), cate["verdadero"][0])),
            "pmt_brecha_cate": esperada(cate["verdadero"][1]),
            "pmt_brecha_cate_hd": esperada(cate["hotdeck"][1]),
            "ideal": brecha(ingreso_relativo(y0, lp)) - brecha(despues(y0, tau, lp, tipo)),
        }
        base = metricas(ev, np.zeros(len(ev), dtype=int), tipo)
        gasto_hogar = w_hogar * costo(ev, tipo)
        comunes = dict(rep=rep, efecto=tipo, fgt0_pre=base["fgt0_post"], fgt1_pre=base["fgt1_post"],
                       ate_cf_verdadero=cate["verdadero"][0], ate_cf_hotdeck=cate["hotdeck"][0],
                       pehe_cf_verdadero=float(np.sqrt(np.mean((cate["verdadero"][1] - tau) ** 2))),
                       pehe_cf_hotdeck=float(np.sqrt(np.mean((cate["hotdeck"][1] - tau) ** 2))),
                       sd_tau=float(tau.std()))
        elegidos = {regla: elegir(puntajes[regla], k, rng) for regla in REGLAS}
        gasto_vigente = float(gasto_hogar @ elegidos["vigente_hotdeck"])
        bloques = [("hogares", elegidos)]
        if tipo == "monto_fijo":
            # Mismo dinero: ordenar por reducción por peso en las reglas que estiman la reducción.
            por_peso = {r: puntajes[r] * ev["peso"].to_numpy() / np.maximum(gasto_hogar, 1e-9)
                        if r in REGLAS_POR_REDUCCION else puntajes[r] for r in REGLAS}
            bloques.append(("dinero", {r: elegir_por_dinero(por_peso[r], gasto_hogar, gasto_vigente, rng_dinero)
                                       for r in REGLAS}))
        for presupuesto, ts in bloques:
            filas_bloque = []
            for regla in REGLAS:
                m = metricas(ev, ts[regla], tipo)
                filas_bloque.append(dict(comunes, presupuesto=presupuesto, regla=regla, k=int(ts[regla].sum()), **m,
                                         reduccion_fgt1=base["fgt1_post"] - m["fgt1_post"],
                                         gasto_rel=float(gasto_hogar @ ts[regla]) / gasto_vigente))
            ideal = next(f["reduccion_fgt1"] for f in filas_bloque if f["regla"] == "ideal")
            for f in filas_bloque:
                f["pct_ideal"] = 100 * f["reduccion_fgt1"] / ideal
            filas += filas_bloque
    return filas


# --------------------------------------------------------------------------
# Resumen y convergencia
# --------------------------------------------------------------------------

CLAVES = ["efecto", "presupuesto", "regla"]


def resumir(r: pd.DataFrame) -> pd.DataFrame:
    g = r.groupby(CLAVES, sort=False)
    out = g[METRICAS].mean()
    mcse = g[METRICAS].std().div(np.sqrt(g.size()), axis=0).add_prefix("mcse_")
    out = pd.concat([out, mcse], axis=1)
    out.insert(0, "reps", g.size())
    return out.reset_index()


def pendientes(res: pd.DataFrame) -> list[str]:
    return [f"{fila['efecto']}/{fila['presupuesto']}/{fila['regla']}:{m}" for _, fila in res.iterrows() for m in METRICAS
            if fila[f"mcse_{m}"] > UMBRAL_MCSE[m] and not (fila["regla"] == "ideal" and m == "pct_ideal")]


def firma(**extra) -> str:
    cfg = dict(SEED=SEED, N_EVAL=N_EVAL, N_ENTRENA=N_ENTRENA, ESCENARIO=ESCENARIO, PMT_CATEGORICAS=PMT_CATEGORICAS,
               PMT_NUMERICAS=PMT_NUMERICAS, REGLAS=REGLAS, TAU=TAU, TIPOS_EFECTO=TIPOS_EFECTO,
               PRESUPUESTOS=PRESUPUESTOS, version=4, **extra)  # 3: cadena de respaldos; 4: presupuesto en dinero
    return hashlib.sha1(json.dumps(cfg, sort_keys=True).encode()).hexdigest()[:12]


def cargar_base() -> tuple[pd.DataFrame, pd.DataFrame]:
    """La tabla de trabajo de las reglas y la tabla de hogares de origen."""
    columnas = list(dict.fromkeys([*contrato.columnas("hogares"), "Grupo_hotdeck", "fex", "personas_ug", *PMT_NUMERICAS,
                                   "viv_acueducto", "viv_alcantarillado"]))
    p_t = p_t_por_celda(pd.read_parquet(REGISTRO, columns=contrato.columnas("registro")))
    df = pd.read_parquet(HOGARES, columns=columnas)
    b = preparar(df, p_t)
    logger.info("Base: %s hogares reales | A/B vigente %.1f %% de los hogares", f"{len(b):,}", 100 * b["vigente_ab"].mean())
    return b, df


def correr(b: pd.DataFrame, salida: Path, salida_resumen: Path, salida_firma: Path, firma_cfg: str, n_jobs: int,
           x_cols: list[str] | None = None) -> pd.DataFrame:
    """Repite en lotes hasta la convergencia (o el máximo), reanudando lo
    guardado si la configuración no cambió. Devuelve cada repetición."""
    from joblib import Parallel, delayed, parallel_config

    r = sin_marca(pd.read_csv(salida)) if (salida.exists() and salida_firma.exists()
                                 and json.loads(salida_firma.read_text()).get("firma") == firma_cfg) else pd.DataFrame()
    if r.empty:
        salida_firma.write_text(json.dumps(dict(firma=firma_cfg)))
    else:
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())

    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        if hechas >= MAX_REPS or (hechas >= MIN_REPS and not pendientes(resumir(r))):
            break
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep, x_cols)
                                             for rep in range(hechas, hechas + LOTE))
        r = pd.concat([r, pd.DataFrame([f for p in partes for f in p])], ignore_index=True)
        marcar_simulado(r).to_csv(salida, index=False)
        logger.info("Lote reps %d-%d en %.0f s | métricas sin converger: %d", hechas, hechas + LOTE - 1,
                    time.time() - t0, len(pendientes(resumir(r))))
    marcar_simulado(resumir(r)).to_csv(salida_resumen, index=False)
    return r


def imprimir(r: pd.DataFrame, titulo: str) -> None:
    res = resumir(r)
    pd.set_option("display.width", 250)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== {titulo}*: {r['rep'].nunique()} repeticiones, evaluación en {N_EVAL:,} hogares reales; "
          f"presupuesto = hogares A/B vigentes ({r.loc[r['regla'] == 'vigente_hotdeck', 'k'].mean():,.0f} por muestra) "
          f"o su mismo dinero ===")
    print(f"Sin programa: FGT0 {r['fgt0_pre'].mean():.4f} | FGT1 {r['fgt1_pre'].mean():.4f}")
    for tipo, g in r[r["presupuesto"] == "hogares"].groupby("efecto", sort=False):
        print(f"Causal Forest ({tipo}): ATE con T verdadero {g['ate_cf_verdadero'].mean():+.4f}, con T por Hot-Deck "
              f"{g['ate_cf_hotdeck'].mean():+.4f}; PEHE {g['pehe_cf_verdadero'].mean():.4f} y "
              f"{g['pehe_cf_hotdeck'].mean():.4f} frente a una desviación de tau de {g['sd_tau'].mean():.4f}")
    for (tipo, presupuesto), g in res.groupby(["efecto", "presupuesto"], sort=False):
        print(f"\n--- Efecto {tipo}, presupuesto en {presupuesto}")
        print(g.drop(columns=["efecto", "presupuesto"]).round(4).to_string(index=False))
    p = pendientes(res)
    print(f"\nConvergencia: {'alcanzada' if not p else 'NO alcanzada: ' + ', '.join(p)}")


def main(n_jobs: int = 3) -> pd.DataFrame:
    b, _ = cargar_base()
    r = correr(b, OUT, OUT_RESUMEN, OUT_FIRMA, firma(), n_jobs)
    imprimir(r, "Reglas de focalización (OE3)")
    print(f"Guardado: {OUT}\nGuardado: {OUT_RESUMEN}")
    return resumir(r)


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
