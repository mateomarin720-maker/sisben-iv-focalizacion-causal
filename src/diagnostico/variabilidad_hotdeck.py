"""Variabilidad de la imputación del Hot-Deck (tarea de la tutoría del
2026-11-03): ¿cuánto cambia el grupo Sisbén imputado a cada hogar de GEIH
si el sorteo se repite con otra semilla?

Repite `hotdeck()` (la misma función del pipeline, sobre los mismos
290.968 hogares GEIH y 3.106.489 donantes) con `N_SORTEOS` semillas. La
semilla 42 es la del pipeline y reproduce exactamente el grupo guardado.
Mide:

1. **Por hogar:** la probabilidad de que dos sorteos le asignen el mismo
   grupo (y el mismo estado A/B), estimada sin sesgo con las frecuencias
   de los sorteos y comparada con la teórica de su celda, Σ_g π_g², donde
   π_g es la proporción de donantes de la celda en el grupo g.
2. **Por celda:** la proporción de hogares GEIH A/B de la celda en cada
   sorteo (ponderada por `fex`); su coeficiente de variación entre
   sorteos (CV = desviación / media) y su error relativo frente a la
   proporción de donantes A/B de la celda, |p_s − π| / π.
3. **Agregados:** la distribución nacional por grupo y la proporción A/B
   por departamento, con su variación entre sorteos.
4. **Estimación:** el contraste placebo (regresión de la pobreza sobre
   A/B con efectos fijos de celda) en cada sorteo, combinado con las
   reglas de Rubin (1987) para imputación múltiple: varianza total =
   varianza dentro + (1 + 1/m) × varianza entre sorteos.

Son datos reales (la imputación real), no simulados.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.diagnostico.variabilidad_hotdeck [n_jobs]
Salidas:
    docs/reports/variabilidad_hotdeck.txt (vía redirección), _celdas.csv,
    _agregados.csv, _estimacion.csv
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento import emparejamiento_hotdeck_geih_sisben as hd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

N_SORTEOS = 100
SEMILLAS = [42] + list(range(1000, 1000 + N_SORTEOS - 1))  # 42 = la del pipeline
GRUPOS = np.array(["A", "B", "C", "D"])
MUESTRA = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
LLAVE = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]
OUT_CELDAS = Path("docs/reports/variabilidad_hotdeck_celdas.csv")
OUT_AGREGADOS = Path("docs/reports/variabilidad_hotdeck_agregados.csv")
OUT_ESTIMACION = Path("docs/reports/variabilidad_hotdeck_estimacion.csv")


_DATOS = None


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Receptor GEIH y donantes Sisbén, como en `emparejamiento_hotdeck_geih_sisben.main`.
    Se cargan una vez por proceso: pasar los 3,1 millones de donantes a
    cada tarea los copiaría en cada una."""
    global _DATOS
    if _DATOS is None:
        _DATOS = (pd.read_parquet(hd.GEIH),
                  pd.read_parquet(hd.SISBEN_BOG, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", *hd.TRAT]))
    return _DATOS


def un_sorteo(semilla: int) -> np.ndarray:
    """Grupo imputado (0..3 = A..D) a cada hogar, en el orden del receptor."""
    receptor, donante = cargar()
    out = hd.hotdeck(receptor, donante, seed=semilla)
    return pd.Categorical(out["Grupo_hotdeck"], categories=GRUPOS).codes.astype(np.int8)


def concordancia_por_hogar(sorteos: np.ndarray, n_categorias: int) -> np.ndarray:
    """Probabilidad de que dos sorteos distintos coincidan, por hogar:
    Σ_g c_g (c_g − 1) / (R (R − 1)), con c_g = sorteos que dieron g. Es el
    estimador insesgado de Σ_g p_g²."""
    r = sorteos.shape[1]
    conteos = np.stack([(sorteos == g).sum(axis=1) for g in range(n_categorias)], axis=1)
    return (conteos * (conteos - 1)).sum(axis=1) / (r * (r - 1))


def concordancia_teorica(celda_receptor: pd.Series, celda_donante: pd.Series, grupo_donante: pd.Series,
                         categorias) -> pd.Series:
    """Σ_g π_g² de la celda de cada receptor, con π_g la proporción de
    donantes de la celda en cada categoría."""
    pi = pd.crosstab(celda_donante, grupo_donante, normalize="index").reindex(columns=categorias, fill_value=0)
    return celda_receptor.map((pi ** 2).sum(axis=1))


def por_celda(celda: np.ndarray, peso: np.ndarray, t: np.ndarray, pi_ab: pd.Series) -> pd.DataFrame:
    """Proporción A/B ponderada de cada celda en cada sorteo; CV entre
    sorteos y error relativo frente a la proporción de donantes A/B."""
    codigos, celdas = pd.factorize(celda)
    k = len(celdas)
    w_celda = np.bincount(codigos, peso, minlength=k)
    prop = np.stack([np.bincount(codigos, peso * t[:, s], minlength=k) / w_celda for s in range(t.shape[1])], axis=1)
    pi = pi_ab.reindex(celdas).to_numpy()
    media, sd = prop.mean(axis=1), prop.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        cv = np.where(media > 0, sd / media, np.nan)
        err_rel = np.where(pi > 0, np.abs(prop - pi[:, None]).mean(axis=1) / pi, np.nan)
    return pd.DataFrame({"celda": celdas, "hogares": np.bincount(codigos, minlength=k), "peso": w_celda,
                         "pi_ab_donantes": pi, "prop_ab_media": media, "prop_ab_sd": sd, "cv": cv,
                         "error_relativo_medio": err_rel})


def contraste_placebo(y: np.ndarray, t: np.ndarray, celda_cod: np.ndarray) -> tuple[float, float]:
    """MCO de Y sobre T con efectos fijos de celda; error estándar robusto."""
    k = celda_cod.max() + 1
    n = np.maximum(np.bincount(celda_cod, minlength=k), 1)
    yd = y - (np.bincount(celda_cod, y, minlength=k) / n)[celda_cod]
    td = t - (np.bincount(celda_cod, t, minlength=k) / n)[celda_cod]
    sxx = (td * td).sum()
    b = (td * yd).sum() / sxx
    e = yd - b * td
    return float(b), float(np.sqrt((td**2 * e**2).sum()) / sxx)


def reglas_de_rubin(estimaciones: np.ndarray, errores: np.ndarray) -> dict:
    """Combinación de m imputaciones (Rubin, 1987)."""
    m = len(estimaciones)
    q, w, b = estimaciones.mean(), (errores**2).mean(), estimaciones.var(ddof=1)
    total = w + (1 + 1 / m) * b
    return dict(m=m, estimacion=float(q), var_dentro=float(w), var_entre=float(b), var_total=float(total),
                error_total=float(np.sqrt(total)), fraccion_info_imputacion=float((1 + 1 / m) * b / total),
                ic_lo=float(q - 1.96 * np.sqrt(total)), ic_hi=float(q + 1.96 * np.sqrt(total)))


def main(n_jobs: int = 3) -> None:
    from joblib import Parallel, delayed

    receptor, donante = cargar()
    receptor = receptor.copy()
    logger.info("Receptor %s hogares | donante %s | %d sorteos", f"{len(receptor):,}", f"{len(donante):,}", N_SORTEOS)

    t0 = time.time()
    sorteos = np.stack(Parallel(n_jobs=n_jobs)(delayed(un_sorteo)(s) for s in SEMILLAS), axis=1)
    logger.info("Sorteos listos en %.0f s", time.time() - t0)
    guardado = pd.read_parquet(hd.OUT, columns=["Grupo_hotdeck"])["Grupo_hotdeck"]
    reproduce = float((GRUPOS[sorteos[:, 0]] == guardado.to_numpy()).mean())
    t = (sorteos <= 1).astype(float)  # A o B

    # Celdas del receptor y del donante (la exacta; el 0,02 % que cae a un
    # respaldo se cuenta con su celda exacta, que no tiene donantes).
    don = donante[donante["Clasificacion"].notna()]
    celda_r = hd.construir_celda(receptor)
    celda_d = hd.construir_celda(don, edad_en_codigos=True)
    peso = pd.to_numeric(receptor["fex"], errors="coerce").fillna(0).to_numpy(float)

    # 1. Por hogar
    conc_g = concordancia_por_hogar(sorteos, 4)
    conc_t = concordancia_por_hogar(t.astype(np.int8), 2)
    teo_g = concordancia_teorica(celda_r, celda_d, don["Grupo"], list(GRUPOS)).to_numpy()
    teo_t = concordancia_teorica(celda_r, celda_d, don["Grupo"].isin(["A", "B"]), [False, True]).to_numpy()
    p_ab = t.mean(axis=1)
    hogar = dict(
        reproduce_semilla_42=reproduce,
        concordancia_grupo=float(np.average(conc_g, weights=peso)),
        concordancia_grupo_teorica=float(np.average(teo_g[~np.isnan(teo_g)], weights=peso[~np.isnan(teo_g)])),
        concordancia_ab=float(np.average(conc_t, weights=peso)),
        concordancia_ab_teorica=float(np.average(teo_t[~np.isnan(teo_t)], weights=peso[~np.isnan(teo_t)])),
        pct_mismo_grupo_en_todos=float(np.average((sorteos == sorteos[:, [0]]).all(axis=1), weights=peso) * 100),
        pct_mismo_ab_en_todos=float(np.average((t == t[:, [0]]).all(axis=1), weights=peso) * 100),
        pct_ab_casi_seguro=float(np.average((p_ab >= 0.9) | (p_ab <= 0.1), weights=peso) * 100),
        pct_ab_incierto=float(np.average((p_ab > 0.3) & (p_ab < 0.7), weights=peso) * 100),
        correlacion_empirica_teorica=float(pd.Series(conc_g).corr(pd.Series(teo_g))),
    )

    # 2. Por celda
    pi_ab = don["Grupo"].isin(["A", "B"]).groupby(celda_d.to_numpy()).mean()
    celdas = por_celda(celda_r.to_numpy(), peso, t, pi_ab)
    celdas.to_csv(OUT_CELDAS, index=False)
    c = celdas.dropna(subset=["cv"])
    w_c = c["peso"] / c["peso"].sum()

    # 3. Agregados
    filas = []
    for g, nombre in enumerate(GRUPOS):
        prop = np.array([np.average(sorteos[:, s] == g, weights=peso) for s in range(N_SORTEOS)]) * 100
        filas.append(dict(nivel="nacional", unidad=nombre, media_pct=prop.mean(), sd_pct=prop.std(ddof=1),
                          cv=prop.std(ddof=1) / prop.mean(), min_pct=prop.min(), max_pct=prop.max(),
                          semilla_42_pct=prop[0]))
    depto = receptor["geo_depto"].astype(str).str.zfill(2).to_numpy()
    for d in sorted(set(depto)):
        m = depto == d
        prop = np.array([np.average(t[m, s], weights=peso[m]) for s in range(N_SORTEOS)]) * 100
        filas.append(dict(nivel="departamento_ab", unidad=d, media_pct=prop.mean(), sd_pct=prop.std(ddof=1),
                          cv=prop.std(ddof=1) / prop.mean(), min_pct=prop.min(), max_pct=prop.max(),
                          semilla_42_pct=prop[0], hogares=int(m.sum())))
    agregados = pd.DataFrame(filas)
    agregados.to_csv(OUT_AGREGADOS, index=False)

    # 4. Estimación placebo con reglas de Rubin
    muestra = pd.read_parquet(MUESTRA, columns=[*LLAVE, "POBRE_MONETARIO", "ingreso_percapita", "POBRE_GEIH"])
    for c_ in LLAVE:
        muestra[c_] = muestra[c_].astype("string")
        receptor[c_] = receptor[c_].astype("string")
    y = receptor[LLAVE].merge(muestra, on=LLAVE, how="left", validate="one_to_one")
    assert len(y) == len(receptor)
    celda_cod = pd.factorize(celda_r)[0]
    filas_est = []
    for col, serie in [("POBRE_MONETARIO", y["POBRE_MONETARIO"].astype(float)),
                       ("POBRE_GEIH", y["POBRE_GEIH"].astype(float)),
                       ("log_ingreso_percapita", np.log1p(y["ingreso_percapita"]))]:
        ok = serie.notna().to_numpy()
        est = np.array([contraste_placebo(serie.to_numpy()[ok], t[ok, s], pd.factorize(celda_cod[ok])[0])
                        for s in range(N_SORTEOS)])
        filas_est.append(dict(outcome=col, semilla_42=est[0, 0], error_semilla_42=est[0, 1],
                              **reglas_de_rubin(est[:, 0], est[:, 1]),
                              pct_sorteos_ic_sin_cero=float(np.mean(np.abs(est[:, 0]) > 1.96 * est[:, 1]) * 100)))
    estimacion = pd.DataFrame(filas_est)
    estimacion.to_csv(OUT_ESTIMACION, index=False)

    pd.set_option("display.width", 220)
    print(f"\n=== Variabilidad de la imputación del Hot-Deck: {N_SORTEOS} sorteos ===")
    print(f"La semilla 42 reproduce el grupo guardado en el {hogar['reproduce_semilla_42'] * 100:.2f} % de los hogares")
    print("\n1. Por hogar (ponderado por fex):")
    for k_, v in hogar.items():
        print(f"   {k_}: {v:.4f}")
    print("\n2. Por celda (proporción A/B de los hogares GEIH de la celda):")
    print(f"   celdas: {len(c)} | CV mediano {c['cv'].median():.3f}, ponderado {np.sum(w_c * c['cv']):.3f}, "
          f"p90 {c['cv'].quantile(0.9):.3f}")
    print(f"   error relativo medio frente a la proporción de donantes: mediano {c['error_relativo_medio'].median():.3f}, "
          f"ponderado {np.sum(w_c * c['error_relativo_medio']):.3f}")
    for umbral in (0.1, 0.2, 0.3):
        print(f"   celdas con CV > {umbral}: {(c['cv'] > umbral).sum()} ({w_c[c['cv'] > umbral].sum() * 100:.1f} % de la población)")
    tramos = pd.cut(c["hogares"], [0, 30, 100, 300, 1000, np.inf], labels=["<30", "30-99", "100-299", "300-999", "1000+"])
    print(c.groupby(tramos, observed=True).agg(celdas=("cv", "size"), cv_mediano=("cv", "median"),
                                               error_relativo_mediano=("error_relativo_medio", "median")).round(3).to_string())
    print("\n3. Agregados:")
    print(agregados[agregados["nivel"] == "nacional"].round(3).to_string(index=False))
    dep = agregados[agregados["nivel"] == "departamento_ab"]
    print(f"   A/B por departamento: CV de {dep['cv'].min():.4f} a {dep['cv'].max():.4f}; "
          f"rango máximo entre sorteos {(dep['max_pct'] - dep['min_pct']).max():.2f} puntos")
    print("\n4. Contraste placebo (efectos fijos de celda) combinado con reglas de Rubin:")
    print(estimacion.round(5).to_string(index=False))
    print(f"\nGuardado: {OUT_CELDAS}\nGuardado: {OUT_AGREGADOS}\nGuardado: {OUT_ESTIMACION}")


if __name__ == "__main__":
    main(*[int(a) for a in sys.argv[1:]])
