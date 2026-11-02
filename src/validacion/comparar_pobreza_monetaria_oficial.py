"""Reconstrucción de la pobreza monetaria frente a la base oficial del DANE.

La base anonimizada de la medición oficial (catálogo 874,
`BDatos-Pobreza_Monetaria_Desigualdad-2024`) trae, por hogar, el ingreso
de la unidad de gasto con y sin arriendo imputado, el per cápita, las
líneas de su área y la clasificación pobre/indigente, con las llaves de
GEIH (`directorio`, `secuencia_p`, `mes`). Eso permite comparar la
reconstrucción (`src/indicadores/pobreza_monetaria_geih.py`) hogar por
hogar.

Dos hechos de la base que cambian la comparación:
  - No incluye los 9 departamentos de la Orinoquía, la Amazonía y San
    Andrés (81, 85, 86, 88, 91, 94, 95, 97, 99): la cifra oficial es de 24
    departamentos y Bogotá. La reconstrucción los incluye; aquí se comparan
    solo los hogares comunes.
  - Las líneas son de cada área (23 ciudades, resto urbano, rural) y
    cambian a mitad de año, no las tres de dominio que usa la
    reconstrucción.

La descomposición separa la diferencia que viene de las líneas de la que
viene del ingreso: se clasifica el ingreso reconstruido con las líneas
oficiales del hogar.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.comparar_pobreza_monetaria_oficial
Salidas:
    data/1_processed/pobreza_monetaria/hogares_oficial_2024.parquet
    docs/reports/comparacion_pobreza_monetaria_oficial.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

OFICIAL = Path("data/0_raw/pobreza_monetaria/BDatos-Pobreza_Monetaria_Desigualdad-2024/HOGARES/Hogares.csv")
RECON = Path("data/2_models/pobreza_monetaria_hogar_2024.parquet")
OUT_OFICIAL = Path("data/1_processed/pobreza_monetaria/hogares_oficial_2024.parquet")
REPORT = Path("docs/reports/comparacion_pobreza_monetaria_oficial.csv")
LLAVE = ["llave_directorio", "llave_secuencia_p", "mes"]
NUMERICAS = ["nper", "npersug", "ingtotug", "ingtotarr", "ingpcug", "lp", "li", "pobre", "indigente", "fex_c"]


def _llave(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").astype("Int64").astype("string")


def cargar_oficial(ruta: Path = OFICIAL) -> pd.DataFrame:
    o = pd.read_csv(ruta, dtype=str, encoding="latin1")
    for c in NUMERICAS:
        o[c] = pd.to_numeric(o[c], errors="coerce")
    o["llave_directorio"], o["llave_secuencia_p"], o["mes"] = _llave(o["directorio"]), _llave(o["secuencia_p"]), _llave(o["mes"])
    o["arriendo_imputado"] = o["ingtotarr"] - o["ingtotug"]
    o["area_pm"] = np.select([o["clase"] == "2", o["dominio"] == "RESTO URBANO"], ["rural", "resto_urbano"], "ciudad")
    return o


def cargar_reconstruccion(ruta: Path = RECON) -> pd.DataFrame:
    r = pd.read_parquet(ruta)
    r["llave_directorio"], r["llave_secuencia_p"], r["mes"] = _llave(r["DIRECTORIO"]), _llave(r["SECUENCIA_P"]), _llave(r["mes"])
    return r


def _tasa(pobre: pd.Series, peso: pd.Series) -> float:
    return float(np.average(pobre, weights=peso) * 100)


def comparar(o: pd.DataFrame, r: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    d = o.merge(r[[*LLAVE, "ingreso_pc_ug", "personas_ug", "POBRE_MONETARIA", "POBRE_EXTREMA", "dominio_pm"]],
                on=LLAVE, how="inner", validate="one_to_one")
    d["peso_personas"] = d["fex_c"] * d["npersug"]
    d["pobre_recon_lineas_oficiales"] = (d["ingreso_pc_ug"] < d["lp"]).astype(int)
    d["indigente_recon_lineas_oficiales"] = (d["ingreso_pc_ug"] < d["li"]).astype(int)
    razon = d["ingreso_pc_ug"] / d["ingpcug"].replace(0, np.nan)

    filas = []
    for nombre, g in [("nacional_24_deptos", d), *[(a, x) for a, x in d.groupby("area_pm")]]:
        w = g["peso_personas"]
        filas.append(dict(
            universo=nombre, hogares=len(g),
            fgt0_oficial=_tasa(g["pobre"], w),
            fgt0_reconstruida=_tasa(g["POBRE_MONETARIA"], w),
            fgt0_recon_con_lineas_oficiales=_tasa(g["pobre_recon_lineas_oficiales"], w),
            extrema_oficial=_tasa(g["indigente"], w),
            extrema_reconstruida=_tasa(g["POBRE_EXTREMA"], w),
            extrema_recon_con_lineas_oficiales=_tasa(g["indigente_recon_lineas_oficiales"], w),
            pct_hogares_misma_clasificacion=float((g["pobre"] == g["POBRE_MONETARIA"]).mean() * 100),
            pct_hogares_ingreso_pc_igual_1pct=float((razon[g.index].sub(1).abs() <= 0.01).mean() * 100),
            razon_ingreso_mediana=float(razon[g.index].median()),
            pct_hogares_misma_ug=float((g["npersug"] == g["personas_ug"]).mean() * 100),
        ))
    tabla = pd.DataFrame(filas)

    resumen = dict(
        hogares_oficial=len(o), hogares_reconstruccion=len(r), hogares_comunes=len(d),
        oficial_sin_reconstruccion=int(len(o) - len(d)),
        matriz_pobre=pd.crosstab(d["pobre"], d["POBRE_MONETARIA"], values=d["peso_personas"], aggfunc="sum",
                                 normalize="all").mul(100).round(1),
    )
    return tabla, resumen


def main() -> None:
    o, r = cargar_oficial(), cargar_reconstruccion()
    OUT_OFICIAL.parent.mkdir(parents=True, exist_ok=True)
    o.drop(columns=["directorio", "secuencia_p"]).to_parquet(OUT_OFICIAL, index=False)

    fuera = r[~r.set_index(LLAVE).index.isin(o.set_index(LLAVE).index)]
    tabla, res = comparar(o, r)

    pd.set_option("display.width", 220)
    print("=== Reconstrucción frente a la base oficial del DANE (catálogo 874) ===")
    print(f"Hogares oficiales: {res['hogares_oficial']:,} | reconstruidos: {res['hogares_reconstruccion']:,} | "
          f"comunes: {res['hogares_comunes']:,} | oficiales sin reconstruir: {res['oficial_sin_reconstruccion']:,}")
    print(f"Reconstruidos fuera de la base oficial: {len(fuera):,} "
          f"(dominio: {fuera['dominio_pm'].value_counts().to_dict()})")
    print("\nTasas por persona (fex_c × personas de la UG), hogares comunes:")
    print(tabla.round(2).T.to_string())
    print("\nClasificación oficial (filas) × reconstruida (columnas), % de personas:")
    print(res["matriz_pobre"].to_string())

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT, index=False)
    print(f"\nGuardado: {REPORT}\nGuardado: {OUT_OFICIAL}")


if __name__ == "__main__":
    main()
