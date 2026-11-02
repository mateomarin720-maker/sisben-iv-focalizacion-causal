"""Outcome: pobreza monetaria sobre la muestra de estimación (hogares).

Pega a `muestra_estimacion_2024.parquet` el ingreso per cápita de la
unidad de gasto y la clasificación de pobreza **reconstruidos** por
`src/indicadores/pobreza_monetaria_geih.py` (escenario base, decisiones
D1-D7 del 2026-11-02). La metodología y la validación contra el DANE
están en `docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md` y
`docs/resultados/RESULTADOS_POBREZA_MONETARIA.md`.

Es una reconstrucción con microdatos públicos, no la cifra oficial: el
DANE cruza GEIH con registros administrativos que no son públicos.

Hasta el 2026-11-02 este script construía su propio ingreso (hogar
completo, dos líneas, ingresos ocasionales incluidos, sin imputación), con
FGT0 ≈ 39 % frente al 31,8 % oficial; la reconstrucción da 33,2 %.

Uso:
    poetry run python src/3b_preprocesamiento_monetario.py
Salida: data/2_models/muestra_estimacion_monetaria_2024.parquet (la tabla
de `3_preprocesamiento.py` + `ingreso_percapita`, `POBRE_MONETARIO`,
`POBRE_EXTREMO_MONETARIO`, `brecha_pobreza_monetaria`,
`brecha_pobreza_extrema`, `dominio_pm`, `personas_ug`).
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE = Path("data/2_models/muestra_estimacion_2024.parquet")
POBREZA_HOGAR = Path("data/2_models/pobreza_monetaria_hogar_2024.parquet")
OUT = Path("data/2_models/muestra_estimacion_monetaria_2024.parquet")
LLAVE = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]
RENOMBRAR = {
    "DIRECTORIO": "llave_directorio", "SECUENCIA_P": "llave_secuencia_p", "HOGAR": "llave_hogar",
    "ingreso_pc_ug": "ingreso_percapita", "POBRE_MONETARIA": "POBRE_MONETARIO",
    "POBRE_EXTREMA": "POBRE_EXTREMO_MONETARIO", "BRECHA_PM": "brecha_pobreza_monetaria",
    "BRECHA_PE": "brecha_pobreza_extrema",
}


def pegar_pobreza(base: pd.DataFrame, pobreza: pd.DataFrame) -> pd.DataFrame:
    pobreza = pobreza.rename(columns=RENOMBRAR)
    for c in LLAVE:
        base[c] = base[c].astype("string")
        pobreza[c] = pobreza[c].astype("string")
    cols = [*LLAVE, "ingreso_percapita", "personas_ug", "dominio_pm", "POBRE_MONETARIO",
            "POBRE_EXTREMO_MONETARIO", "brecha_pobreza_monetaria", "brecha_pobreza_extrema"]
    df = base.merge(pobreza[cols], on=LLAVE, how="left", validate="one_to_one")
    for c in ("POBRE_MONETARIO", "POBRE_EXTREMO_MONETARIO"):
        df[c] = df[c].astype("Int8")
    return df


def main() -> None:
    for f, script in ((BASE, "src/3_preprocesamiento.py"),
                      (POBREZA_HOGAR, "-m src.indicadores.pobreza_monetaria_geih")):
        if not f.exists():
            raise SystemExit(f"Falta {f}: corra {script} primero")
    df = pegar_pobreza(pd.read_parquet(BASE), pd.read_parquet(POBREZA_HOGAR))
    sin = df["ingreso_percapita"].isna().sum()
    assert sin < len(df) * 0.01, f"{sin} hogares sin ingreso reconstruido: revisar llaves"

    w = pd.to_numeric(df["fex"], errors="coerce").fillna(0)
    tasa = lambda c: (w * df[c].astype(float)).sum() / w.sum()  # noqa: E731
    print("\n=== Outcome pobreza monetaria (reconstrucción GEIH, escenario base) ===")
    print(f"Hogares: {len(df):,} | sin ingreso reconstruido: {sin}")
    print(f"Ingreso per cápita UG — mediana: ${df['ingreso_percapita'].median():,.0f}")
    print(f"Hogares pobres (ponderado por fex): {tasa('POBRE_MONETARIO')*100:.1f}% | "
          f"pobres extremos: {tasa('POBRE_EXTREMO_MONETARIO')*100:.1f}%")
    print("(La tasa oficial, 31,8 %, es sobre personas; la de personas reconstruida está en "
          "docs/reports/validacion_pobreza_monetaria.csv)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"\nGuardado: {OUT}")


if __name__ == "__main__":
    main()
