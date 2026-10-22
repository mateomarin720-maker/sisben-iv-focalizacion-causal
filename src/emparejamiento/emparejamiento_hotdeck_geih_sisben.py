"""Hot-Deck GEIH (receptor) <- Sisbén IV (donante) sobre las bases ESTANDARIZADAS.

Receptor: una fila por hogar GEIH (jefe P6050==1) -> geih_estandarizado_2024.parquet
Donante : una fila por hogar Sisbén (jefe PER003==1) -> sisben_estandarizado_2024.parquet
          (o la version con Bogotá si existe sisben_estandarizado_2024_con_bogota.parquet)

Celda = geo_depto + tramo de edad del jefe + tramo de número de cuartos
(`viv_cuartos`) — ver "Próximos pasos" del documento de pipeline ("sumar
variables de vivienda a la celda"). Se usa SOLO `viv_cuartos` (un conteo
cardinal: 1, 2, 3+ cuartos) y no `viv_paredes`/`viv_pisos` porque esas dos
son categóricas y sus códigos NO están verificados entre GEIH y Sisbén
(dos sistemas de codificación independientes — ver
docs/insumos/DICCIONARIO_HOTDECK.md §8); agregarlas a la celda con una
dirección equivocada sería peor que no agregarlas. `viv_cuartos` no tiene
ese problema: es un conteo, comparable sin necesidad de homologar categorías.
Degradación jerárquica:
    celda_exacta (depto+edad+cuartos) -> solo_depto_edad (depto+edad, sin
    cuartos) -> solo_depto -> pool_nacional
Solo se usan como donantes hogares con tratamiento (Clasificacion) observado.
Valido solo a nivel poblacional: no identifica el mismo hogar (supuesto de
independencia condicional del matching estadístico).

Uso:
    poetry run python -m src.emparejamiento.emparejamiento_hotdeck_geih_sisben
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DIR = Path("data/2_models")
GEIH = DIR / "geih_estandarizado_2024.parquet"
SISBEN_BOG = DIR / "sisben_estandarizado_2024_con_bogota.parquet"
SISBEN = DIR / "sisben_estandarizado_2024.parquet"
OUT = DIR / "geih_sisben_fusionado_2024.parquet"

# Sisbén (extracto anonimizado) trae PER002 como CODIGO de ciclo de vida, no años.
# Corroborado indirectamente 2026-10-10 (ver docs/insumos/DICCIONARIO_HOTDECK.md
# §5): 3=12-17, 4=18-28, 5=29-59, 6=60+.
TRAMOS_EDAD = [0, 17, 28, 59, 200]
LABELS_EDAD = ["ciclo3", "ciclo4", "ciclo5", "ciclo6"]
CODIGO_A_CICLO = {"3": "ciclo3", "4": "ciclo4", "5": "ciclo5", "6": "ciclo6"}
TRAMOS_CUARTOS = [0, 1, 2, 100]
LABELS_CUARTOS = ["1cuarto", "2cuartos", "3omascuartos"]
TRAT = ["Grupo", "Nivel", "Clasificacion"]


def _tramo_edad(df: pd.DataFrame, edad_en_codigos: bool) -> pd.Series:
    if edad_en_codigos:  # Sisbén: jefe_edad ya es codigo de ciclo de vida
        return df["jefe_edad"].astype(str).map(CODIGO_A_CICLO).fillna("NA")
    edad = pd.to_numeric(df["jefe_edad"], errors="coerce")  # GEIH: jefe_edad en años
    return pd.cut(edad, bins=TRAMOS_EDAD, labels=LABELS_EDAD).astype("object").fillna("NA")


def _tramo_cuartos(df: pd.DataFrame) -> pd.Series:
    cuartos = pd.to_numeric(df["viv_cuartos"], errors="coerce") if "viv_cuartos" in df else pd.Series(np.nan, index=df.index)
    return pd.cut(cuartos, bins=TRAMOS_CUARTOS, labels=LABELS_CUARTOS).astype("object").fillna("NA")


def construir_celda(df: pd.DataFrame, edad_en_codigos: bool = False, incluir_vivienda: bool = True) -> pd.Series:
    base = df["geo_depto"].astype(str).str.zfill(2) + "|" + _tramo_edad(df, edad_en_codigos).astype(str)
    if incluir_vivienda:
        return base + "|" + _tramo_cuartos(df).astype(str)
    return base


def _sortear(grupos: dict, claves: pd.Series, rng) -> tuple[np.ndarray, np.ndarray]:
    """Para cada clave devuelve el indice (posicional) de un donante al azar;
    -1 si la clave no tiene donantes."""
    res = np.full(len(claves), -1, dtype=np.int64)
    pos = pd.Series(np.arange(len(claves)))
    for clave, idx in pos.groupby(claves.values).__iter__():
        donantes = grupos.get(clave)
        if donantes is not None and len(donantes):
            res[idx.values] = donantes[rng.integers(0, len(donantes), size=len(idx))]
    return res


def hotdeck(receptor: pd.DataFrame, donante: pd.DataFrame, seed: int = 42, incluir_vivienda: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    donante = donante[donante["Clasificacion"].notna()].reset_index(drop=True)
    receptor = receptor.copy().reset_index(drop=True)

    # Tres niveles de celda, de más a menos fina: depto+edad+cuartos ->
    # depto+edad -> solo depto. `incluir_vivienda=False` reproduce el
    # comportamiento anterior (solo depto+edad como celda_exacta), útil
    # para comparar sensibilidad.
    cr_full = construir_celda(receptor, incluir_vivienda=incluir_vivienda)
    cd_full = construir_celda(donante, edad_en_codigos=True, incluir_vivienda=incluir_vivienda)
    cr_depto_edad = construir_celda(receptor, incluir_vivienda=False)
    cd_depto_edad = construir_celda(donante, edad_en_codigos=True, incluir_vivienda=False)
    dr, dd = cr_depto_edad.str.split("|").str[0], cd_depto_edad.str.split("|").str[0]

    g_full = {k: v.values for k, v in pd.Series(np.arange(len(donante))).groupby(cd_full.values)}
    g_depto_edad = {k: v.values for k, v in pd.Series(np.arange(len(donante))).groupby(cd_depto_edad.values)}
    g_depto = {k: v.values for k, v in pd.Series(np.arange(len(donante))).groupby(dd.values)}

    elegido = _sortear(g_full, cr_full, rng)
    nivel = np.where(elegido >= 0, "celda_exacta", "").astype(object)

    falta = elegido < 0
    if falta.any() and incluir_vivienda:
        e2 = _sortear(g_depto_edad, cr_depto_edad[falta].reset_index(drop=True), rng)
        elegido[falta] = e2
        nivel[falta] = np.where(e2 >= 0, "solo_depto_edad", "").astype(object)

    falta = elegido < 0
    if falta.any():
        e3 = _sortear(g_depto, dr[falta].reset_index(drop=True), rng)
        elegido[falta] = e3
        nivel[falta] = np.where(e3 >= 0, "solo_depto", "").astype(object)

    falta = elegido < 0
    if falta.any():
        elegido[falta] = rng.integers(0, len(donante), size=int(falta.sum()))
        nivel[falta] = "pool_nacional"

    for c in TRAT:
        receptor[f"{c}_hotdeck"] = donante[c].values[elegido]
    receptor["_hotdeck_nivel"] = nivel
    receptor["_hotdeck_celda"] = cr_full.values
    return receptor


def main() -> None:
    if not GEIH.exists():
        raise SystemExit(f"Falta {GEIH}: corra src.armonizacion.armonizar_geih_hogar_2024")
    sb = SISBEN_BOG if SISBEN_BOG.exists() else SISBEN
    logger.info("Donante: %s", sb)
    rec = pd.read_parquet(GEIH)
    don = pd.read_parquet(sb, columns=["geo_depto", "jefe_edad", "viv_cuartos", *TRAT])
    logger.info("Receptor GEIH: %s hogares | Donante Sisbén: %s hogares", f"{len(rec):,}", f"{len(don):,}")
    out = hotdeck(rec, don)
    out.to_parquet(OUT, index=False)
    n = len(out)
    print("\n=== Resumen Hot-Deck ===")
    print(f"Hogares GEIH fusionados: {n:,}")
    print((out["_hotdeck_nivel"].value_counts() / n * 100).round(1).astype(str) + " %")
    print("\nGrupo asignado (% ponderado por fex):")
    w = pd.to_numeric(out["fex"], errors="coerce").fillna(0) if "fex" in out else pd.Series(1.0, index=out.index)
    print((w.groupby(out["Grupo_hotdeck"]).sum() / w.sum() * 100).round(1))
    print(f"\nGuardado: {OUT}")


if __name__ == "__main__":
    main()
