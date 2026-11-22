"""¿Qué variables entran en la celda del Hot-Deck?

Compara las celdas anidadas que se han considerado:
  1. depto + ciclo de vida del jefe + cuartos (la oficial hasta el 2026-11-02)
  2. 1 + pisos (la oficial del 2026-11-02 al 2026-11-14)
  3. 2 + paredes (descartada: triplica las celdas sin mejorar nada)
  4. 2 + personas del hogar en 4 tramos (1, 2, 3-4, 5 o más)
  5. 4 + menores de 18 años (0, 1, 2 o más): la más fina; pasa el umbral
     de celdas pequeñas
  6. 2 + personas en 3 tramos (1-2, 3-4, 5 o más) + menores (0, 1, 2 o
     más): cierra igual que la 7 pero deja 5,1 % en celdas pequeñas
  7. 2 + personas en 2 tramos (1-2, 3 o más) + menores (0, 1, 2 o más):
     **la oficial desde el 2026-11-14**

Pisos y paredes entran por la escala común de
`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`, agrupada en tres
niveles para no fragmentar las celdas:
  pisos:   acabado (P1-P2) | cemento o madera burda (P3-P4) | tierra (P5)
  paredes: ladrillo/bloque (H1) | tapia o bahareque (H2-H3) | precarias (H4-H7)
Los códigos crudos no se comparan entre fuentes (en pisos van al revés).
Personas y menores son conteos: no necesitan tabla de equivalencias.

Para cada celda: cobertura (cuántos hogares GEIH encuentran donante en la
celda exacta), tamaño de las celdas, distribución de grupos A-D, cuánto
varía P(T | celda) (lo único que mueve el tratamiento imputado) y su
correlación con la pobreza monetaria del receptor, y el ancho medio de la
cota de Fréchet de P(Y=1, T=1 | celda) (`delta_frechet`: cuanto más
chico, más cierran las cotas del ATE). Para las celdas que agregan una
variable del hogar, `delta_frechet_placebo` repite el cálculo con la
variable agregada barajada dentro de la celda anterior: es lo que se
"gana" solo por partir la celda, sin información. Umbrales de aceptación:
al menos 99,5 % de hogares en celda exacta y no más del 5 % en celdas con
menos de 30 donantes.

Las demás variables comunes a las tres fuentes se evaluaron en
`src/validacion/candidatas_celda_catalogo.py`.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.comparar_celdas_hotdeck_vivienda
Salida: docs/reports/comparacion_celdas_hotdeck_vivienda.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import (
    CELDA_COLUMNAS, SISBEN, SISBEN_BOG, _sortear, construir_celda, peso_donante, proporcion_por_celda, nivel_pisos, tramo_menores, tramo_personas,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RECEPTOR = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
REPORT = Path("docs/reports/comparacion_celdas_hotdeck_vivienda.csv")
SEED = 42
MIN_DONANTES = 30
PERMUTACIONES_PLACEBO = 3
UMBRAL_EXACTA, UMBRAL_PEQUENAS = 99.5, 5.0

PAREDES = {  # código crudo -> nivel común (pisos: `nivel_pisos` del Hot-Deck)
    "geih": {"1": "ladrillo", "2": "ladrillo", "3": "tapia_bahareque", "4": "tapia_bahareque",
             "5": "precaria", "6": "precaria", "7": "precaria", "8": "precaria", "9": "precaria"},
    "sisben": {"1": "ladrillo", "4": "ladrillo", "2": "tapia_bahareque", "3": "tapia_bahareque",
               "5": "precaria", "6": "precaria", "7": "precaria", "0": "precaria"},
}


def _personas_4(df: pd.DataFrame) -> pd.Series:
    """Personas en 4 tramos (1, 2, 3-4, 5 o más): la variante fina, descartada."""
    n = pd.to_numeric(df["hog_num_personas"], errors="coerce")
    return pd.cut(n, [0, 1, 2, 4, 1000], labels=["1persona", "2personas", "3a4personas", "5omaspersonas"]) \
        .astype("object").fillna("NA").reset_index(drop=True)


def _personas_3(df: pd.DataFrame) -> pd.Series:
    """Personas en 3 tramos (1-2, 3-4, 5 o más): cierra igual que la oficial, fragmenta más."""
    n = pd.to_numeric(df["hog_num_personas"], errors="coerce")
    return pd.cut(n, [0, 2, 4, 1000], labels=["1a2personas", "3a4personas", "5omaspersonas"]) \
        .astype("object").fillna("NA").reset_index(drop=True)


def _celdas(df: pd.DataFrame, fuente: str) -> dict[str, pd.Series]:
    """Claves de cada celda y, para las que agregan una variable del hogar,
    (celda anterior, bloque agregado) para el placebo."""
    sisben = fuente == "sisben"
    base = construir_celda(df, edad_en_codigos=sisben, incluir_pisos=False).reset_index(drop=True)
    pisos = nivel_pisos(df, sisben=sisben).reset_index(drop=True)
    paredes = df["viv_paredes"].astype(str).map(PAREDES[fuente]).fillna("NA").reset_index(drop=True)
    p4, p3, p2 = _personas_4(df), _personas_3(df), tramo_personas(df).reset_index(drop=True)
    menores = tramo_menores(df).reset_index(drop=True)
    con_pisos = base + "|" + pisos
    return {
        "1_depto_edad_cuartos": base,
        "2_mas_pisos": con_pisos,
        "3_mas_pisos_paredes": con_pisos + "|" + paredes,
        "4_mas_personas4": con_pisos + "|" + p4,
        "5_mas_personas4_menores": con_pisos + "|" + p4 + "|" + menores,
        "6_mas_personas3_menores": con_pisos + "|" + p3 + "|" + menores,
        "7_mas_personas2_menores": con_pisos + "|" + p2 + "|" + menores,
    }, {
        "4_mas_personas4": (con_pisos, p4),
        "5_mas_personas4_menores": (con_pisos + "|" + p4, menores),
        "6_mas_personas3_menores": (con_pisos, p3 + "|" + menores),
        "7_mas_personas2_menores": (con_pisos, p2 + "|" + menores),
    }


def delta_frechet(cr: pd.Series, cd: pd.Series, rec: pd.DataFrame, don: pd.DataFrame) -> float:
    """Ancho medio (ponderado por fex) de la cota de Fréchet-Hoeffding de
    P(Y=1, T=1 | celda), con Y la pobreza monetaria del receptor y T el
    grupo A/B del donante: min(p, e) − max(0, p + e − 1)."""
    y = pd.to_numeric(rec["POBRE_MONETARIO"], errors="coerce").to_numpy()
    w = pd.to_numeric(rec["fex"], errors="coerce").fillna(0).to_numpy()
    g = pd.DataFrame({"c": cr.to_numpy(), "w": w, "yw": y * w}).dropna().groupby("c")[["w", "yw"]].sum()
    p = (g["yw"] / g["w"]).where(g["w"] > 0)
    e = proporcion_por_celda(don["Grupo"].isin(["A", "B"]), cd, peso_donante(don))
    m = pd.DataFrame({"p": p, "e": e, "w": g["w"]}).dropna()
    return float(np.average(np.minimum(m["p"], m["e"]) - np.maximum(0, m["p"] + m["e"] - 1), weights=m["w"]))


def _permutar(bloque: pd.Series, celda: pd.Series, rng: np.random.Generator) -> pd.Series:
    """Baraja `bloque` dentro de cada valor de `celda`: conserva la
    distribución de la variable agregada en cada celda anterior y le quita
    toda relación con el hogar."""
    out = bloque.to_numpy().copy()
    for idx in pd.Series(np.arange(len(celda))).groupby(celda.to_numpy()).indices.values():
        out[idx] = out[rng.permutation(idx)]
    return pd.Series(out)


def delta_placebo(base_r: pd.Series, bloque_r: pd.Series, base_d: pd.Series, bloque_d: pd.Series,
                  rec: pd.DataFrame, don: pd.DataFrame) -> float:
    rng = np.random.default_rng(SEED)
    valores = [delta_frechet(base_r + "|" + _permutar(bloque_r, base_r, rng), base_d + "|" + _permutar(bloque_d, base_d, rng),
                             rec, don) for _ in range(PERMUTACIONES_PLACEBO)]
    return float(np.mean(valores))


def _evaluar(nombre: str, cr: pd.Series, cd: pd.Series, rec: pd.DataFrame, don: pd.DataFrame) -> dict:
    rng = np.random.default_rng(SEED)
    peso = peso_donante(don)
    grupos = {k: v.values for k, v in pd.Series(np.arange(len(don))).groupby(cd.values)}
    elegido = _sortear(grupos, cr, rng, peso)
    exacta = elegido >= 0
    # Respaldo igual al del Hot-Deck: depto + edad, luego depto.
    respaldos = [
        (construir_celda(rec, incluir_vivienda=False), construir_celda(don, edad_en_codigos=True, incluir_vivienda=False)),
        (rec["geo_depto"].astype(str).str.zfill(2), don["geo_depto"].astype(str).str.zfill(2)),
    ]
    for clave_rec, clave_don in respaldos:
        falta = elegido < 0
        if not falta.any():
            break
        g = {k: v.values for k, v in pd.Series(np.arange(len(don))).groupby(clave_don.values)}
        elegido[falta] = _sortear(g, clave_rec.reset_index(drop=True)[falta].reset_index(drop=True), rng, peso)
    acum = np.cumsum(peso)
    elegido[elegido < 0] = np.searchsorted(acum, rng.random(int((elegido < 0).sum())) * acum[-1], side="right")

    grupo = pd.Series(don["Grupo"].values[elegido])
    t = grupo.isin(["A", "B"]).astype(float)
    w = pd.to_numeric(rec["fex"], errors="coerce").fillna(0).to_numpy()
    n_don = cr.map(pd.Series({k: len(v) for k, v in grupos.items()})).fillna(0)
    celdas_rec = cr.nunique()
    p_celda = proporcion_por_celda(don["Grupo"].isin(["A", "B"]), cd, peso)
    p_rec = cr.map(p_celda)
    pobre = pd.to_numeric(rec["POBRE_MONETARIO"], errors="coerce").to_numpy()
    ok = ~np.isnan(pobre)
    dif_naive = (np.average(pobre[ok & (t == 1)], weights=w[ok & (t == 1)])
                 - np.average(pobre[ok & (t == 0)], weights=w[ok & (t == 0)]))
    fila = dict(
        celda=nombre, celdas_con_receptores=celdas_rec,
        pct_hogares_celda_exacta=exacta.mean() * 100,
        donantes_mediana=float(n_don[exacta].median()), donantes_p5=float(n_don[exacta].quantile(0.05)),
        pct_hogares_celda_menos_30_donantes=float((n_don < MIN_DONANTES).mean() * 100),
        sd_p_t_celda=float(p_rec.std()), p_t_p5=float(p_rec.quantile(0.05)), p_t_p95=float(p_rec.quantile(0.95)),
        corr_p_t_celda_pobre_monetario=float(pd.Series(p_rec.to_numpy()[ok]).corr(pd.Series(pobre[ok]))),
        dif_pobreza_T1_menos_T0=float(dif_naive),
    )
    for g in "ABCD":
        fila[f"pct_grupo_{g}"] = float(np.average(grupo == g, weights=w) * 100)
    fila["delta_frechet"] = delta_frechet(cr, cd, rec, don)
    fila["cumple_umbrales"] = bool(fila["pct_hogares_celda_exacta"] >= UMBRAL_EXACTA
                                   and fila["pct_hogares_celda_menos_30_donantes"] <= UMBRAL_PEQUENAS)
    return fila


def main() -> None:
    rec = pd.read_parquet(RECEPTOR).reset_index(drop=True)
    sb = SISBEN_BOG if SISBEN_BOG.exists() else SISBEN
    don = pd.read_parquet(sb, columns=[*CELDA_COLUMNAS, "viv_paredes", "Grupo", "Clasificacion", "fex"])
    don = don[don["Clasificacion"].notna()].reset_index(drop=True)
    logger.info("Receptor GEIH: %s hogares | Donante Sisbén: %s hogares", f"{len(rec):,}", f"{len(don):,}")

    (c_rec, placebo_rec), (c_don, placebo_don) = _celdas(rec, "geih"), _celdas(don, "sisben")
    filas = []
    for n in c_rec:
        fila = _evaluar(n, c_rec[n], c_don[n], rec, don)
        if n in placebo_rec:
            (br, xr), (bd, xd) = placebo_rec[n], placebo_don[n]
            fila["delta_frechet_placebo"] = delta_placebo(br, xr, bd, xd, rec, don)
        filas.append(fila)
        logger.info("%s: delta %.4f | exacta %.2f %% | pequeñas %.2f %%", n, fila["delta_frechet"],
                    fila["pct_hogares_celda_exacta"], fila["pct_hogares_celda_menos_30_donantes"])
    tabla = pd.DataFrame(filas)

    pd.set_option("display.width", 220)
    print("\n=== Celdas del Hot-Deck: vivienda homologada, personas y menores ===")
    print(tabla.round(4).T.to_string())
    print("\nLectura: la celda 7 es la oficial desde el 2026-11-14 (cumple los umbrales y cierra más las cotas);")
    print("la 5 y la 6 cierran igual o un poco más, pero dejan más del 5 % de los hogares en celdas pequeñas.")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT, index=False)
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
