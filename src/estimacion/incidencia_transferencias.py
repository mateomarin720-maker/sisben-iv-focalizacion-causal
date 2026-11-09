"""A quién llegan las ayudas del gobierno que los hogares declaran en la GEIH 2024.

Descriptivo, con datos reales: no usa el Hot-Deck ni estima un efecto causal. La
participación se declara en la misma encuesta que el ingreso (`P750S2`, ayudas del
gobierno; `P1661S1`-`S3`, Más Familias en Acción, Jóvenes en Acción y Colombia
Mayor). No identifica un efecto: quién participa no es aleatorio y la participación
en Colombia Mayor sube gradualmente con la edad, sin salto aprovechable.

"Sin ayuda" es contabilidad: al ingreso se le resta el dinero declarado, suponiendo
que el hogar no cambiaría su conducta sin él. El monto es `P750S2A1`, que ya contiene
el de cada programa (no se suman: `docs/metodologia/pobreza_monetaria/`).

Las cantidades son de un mes promedio de 2024: el factor de expansión de cada mes
reproduce la población, así que se divide por 12.

Uso:
    poetry run python -m src.estimacion.incidencia_transferencias
Interpretación: `docs/resultados/RECOMENDACION_VARIABLES_POBREZA.md`.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.estimacion.variables_candidatas_pobreza import K3, MESES, SI, _leer
from src.utils.variables_canonicas import normalizar_llave

logger = logging.getLogger(__name__)

HOGARES_POBREZA = Path("data/2_models/pobreza_monetaria_hogar_2024.parquet")
MUESTRA = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
REPORTES = Path("docs/reports")
OUT_PROGRAMAS = REPORTES / "incidencia_transferencias_programas.csv"
OUT_QUINTILES = REPORTES / "incidencia_transferencias_quintiles.csv"
OUT_POBREZA = REPORTES / "incidencia_transferencias_pobreza.csv"
PROGRAMAS = {"familias_en_accion": "P1661S1", "jovenes_en_accion": "P1661S2", "colombia_mayor": "P1661S3"}
NO_SABE = [98, 99]
EMPLEADO_DOMESTICO = "10"  # no pertenece a la unidad de gasto (`P6050`)
MESES_ANIO = 12


def por_hogar(p: pd.DataFrame) -> pd.DataFrame:
    """De personas a hogares. La ayuda mensual solo cuenta lo que entra al ingreso de
    la unidad de gasto y deja por fuera los códigos de no sabe."""
    p = p.copy()
    llaves = [p[c] for c in K3 + ["mes"]]
    monto = pd.to_numeric(p["P750S2A1"], errors="coerce")
    valido = p["P750S2"].eq(SI) & ~monto.isin(NO_SABE) & p["P6050"].ne(EMPLEADO_DOMESTICO)
    p["ayuda_mes"] = monto.where(valido, 0.0).fillna(0.0) / MESES_ANIO
    columnas = ["P750S2", *PROGRAMAS.values()]
    salida = {"ayuda_mes": p["ayuda_mes"].groupby(llaves).sum(),
              "alguna_ayuda": p[columnas].eq(SI).any(axis=1).groupby(llaves).any()}
    salida.update({n: p[c].eq(SI).groupby(llaves).any() for n, c in PROGRAMAS.items()})
    return pd.DataFrame(salida).reset_index()


def beneficiarios_directos(p: pd.DataFrame) -> dict[str, float]:
    """Personas que declaran haber recibido cada programa (mes promedio)."""
    peso = pd.to_numeric(p["FEX_C18"], errors="coerce").fillna(0.0) / MESES_ANIO
    res = {n: float(peso[p[c].eq(SI)].sum()) for n, c in PROGRAMAS.items()}
    res["alguna_ayuda"] = float(peso[p[["P750S2", *PROGRAMAS.values()]].eq(SI).any(axis=1)].sum())
    return res


def ingreso_sin_ayuda(ingreso_pc: np.ndarray, ayuda_mes: np.ndarray, personas: np.ndarray) -> np.ndarray:
    """Ingreso per cápita al restar la ayuda del hogar, nunca negativo."""
    return np.maximum(np.asarray(ingreso_pc, float) - np.asarray(ayuda_mes, float) / np.asarray(personas, float), 0.0)


def tabla_programas(t: pd.DataFrame, directos: dict[str, float]) -> pd.DataFrame:
    """Hogares y personas por programa, según pobreza antes de la ayuda. `t` trae
    `h` (hogares que representa cada fila), `n` (personas), `pobre_sin_ayuda` y una
    columna booleana por programa."""
    pobre = t["pobre_sin_ayuda"].to_numpy(bool)
    h, n = t["h"].to_numpy(float), t["n"].to_numpy(float)
    filas = []
    for programa in ["alguna_ayuda", *PROGRAMAS]:
        r = t[programa].to_numpy(bool)
        filas.append(dict(
            programa=programa, personas_que_declaran=directos[programa],
            hogares_receptores=h[r].sum(), personas_en_receptores=n[r].sum(),
            hogares_pobres_receptores=h[r & pobre].sum(), personas_pobres_receptores=n[r & pobre].sum(),
            hogares_pobres_sin_programa=h[~r & pobre].sum(), personas_pobres_sin_programa=n[~r & pobre].sum(),
            hogares_no_pobres_receptores=h[r & ~pobre].sum(), personas_no_pobres_receptores=n[r & ~pobre].sum(),
            pct_receptores_pobres=100 * h[r & pobre].sum() / h[r].sum(),
            pct_pobres_cubiertos=100 * h[r & pobre].sum() / h[pobre].sum(),
            pct_no_pobres_cubiertos=100 * h[r & ~pobre].sum() / h[~pobre].sum()))
    return pd.DataFrame(filas)


def tabla_pobreza(y_con: np.ndarray, y_sin: np.ndarray, linea: np.ndarray, h: np.ndarray, n: np.ndarray, nombre: str) -> dict:
    """Pobres con y sin la ayuda, y quienes quedan sobre la línea solo por ella."""
    con, sin = y_con < linea, y_sin < linea
    cruzan = sin & ~con
    fgt1 = lambda y: float(np.average(((linea - y) / linea).clip(0, 1) * (y < linea), weights=h)) * 100  # noqa: E731
    return dict(linea=nombre, pct_hogares_con_ayuda=100 * h[con].sum() / h.sum(), pct_hogares_sin_ayuda=100 * h[sin].sum() / h.sum(),
                hogares_con_ayuda=h[con].sum(), hogares_sin_ayuda=h[sin].sum(), personas_con_ayuda=n[con].sum(),
                personas_sin_ayuda=n[sin].sum(), hogares_sobre_linea_por_ayuda=h[cruzan].sum(),
                personas_sobre_linea_por_ayuda=n[cruzan].sum(), brecha_con_ayuda=fgt1(y_con), brecha_sin_ayuda=fgt1(y_sin))


def quintiles(y_sin: np.ndarray, h: np.ndarray) -> np.ndarray:
    """Quintil (0 el más pobre) de hogares por ingreso sin ayuda, con pesos."""
    orden = np.argsort(y_sin, kind="stable")
    q = np.empty(len(y_sin), dtype=int)
    q[orden] = np.minimum(((np.cumsum(h[orden]) - h[orden]) / h.sum() * 5).astype(int), 4)
    return q


def tabla_quintiles(t: pd.DataFrame) -> pd.DataFrame:
    h, n, ayuda = t["h"].to_numpy(float), t["n"].to_numpy(float), t["ayuda_mes"].to_numpy(float)
    q, r = quintiles(t["y_sin"].to_numpy(float), h), t["alguna_ayuda"].to_numpy(bool)
    total = (ayuda * h).sum()
    return pd.DataFrame([dict(quintil=k + 1, hogares=h[q == k].sum(), personas=n[q == k].sum(),
                              hogares_con_ayuda=h[(q == k) & r].sum(), personas_con_ayuda=n[(q == k) & r].sum(),
                              pct_hogares_con_ayuda=100 * h[(q == k) & r].sum() / h[q == k].sum(),
                              millones_al_anio=(ayuda * h)[q == k].sum() * MESES_ANIO / 1e6,
                              pct_dinero=100 * (ayuda * h)[q == k].sum() / total) for k in range(5)])


def _personas() -> pd.DataFrame:
    partes = []
    for mes in MESES:
        d = _leer(mes, "otros_ingresos", K3 + ["ORDEN", "FEX_C18", "P750S2", "P750S2A1", *PROGRAMAS.values()])
        c = _leer(mes, "caracteristicas_generales", K3 + ["ORDEN", "P6050"])
        partes.append(d.merge(c, on=K3 + ["ORDEN"], how="left", validate="1:1").assign(mes=mes))
    return pd.concat(partes, ignore_index=True)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    p = _personas()
    b = pd.read_parquet(HOGARES_POBREZA)
    m = pd.read_parquet(MUESTRA, columns=["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes", "fex", "hog_num_personas"]).rename(
        columns={"llave_directorio": "DIRECTORIO", "llave_secuencia_p": "SECUENCIA_P", "llave_hogar": "HOGAR"})
    for d in (b, m):
        for c in K3:
            d[c] = normalizar_llave(d[c])
    t = b.merge(m, on=K3 + ["mes"], validate="1:1").merge(por_hogar(p), on=K3 + ["mes"], how="left", validate="1:1")
    for c in ["alguna_ayuda", *PROGRAMAS]:
        t[c] = t[c].eq(True)
    t["ayuda_mes"] = t["ayuda_mes"].fillna(0.0)
    t["h"] = pd.to_numeric(t["fex"], errors="coerce") / MESES_ANIO
    t["n"] = t["h"] * pd.to_numeric(t["hog_num_personas"], errors="coerce")
    y_con = t["ingreso_pc_ug"].to_numpy(float)
    t["y_sin"] = ingreso_sin_ayuda(y_con, t["ayuda_mes"], t["personas_ug"])
    t["pobre_sin_ayuda"] = t["y_sin"] < t["LP_2024"]

    h, n = t["h"].to_numpy(float), t["n"].to_numpy(float)
    programas = tabla_programas(t, beneficiarios_directos(p))
    pobreza = pd.DataFrame([tabla_pobreza(y_con, t["y_sin"].to_numpy(float), t[c].to_numpy(float), h, n, nombre)
                            for c, nombre in (("LP_2024", "pobreza"), ("LI_2024", "pobreza_extrema"))])
    qs = tabla_quintiles(t)
    REPORTES.mkdir(parents=True, exist_ok=True)
    programas.to_csv(OUT_PROGRAMAS, index=False)
    pobreza.to_csv(OUT_POBREZA, index=False)
    qs.to_csv(OUT_QUINTILES, index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(f"=== Incidencia de ayudas declaradas: {h.sum():,.0f} hogares y {n.sum():,.0f} personas en un mes promedio ===")
    print(f"Dinero declarado al año: {(t['ayuda_mes'] * h).sum() * MESES_ANIO / 1e9:,.1f} miles de millones de pesos\n")
    print(programas.round(1).T.to_string(), "\n\n", pobreza.round(2).T.to_string(), "\n\n", qs.round(1).T.to_string())


if __name__ == "__main__":
    main()
