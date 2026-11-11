"""Parámetros agregados para el modo simulado (paso 6 del diseño).

Lo corre solo quien tiene los microdatos. Resume la tabla canónica de
hogares (GEIH) y el registro (Sisbén) en proporciones y momentos por
grupo, para que `generador.py` produzca una población sintética con las
columnas canónicas sin versionar ningún hogar.

Cadena de condicionales (diseño, sección 4):
  departamento → zona | depto → dominio de la línea | depto × zona →
  (ciclo de vida, cuartos, pisos) | depto × zona → paredes | zona × nivel
  de pisos → jefe mujer | zona × ciclo → ingreso | depto × zona × nivel de
  pisos (proporción sin ingreso, media y desviación del log-ingreso, más el
  efecto de jefe mujer y paredes precarias) → P(T | celda) del registro.

Protección de datos: un grupo con menos de `UMBRAL` hogares no se guarda;
el generador usa el del nivel superior (depto × zona → depto → nacional),
la misma idea de la cadena de respaldos del Hot-Deck. P(T | celda) se
guarda por celda exacta, tomando el primer nivel de la cadena con al
menos `UMBRAL` hogares del registro. El JSON solo tiene proporciones y
momentos, con el número de hogares de cada grupo para auditarlo.

Las proporciones son de la muestra (sin factor de expansión), igual que
la evaluación semisintética, que usa los hogares de la encuesta.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.simulacion.calibrar
Salida: src/simulacion/parametros/poblacion_2024.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import PISOS_NIVEL, claves_por_nivel
from src.simulacion import contrato
from src.utils.variables_canonicas import edad_a_ciclo

logger = logging.getLogger(__name__)

UMBRAL = 30
CUARTOS_MAX = 6  # 6 = seis o más (la celda solo distingue 1, 2 y 3 o más)
PARAMETROS = Path(__file__).parent / "parametros" / "poblacion_2024.json"
TODOS = "*"
SEP = "|"


def _nivel_pisos(pisos: pd.Series) -> pd.Series:
    return pisos.astype(str).map(PISOS_NIVEL["geih"])


def variables(hogares: pd.DataFrame) -> pd.DataFrame:
    """Las variables de la cadena, a partir de las columnas canónicas."""
    cuartos = pd.to_numeric(hogares["viv_cuartos"], errors="coerce").clip(upper=CUARTOS_MAX).astype(int)
    ingreso = pd.to_numeric(hogares["ingreso_percapita"], errors="coerce")
    return pd.DataFrame({
        "depto": hogares["geo_depto"].astype(str), "zona": hogares["geo_zona"].astype(str),
        "dominio": hogares["dominio_pm"].astype(str), "ciclo": edad_a_ciclo(hogares["jefe_edad"]).astype(str),
        "vivienda": edad_a_ciclo(hogares["jefe_edad"]).astype(str) + SEP + cuartos.astype(str) + SEP
                    + hogares["viv_pisos"].astype(str),
        "nivel_pisos": _nivel_pisos(hogares["viv_pisos"]), "paredes": hogares["viv_paredes"].astype(str),
        "mujer": (hogares["jefe_sexo"].astype(str) == "2").astype(float),
        "precaria": (hogares["viv_paredes"].astype(str) != "1").astype(float),
        "ingreso": ingreso, "y": np.log1p(ingreso.clip(lower=0)),
    }, index=hogares.index)


def distribuciones(v: pd.DataFrame, por: list[list[str]], columna: str) -> dict:
    """Proporciones de `columna` dentro de cada grupo de cada nivel de
    `por` (del más fino al más grueso; [] es el nacional). Solo grupos con
    al menos UMBRAL hogares."""
    out = {}
    for claves in por:
        grupos = v.groupby(claves) if claves else [((), v)]
        for k, g in grupos:
            if len(g) < UMBRAL:
                continue
            clave = SEP.join(k if isinstance(k, tuple) else (k,)) if claves else TODOS
            out[clave] = dict(n=int(len(g)), p=g[columna].value_counts(normalize=True).sort_index().round(6).to_dict())
    return out


def modelo_ingreso(v: pd.DataFrame) -> dict:
    """Proporción sin ingreso y log-ingreso de los que tienen ingreso por
    grupo, con el efecto común de jefe mujer y paredes precarias (efectos
    fijos de depto × zona × nivel de pisos)."""
    pos = v[v["ingreso"] > 0].copy()
    pos["g"] = pos["depto"] + SEP + pos["zona"] + SEP + pos["nivel_pisos"]
    z = pos[["mujer", "precaria"]] - pos.groupby("g")[["mujer", "precaria"]].transform("mean")
    yd = pos["y"] - pos.groupby("g")["y"].transform("mean")
    coef = np.linalg.lstsq(z.to_numpy(), yd.to_numpy(), rcond=None)[0]
    pos["resid"] = pos["y"] - pos[["mujer", "precaria"]].to_numpy() @ coef  # log-ingreso sin el efecto de X
    v = v.assign(cero=(v["ingreso"] <= 0).astype(float), g=TODOS)
    pos["g"] = TODOS
    grupos = {}
    for claves in (["depto", "zona", "nivel_pisos"], ["depto", "zona"], ["depto"], ["g"]):
        todos = v.groupby(claves).agg(n=("cero", "size"), p_cero=("cero", "mean"))
        positivos = pos.groupby(claves)["resid"].agg(["mean", "std", "size"])
        tabla = todos.join(positivos, how="inner")
        tabla = tabla[(tabla["n"] >= UMBRAL) & (tabla["size"] >= UMBRAL)]
        for k, f in tabla.iterrows():
            clave = SEP.join(k) if isinstance(k, tuple) else str(k)
            grupos[clave] = dict(n=int(f["n"]), p_cero=round(float(f["p_cero"]), 6),
                                 media=round(float(f["mean"]), 6), sd=round(float(f["std"]), 6))
    return dict(coef=dict(mujer=round(float(coef[0]), 6), precaria=round(float(coef[1]), 6)), grupos=grupos)


def p_t_por_celda_exacta(hogares: pd.DataFrame, registro: pd.DataFrame) -> dict:
    """P(T = A o B | celda) para cada celda exacta de `hogares`, del primer
    nivel de la cadena de respaldos con al menos UMBRAL hogares del
    registro."""
    reg = registro[registro["Clasificacion"].notna()]
    t = reg["Grupo"].isin(["A", "B"]).astype(float).to_numpy()
    niveles_h = claves_por_nivel(hogares, edad_en_codigos=False)
    niveles_r = claves_por_nivel(reg, edad_en_codigos=True)
    exacta = niveles_h[0][1].astype(str).to_numpy()
    p = pd.Series(np.nan, index=hogares.index)
    for (_, clave_h), (_, clave_r) in zip(niveles_h, niveles_r):
        agg = pd.DataFrame({"k": clave_r.astype(str).to_numpy(), "t": t}).groupby("k")["t"].agg(["mean", "size"])
        agg = agg[agg["size"] >= UMBRAL]["mean"]
        faltan = p.isna()
        p[faltan] = clave_h.astype(str)[faltan].map(agg)
    p = p.fillna(float(t.mean()))
    return pd.Series(p.to_numpy(), index=exacta).groupby(level=0).first().round(6).to_dict()


def calibrar(hogares: pd.DataFrame, registro: pd.DataFrame) -> dict:
    contrato.validar(hogares, "hogares")
    contrato.validar(registro, "registro")
    v = variables(hogares)
    reg = registro[registro["Clasificacion"].notna()]
    return dict(
        version=1, umbral=UMBRAL, n_hogares=int(len(v)), cuartos_max=CUARTOS_MAX,
        depto=distribuciones(v, [[]], "depto"),
        zona=distribuciones(v, [["depto"], []], "zona"),
        dominio=distribuciones(v, [["depto", "zona"], ["zona"]], "dominio"),
        vivienda=distribuciones(v, [["depto", "zona"], ["depto"], []], "vivienda"),
        paredes=distribuciones(v, [["zona", "nivel_pisos"], ["nivel_pisos"], []], "paredes"),
        mujer=distribuciones(v.assign(m=v["mujer"].astype(int).astype(str)), [["zona", "ciclo"], []], "m"),
        ingreso=modelo_ingreso(v),
        p_t_celda=p_t_por_celda_exacta(hogares, registro),
        p_t_media=round(float(reg["Grupo"].isin(["A", "B"]).mean()), 6),
    )


def main() -> None:
    from src.simulacion.evaluacion import HOGARES, REGISTRO

    hogares = pd.read_parquet(HOGARES, columns=contrato.columnas("hogares"))
    registro = pd.read_parquet(REGISTRO, columns=contrato.columnas("registro"))
    p = calibrar(hogares, registro)
    PARAMETROS.parent.mkdir(exist_ok=True)
    PARAMETROS.write_text(json.dumps(p, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"Guardado: {PARAMETROS} ({p['n_hogares']:,} hogares; {len(p['p_t_celda'])} celdas con P(T | celda))")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()
