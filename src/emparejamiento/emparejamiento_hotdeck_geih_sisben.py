"""Hot-Deck GEIH (receptor) <- Sisbén IV (donante) sobre las bases ESTANDARIZADAS.

Receptor: una fila por hogar GEIH (jefe P6050==1) -> geih_estandarizado_2024.parquet
Donante : una fila por hogar Sisbén (jefe PER003==1) -> sisben_estandarizado_2024.parquet
          (o la version con Bogotá si existe sisben_estandarizado_2024_con_bogota.parquet)

Celda (desde el 2026-11-14) = geo_depto + tramo de edad del jefe + tramo
de número de cuartos (`viv_cuartos`) + nivel de material de pisos + tramo
de personas del hogar (1-2, 3 o más) + tramo de menores de 18 años (0, 1,
2 o más).

Los pisos entran por la escala común de
`docs/insumos/HOMOLOGACION_VIVIENDA_GEIH_SISBEN.md`, agrupada en tres
niveles (acabado | cemento o madera burda | tierra); los códigos crudos no
se comparan entre fuentes (en pisos van al revés). Personas y menores son
conteos (`hog_num_personas`, `hog_num_menores`) y no necesitan tabla de
equivalencias; se agrupan en tramos para no fragmentar la celda.

Cómo se eligió (`src/validacion/comparar_celdas_hotdeck_vivienda.py` y
`src/validacion/candidatas_celda_catalogo.py`): pisos subió la correlación
entre P(T | celda) y la pobreza monetaria del receptor de 0,20 a 0,29
(2026-11-02); personas y menores la suben a 0,41 y cierran el ancho de las
cotas de Fréchet por celda de 0,200 a 0,148 (2026-11-14), con 99,9 % de
los hogares en celda exacta y 3,7 % en celdas con menos de 30 donantes
(personas en tres tramos, 1-2, 3-4 y 5 o más, cierra igual pero deja
5,1 % en celdas pequeñas, sobre el umbral del 5 %).
Las demás variables comunes a las tres fuentes no aportan (zona, paredes,
sexo del jefe, servicios), no homologan (tipo de vivienda, tenencia) o son
privaciones del IPM (acueducto, alcantarillado: tautología con el
resultado). Las celdas anteriores quedan como sensibilidad
(`incluir_menores=False`, `incluir_personas=False`, `incluir_pisos=False`).
Degradación jerárquica (se suelta primero la variable que menos aporta):
    celda_exacta (depto+edad+cuartos+pisos+personas+menores) -> sin_menores
    -> sin_personas (la celda del 2026-11-02) -> sin_pisos (depto+edad+cuartos)
    -> solo_depto_edad -> solo_depto -> pool_nacional
Solo se usan como donantes hogares con tratamiento (Clasificacion) observado.
El donante se sortea con probabilidad proporcional a su factor de expansión
(`fex`): el Sisbén nacional de ANDA es una muestra expandible (1,83
millones de hogares, 11,4 millones expandidos) que sobrerrepresenta los
grupos A y B; el de Bogotá (SDP) es el registro completo (`fex` = 1).
Hasta el 2026-11-21 se sorteaba sin ponderar y la proporción de A/B
imputada salía 44,7 % en vez de 42,2 % (`peso_donante`).
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
TRAMOS_PERSONAS = [0, 2, 1000]
LABELS_PERSONAS = ["1a2personas", "3omaspersonas"]
TRAMOS_MENORES = [-1, 0, 1, 1000]
LABELS_MENORES = ["0menores", "1menor", "2omasmenores"]
TRAT = ["Grupo", "Nivel", "Clasificacion"]
# Columnas canónicas que necesita la celda, en receptor y donante.
CELDA_COLUMNAS = ["geo_depto", "jefe_edad", "viv_cuartos", "viv_pisos", "hog_num_personas", "hog_num_menores"]

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


def _tramo(df: pd.DataFrame, columna: str, cortes: list, etiquetas: list[str]) -> pd.Series:
    """Tramo de un conteo; sin la columna o fuera de rango queda "NA"."""
    valor = pd.to_numeric(df[columna], errors="coerce") if columna in df else pd.Series(np.nan, index=df.index)
    return pd.cut(valor, bins=cortes, labels=etiquetas).astype("object").fillna("NA")


def _tramo_cuartos(df: pd.DataFrame) -> pd.Series:
    return _tramo(df, "viv_cuartos", TRAMOS_CUARTOS, LABELS_CUARTOS)


def tramo_personas(df: pd.DataFrame) -> pd.Series:
    return _tramo(df, "hog_num_personas", TRAMOS_PERSONAS, LABELS_PERSONAS)


def tramo_menores(df: pd.DataFrame) -> pd.Series:
    return _tramo(df, "hog_num_menores", TRAMOS_MENORES, LABELS_MENORES)


def nivel_pisos(df: pd.DataFrame, sisben: bool) -> pd.Series:
    """Nivel común de pisos; `sisben` elige la tabla de códigos de la fuente."""
    if "viv_pisos" not in df:
        return pd.Series("NA", index=df.index, dtype="object")
    codigos = pd.to_numeric(df["viv_pisos"], errors="coerce").astype("Int64").astype("string")
    return codigos.map(PISOS_NIVEL["sisben" if sisben else "geih"]).astype("object").fillna("NA")


def construir_celda(df: pd.DataFrame, edad_en_codigos: bool = False, incluir_vivienda: bool = True,
                    incluir_pisos: bool = True, incluir_personas: bool = True,
                    incluir_menores: bool = True) -> pd.Series:
    """`edad_en_codigos=True` marca al Sisbén (edad en ciclo de vida y su
    tabla de pisos). Cada `incluir_*=False` corta la celda ahí:
    `incluir_menores=False` deja la celda con personas; `incluir_personas=False`
    la del 2026-11-02 (depto + edad + cuartos + pisos); `incluir_pisos=False`
    la anterior a esa; `incluir_vivienda=False` deja depto + edad."""
    base = df["geo_depto"].astype(str).str.zfill(2) + "|" + _tramo_edad(df, edad_en_codigos).astype(str)
    if not incluir_vivienda:
        return base
    base = base + "|" + _tramo_cuartos(df).astype(str)
    if not incluir_pisos:
        return base
    base = base + "|" + nivel_pisos(df, sisben=edad_en_codigos).astype(str)
    if not incluir_personas:
        return base
    base = base + "|" + tramo_personas(df).astype(str)
    if not incluir_menores:
        return base
    return base + "|" + tramo_menores(df).astype(str)


def claves_por_nivel(df: pd.DataFrame, edad_en_codigos: bool = False, incluir_vivienda: bool = True,
                     incluir_pisos: bool = True, incluir_personas: bool = True,
                     incluir_menores: bool = True) -> list[tuple[str, pd.Series]]:
    """Cadena de respaldos: (nombre del nivel, clave de celda), de la más
    fina a la más gruesa. La usan el Hot-Deck y la simulación
    (`src/simulacion/vinculo.py`), para que sorteen igual. Después del
    último nivel queda el sorteo en todo el registro (`pool_nacional`).
    El primer nivel se llama siempre `celda_exacta`, aunque la celda de
    sensibilidad sea más corta."""
    pasos = [  # (nombre del respaldo, qué se quita, si ese paso existe en esta celda), en el orden en que se sueltan
        ("sin_menores", "incluir_menores", incluir_vivienda and incluir_pisos and incluir_personas and incluir_menores),
        ("sin_personas", "incluir_personas", incluir_vivienda and incluir_pisos and incluir_personas),
        ("sin_pisos", "incluir_pisos", incluir_vivienda and incluir_pisos),
        ("solo_depto_edad", "incluir_vivienda", incluir_vivienda),
    ]
    kw = dict(incluir_vivienda=incluir_vivienda, incluir_pisos=incluir_pisos, incluir_personas=incluir_personas,
              incluir_menores=incluir_menores)
    configs = [("celda_exacta", dict(kw))]
    for nombre, quitar, aplica in pasos:
        if aplica:
            kw = {**kw, quitar: False}
            configs.append((nombre, dict(kw)))
    niveles = [(nombre, construir_celda(df, edad_en_codigos=edad_en_codigos, **c)) for nombre, c in configs]
    niveles.append(("solo_depto", niveles[-1][1].str.split("|").str[0]))
    return niveles


def peso_donante(donante: pd.DataFrame) -> np.ndarray:
    """Factor de expansión de cada donante del Sisbén. Se exige: sin él, el
    sorteo y las proporciones por celda tratarían la muestra de ANDA como si
    fuera el registro y sobrerrepresentarían A y B, sin dar error."""
    if "fex" not in donante:
        raise ValueError("El donante necesita `fex` (factor de expansión del Sisbén; 1 en Bogotá)")
    w = pd.to_numeric(donante["fex"], errors="coerce").to_numpy(float)
    if not np.isfinite(w).all() or (w <= 0).any():
        raise ValueError("`fex` del donante debe ser positivo y sin faltantes")
    return w


def proporcion_por_celda(indicador: pd.Series, clave: pd.Series, peso: np.ndarray) -> pd.Series:
    """Proporción ponderada por `fex` de un indicador entre los donantes de
    cada celda (la que usan el Hot-Deck, la FHDI y las cotas de Fréchet)."""
    x = pd.Series(np.asarray(indicador, float) * peso)
    w = pd.Series(peso)
    c = np.asarray(clave)
    return x.groupby(c).sum() / w.groupby(c).sum()


def _sortear(grupos: dict, claves: pd.Series, rng, peso: np.ndarray) -> np.ndarray:
    """Para cada clave devuelve el indice (posicional) de un donante sorteado
    con probabilidad proporcional a `peso`; -1 si la clave no tiene donantes."""
    res = np.full(len(claves), -1, dtype=np.int64)
    pos = pd.Series(np.arange(len(claves)))
    for clave, idx in pos.groupby(claves.values).__iter__():
        donantes = grupos.get(clave)
        if donantes is not None and len(donantes):
            acum = np.cumsum(peso[donantes])
            res[idx.values] = donantes[np.searchsorted(acum, rng.random(len(idx)) * acum[-1], side="right")]
    return res


def hotdeck(receptor: pd.DataFrame, donante: pd.DataFrame, seed: int = 42, incluir_vivienda: bool = True,
            incluir_pisos: bool = True, incluir_personas: bool = True, incluir_menores: bool = True) -> pd.DataFrame:
    # Sin la columna, todo caería al respaldo correspondiente sin dar error.
    requeridas = {"viv_pisos": incluir_vivienda and incluir_pisos,
                  "hog_num_personas": incluir_vivienda and incluir_pisos and incluir_personas,
                  "hog_num_menores": incluir_vivienda and incluir_pisos and incluir_personas and incluir_menores}
    faltan = [c for c, requerida in requeridas.items() if requerida and c not in set(receptor) & set(donante)]
    if faltan:
        raise ValueError(f"La celda requiere {faltan} en receptor y donante")
    rng = np.random.default_rng(seed)
    donante = donante[donante["Clasificacion"].notna()].reset_index(drop=True)
    peso = peso_donante(donante)
    receptor = receptor.copy().reset_index(drop=True)

    # Niveles de celda, de más fina a más gruesa; cada uno solo se usa para
    # los receptores sin donante en el anterior. Los `incluir_*=False`
    # reproducen las celdas anteriores, para sensibilidad.
    kw = dict(incluir_vivienda=incluir_vivienda, incluir_pisos=incluir_pisos, incluir_personas=incluir_personas,
              incluir_menores=incluir_menores)
    claves = [(nombre, cr, cd) for (nombre, cr), (_, cd) in
              zip(claves_por_nivel(receptor, **kw), claves_por_nivel(donante, edad_en_codigos=True, **kw))]

    elegido = np.full(len(receptor), -1, dtype=np.int64)
    nivel = np.full(len(receptor), "", dtype=object)
    for nombre, cr, cd in claves:
        falta = elegido < 0
        if not falta.any():
            break
        grupos = {k: v.values for k, v in pd.Series(np.arange(len(donante))).groupby(cd.values)}
        e = _sortear(grupos, cr[falta].reset_index(drop=True), rng, peso)
        elegido[falta] = e
        nivel[falta] = np.where(e >= 0, nombre, "").astype(object)

    falta = elegido < 0
    if falta.any():
        acum = np.cumsum(peso)
        elegido[falta] = np.searchsorted(acum, rng.random(int(falta.sum())) * acum[-1], side="right")
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
    don = pd.read_parquet(sb, columns=[*CELDA_COLUMNAS, *TRAT, "fex"])
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
