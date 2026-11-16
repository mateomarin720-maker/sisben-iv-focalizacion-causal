"""¿Queda alguna variable de los catálogos que valga la pena sumar a la
celda del Hot-Deck?

Toma las variables de vivienda y hogar que GEIH, el Sisbén nacional y el
Sisbén de Bogotá (SDP) traen en común y que no están en la celda, las
homologa por categorías comunes (los códigos crudos no se comparan entre
fuentes) y mide qué aporta cada una sobre la celda vigente: cobertura,
fragmentación, correlación de P(T | celda) con la pobreza monetaria y
ancho de la cota de Fréchet por celda (`delta_frechet`, ver
`comparar_celdas_hotdeck_vivienda.py`). También prueba si la suma de las
débiles sirve: un puntaje P(A/B | candidatas) estimado en el Sisbén,
cortado en terciles o quintiles, como una sola dimensión más de la celda.

Primero el filtro de homologación: la distribución de cada variable en
las tres fuentes. Una variable cuya distribución no cuadra entre fuentes
(por ejemplo "cuarto" como tipo de vivienda: 2 % en GEIH, 29 % en el
Sisbén nacional) no se puede usar aunque mejore las métricas.

Fuera de la evaluación, por principio: las privaciones del IPM (acueducto,
alcantarillado, sanitario, fuente de agua, educación, salud, ocupación):
son el resultado, y usarlas en la celda ata el grupo imputado al propio
resultado. Y lo que falta en una fuente: estrato (el archivo nacional del
DNP no lo entrega), internet (no está en la GEIH), educación y ocupación
(no están en Bogotá).

Dos fases, cada variable con su placebo (barajada dentro de la celda
base: lo que se gana solo por partir la celda):
  1. Sobre la celda sin menores: así entró menores (Δ 0,177 → 0,148;
     placebo 0,175).
  2. Sobre la celda final, con zona, paredes y sexo del jefe además de las
     candidatas: es la tabla de variables descartadas
     (`docs/insumos/DICCIONARIO_HOTDECK.md` §6.1).

Resultado del 2026-11-16: sobre la celda final (Δ 0,148) ninguna aporta;
quedan entre 0,144 y 0,148, a lo sumo 0,002 por debajo de su placebo, y
casi todas pasan el 5 % de celdas pequeñas. La suma de todas en un
puntaje da 0,003 después del placebo con 10-14 % de celdas pequeñas.

Lee el Sisbén de Bogotá del banco de datos en memoria (no lo descarga).
Tarda unos 30 minutos.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.candidatas_celda_catalogo
Salida: docs/reports/candidatas_celda_catalogo.csv (+ la distribución por fuente en consola)
"""
from __future__ import annotations

import io
import logging
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import OneHotEncoder

from src.emparejamiento.emparejamiento_hotdeck_geih_sisben import CELDA_COLUMNAS, SISBEN_BOG, construir_celda
from src.utils.azure_storage import leer_bytes
from src.utils.variables_canonicas import es_menor, normalizar_llave
from src.validacion.comparar_celdas_hotdeck_vivienda import PAREDES, RECEPTOR, _evaluar, delta_placebo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

REPORT = Path("docs/reports/candidatas_celda_catalogo.csv")
GEIH_DIR = Path("data/1_processed/geih/2024")
SISBEN_DIR = Path("data/1_processed/sisben_iv/2024")
SDP_AZURE = "sisben/bogota/Sisben_03082026_bog.zip"
FECHA_REF = pd.Timestamp("2024-12-31")
MESES = [f"{m:02d}" for m in range(1, 13)]
LLAVE_GEIH = ["llave_directorio", "llave_secuencia_p", "llave_hogar", "mes"]
SI_NO = {"1": "si", "2": "no"}
# Mapas código crudo -> categoría común (diccionario GEIH 2024 y ficha del Sisbén IV).
MAPAS = {
    "tipo_viv": ({"1": "casa", "2": "apto", "3": "cuarto", "4": "cuarto", "5": "otro", "6": "otro"},
                 {"1": "casa", "2": "apto", "3": "cuarto", "4": "otro", "5": "otro"}),
    "tenencia": ({"1": "propia", "2": "propia", "3": "arriendo", "4": "otra", "5": "otra", "6": "otra"},
                 {"1": "arriendo", "2": "propia", "3": "propia", "4": "otra", "5": "otra", "6": "otra"}),
    "sanitario": ({"1": "alc", "2": "pozo", "3": "otro", "4": "otro", "5": "otro", "6": "otro"},
                  {"1": "alc", "2": "pozo", "3": "otro", "4": "otro", "5": "otro"}),
    "sanit_excl": ({"1": "excl", "2": "comp"}, {"1": "excl", "2": "comp", "3": "comp"}),
    "agua": ({str(i): ("acued" if i == 1 else "otra") for i in range(1, 12)},
             {str(i): ("acued" if i == 1 else "otra") for i in range(1, 10)}),
    "cocina": ({"1": "limpia", "3": "limpia", "4": "limpia", "2": "otra", "5": "otra", "6": "otra", "7": "otra", "8": "otra"},
               {"1": "limpia", "2": "limpia", "3": "limpia", "4": "otra", "5": "otra", "6": "otra", "7": "otra"}),
}
CANDIDATAS = ["tipo_viv", "tenencia", "dormitorios", "energia", "gas", "recoleccion", "sanitario", "sanit_excl", "agua",
              "cocina", "conyuge", "menores", "mayores"]
DEBILES = [c for c in CANDIDATAS if c != "menores"]  # las que, una a una, aportan poco
# Variables del esquema canónico que no están en la celda (homologadas en `armonizacion/`).
CANONICAS = ["zona", "paredes", "sexo"]
EXCLUIDAS = CANONICAS + DEBILES  # todo lo que quedó fuera de la celda final


def _mapa(serie: pd.Series, mapa: dict) -> pd.Series:
    return serie.astype(str).str.strip().map(mapa).fillna("NA")


def _tramo(serie: pd.Series, cortes: list, etiquetas: list[str]) -> pd.Series:
    return pd.cut(pd.to_numeric(serie, errors="coerce"), cortes, labels=etiquetas).astype("object").fillna("NA")


def _composicion(edad: pd.Series, conyuge: pd.Series, llaves: list[pd.Series], en_codigos: bool,
                 mayor: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"menores": es_menor(edad, en_codigos), "mayores": mayor, "conyuge": conyuge}) \
        .groupby(llaves).agg(menores=("menores", "sum"), mayores=("mayores", "sum"), conyuge=("conyuge", "any")).reset_index()


def _derivadas(d: pd.DataFrame, comp: pd.DataFrame, k: list[str]) -> pd.DataFrame:
    d = d.merge(comp, on=k, how="left")
    return pd.DataFrame({
        "conyuge": d["conyuge"].map({True: "si", False: "no"}).fillna("NA"),
        "menores": _tramo(d["menores"], [-1, 0, 1, 100], ["m0", "m1", "m2"]),
        "mayores": _tramo(d["mayores"], [-1, 0, 100], ["a0", "a1"]),
    }, index=d.index), d


def candidatas_geih() -> pd.DataFrame:
    hv, cg = [], []
    for m in MESES:
        h = pd.read_parquet(GEIH_DIR / m / "hogar_vivienda.parquet",
                            columns=["DIRECTORIO", "SECUENCIA_P", "HOGAR", "P4000", "P4030S1", "P4030S2", "P4030S4",
                                     "P5010", "P5020", "P5030", "P5050", "P5080", "P5090"])
        p = pd.read_parquet(GEIH_DIR / m / "caracteristicas_generales.parquet",
                            columns=["DIRECTORIO", "SECUENCIA_P", "HOGAR", "P6040", "P6050"])
        h["mes"], p["mes"] = m, m
        hv.append(h), cg.append(p)
    hv, cg = pd.concat(hv, ignore_index=True), pd.concat(cg, ignore_index=True)
    for d in (hv, cg):
        for c in ("DIRECTORIO", "SECUENCIA_P", "HOGAR"):
            d[c] = normalizar_llave(d[c])
    k = ["DIRECTORIO", "SECUENCIA_P", "HOGAR", "mes"]
    edad = pd.to_numeric(cg["P6040"], errors="coerce")
    comp = _composicion(cg["P6040"], cg["P6050"].astype(str) == "2", [cg[c] for c in k], False, edad >= 60)
    g = hv.drop_duplicates(k)
    der, g = _derivadas(g, comp, k)
    out = pd.DataFrame({
        "tipo_viv": _mapa(g["P4000"], MAPAS["tipo_viv"][0]), "tenencia": _mapa(g["P5090"], MAPAS["tenencia"][0]),
        "dormitorios": _tramo(g["P5010"], [-1, 1, 2, 100], ["d1", "d2", "d3"]),
        "energia": _mapa(g["P4030S1"], SI_NO), "gas": _mapa(g["P4030S2"], SI_NO), "recoleccion": _mapa(g["P4030S4"], SI_NO),
        "sanitario": _mapa(g["P5020"], MAPAS["sanitario"][0]), "sanit_excl": _mapa(g["P5030"], MAPAS["sanit_excl"][0]),
        "agua": _mapa(g["P5050"], MAPAS["agua"][0]), "cocina": _mapa(g["P5080"], MAPAS["cocina"][0]),
        **{c: der[c] for c in ("conyuge", "menores", "mayores")},
    }, index=g.index)
    out[LLAVE_GEIH] = g[k].to_numpy()
    return out


def candidatas_sisben_nacional() -> pd.DataFrame:
    kv = ["cod_mpio", "ZONA", "llave", "CORTE"]
    v = pd.read_parquet(SISBEN_DIR / "viviendas.parquet", columns=kv + ["VIV001", "VIV004", "VIV006", "VIV007"])
    h = pd.read_parquet(SISBEN_DIR / "hogares.parquet", columns=kv + ["HOGAR", "HOG001", "HOG003", "HOG004", "HOG006", "HOG007", "HOG017"])
    p = pd.read_parquet(SISBEN_DIR / "personas.parquet", columns=kv + ["HOGAR", "PER002", "PER003"])
    kh = kv + ["HOGAR"]
    comp = _composicion(p["PER002"], p["PER003"].astype(str) == "2", [p[c] for c in kh], True, p["PER002"].astype(str) == "6")
    n = h.merge(v.drop_duplicates(kv), on=kv, how="left")
    der, n = _derivadas(n, comp, kh)
    out = pd.DataFrame({
        "tipo_viv": _mapa(n["VIV001"], MAPAS["tipo_viv"][1]), "tenencia": _mapa(n["HOG001"], MAPAS["tenencia"][1]),
        "dormitorios": _tramo(n["HOG003"], [-1, 1, 2, 100], ["d1", "d2", "d3"]),
        "energia": _mapa(n["VIV004"], SI_NO), "gas": _mapa(n["VIV006"], SI_NO), "recoleccion": _mapa(n["VIV007"], SI_NO),
        "sanitario": _mapa(n["HOG004"], MAPAS["sanitario"][1]), "sanit_excl": _mapa(n["HOG006"], MAPAS["sanit_excl"][1]),
        "agua": _mapa(n["HOG007"], MAPAS["agua"][1]), "cocina": _mapa(n["HOG017"], MAPAS["cocina"][1]),
        **{c: der[c] for c in ("conyuge", "menores", "mayores")},
    }, index=n.index)
    out["llave_hogar_sisben"] = n[kh].astype(str).agg("|".join, axis=1)
    return out


def candidatas_sdp() -> pd.DataFrame:
    cols = ["ide_ficha_origen", "ide_hogar", "tip_parentesco", "fec_nacimiento", "tip_vivienda", "tip_ocupa_vivienda",
            "num_cuartos_dormir", "ind_tiene_energia", "ind_tiene_gas", "ind_tiene_recoleccion", "tip_sanitario",
            "tip_uso_sanitario", "tip_origen_agua", "tip_energia_cocina"]
    with zipfile.ZipFile(io.BytesIO(leer_bytes(SDP_AZURE))) as z, z.open(z.namelist()[0]) as f:
        s = pd.read_csv(f, sep=";", dtype=str, usecols=cols, encoding="utf-8-sig")
    edad = (FECHA_REF - pd.to_datetime(s["fec_nacimiento"], errors="coerce", dayfirst=True)).dt.days / 365.25
    k = ["ide_ficha_origen", "ide_hogar"]
    comp = _composicion(edad, s["tip_parentesco"] == "2", [s[c] for c in k], False, edad >= 60)
    j = s[s["tip_parentesco"] == "1"].drop_duplicates(k)
    der, j = _derivadas(j, comp, k)
    out = pd.DataFrame({
        "tipo_viv": _mapa(j["tip_vivienda"], MAPAS["tipo_viv"][1]), "tenencia": _mapa(j["tip_ocupa_vivienda"], MAPAS["tenencia"][1]),
        "dormitorios": _tramo(j["num_cuartos_dormir"], [-1, 1, 2, 100], ["d1", "d2", "d3"]),
        "energia": _mapa(j["ind_tiene_energia"], SI_NO), "gas": _mapa(j["ind_tiene_gas"], SI_NO),
        "recoleccion": _mapa(j["ind_tiene_recoleccion"], SI_NO),
        "sanitario": _mapa(j["tip_sanitario"], MAPAS["sanitario"][1]), "sanit_excl": _mapa(j["tip_uso_sanitario"], MAPAS["sanit_excl"][1]),
        "agua": _mapa(j["tip_origen_agua"], MAPAS["agua"][1]), "cocina": _mapa(j["tip_energia_cocina"], MAPAS["cocina"][1]),
        **{c: der[c] for c in ("conyuge", "menores", "mayores")},
    }, index=j.index)
    out["llave_directorio"], out["llave_hogar"] = j["ide_ficha_origen"].astype(str), j["ide_hogar"].astype(str)
    return out


def puntaje(don: pd.DataFrame, rec: pd.DataFrame, variables: list[str], cortes: int) -> tuple[pd.Series, pd.Series, float]:
    """P(A/B | variables) estimada en el Sisbén y aplicada a la GEIH, en
    `cortes` tramos por cuantiles del Sisbén; devuelve (receptor, donante, AUC)."""
    enc = OneHotEncoder(handle_unknown="ignore", min_frequency=100)
    xd = enc.fit_transform(don[variables].fillna("NA").astype(str))
    xr = enc.transform(rec[variables].fillna("NA").astype(str))
    y = don["Grupo"].isin(["A", "B"]).astype(int)
    modelo = LogisticRegression(max_iter=2000).fit(xd, y)
    sd, sr = modelo.predict_proba(xd)[:, 1], modelo.predict_proba(xr)[:, 1]
    q = np.quantile(sd, np.arange(1, cortes) / cortes)
    tramo = lambda s: pd.Series(np.digitize(s, q)).map(lambda i: f"q{i}")
    return tramo(sr), tramo(sd), float(roc_auc_score(y, sd))


def main() -> None:
    rec = pd.read_parquet(RECEPTOR).reset_index(drop=True)
    for c in LLAVE_GEIH[:3]:
        rec[c] = normalizar_llave(rec[c])
    rec = rec.merge(candidatas_geih(), on=LLAVE_GEIH, how="left")
    don = pd.read_parquet(SISBEN_BOG, columns=[*CELDA_COLUMNAS, "Grupo", "Clasificacion", "llave_hogar_sisben", "fuente",
                                               "llave_directorio", "llave_hogar", "geo_zona", "viv_paredes", "jefe_sexo"])
    don = don[don["Clasificacion"].notna()].reset_index(drop=True)
    bog = don["fuente"].str.startswith("sdp")
    d_n = don[~bog].merge(candidatas_sisben_nacional(), on="llave_hogar_sisben", how="left")
    d_b = don[bog].astype({"llave_directorio": str, "llave_hogar": str}).merge(candidatas_sdp(), on=["llave_directorio", "llave_hogar"], how="left")
    don = pd.concat([d_n, d_b], ignore_index=True)
    logger.info("Receptores con candidatas: %.4f | donantes nacional %.4f, Bogotá %.4f", rec["tipo_viv"].notna().mean(),
                d_n["tipo_viv"].notna().mean(), d_b["tipo_viv"].notna().mean())

    # Canónicas fuera de la celda: zona (1 = cabecera en las tres fuentes), paredes por la escala común
    # de `comparar_celdas_hotdeck_vivienda` y sexo del jefe (2 = mujer en las dos fuentes).
    for df, fuente in ((rec, "geih"), (don, "sisben")):
        df["zona"] = np.where(df["geo_zona"].astype(str).str.strip() == "1", "cabecera", "resto")
        df["paredes"] = df["viv_paredes"].astype(str).map(PAREDES[fuente]).fillna("NA")
        df["sexo"] = df["jefe_sexo"].astype(str).str.strip().map({"1": "hombre", "2": "mujer"}).fillna("NA")
    d_n, d_b = don[~don["fuente"].str.startswith("sdp")], don[don["fuente"].str.startswith("sdp")]

    w = pd.to_numeric(rec["fex"], errors="coerce").fillna(0)
    print("\n=== Filtro de homologación: distribución por fuente (GEIH ponderada | Sisbén nacional | Sisbén Bogotá)")
    for c in CANONICAS + CANDIDATAS:
        a = (w.groupby(rec[c]).sum() / w.sum()).round(3).to_dict()
        b = d_n[c].value_counts(normalize=True).round(3).to_dict()
        e = d_b[c].value_counts(normalize=True).round(3).to_dict()
        print(f"{c}: {a} | {b} | {e}")

    filas = []

    def evaluar(fase: str, nombre: str, base_r: pd.Series, base_d: pd.Series,
                xr: pd.Series | None = None, xd: pd.Series | None = None) -> None:
        """Evalúa la celda base o, con (xr, xd), la base más esa variable y su
        placebo: la variable barajada dentro de cada celda base (lo que se
        gana solo por partir la celda)."""
        cr, cd = (base_r, base_d) if xr is None else (base_r + "|" + xr, base_d + "|" + xd)
        fila = _evaluar(nombre, cr, cd, rec, don)
        fila["fase"] = fase
        if xr is not None:
            fila["delta_frechet_placebo"] = delta_placebo(base_r, xr, base_d, xd, rec, don)
        filas.append(fila)
        logger.info("%s %s: delta %.4f (placebo %.4f) | pequeñas %.2f %%", fase, nombre, fila["delta_frechet"],
                    fila.get("delta_frechet_placebo", np.nan), fila["pct_hogares_celda_menos_30_donantes"])

    def var(df: pd.DataFrame, c: str) -> pd.Series:
        return df[c].fillna("NA").astype(str).reset_index(drop=True)

    # Fase 1: sobre la celda sin menores, qué aporta cada candidata (así entró menores).
    base_r = construir_celda(rec, incluir_menores=False).reset_index(drop=True)
    base_d = construir_celda(don, edad_en_codigos=True, incluir_menores=False).reset_index(drop=True)
    f1 = "1_sobre_celda_sin_menores"
    evaluar(f1, "oficial_sin_menores", base_r, base_d)
    for c in CANDIDATAS:
        evaluar(f1, f"+{c}", base_r, base_d, var(rec, c), var(don, c))
    for nombre, variables in (("todas", CANDIDATAS), ("debiles_sin_menores", DEBILES)):
        for cortes in (3, 5):
            pr, pdn, auc = puntaje(don, rec, variables, cortes)
            evaluar(f1, f"+puntaje_{nombre}_{cortes}", base_r, base_d, pr, pdn)
            filas[-1]["auc_puntaje"] = auc

    # Fase 2: sobre la celda final, qué aportaría cada variable que quedó fuera (tabla de excluidas).
    fin_r = construir_celda(rec).reset_index(drop=True)
    fin_d = construir_celda(don, edad_en_codigos=True).reset_index(drop=True)
    f2 = "2_sobre_celda_final"
    evaluar(f2, "oficial", fin_r, fin_d)
    for c in EXCLUIDAS:
        evaluar(f2, f"+{c}", fin_r, fin_d, var(rec, c), var(don, c))
    for cortes in (3, 5):
        pr, pdn, auc = puntaje(don, rec, EXCLUIDAS, cortes)
        evaluar(f2, f"+puntaje_excluidas_{cortes}", fin_r, fin_d, pr, pdn)
        filas[-1]["auc_puntaje"] = auc

    tabla = pd.DataFrame(filas).set_index(["fase", "celda"])
    cols = ["celdas_con_receptores", "pct_hogares_celda_exacta", "pct_hogares_celda_menos_30_donantes",
            "corr_p_t_celda_pobre_monetario", "delta_frechet", "delta_frechet_placebo", "cumple_umbrales"]
    pd.set_option("display.width", 250)
    for fase, titulo in ((f1, "Fase 1: candidatas sobre la celda sin menores (depto + edad + cuartos + pisos + personas)"),
                         (f2, "Fase 2: variables excluidas sobre la celda final (+ menores)")):
        print(f"\n=== {titulo} ===")
        print(tabla.loc[fase].sort_values("delta_frechet")[cols].round(4).to_string())
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT)
    print(f"\nGuardado: {REPORT}")


if __name__ == "__main__":
    main()
