"""Pobreza monetaria 2024 reconstruida con los microdatos públicos de GEIH.

Implementa la metodología de
`docs/metodologia/pobreza_monetaria/00_auditoria_y_metodologia.md` con las
decisiones D1-D7 cerradas el 2026-11-02 (ver
`docs/metodologia/pobreza_monetaria/01_diccionario_ingreso.md`). Es una
**reconstrucción**, no la cifra oficial: el DANE además cruza GEIH con
registros administrativos (ayudas institucionales, PILA) que no son
públicos.

Escenario base:
- Unidad de gasto (UG) = hogar sin servicio doméstico ni sus parientes
  (`P6050` = 10). Los códigos 11 y 12 se quedan y se excluyen solo en la
  sensibilidad `ug_sin_11_12` (D2).
- Ingreso corriente de la persona = `INGLABO` + componentes laborales que
  `INGLABO` no incluye (extras, primas, bonificaciones y auxilios
  declarados como no incluidos, primas anuales ÷ 12, especie de
  independientes) + trabajo de no ocupados + arriendos, pensiones,
  pensión alimenticia + transferencias, ayudas (solo el total) y capital
  ÷ 12. Sin ingresos ocasionales (`P7510S7A1`), sin cesantías ni pagos por
  accidente (D5, en sensibilidad).
- No respuesta laboral (`INGLABO` vacío o 0 en ocupados remunerados):
  hot-deck dentro de celdas de GEIH (sexo × edad × educación × posición
  ocupacional × rama × dominio, con respaldo a celdas más gruesas). Nunca
  con variables del Sisbén. Sin remuneración son `P6430` = 6 y 8: el 7 es
  jornalero (los números no siguen el orden de las letras del diccionario).
- Arriendo imputado (`P5130`) a propietarios y usufructuarios
  (`P5090` ∈ {1, 2, 4}), como documenta la ficha metodológica del DANE
  (catálogo 874). Sensibilidad sin él (D3).
- Ganancia rural: `P6750` del mes, que es lo que usa `INGLABO` (94,5 % de
  igualdad exacta); `P550` ÷ 12 en sensibilidad (D4).
- Líneas por dominio (13 ciudades y A.M., otras cabeceras, centros
  poblados y rural disperso), versión B de la auditoría (D7).
- Tasas sobre personas de la UG, ponderadas por `FEX_C18 / 12`.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.indicadores.pobreza_monetaria_geih
Salidas:
    data/2_models/muestra_pobreza_monetaria_reconstruida_2024.parquet (personas)
    data/2_models/pobreza_monetaria_hogar_2024.parquet (hogares, para 3b)
    docs/reports/validacion_pobreza_monetaria.csv
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

GEIH_DIR = Path("data/1_processed/geih/2024")
OUT_PERSONAS = Path("data/2_models/muestra_pobreza_monetaria_reconstruida_2024.parquet")
OUT_HOGAR = Path("data/2_models/pobreza_monetaria_hogar_2024.parquet")
REPORT = Path("docs/reports/validacion_pobreza_monetaria.csv")
MESES = [f"{m:02d}" for m in range(1, 13)]
SEED = 42
K3 = ["DIRECTORIO", "SECUENCIA_P", "HOGAR"]

# Boletín DANE Pobreza Monetaria 2024, tablas 1 y 4 (pesos corrientes, mensual per cápita).
CIUDADES_13 = {"05", "08", "11", "13", "17", "23", "50", "52", "54", "66", "68", "73", "76"}
LINEAS = {  # dominio: (pobreza, pobreza extrema)
    "13_ciudades": (566_228.0, 256_922.0),
    "otras_cabeceras": (434_323.0, 222_730.0),
    "rural": (291_998.0, 176_154.0),
}
OFICIAL = {  # dominio: (FGT0 pobreza, FGT0 extrema, FGT1 pobreza, Gini)
    "nacional": (0.318, 0.117, 0.126, 0.551),
    "cabeceras": (0.286, 0.087, 0.110, 0.530),
    "13_ciudades": (0.240, 0.059, 0.089, 0.522),
    "otras_cabeceras": (0.348, 0.124, 0.139, 0.490),
    "rural": (0.425, 0.218, 0.179, 0.482),
}

ESCENARIOS = {
    "base": {},
    "nr_cero": {"nr": "cero"},
    "nr_caso_completo": {"nr": "caso_completo"},
    "ug_sin_11_12": {"excluir_parentesco": {"10", "11", "12"}},
    "sin_arriendo_imputado": {"arriendo": False},
    "arriendo_solo_propietarios": {"tenencias_arriendo": {"1", "2"}},
    "rural_p550": {"rural_p550": True},
    "con_cesantias_accidentes": {"cesantias": True},
}


def _norm_llave(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce").astype("Int64").astype("string")


def _leer(mes: str, modulo: str, cols: list[str]) -> pd.DataFrame:
    df = pd.read_parquet(GEIH_DIR / mes / f"{modulo}.parquet", columns=cols).replace("", pd.NA)
    for c in K3 + (["ORDEN"] if "ORDEN" in cols else []):
        df[c] = _norm_llave(df[c])
    return df


def _monto(df: pd.DataFrame, col: str, recibio: str | None = None, valor_si: str = "1") -> pd.Series:
    """Monto en pesos; 98/99 ("recibió, no sabe el monto") cuenta como 0 y
    se reporta aparte. Si hay pregunta filtro, solo cuenta cuando es "Sí"."""
    v = pd.to_numeric(df[col], errors="coerce")
    v = v.where(~v.isin([98, 99]))
    if recibio is not None:
        v = v.where(df[recibio] == valor_si)
    return v.fillna(0.0)


def _personas_mes(mes: str) -> pd.DataFrame:
    cg = _leer(mes, "caracteristicas_generales",
               [*K3, "ORDEN", "P6050", "P3271", "P6040", "P3042", "CLASE", "AREA", "DPTO", "FEX_C18"])

    cols_oc = [*K3, "ORDEN", "P6430", "INGLABO", "P6750", "P550", "RAMA2D_R4",
               "P6510", "P6510S1", "P6510S2", "P6545", "P6545S1", "P6545S2", "P6580", "P6580S1", "P6580S2",
               *[f"P6585S{i}{s}" for i in range(1, 5) for s in ("", "A1", "A2")],
               *[f"P6630S{i}{s}" for i in (1, 2, 3, 4, 6) for s in ("", "A1")],
               "P3054", "P3054S1", "P3055", "P3055S1"]
    oc = _leer(mes, "ocupados", cols_oc)
    o = oc[[*K3, "ORDEN", "P6430", "RAMA2D_R4"]].copy()
    o["ocupado"] = True
    o["inglabo"] = pd.to_numeric(oc["INGLABO"], errors="coerce")
    o["p6750"] = pd.to_numeric(oc["P6750"], errors="coerce")
    o["p550_mes"] = pd.to_numeric(oc["P550"], errors="coerce") / 12
    # Componentes que INGLABO no trae: solo si el hogar dijo que no estaban incluidos (S2/A2 = 2).
    o["lab_no_incluido"] = (
        _monto(oc, "P6510S1", "P6510S2", "2") + _monto(oc, "P6545S1", "P6545S2", "2")
        + _monto(oc, "P6580S1", "P6580S2", "2")
        + sum(_monto(oc, f"P6585S{i}A1", f"P6585S{i}A2", "2") for i in range(1, 5))
    )
    o["primas_anuales"] = sum(_monto(oc, f"P6630S{i}A1", f"P6630S{i}") for i in (1, 2, 3, 4)) / 12
    o["accidentes"] = _monto(oc, "P6630S6A1", "P6630S6") / 12
    # Especie de independientes: INGLABO = P6750 en el 96 % de quienes la declaran, así que no la trae.
    indep = oc["P6430"].isin(["4", "5", "9"])
    o["especie_indep"] = (_monto(oc, "P3054S1", "P3054") + _monto(oc, "P3055S1", "P3055")).where(indep, 0.0)
    o["n_98"] = sum(pd.to_numeric(oc[c], errors="coerce").isin([98, 99]).astype(int)
                    for c in cols_oc if c.endswith(("S1", "A1")))

    no = _leer(mes, "no_ocupados", [*K3, "ORDEN", "P7422", "P7422S1"])
    no["trabajo_no_ocupado"] = _monto(no, "P7422S1", "P7422")

    oi = _leer(mes, "otros_ingresos", [*K3, "ORDEN",
                                       *[f"P7500S{i}{s}" for i in (1, 2, 3) for s in ("", "A1")],
                                       *[f"P7510S{i}{s}" for i in (1, 2, 3, 5, 6) for s in ("", "A1")]])
    oi["no_laboral"] = (
        sum(_monto(oi, f"P7500S{i}A1", f"P7500S{i}") for i in (1, 2, 3))
        + sum(_monto(oi, f"P7510S{i}A1", f"P7510S{i}") for i in (1, 2, 3, 5)) / 12
    )
    oi["cesantias"] = _monto(oi, "P7510S6A1", "P7510S6") / 12

    p = (cg.merge(o, on=[*K3, "ORDEN"], how="left")
           .merge(no[[*K3, "ORDEN", "trabajo_no_ocupado"]], on=[*K3, "ORDEN"], how="left")
           .merge(oi[[*K3, "ORDEN", "no_laboral", "cesantias"]], on=[*K3, "ORDEN"], how="left"))
    p["ocupado"] = p["ocupado"].notna()
    for c in ("lab_no_incluido", "primas_anuales", "accidentes", "especie_indep", "n_98",
              "trabajo_no_ocupado", "no_laboral", "cesantias"):
        p[c] = p[c].fillna(0.0)

    hv = _leer(mes, "hogar_vivienda", [*K3, "P5090", "P5130"])
    hv["arriendo_imputado"] = pd.to_numeric(hv["P5130"], errors="coerce").where(lambda s: ~s.isin([98, 99])).fillna(0.0)
    p = p.merge(hv[[*K3, "P5090", "arriendo_imputado"]], on=K3, how="left")
    p["mes"] = mes
    return p


def _dominio(p: pd.DataFrame) -> pd.Series:
    area = pd.to_numeric(p["AREA"], errors="coerce").astype("Int64").astype("string").str.zfill(2)
    return pd.Series(np.select(
        [p["CLASE"] == "2", area.isin(CIUDADES_13).fillna(False)],
        ["rural", "13_ciudades"], "otras_cabeceras"), index=p.index)


def _celdas_hotdeck(p: pd.DataFrame) -> list[pd.Series]:
    """Celdas de imputación de la más fina a la más gruesa (solo GEIH)."""
    edad = pd.cut(pd.to_numeric(p["P6040"], errors="coerce"), [0, 24, 34, 44, 54, 64, 200], labels=False)
    educ = pd.to_numeric(p["P3042"], errors="coerce")
    educ = pd.cut(educ.where(educ != 99), [0, 3, 4, 7, 9, 13], labels=False)
    posicion = p["P6430"].map({"1": "asal", "2": "asal", "3": "dom", "4": "indep", "5": "patron",
                               "7": "jornal"}).fillna("otro")
    rama = p["RAMA2D_R4"].astype("string").str[:1]
    base = [p["P3271"].astype(str), edad.astype(str), educ.astype(str), posicion, rama.astype(str), p["dominio"]]
    niveles = [base, base[:4] + base[5:], [base[0], base[1], base[3], base[5]], [base[3], base[5]], [base[5]]]
    return [pd.concat(n, axis=1).astype(str).agg("|".join, axis=1) for n in niveles]


def _remunerado(p: pd.DataFrame) -> pd.Series:
    """Ocupados con trabajo remunerado. En los microdatos 2024 los códigos de
    `P6430` no siguen el orden de las letras del diccionario: el 7 es
    jornalero o peón (99 % declara `P6500`); sin remuneración son el 6
    (familiar) y el 8 (otros hogares, casi vacío)."""
    return p["ocupado"] & ~p["P6430"].isin(["6", "8"])


def _imputar_laboral(p: pd.DataFrame) -> pd.Series:
    """INGLABO para ocupados remunerados sin ingreso declarado (vacío o falso
    cero), con un donante al azar de su celda; los no remunerados valen 0."""
    rng = np.random.default_rng(SEED)
    remunerado = _remunerado(p)
    falta = remunerado & ~(p["inglabo"] > 0)
    donante = remunerado & (p["inglabo"] > 0)
    out = p["inglabo"].fillna(0.0).where(p["ocupado"], 0.0)
    if not falta.any():
        return out
    pendiente = falta.copy()
    for celda in _celdas_hotdeck(p):
        if not pendiente.any():
            break
        valores = p.loc[donante, "inglabo"].groupby(celda[donante]).apply(np.asarray)
        receptores = celda[pendiente]
        ok = receptores.isin(valores.index)
        for c, idx in receptores[ok].groupby(receptores[ok]).groups.items():
            out.loc[idx] = rng.choice(valores[c], size=len(idx))
        pendiente.loc[receptores[ok].index] = False
    logger.info("Hot-deck laboral: %s ocupados imputados (%.1f%% de los remunerados), %s sin donante",
                f"{falta.sum():,}", falta.sum() / remunerado.sum() * 100, pendiente.sum())
    return out


def _construir(p: pd.DataFrame, lab_imputado: pd.Series, *, nr: str = "hotdeck",
               excluir_parentesco: set[str] = frozenset({"10"}), arriendo: bool = True,
               tenencias_arriendo: set[str] = frozenset({"1", "2", "4"}), rural_p550: bool = False,
               cesantias: bool = False) -> pd.DataFrame:
    falta = _remunerado(p) & ~(p["inglabo"] > 0)
    lab = {"hotdeck": lab_imputado, "cero": p["inglabo"].fillna(0.0).where(p["ocupado"], 0.0),
           "caso_completo": lab_imputado}[nr]
    if rural_p550:
        usa = (p["p550_mes"] > 0) & p["p6750"].notna()
        lab = lab.where(~usa, lab - p["p6750"] + p["p550_mes"])
    ingreso = (lab + p["lab_no_incluido"] + p["primas_anuales"] + p["especie_indep"]
               + p["trabajo_no_ocupado"] + p["no_laboral"])
    if cesantias:
        ingreso = ingreso + p["cesantias"] + p["accidentes"]

    ug = p.loc[~p["P6050"].isin(excluir_parentesco)].assign(_ing=ingreso, _falta=falta)
    hog = ug.groupby(["mes", *K3]).agg(ingreso_ug=("_ing", "sum"), personas_ug=("ORDEN", "size"),
                                        falta_lab=("_falta", "any"), P5090=("P5090", "first"),
                                        arriendo_imputado=("arriendo_imputado", "first"))
    if arriendo:
        hog["ingreso_ug"] += hog["arriendo_imputado"].where(hog["P5090"].isin(tenencias_arriendo), 0.0)
    hog["ingreso_pc_ug"] = hog["ingreso_ug"] / hog["personas_ug"]

    per = ug[["mes", *K3, "ORDEN", "dominio", "peso", "DPTO", "AREA", "CLASE"]].merge(
        hog[["ingreso_pc_ug", "personas_ug", "falta_lab"]].reset_index(), on=["mes", *K3])
    if nr == "caso_completo":
        per = per.loc[~per["falta_lab"]].copy()
        # Reponderar dentro del dominio para conservar la población expandida.
        tot = ug.groupby("dominio")["peso"].sum() / per.groupby("dominio")["peso"].sum()
        per["peso"] = per["peso"] * per["dominio"].map(tot)
    lp = per["dominio"].map({k: v[0] for k, v in LINEAS.items()})
    li = per["dominio"].map({k: v[1] for k, v in LINEAS.items()})
    per["LP_2024"], per["LI_2024"] = lp, li
    per["POBRE_MONETARIA"] = (per["ingreso_pc_ug"] < lp).astype("int8")
    per["POBRE_EXTREMA"] = (per["ingreso_pc_ug"] < li).astype("int8")
    per["BRECHA_PM"] = ((lp - per["ingreso_pc_ug"]) / lp).clip(lower=0)
    per["BRECHA_PE"] = ((li - per["ingreso_pc_ug"]) / li).clip(lower=0)
    return per


def _gini(x: np.ndarray, w: np.ndarray) -> float:
    orden = np.argsort(x)
    x, w = x[orden], w[orden]
    cw = np.cumsum(w)
    cxw = np.cumsum(x * w)
    return float(1 - np.sum(w * (cxw + np.concatenate([[0], cxw[:-1]]))) / (cw[-1] * cxw[-1]))


def _indicadores(per: pd.DataFrame, escenario: str) -> list[dict]:
    filas = []
    dominios = {"nacional": per.index == per.index, "cabeceras": per["dominio"] != "rural",
                **{d: per["dominio"] == d for d in LINEAS}}
    for nombre, m in dominios.items():
        d, w = per.loc[m], per.loc[m, "peso"]
        prom = lambda s: float((s * w).sum() / w.sum())  # noqa: E731
        ofi = OFICIAL[nombre]
        filas.append(dict(
            escenario=escenario, dominio=nombre, personas=int(m.sum()),
            fgt0_pobreza=prom(d["POBRE_MONETARIA"]), fgt0_oficial=ofi[0],
            fgt1_pobreza=prom(d["BRECHA_PM"]), fgt1_oficial=ofi[2],
            fgt2_pobreza=prom(d["BRECHA_PM"] ** 2),
            fgt0_extrema=prom(d["POBRE_EXTREMA"]), fgt0_extrema_oficial=ofi[1],
            gini=_gini(d["ingreso_pc_ug"].to_numpy(), w.to_numpy()), gini_oficial=ofi[3],
        ))
    return filas


def main() -> None:
    p = pd.concat([_personas_mes(m) for m in MESES], ignore_index=True)
    p["dominio"] = _dominio(p)
    p["peso"] = pd.to_numeric(p["FEX_C18"], errors="coerce") / 12
    logger.info("Personas GEIH 2024: %s | población expandida: %.2f M", f"{len(p):,}", p["peso"].sum() / 1e6)
    logger.info("Montos 98/99 tratados como 0: %s", f"{int(p['n_98'].sum()):,}")
    lab = _imputar_laboral(p)

    filas, base = [], None
    for nombre, kw in ESCENARIOS.items():
        per = _construir(p, lab, **kw)
        filas += _indicadores(per, nombre)
        if nombre == "base":
            base = per
    tabla = pd.DataFrame(filas)

    pd.set_option("display.width", 200)
    print("\n=== Pobreza monetaria reconstruida 2024 (personas, FEX_C18/12) vs. DANE oficial ===")
    vista = tabla.assign(**{c: (tabla[c] * 100).round(1) for c in tabla.columns if c.startswith("fgt")})
    print(vista[vista["escenario"] == "base"].drop(columns="escenario").to_string(index=False))
    print("\nSensibilidad (nacional):")
    print(vista[vista["dominio"] == "nacional"][["escenario", "fgt0_pobreza", "fgt1_pobreza",
                                                 "fgt0_extrema", "gini"]].to_string(index=False))

    base = base.assign(FUENTE_PM="reconstruccion_geih_publica")
    OUT_PERSONAS.parent.mkdir(parents=True, exist_ok=True)
    base.to_parquet(OUT_PERSONAS, index=False)
    hogar = (base.groupby(["mes", *K3])
                 .agg(ingreso_pc_ug=("ingreso_pc_ug", "first"), personas_ug=("personas_ug", "first"),
                      dominio_pm=("dominio", "first"), LP_2024=("LP_2024", "first"),
                      LI_2024=("LI_2024", "first"), POBRE_MONETARIA=("POBRE_MONETARIA", "first"),
                      POBRE_EXTREMA=("POBRE_EXTREMA", "first"), BRECHA_PM=("BRECHA_PM", "first"),
                      BRECHA_PE=("BRECHA_PE", "first"))
                 .reset_index())
    hogar.to_parquet(OUT_HOGAR, index=False)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(REPORT, index=False)
    print(f"\nGuardado: {OUT_PERSONAS} ({len(base):,} personas)\nGuardado: {OUT_HOGAR} ({len(hogar):,} hogares)\n"
          f"Guardado: {REPORT}")


if __name__ == "__main__":
    main()
