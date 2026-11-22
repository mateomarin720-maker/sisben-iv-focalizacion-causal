"""Corre la FHDI con los datos del banco de Azure (leídos en memoria) y la
compara con el Hot-Deck.

1. Validación interna en el Sisbén (`validacion.py`): acierto del enlace
   por celda con el sorteo, la moda, la FHDI y FEFI.
2. FHDI (M = 10, pesos calibrados) y FEFI sobre los 290.968 hogares de la
   GEIH: proporción por grupo, A/B por departamento, pobreza dentro de
   A/B y errores de exclusión e inclusión, con error estándar jackknife
   (GEIH) y bootstrap de los donantes (Sisbén, `varianza.py`).
   Se comparan con el sorteo guardado (semilla 42) y con la media y la
   desviación entre los 100 sorteos (`variabilidad_hotdeck`). FEFI debe
   coincidir con el valor «con independencia» de
   `errores_focalizacion_frechet` (el mismo cálculo por otro camino).
3. Contraste placebo (pobreza sobre A/B con efectos fijos de celda): con
   pesos calibrados es 0 exacto (Proposición 1), frente a la combinación
   de Rubin de los 100 sorteos.

Son datos reales (la imputación real), no simulados.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.emparejamiento.fhdi > docs/reports/fhdi.txt 2>&1
Salidas: docs/reports/fhdi_validacion.csv, fhdi_comparacion.csv, fhdi_placebo.csv
"""
from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import CELDA_COLUMNAS, construir_celda
from src.emparejamiento.fhdi import reglas, validacion
from src.emparejamiento.fhdi.varianza import asignar_grupos, bootstrap_donantes, razon_jackknife
from src.utils.azure_storage import leer_bytes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

AZ_GEIH = "2_models/muestra_estimacion_monetaria_2024.parquet"
AZ_SISBEN = "2_models/sisben_estandarizado_2024_con_bogota.parquet"
REPORTES = Path("docs/reports")
OUT_VALIDACION = REPORTES / "fhdi_validacion.csv"
OUT_COMPARACION = REPORTES / "fhdi_comparacion.csv"
OUT_PLACEBO = REPORTES / "fhdi_placebo.csv"
POBREZA = ["POBRE_MONETARIO", "POBRE_GEIH"]


def cargar() -> tuple[pd.DataFrame, pd.DataFrame]:
    """GEIH (receptor, con la pobreza y el grupo del sorteo guardado) y
    Sisbén (donantes), del banco de Azure en memoria."""
    geih = pd.read_parquet(io.BytesIO(leer_bytes(AZ_GEIH)),
                           columns=[*CELDA_COLUMNAS, "fex", "Grupo_hotdeck", *POBREZA, "ingreso_percapita"])
    geih["fex"] = pd.to_numeric(geih["fex"], errors="coerce").fillna(0).astype(float)
    for c in [*POBREZA, "ingreso_percapita"]:
        geih[c] = pd.to_numeric(geih[c], errors="coerce").astype(float)
    sisben = pd.read_parquet(io.BytesIO(leer_bytes(AZ_SISBEN)), columns=[*CELDA_COLUMNAS, "Grupo", "Clasificacion", "fex"])
    sisben = sisben[sisben["Clasificacion"].notna()].reset_index(drop=True)
    return geih, sisben


def cantidades(q: np.ndarray, geih: pd.DataFrame, grupos_jk: np.ndarray) -> list[dict]:
    """Razones ponderadas a partir de q (n × 4, probabilidad de cada grupo
    por hogar) con su error jackknife."""
    w = geih["fex"].to_numpy(float)
    q_ab = q[:, list(reglas.ELEGIBLE)].sum(axis=1)
    uno = np.ones(len(geih))
    filas = []

    def fila(nombre, a, b):
        r, se = razon_jackknife(w, a, b, grupos_jk)
        filas.append(dict(cantidad=nombre, valor=r, error_jackknife=se))

    for k, g in enumerate(reglas.GRUPOS):
        fila(f"pct_grupo_{g}", q[:, k] * 100, uno)
    fila("pct_ab", q_ab * 100, uno)
    depto = geih["geo_depto"].astype(str).str.zfill(2).to_numpy()
    for d in sorted(set(depto)):
        m = (depto == d).astype(float)
        fila(f"pct_ab_depto_{d}", q_ab * m * 100, m)
    for y in POBREZA:
        yy = geih[y].to_numpy(float)
        fila(f"exclusion_{y}", yy * (1 - q_ab), yy)
        fila(f"inclusion_{y}", (1 - yy) * q_ab, q_ab)
        fila(f"pobreza_en_ab_{y}", yy * q_ab, q_ab)
        fila(f"pobreza_en_cd_{y}", yy * (1 - q_ab), 1 - q_ab)
    return filas


def referencia_hotdeck() -> pd.DataFrame:
    """Media y desviación entre los 100 sorteos (`variabilidad_hotdeck`)."""
    ag = pd.read_csv(REPORTES / "variabilidad_hotdeck_agregados.csv", dtype={"unidad": str})
    nac = ag[ag["nivel"] == "nacional"].assign(cantidad=lambda d: "pct_grupo_" + d["unidad"])
    dep = ag[ag["nivel"] == "departamento_ab"].assign(
        cantidad=lambda d: "pct_ab_depto_" + d["unidad"].str.zfill(2))
    ref = pd.concat([nac, dep])[["cantidad", "media_pct", "sd_pct"]]
    return ref.rename(columns={"media_pct": "hotdeck_100_media", "sd_pct": "hotdeck_100_sd_entre_sorteos"})


def main() -> None:
    t0 = time.time()
    geih, sisben = cargar()
    logger.info("GEIH %s hogares | Sisbén %s donantes (Azure, %.0f s)", f"{len(geih):,}", f"{len(sisben):,}",
                time.time() - t0)

    # 1. Validación interna
    val = validacion.validar(sisben)
    val.to_csv(OUT_VALIDACION, index=False)

    # 2. FHDI y FEFI sobre la GEIH
    n = len(geih)
    exp = reglas.donantes_fraccionales(geih, sisben)
    q_fhdi = reglas.probabilidad_por_receptor(exp, n)
    pi, nivel = reglas.probabilidades(geih, sisben)
    sorteo = pd.Categorical(geih["Grupo_hotdeck"], categories=reglas.GRUPOS).codes
    q_sorteo = np.eye(len(reglas.GRUPOS))[sorteo]
    grupos_jk = asignar_grupos(n)

    tablas = {nombre: pd.DataFrame(cantidades(q, geih, grupos_jk)).set_index("cantidad")
              for nombre, q in [("hotdeck_semilla_42", q_sorteo), ("fhdi", q_fhdi), ("fefi", pi)]}
    comp = pd.DataFrame({
        "hotdeck_semilla_42": tablas["hotdeck_semilla_42"]["valor"],
        "fhdi": tablas["fhdi"]["valor"],
        "fhdi_error_jackknife": tablas["fhdi"]["error_jackknife"],
        "fefi": tablas["fefi"]["valor"],
        "fefi_error_jackknife": tablas["fefi"]["error_jackknife"],
    })
    # Lado del Sisbén: bootstrap de los donantes (Bogotá, registro completo, fijo).
    bogota = sisben["geo_depto"].astype(str).str.zfill(2).to_numpy() == "11"
    nombres = tablas["fefi"].index
    error_sisben = bootstrap_donantes(geih, sisben, lambda q: pd.DataFrame(cantidades(q, geih, grupos_jk))
                                      .set_index("cantidad").loc[nombres, "valor"].to_numpy(), fijos=bogota)
    comp["fefi_error_sisben"] = error_sisben
    comp["fefi_error_total"] = np.sqrt(comp["fefi_error_jackknife"] ** 2 + comp["fefi_error_sisben"] ** 2)
    comp = comp.reset_index()
    comp = comp.merge(referencia_hotdeck(), on="cantidad", how="left")

    # FEFI = valor con independencia de errores_focalizacion_frechet.
    frechet = pd.read_csv(REPORTES / "errores_focalizacion_frechet.csv", dtype={"depto": str})
    frechet = frechet[(frechet["ambito"] == "nacional") & (frechet["elegible"] == "A-B")].set_index("pobreza")
    for y in POBREZA:
        for tasa in ("exclusion", "inclusion"):
            fila = comp["cantidad"] == f"{tasa}_{y}"
            comp.loc[fila, "frechet_lo"] = frechet.loc[y, f"{tasa}_lo"]
            comp.loc[fila, "frechet_independencia"] = frechet.loc[y, f"{tasa}_ind"]
            comp.loc[fila, "frechet_hi"] = frechet.loc[y, f"{tasa}_hi"]
    comp.to_csv(OUT_COMPARACION, index=False)

    # 3. Contraste placebo
    celda = construir_celda(geih).to_numpy()
    w = geih["fex"].to_numpy(float)
    rubin = pd.read_csv(REPORTES / "variabilidad_hotdeck_estimacion.csv").set_index("outcome")
    filas = []
    for y_nombre, y in [("POBRE_MONETARIO", geih["POBRE_MONETARIO"].to_numpy(float)),
                        ("POBRE_GEIH", geih["POBRE_GEIH"].to_numpy(float)),
                        ("log_ingreso_percapita", np.log1p(geih["ingreso_percapita"].to_numpy(float)))]:
        b, se = reglas.contraste_placebo(y, w, celda, exp)
        filas.append(dict(outcome=y_nombre, fhdi=b, fhdi_error=se,
                          rubin_100_sorteos=rubin.loc[y_nombre, "estimacion"],
                          rubin_ic_lo=rubin.loc[y_nombre, "ic_lo"], rubin_ic_hi=rubin.loc[y_nombre, "ic_hi"],
                          rubin_fraccion_imputacion=rubin.loc[y_nombre, "fraccion_info_imputacion"]))
    placebo = pd.DataFrame(filas)
    placebo.to_csv(OUT_PLACEBO, index=False)

    # Reporte
    pd.set_option("display.width", 220)
    hogares = exp.groupby("receptor").agg(donantes=("donante", "size"), calibrado=("calibrado", "first"))
    print("=== Imputación fraccional (FHDI) frente al Hot-Deck: datos reales del banco de Azure ===")
    print(f"GEIH {n:,} hogares | Sisbén {len(sisben):,} donantes | M = {reglas.M_DONANTES}")
    print("Nivel de la cadena: " + ", ".join(f"{k} {v:.2f} %" for k, v in
                                               (pd.Series(nivel).value_counts(normalize=True) * 100).items()))
    print(f"Donantes por hogar: mediana {hogares['donantes'].median():.0f}; base expandida {len(exp):,} filas; "
          f"hogares con pesos calibrados exactamente: {hogares['calibrado'].mean() * 100:.2f} %")
    print("\n1. Validación interna en el Sisbén (20 % de los hogares con el grupo escondido):")
    print(val.round(4).to_string(index=False))
    print("\n2. Cantidades (en %, o proporción en tasas y pobreza):")
    principales = comp[~comp["cantidad"].str.startswith("pct_ab_depto_")]
    print(principales.round(4).to_string(index=False))
    dep = comp[comp["cantidad"].str.startswith("pct_ab_depto_")]
    print(f"\n   A/B por departamento ({len(dep)}): |FHDI − FEFI| máx {(dep['fhdi'] - dep['fefi']).abs().max():.4f} pp; "
          f"|sorteo 42 − FEFI| máx {(dep['hotdeck_semilla_42'] - dep['fefi']).abs().max():.3f} pp; "
          f"desviación entre sorteos máx {dep['hotdeck_100_sd_entre_sorteos'].max():.3f} pp; "
          f"error jackknife FEFI máx {dep['fefi_error_jackknife'].max():.3f} pp; "
          f"error total FEFI (GEIH + Sisbén) máx {dep['fefi_error_total'].max():.3f} pp")
    print("\n3. Contraste placebo (efectos fijos de celda):")
    print(placebo.round(5).to_string(index=False))
    print(f"\nGuardado: {OUT_VALIDACION}\nGuardado: {OUT_COMPARACION}\nGuardado: {OUT_PLACEBO}")
    logger.info("Listo en %.0f s", time.time() - t0)


if __name__ == "__main__":
    main()
