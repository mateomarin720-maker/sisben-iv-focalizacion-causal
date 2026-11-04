"""Hot-Deck GEIH (receptor) <- Sisbén IV (donante) sobre las bases ESTANDARIZADAS.

Receptor: una fila por hogar GEIH (jefe P6050==1) -> geih_estandarizado_2024.parquet
Donante : una fila por hogar Sisbén (jefe PER003==1) -> sisben_estandarizado_2024.parquet
          (o la version con Bogotá si existe sisben_estandarizado_2024_con_bogota.parquet)

Celda (desde el 2026-11-02) = geo_depto + tramo de edad del jefe + tramo
de número de cuartos (`viv_cuartos`) + nivel de material de pisos.

Los pisos entran por la escala común de
`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`, agrupada en tres
niveles (acabado | cemento o madera burda | tierra); los códigos crudos no
se comparan entre fuentes (en pisos van al revés). Se eligió esta celda
frente a la anterior (sin pisos) y a una con pisos y paredes
(`src/validacion/comparar_celdas_hotdeck_vivienda.py`): con pisos, la
correlación entre P(T | celda) y la pobreza monetaria del receptor sube de
0,20 a 0,29 con 99,98 % de cobertura; paredes triplica las celdas sin
mejorar nada. La celda anterior queda como sensibilidad
(`incluir_pisos=False`).
Degradación jerárquica:
    celda_exacta (depto+edad+cuartos+pisos) -> sin_pisos (depto+edad+cuartos)
    -> solo_depto_edad -> solo_depto -> pool_nacional
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

from src.utils.variables_canonicas import CODIGOS_CICLO, edad_a_ciclo

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
# Tramos en src/utils/variables_canonicas.py (los mismos para GEIH y el Sisbén de Bogotá).
CODIGO_A_CICLO = {c: f"ciclo{c}" for c in CODIGOS_CICLO}
TRAMOS_CUARTOS = [0, 1, 2, 100]
LABELS_CUARTOS = ["1cuarto", "2cuartos", "3omascuartos"]
TRAT = ["Grupo", "Nivel", "Clasificacion"]

# Código crudo de material de pisos -> nivel común (HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md).
PISOS_NIVEL = {
    "geih": {"4": "acabado", "5": "acabado", "6": "acabado", "7": "acabado",
             "2": "cemento_madera", "3": "cemento_madera", "1": "tierra"},
    "sisben": {"1": "acabado", "2": "acabado", "3": "cemento_madera", "4": "cemento_madera", "5": "tierra"},
}


def _tramo_edad(df: pd.DataFrame, edad_en_codigos: bool) -> pd.Series:
    if edad_en_codigos:  # Sisbén: jefe_edad ya es codigo de ciclo de vida
        return df["jefe_edad"].astype(str).map(CODIGO_A_CICLO).fillna("NA")
    return edad_a_ciclo(df["jefe_edad"]).map(CODIGO_A_CICLO).fillna("NA")  # GEIH: jefe_edad en años


def _tramo_cuartos(df: pd.DataFrame) -> pd.Series:
    cuartos = pd.to_numeric(df["viv_cuartos"], errors="coerce") if "viv_cuartos" in df else pd.Series(np.nan, index=df.index)
    return pd.cut(cuartos, bins=TRAMOS_CUARTOS, labels=LABELS_CUARTOS).astype("object").fillna("NA")


def nivel_pisos(df: pd.DataFrame, sisben: bool) -> pd.Series:
    """Nivel común de pisos; `sisben` elige la tabla de códigos de la fuente."""
    if "viv_pisos" not in df:
        return pd.Series("NA", index=df.index, dtype="object")
    codigos = pd.to_numeric(df["viv_pisos"], errors="coerce").astype("Int64").astype("string")
    return codigos.map(PISOS_NIVEL["sisben" if sisben else "geih"]).astype("object").fillna("NA")


def construir_celda(df: pd.DataFrame, edad_en_codigos: bool = False, incluir_vivienda: bool = True,
                    incluir_pisos: bool = True) -> pd.Series:
    """`edad_en_codigos=True` marca al Sisbén (edad en ciclo de vida y su
    tabla de pisos). `incluir_vivienda=False` deja depto + edad;
    `incluir_pisos=False` deja la celda anterior al 2026-11-02."""
    base = df["geo_depto"].astype(str).str.zfill(2) + "|" + _tramo_edad(df, edad_en_codigos).astype(str)
    if not incluir_vivienda:
        return base
    base = base + "|" + _tramo_cuartos(df).astype(str)
    if not incluir_pisos:
        return base
    return base + "|" + nivel_pisos(df, sisben=edad_en_codigos).astype(str)


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


def hotdeck(receptor: pd.DataFrame, donante: pd.DataFrame, seed: int = 42, incluir_vivienda: bool = True,
            incluir_pisos: bool = True) -> pd.DataFrame:
    if incluir_vivienda and incluir_pisos and not {"viv_pisos"} <= set(receptor) & set(donante):
        # Sin la columna todo caería al respaldo sin pisos sin dar error.
        raise ValueError("La celda con pisos requiere `viv_pisos` en receptor y donante")
    rng = np.random.default_rng(seed)
    donante = donante[donante["Clasificacion"].notna()].reset_index(drop=True)
    receptor = receptor.copy().reset_index(drop=True)

    # Niveles de celda, de más fina a más gruesa; cada uno solo se usa para
    # los receptores sin donante en el anterior. `incluir_pisos=False`
    # reproduce la celda anterior y `incluir_vivienda=False` la de
    # depto + edad, para sensibilidad.
    niveles = []
    if incluir_vivienda and incluir_pisos:
        niveles.append(("celda_exacta", dict(incluir_vivienda=True, incluir_pisos=True)))
    if incluir_vivienda:
        niveles.append(("celda_exacta" if not niveles else "sin_pisos",
                        dict(incluir_vivienda=True, incluir_pisos=False)))
    niveles.append(("celda_exacta" if not niveles else "solo_depto_edad", dict(incluir_vivienda=False)))

    claves = [(nombre, construir_celda(receptor, **kw), construir_celda(donante, edad_en_codigos=True, **kw))
              for nombre, kw in niveles]
    claves.append(("solo_depto", claves[-1][1].str.split("|").str[0], claves[-1][2].str.split("|").str[0]))

    elegido = np.full(len(receptor), -1, dtype=np.int64)
    nivel = np.full(len(receptor), "", dtype=object)
    for nombre, cr, cd in claves:
        falta = elegido < 0
        if not falta.any():
            break
        grupos = {k: v.values for k, v in pd.Series(np.arange(len(donante))).groupby(cd.values)}
        e = _sortear(grupos, cr[falta].reset_index(drop=True), rng)
        elegido[falta] = e
        nivel[falta] = np.where(e >= 0, nombre, "").astype(object)

    falta = elegido < 0
    if falta.any():
        elegido[falta] = rng.integers(0, len(donante), size=int(falta.sum()))
        nivel[falta] = "pool_nacional"

    for c in TRAT:
        receptor[f"{c}_hotdeck"] = donante[c].values[elegido]
    receptor["_hotdeck_nivel"] = nivel
    receptor["_hotdeck_celda"] = claves[0][1].values
    if "viv_pisos" in receptor:
        receptor["viv_pisos_nivel"] = nivel_pisos(receptor, sisben=False).values
    return receptor


def main() -> None:
    if not GEIH.exists():
        raise SystemExit(f"Falta {GEIH}: corra src.armonizacion.armonizar_geih_hogar_2024")
    sb = SISBEN_BOG if SISBEN_BOG.exists() else SISBEN
    logger.info("Donante: %s", sb)
    rec = pd.read_parquet(GEIH)
    don = pd.read_parquet(sb, columns=["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", *TRAT])
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
