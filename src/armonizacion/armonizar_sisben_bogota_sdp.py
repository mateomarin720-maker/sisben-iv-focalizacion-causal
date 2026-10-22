"""Estandariza el Sisbén IV de Bogotá (entrega SDP, lote recibido 03/08/2026) al
esquema canónico de sisben_estandarizado_2024.parquet, a nivel de hogar (jefe).

Estructura de la fuente: una fila por persona, separador ';', UTF-8 con BOM.
Llave de hogar: ide_ficha_origen + ide_hogar. Jefe: tip_parentesco == 1.

⚠️ El SDP es un registro administrativo CONTINUO, no un corte único: trae
`fec_fin_encuesta` por hogar con fechas entre 2019-03-22 y 2026-07-29 (verificado
2026-10-10). Cada hogar aparece UNA sola vez en el archivo (no hay fila
duplicada con el mismo valor repetida año a año) — su fecha es la de su único
registro, vigente hasta que se actualice.

Filtro elegido: `fec_fin_encuesta <= FECHA_CORTE` (corte por VIGENCIA, no año
exacto de encuesta). Se descartó exigir año==2024 exacto porque el Sisbén no
re-encuesta a todos los hogares cada año — un hogar registrado en 2022 sigue
vigente en 2024 aunque no lo hayan vuelto a visitar. Exigir año exacto dejaba
solo 75.488 de 1.458.474 hogares (5,2 %, los recién actualizados), subestimando
el universo vigente y sesgando la muestra hacia hogares con actualización
reciente. El nacional (`sisben_estandarizado_2024.parquet`) tampoco trae fecha
real por hogar (su `CORTE` es el literal fijo "SIV_2024"), así que lo más
consistente es tratar ambas fuentes como "stock vigente a una fecha", no como
"encuestados ese año exacto". Se conserva la fecha real de cada hogar en
`CORTE` (no un valor fijo).

Uso:
    poetry run python -m src.armonizacion.armonizar_sisben_bogota_sdp RUTA_CSV
Salida: data/2_models/sisben_bogota_estandarizado.parquet
        (+ opcional fusión con nacional sustituyendo cod_mpio 11001)
"""
from __future__ import annotations
import sys
from pathlib import Path
import pandas as pd

OUT = Path("data/2_models/sisben_bogota_estandarizado.parquet")
NACIONAL = Path("data/2_models/sisben_estandarizado_2024.parquet")
OUT_FUSION = Path("data/2_models/sisben_estandarizado_2024_con_bogota.parquet")
FECHA_REF_EDAD = pd.Timestamp("2024-12-31")  # misma referencia que GEIH 2024
FECHA_CORTE = pd.Timestamp("2024-12-31")  # hogares vigentes hasta esta fecha (stock, no año exacto)
COLS = ["ide_ficha_origen", "ide_hogar", "ide_persona", "Cod_clase", "Cod_comuna",
        "tip_parentesco", "sexo_persona", "fec_nacimiento", "Grupo", "Clasificacion",
        "tip_mat_paredes", "tip_mat_pisos", "num_cuartos_vivienda",
        "ind_tiene_acueducto", "ind_tiene_alcantarillado", "fec_fin_encuesta"]


def armonizar_sisben_bogota(csv: str, fecha_corte: pd.Timestamp = FECHA_CORTE) -> pd.DataFrame:
    df = pd.read_csv(csv, sep=";", usecols=COLS, dtype=str, encoding="utf-8-sig")
    k = ["ide_ficha_origen", "ide_hogar"]
    n_pers = df.groupby(k).size().rename("hog_num_personas").reset_index()
    jefes_todos = df[df["tip_parentesco"] == "1"].drop_duplicates(k, keep="first")

    fec_encuesta = pd.to_datetime(jefes_todos["fec_fin_encuesta"], errors="coerce")
    vigente = fec_encuesta <= fecha_corte
    n_total, n_filtrado = len(jefes_todos), int(vigente.sum())
    print(
        f"Sisbén Bogotá (SDP): {n_total:,} jefes en el archivo crudo "
        f"(fec_fin_encuesta {fec_encuesta.min().date()}..{fec_encuesta.max().date()}); "
        f"{n_filtrado:,} ({n_filtrado / n_total * 100:.1f} %) vigentes al "
        f"{fecha_corte.date()} -> estos son los que se conservan "
        f"({int((~vigente).sum()):,} descartados por ser posteriores al corte)."
    )
    jefes = jefes_todos[vigente].copy()

    h = jefes.merge(n_pers, on=k, how="left")
    nac = pd.to_datetime(h["fec_nacimiento"], errors="coerce")
    out = pd.DataFrame({
        "llave_directorio": h["ide_ficha_origen"],
        "llave_hogar": h["ide_hogar"],
        "geo_depto": "11",
        "cod_mpio": "11001",
        "geo_localidad": h["Cod_comuna"],
        "geo_zona": h["Cod_clase"],
        "jefe_sexo": h["sexo_persona"],
        # Mismo CODIGO de ciclo de vida que PER002 del Sisbén nacional (corroborado
        # indirectamente, ver docs/DICCIONARIO_HOTDECK.md §5):
        # 3=12-17, 4=18-28, 5=29-59, 6=60+  (asi la celda del Hot-Deck es comparable)
        "jefe_edad": pd.cut(((FECHA_REF_EDAD - nac).dt.days // 365.25), bins=[-1, 17, 28, 59, 200],
                            labels=["3", "4", "5", "6"]).astype("object"),
        "viv_paredes": h["tip_mat_paredes"],
        "viv_pisos": h["tip_mat_pisos"],
        "viv_cuartos": pd.to_numeric(h["num_cuartos_vivienda"], errors="coerce"),
        "viv_alcantarillado": h["ind_tiene_alcantarillado"],
        "viv_acueducto": h["ind_tiene_acueducto"],
        "hog_num_personas": h["hog_num_personas"],
        "Grupo": h["Grupo"],
        "Clasificacion": h["Clasificacion"],
        "Nivel": h["Clasificacion"].str.extract(r"(\d+)")[0],
        # Fecha REAL de la encuesta de cada hogar (ya filtrada a vigentes al
        # corte), no un valor fijo — el SDP es un registro continuo, no un
        # corte único.
        "CORTE": pd.to_datetime(h["fec_fin_encuesta"], errors="coerce").dt.strftime("%Y-%m-%d"),
        "HOGAR": h["ide_hogar"],
        "llave": h["ide_ficha_origen"],
        "fex": 1.0,  # la entrega SDP no trae factor de expansión (censo administrativo)
        "fuente": f"sdp_bogota_vigente_{fecha_corte.date()}",
    })
    out["llave_hogar_sisben"] = "11001|" + out["geo_zona"].astype(str) + "|" + out["llave"].astype(str) + "|" + out["CORTE"] + "|" + out["HOGAR"].astype(str)
    out["jefe_sexo"] = out["jefe_sexo"].where(out["jefe_sexo"].isin(["1", "2"]))  # sexo=4 invalido -> nulo
    assert out["llave_hogar_sisben"].is_unique
    return out


def main() -> None:
    arg = sys.argv[1]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if arg.lower().endswith(".parquet"):   # ya estandarizado: solo fusionar con el nacional
        b = pd.read_parquet(arg)
    else:
        b = armonizar_sisben_bogota(arg)
        b.to_parquet(OUT, index=False)
    print(f"Bogotá: {len(b):,} hogares -> {OUT}")
    if NACIONAL.exists():
        n = pd.read_parquet(NACIONAL)
        n = n[n["cod_mpio"].astype(str).str[:5] != "11001"] if "cod_mpio" in n else n[n["geo_depto"] != "11"]
        n["fuente"] = "dnp_nacional_2024-05"
        f = pd.concat([n, b], ignore_index=True)
        # Columnas object con tipos mezclados (texto + entero, ej. hog_num_personas): a texto
        for c in f.columns:
            if f[c].dtype == object:
                f[c] = f[c].astype("string")
        f.to_parquet(OUT_FUSION, index=False)
        print(f"Fusionado (Bogotá reemplaza 11001 del nacional): {len(f):,} -> {OUT_FUSION}")


if __name__ == "__main__":
    main()
