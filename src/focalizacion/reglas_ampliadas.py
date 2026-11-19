"""Reglas de focalización ampliadas (fase 3 de
`docs/metodologia/METODOLOGIA_FHDI.md`): el Causal Forest dentro de la
celda y el enlace fraccional (FHDI) en las reglas del OE3, junto a las
vigentes, que no cambian.

`reglas_focalizacion.py` no se toca: este módulo repite sus sorteos
(mismas muestras, mismo mundo semisintético, mismo donante del Hot-Deck)
y agrega solo las reglas nuevas, que eligen con su propio generador
aleatorio. Control: `vigente_hotdeck`, `pmt_ingreso` e `ideal` se
recalculan y deben coincidir con la corrida vigente repetición por
repetición (la corrida imprime la diferencia máxima).

Reglas nuevas:
  vigente_fhdi               la clasificación vigente con el enlace
                             fraccional: cada hogar cuenta con su
                             probabilidad de estar en A/B según su celda
                             (`fhdi_p_AB` de `geih_sisben_fhdi_2024.parquet`)
                             en vez de un sorteo. Es el valor esperado de
                             la vigente sobre los sorteos del Hot-Deck;
                             trata en promedio el mismo número de hogares
  pmt_brecha_cate_intra      como `pmt_brecha_cate` (T verdadero), con el
                             Causal Forest dentro de la celda (pregunta 8
                             de la sensibilidad): Y, T y controles sin la
                             media de su celda
  pmt_brecha_cate_hd_intra   igual, con T imputado por Hot-Deck
  pmt_brecha_cate_fhdi       el CATE entrenado con T = probabilidad de la
                             celda (FHDI sin vínculo): no identificable,
                             porque T es función de la celda. Se reporta
                             así, sin caer a otra regla

Métricas de `vigente_fhdi`: el valor esperado con tratamiento de Bernoulli
(p) independiente por hogar. Exclusión, FGT0 y FGT1 son exactos; la
inclusión es el cociente de los valores esperados (con miles de hogares
tratados, igual al esperado del cociente hasta el tercer decimal).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.focalizacion.reglas_ampliadas [n_jobs]
Salidas:
    docs/reports/reglas_ampliadas.csv (cada repetición)
    docs/reports/reglas_ampliadas_resumen.csv
    docs/reports/reglas_ampliadas_tablas.md (vigentes y nuevas lado a lado)
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.focalizacion import reglas_focalizacion as rf
from src.simulacion.asignacion import asignar
from src.simulacion.base import celdas_por_nivel, firma_con_datos
from src.simulacion.escenarios import ESCENARIOS
from src.simulacion.reportes import NOTA_SIMULADO, marcar_simulado, sin_marca
from src.simulacion.sensibilidad_semisintetica import _bosque, _intra_celda
from src.simulacion.vinculo import sortear_donante
from src.utils.variables_canonicas import normalizar_llave

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OUT = Path("docs/reports/reglas_ampliadas.csv")
OUT_RESUMEN = Path("docs/reports/reglas_ampliadas_resumen.csv")
OUT_FIRMA = Path("docs/reports/reglas_ampliadas_config.json")
OUT_TABLAS = Path("docs/reports/reglas_ampliadas_tablas.md")
FHDI = Path("data/2_models/geih_sisben_fhdi_2024.parquet")
LLAVES = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]

CONTROL = ("vigente_hotdeck", "pmt_ingreso", "ideal")  # recalculadas: deben dar lo mismo que la vigente
NUEVAS_ORDINALES = ("pmt_brecha_cate_intra", "pmt_brecha_cate_hd_intra")
NUEVAS = ("vigente_fhdi", *NUEVAS_ORDINALES, "pmt_brecha_cate_fhdi")
NO_IDENTIFICABLES = ("pmt_brecha_cate_fhdi",)


# --------------------------------------------------------------------------
# Piezas
# --------------------------------------------------------------------------

def cargar_base() -> pd.DataFrame:
    """La tabla de trabajo de las reglas con la probabilidad A/B de la FHDI
    de cada hogar (el parquet guarda los hogares en el orden de la muestra
    de estimación; se comprueba con las llaves)."""
    b, _ = rf.cargar_base()
    df = pd.read_parquet(rf.HOGARES, columns=LLAVES)  # las mismas filas y el mismo orden que la tabla de trabajo
    f = pd.read_parquet(FHDI, columns=[*LLAVES, "fhdi_p_AB"])
    iguales = all((normalizar_llave(f[c]).to_numpy() == normalizar_llave(df[c]).to_numpy()).all() for c in LLAVES)
    if len(f) != len(df) or not iguales:
        raise ValueError(f"{FHDI} no tiene los hogares de la muestra en el mismo orden")
    b["p_ab_fhdi"] = f["fhdi_p_AB"].to_numpy(float)
    return b


def metricas_fraccionales(d: pd.DataFrame, p: np.ndarray, tipo: str) -> dict:
    """`rf.metricas` en valor esperado cuando cada hogar se trata con
    probabilidad p, independiente. La inclusión es el cociente de valores
    esperados; lo demás es exacto (es lineal en el tratamiento de cada
    hogar)."""
    w, lp, y0 = d["peso"].to_numpy(), d["lp"].to_numpy(), d["y0"].to_numpy()
    p = np.asarray(p, float)
    pobre = (rf.ingreso_relativo(y0, lp) < 1).astype(float)
    x0 = rf.ingreso_relativo(y0, lp)
    x1 = rf.despues(y0, d["tau"].to_numpy(), lp, tipo)
    return dict(
        error_inclusion=float(np.sum(w * p * (1 - pobre)) / max(np.sum(w * p), 1e-12)),
        error_exclusion=float(np.sum(w * pobre * (1 - p)) / max(np.sum(w * pobre), 1e-12)),
        fgt0_post=float(np.average(p * (x1 < 1) + (1 - p) * (x0 < 1), weights=w)),
        fgt1_post=float(np.average(p * rf.brecha(x1) + (1 - p) * rf.brecha(x0), weights=w)),
    )


def bosque_intra_celda(en: pd.DataFrame, y: np.ndarray, t: np.ndarray, ev: pd.DataFrame) -> tuple[float, np.ndarray]:
    """Causal Forest dentro de la celda (`sensibilidad_semisintetica`,
    pregunta 8) entrenado en `en`; devuelve su ATE en `en` y el CATE en
    los hogares de `ev` (la celda solo entra al quitar medias: el CATE
    depende de X)."""
    yd, td, W, X, modelo, _ = _intra_celda(en, y, t)
    m = _bosque(modelo(), modelo(), discreto=False)
    m.fit(yd, td, X=X, W=W)
    x_ev = ev[rf.estimacion5().X_COLS].to_numpy(float)
    return float(m.ate(X)), np.ravel(m.effect(x_ev))


# --------------------------------------------------------------------------
# Una repetición
# --------------------------------------------------------------------------

def una_repeticion(b: pd.DataFrame, rep: int) -> list[dict]:
    """Las reglas nuevas y las de control en la repetición `rep` de
    `rf.una_repeticion`, con sus mismos sorteos. Los modificadores X son
    los de `5_estimacion.py` (los de la corrida vigente)."""
    rng = np.random.default_rng([rf.SEED, rep])
    rng_dinero = np.random.default_rng([rf.SEED, rep, 1])
    rng_nuevo = np.random.default_rng([rf.SEED, rep, 3])         # las reglas nuevas no mueven a las demás
    rng_nuevo_dinero = np.random.default_rng([rf.SEED, rep, 4])
    n_ev, n_en = rf.N_EVAL, rf.N_ENTRENA
    idx = rng.permutation(len(b))
    ev = b.iloc[idx[:n_ev]].reset_index(drop=True)
    en = b.iloc[idx[n_ev:n_ev + n_en]].reset_index(drop=True)
    reg = idx[n_ev + n_en:]
    k = int(ev["vigente_ab"].sum())

    pmt, residuos = rf.ajustar_pmt(en)
    media = pmt.predict(ev[rf.PMT_CATEGORICAS + rf.PMT_NUMERICAS])

    t_mundo, _, _ = asignar(b, ESCENARIOS[rf.ESCENARIO], rng)
    t_en = t_mundo[idx[n_ev:n_ev + n_en]]
    niveles = celdas_por_nivel(b)
    donante = reg[sortear_donante(niveles[idx[n_ev:n_ev + n_en]], niveles[reg], rng)]
    y0_en, tau_en, lp_en = en["y0"].to_numpy(), en["tau"].to_numpy(), en["lp"].to_numpy()
    w_hogar = ev["fex"].to_numpy()
    p_fhdi = ev["p_ab_fhdi"].to_numpy()

    filas = []
    for tipo in rf.TIPOS_EFECTO:
        if tipo == "proporcional":
            y_en = y0_en + tau_en * t_en
        else:
            y_en = np.minimum(rf.ingreso_relativo(y0_en, lp_en), 10) + tau_en * t_en
        cate = {nombre: bosque_intra_celda(en, y_en, t, ev)
                for nombre, t in [("verdadero", t_en), ("hotdeck", t_mundo[donante])]}
        lp, y0, tau = ev["lp"].to_numpy(), ev["y0"].to_numpy(), ev["tau"].to_numpy()

        def esperada(ef):
            return rf.reduccion_esperada(media, residuos, ef, lp, tipo)

        puntajes = {
            "vigente_hotdeck": ev["vigente_ab"].to_numpy(float),
            "pmt_ingreso": -media,
            "ideal": rf.brecha(rf.ingreso_relativo(y0, lp)) - rf.brecha(rf.despues(y0, tau, lp, tipo)),
            "pmt_brecha_cate_intra": esperada(cate["verdadero"][1]),
            "pmt_brecha_cate_hd_intra": esperada(cate["hotdeck"][1]),
        }
        # Los mismos números aleatorios que la vigente, en el mismo orden: el
        # puntaje de `aleatoria` y el desempate de cada regla base.
        rng.random(len(ev))
        elegidos = {}
        for regla in rf.REGLAS_BASE:
            if regla in CONTROL:
                elegidos[regla] = rf.elegir(puntajes[regla], k, rng)
            else:
                rng.random(len(ev))
        elegidos |= {regla: rf.elegir(puntajes[regla], k, rng_nuevo) for regla in NUEVAS_ORDINALES}

        base = rf.metricas(ev, np.zeros(len(ev), dtype=int), tipo)
        gasto_hogar = w_hogar * rf.costo(ev, tipo)
        gasto_vigente = float(gasto_hogar @ elegidos["vigente_hotdeck"])
        comunes = dict(rep=rep, efecto=tipo, fgt0_pre=base["fgt0_post"], fgt1_pre=base["fgt1_post"],
                       ate_cf_intra_verdadero=cate["verdadero"][0], ate_cf_intra_hotdeck=cate["hotdeck"][0],
                       pehe_cf_intra_verdadero=float(np.sqrt(np.mean((cate["verdadero"][1] - tau) ** 2))),
                       pehe_cf_intra_hotdeck=float(np.sqrt(np.mean((cate["hotdeck"][1] - tau) ** 2))),
                       sd_tau=float(tau.std()))
        bloques = [("hogares", elegidos)]
        if tipo == "monto_fijo":
            por_peso = {r: puntajes[r] * ev["peso"].to_numpy() / np.maximum(gasto_hogar, 1e-9)
                        if r in rf.REGLAS_POR_REDUCCION or r in NUEVAS_ORDINALES else puntajes[r] for r in puntajes}
            dinero = {}
            for regla in rf.REGLAS:  # mismo orden de sorteos que la vigente
                if regla in CONTROL:
                    dinero[regla] = rf.elegir_por_dinero(por_peso[regla], gasto_hogar, gasto_vigente, rng_dinero)
                else:
                    rng_dinero.random(len(ev))
            dinero |= {r: rf.elegir_por_dinero(por_peso[r], gasto_hogar, gasto_vigente, rng_nuevo_dinero)
                       for r in NUEVAS_ORDINALES}
            bloques.append(("dinero", dinero))
        for presupuesto, ts in bloques:
            filas_bloque = []
            for regla in [*CONTROL, *NUEVAS_ORDINALES]:
                m = rf.metricas(ev, ts[regla], tipo)
                filas_bloque.append(dict(comunes, presupuesto=presupuesto, regla=regla, identificable=True,
                                         k=float(ts[regla].sum()), **m,
                                         reduccion_fgt1=base["fgt1_post"] - m["fgt1_post"],
                                         gasto_rel=float(gasto_hogar @ ts[regla]) / gasto_vigente))
            m = metricas_fraccionales(ev, p_fhdi, tipo)
            filas_bloque.append(dict(comunes, presupuesto=presupuesto, regla="vigente_fhdi", identificable=True,
                                     k=float(p_fhdi.sum()), **m, reduccion_fgt1=base["fgt1_post"] - m["fgt1_post"],
                                     gasto_rel=float(gasto_hogar @ p_fhdi) / gasto_vigente))
            for regla in NO_IDENTIFICABLES:
                filas_bloque.append(dict(comunes, presupuesto=presupuesto, regla=regla, identificable=False, k=0.0,
                                         **{c: np.nan for c in rf.METRICAS}))
            ideal = next(f["reduccion_fgt1"] for f in filas_bloque if f["regla"] == "ideal")
            for f in filas_bloque:
                if f["identificable"]:
                    f["pct_ideal"] = 100 * f["reduccion_fgt1"] / ideal
            filas += filas_bloque
    return filas


# --------------------------------------------------------------------------
# Corrida, control y tabla
# --------------------------------------------------------------------------

def control_reproduccion(r: pd.DataFrame, vigente: Path = rf.OUT) -> float:
    """Máxima diferencia, repetición por repetición, de las reglas de
    control frente a la corrida vigente (debe ser ≈0: mismos sorteos)."""
    v = sin_marca(pd.read_csv(vigente))
    clave = ["rep", *rf.CLAVES]
    a = r[r["regla"].isin(CONTROL)]
    m = a.merge(v, on=clave, suffixes=("", "_vigente"))
    if m.empty:
        return float("nan")
    return float(max((m[c] - m[f"{c}_vigente"]).abs().max() for c in rf.METRICAS))


def num(v: float, fmt: str) -> str:
    """Cifra simulada con coma decimal y asterisco."""
    return format(v, fmt).replace(".", ",") + "\\*"


def tabla_comparativa(nueva: pd.DataFrame, vigente: Path = rf.OUT_RESUMEN) -> str:
    """Markdown: las reglas vigentes (de la corrida de `reglas_focalizacion`)
    y las nuevas, por modelo del efecto y presupuesto."""
    v = sin_marca(pd.read_csv(vigente))
    x = pd.concat([v.assign(origen="vigente"), nueva[nueva["regla"].isin(NUEVAS)].assign(origen="nueva")],
                  ignore_index=True)
    cols = [("error_inclusion", "Inclusión"), ("error_exclusion", "Exclusión"), ("reduccion_fgt1", "Reducción FGT1"),
            ("pct_ideal", "% del ideal"), ("gasto_rel", "Gasto / vigente")]
    formato = {"error_inclusion": ".3f", "error_exclusion": ".3f", "reduccion_fgt1": ".4f", "pct_ideal": ".1f",
               "gasto_rel": ".3f"}
    partes = [NOTA_SIMULADO, ""]
    for (tipo, presupuesto), g in x.groupby(["efecto", "presupuesto"], sort=False):
        partes.append(f"### Efecto {tipo.replace('_', ' ')}, presupuesto en {presupuesto}\n")
        partes.append("| Regla | " + " | ".join(t for _, t in cols) + " |")
        partes.append("|" + "---|" * (len(cols) + 1))
        for _, f in g.iterrows():
            nombre = f"**{f['regla']}** (nueva)" if f["origen"] == "nueva" else f["regla"]
            if f["regla"] in NO_IDENTIFICABLES:
                celdas = ["no identificable"] * len(cols)
            else:
                celdas = [num(f[c], formato[c]) for c, _ in cols]
            partes.append(f"| {nombre} | " + " | ".join(celdas) + " |")
        partes.append("")
    return "\n".join(partes)


def main(n_jobs: int = 3) -> pd.DataFrame:
    from joblib import Parallel, delayed, parallel_config

    b = cargar_base()
    firma = firma_con_datos(rf.firma(ampliadas=1, NUEVAS=NUEVAS), b)
    r = pd.DataFrame()
    if OUT.exists() and OUT_FIRMA.exists() and json.loads(OUT_FIRMA.read_text()).get("firma") == firma:
        r = sin_marca(pd.read_csv(OUT))
        logger.info("Reanudando: %d repeticiones ya guardadas", r["rep"].nunique())
    else:
        OUT_FIRMA.write_text(json.dumps(dict(firma=firma)))
    while True:
        hechas = 0 if r.empty else r["rep"].nunique()
        if hechas >= rf.MAX_REPS or (hechas >= rf.MIN_REPS and not rf.pendientes(rf.resumir(r))):
            break
        t0 = time.time()
        with parallel_config(backend="loky", inner_max_num_threads=1):
            partes = Parallel(n_jobs=n_jobs)(delayed(una_repeticion)(b, rep) for rep in range(hechas, hechas + rf.LOTE))
        r = pd.concat([r, pd.DataFrame([f for p in partes for f in p])], ignore_index=True)
        marcar_simulado(r).to_csv(OUT, index=False)
        logger.info("Lote reps %d-%d en %.0f s | métricas sin converger: %d", hechas, hechas + rf.LOTE - 1,
                    time.time() - t0, len(rf.pendientes(rf.resumir(r))))
    res = rf.resumir(r)
    marcar_simulado(res).to_csv(OUT_RESUMEN, index=False)
    tablas = tabla_comparativa(res)
    OUT_TABLAS.write_text(tablas, encoding="utf-8")

    p = rf.pendientes(res)
    print(f"\n{NOTA_SIMULADO}")
    print(f"\n=== Reglas de focalización ampliadas*: {r['rep'].nunique()} repeticiones, evaluación en "
          f"{rf.N_EVAL:,} hogares reales ===")
    print(f"Convergencia: {'alcanzada' if not p else 'NO alcanzada: ' + ', '.join(p)}")
    print(f"Control: las reglas vigentes recalculadas reproducen la corrida vigente "
          f"(diferencia máxima por repetición {control_reproduccion(r):.2e})")
    for tipo, g in r[r["presupuesto"] == "hogares"].groupby("efecto", sort=False):
        print(f"Causal Forest dentro de la celda ({tipo}): ATE con T verdadero {g['ate_cf_intra_verdadero'].mean():+.4f}, "
              f"con T por Hot-Deck {g['ate_cf_intra_hotdeck'].mean():+.4f}; PEHE {g['pehe_cf_intra_verdadero'].mean():.4f} "
              f"y {g['pehe_cf_intra_hotdeck'].mean():.4f} frente a una desviación de tau de {g['sd_tau'].mean():.4f}")
    print("\n" + tablas)
    print(f"Guardado: {OUT}\nGuardado: {OUT_RESUMEN}\nGuardado: {OUT_TABLAS}")
    return res


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
