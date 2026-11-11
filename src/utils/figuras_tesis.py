"""Figuras del documento de la tesis.

  fig_cotas_por_celda.png       cota de Fréchet del contraste A/B en pobreza
                                monetaria, celda por celda, frente al IC del DML
  fig_errores_por_departamento  cotas del error de exclusión por departamento
  fig_atenuacion.png            estimación* según la fracción de hogares bien
                                vinculados (Proposición 2)
  fig_propension_celda.png      propensión estimada frente a P(T | celda)
                                empírica: indicadoras de celda y la celda como
                                número (el error corregido el 2026-11-02)
  fig_arquitectura.png          flujo de datos y componentes del repositorio
  fig_estabilidad_hotdeck.png   el Hot-Deck es estable por celda e inestable por
                                hogar (100 sorteos)
  fig_importancia_variables_oe1 importancia de las variables en el grupo del
                                Sisbén (LASSO, Ridge, SHAP)

Todas menos la de propensión salen de `docs/reports/`; la de propensión lee la
muestra de estimación (`data/2_models/`, no versionada).

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.utils.figuras_tesis [sin_datos]
Salidas: docs/anexos_tesis/figuras/*.png
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

R = Path("docs/reports")
OUT = Path("docs/anexos_tesis/figuras")

# Paleta de referencia (modo claro), en orden fijo.
AZUL, NARANJA, AGUA = "#2a78d6", "#eb6834", "#1baf7a"
TINTA, TINTA_2, TENUE, REJILLA, FONDO = "#0b0b0b", "#52514e", "#a3a29c", "#e6e5e0", "#fcfcfb"
DPTOS = {"05": "Antioquia", "08": "Atlántico", "11": "Bogotá", "13": "Bolívar", "15": "Boyacá", "17": "Caldas",
         "18": "Caquetá", "19": "Cauca", "20": "Cesar", "23": "Córdoba", "25": "Cundinamarca", "27": "Chocó",
         "41": "Huila", "44": "La Guajira", "47": "Magdalena", "50": "Meta", "52": "Nariño",
         "54": "Norte de Santander", "63": "Quindío", "66": "Risaralda", "68": "Santander", "70": "Sucre",
         "73": "Tolima", "76": "Valle del Cauca", "81": "Arauca", "85": "Casanare", "86": "Putumayo",
         "88": "San Andrés", "91": "Amazonas", "94": "Guainía", "95": "Guaviare", "97": "Vaupés", "99": "Vichada"}


def _estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
        "font.size": 9, "axes.edgecolor": TENUE, "axes.labelcolor": TINTA_2, "xtick.color": TINTA_2,
        "ytick.color": TINTA_2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.color": REJILLA, "grid.linewidth": 0.6, "axes.titlesize": 10, "axes.titleweight": "bold",
        "axes.titlecolor": TINTA, "axes.titlelocation": "left", "legend.frameon": False,
    })


def _coma(ax, eje: str = "y", dec: int = 2) -> None:
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.{dec}f}".replace(".", ",").replace("-", "−"))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(fmt)


def _guardar(fig, nombre: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    ruta = OUT / nombre
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return ruta


def cotas_por_celda() -> Path:
    c = pd.read_csv(R / "cotas_frechet_manski_pobre_monetario.csv")
    # Celdas de al menos 30 hogares (umbral de las cotas por parámetro): en las
    # muy pequeñas todos o ninguno es pobre y la cota se reduce al punto 0.
    c = c[c["n_geih"] >= 30]
    c = c.assign(medio=(c["cate_lo"] + c["cate_hi"]) / 2).sort_values("medio").reset_index(drop=True)
    texto = (R / "estimacion_ate_att_atu_cate.txt").read_text(encoding="utf-8")
    bloque = texto.split("# Outcome: POBRE_MONETARIO ")[1].split("W = CELDA EXACTA")[1]
    lo, hi = (float(x) for x in bloque.split("IC95%=(")[1].split(")")[0].split(", "))
    fig, ax = plt.subplots(figsize=(7, 3.6))
    x = np.arange(len(c))
    ax.vlines(x, c["cate_lo"], c["cate_hi"], color=TENUE, linewidth=0.6, label="Cota de Fréchet de cada celda")
    ax.axhline(0, color=TINTA_2, linewidth=0.8)
    ax.axhspan(lo, hi, color=AZUL, linewidth=0, label="IC 95 % del DML con el grupo imputado")
    ax.annotate(f"IC del DML: [{lo:+.4f}; {hi:+.4f}]".replace(".", ",").replace("-", "−"), (len(c) * 0.62, hi),
                (len(c) * 0.62, 0.55), fontsize=8, color=AZUL, ha="center", bbox=dict(boxstyle="round,pad=0.25", facecolor=FONDO, edgecolor="none"),
                arrowprops=dict(arrowstyle="-|>", color=AZUL, linewidth=1))
    ax.set_xlim(-5, len(c) + 5)
    ax.set_ylim(-1.02, 1.02)
    ax.set_xlabel(f"Celdas del Hot-Deck con 30 hogares o más en la GEIH ({len(c)}), ordenadas por el centro de su cota")
    ax.set_ylabel("Efecto sobre la pobreza monetaria")
    ax.set_xticks([])
    ax.set_yticks([-1, -0.5, 0, 0.5, 1])
    _coma(ax, dec=1)
    ax.set_title("El intervalo del DML es mucho más estrecho que lo que los datos permiten")
    ax.legend(loc="lower left", fontsize=8)
    return _guardar(fig, "fig_cotas_por_celda.png")


def errores_por_departamento() -> Path:
    e = pd.read_csv(R / "errores_focalizacion_frechet.csv", dtype={"depto": str})
    e = e[(e["elegible"] == "A-B") & (e["pobreza"] == "POBRE_MONETARIO")]
    nal = e[e["ambito"] == "nacional"].iloc[0]
    d = e[e["ambito"] == "departamento"].copy()
    d["nombre"] = d["depto"].str.zfill(2).map(DPTOS)
    d = d.sort_values("exclusion_hi").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(6.5, 7))
    y = np.arange(len(d))
    ax.hlines(y, d["exclusion_lo"] * 100, d["exclusion_hi"] * 100, color=AZUL, linewidth=2.2)
    piso = d["exclusion_lo"] > 0.05
    ax.plot(d.loc[piso, "exclusion_lo"] * 100, y[piso], "o", color=NARANJA, markersize=5,
            label="Piso de la exclusión mayor que 5 %")
    ax.axvspan(nal["exclusion_lo"] * 100, nal["exclusion_hi"] * 100, color=REJILLA, alpha=0.6, zorder=0,
               label=f"Nacional: {nal['exclusion_lo'] * 100:.1f} % a {nal['exclusion_hi'] * 100:.1f} %".replace(".", ","))
    ax.set_yticks(y, d["nombre"], fontsize=7.5)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Error de exclusión: pobres monetarios fuera de A/B (%)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Error de exclusión por departamento: lo que permiten los datos sin enlace")
    ax.legend(loc="lower right", fontsize=8)
    return _guardar(fig, "fig_errores_por_departamento.png")


def atenuacion() -> Path:
    s = pd.read_csv(R / "simulacion_semisintetica_resumen.csv")
    s = s[(s["escenario"] == "confusion_observada") & (s["outcome"] == "log_ingreso")]
    frac = {"hotdeck": 0.0, "vinculo_parcial_50": 0.5, "oraculo": 1.0}
    tau = s["efecto_verdadero"].mean()
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.plot([0, 1], [0, tau], color=TENUE, linewidth=1.5, linestyle="--", label="L × efecto verdadero")
    for est, color, nom in [("regresion_efectos_fijos", AZUL, "Regresión con efectos fijos"),
                            ("linear_dml", NARANJA, "LinearDML")]:
        g = s[s["estimador"] == est].assign(L=lambda t: t["vinculo"].map(frac)).sort_values("L")
        ax.errorbar(g["L"], g["estimacion"], yerr=1.96 * g["mcse_sesgo"], color=color, marker="o", markersize=6,
                    linewidth=2, capsize=0, label=nom)
    ax.axhline(0, color=TINTA_2, linewidth=0.8)
    ax.set_xticks([0, 0.5, 1], ["0\n(Hot-Deck)", "0,5", "1\n(vínculo hogar a hogar)"])
    ax.set_xlabel("Fracción de hogares bien vinculados (L)")
    ax.set_ylabel("Efecto estimado en log-ingreso*")
    _coma(ax, dec=2)
    ax.set_title("La estimación cae en proporción al vínculo faltante*")
    ax.legend(loc="upper left", fontsize=8)
    fig.text(0.01, -0.1, "* Resultado simulado: efecto verdadero fijado en la simulación semisintética "
             f"({tau:.3f}; 432 repeticiones, confusión observada).".replace(".", ",", 1), fontsize=7, color=TINTA_2)
    return _guardar(fig, "fig_atenuacion.png")


def propension_celda() -> Path:
    from sklearn.linear_model import LogisticRegression

    from src.simulacion.estimadores import estimacion5

    est5 = estimacion5()
    d = est5._preparar(pd.read_parquet(est5.DATA))
    W = d[["hotdeck_celda_cat"]].to_numpy(float)
    _, modelo_t = est5._modelos_auxiliares(est5.W_CELDA, con_x=False)
    bien = modelo_t.fit(W, d["T"]).predict_proba(W)[:, 1]
    mal = LogisticRegression(C=10.0, max_iter=2000).fit(W, d["T"]).predict_proba(W)[:, 1]
    t = pd.DataFrame({"celda": d["hotdeck_celda_cat"], "emp": d["T"], "bien": bien, "mal": mal})
    c = t.groupby("celda").agg(n=("emp", "size"), emp=("emp", "mean"), bien=("bien", "mean"), mal=("mal", "mean"))
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.plot([0, 1], [0, 1], color=TENUE, linewidth=1, linestyle="--")
    tam = np.clip(np.sqrt(c["n"]) / 3, 4, 40)
    ax.scatter(c["emp"], c["mal"], s=tam, color=NARANJA, alpha=0.7, edgecolor=FONDO, linewidth=0.5,
               label="Celda como número (error anterior)")
    ax.scatter(c["emp"], c["bien"], s=tam, color=AZUL, alpha=0.7, edgecolor=FONDO, linewidth=0.5,
               label="Celda como indicadoras (vigente)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("P(A o B | celda) empírica")
    ax.set_ylabel("Propensión estimada (media de la celda)")
    _coma(ax, "x", 1)
    _coma(ax, "y", 1)
    ax.set_title("La propensión debe reproducir el sorteo por celda")
    ax.legend(loc="upper left", fontsize=8)
    return _guardar(fig, "fig_propension_celda.png")


def arquitectura() -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis("off")

    def caja(x, y, w, h, titulo, detalle="", color=TINTA_2, relleno="#ffffff"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", linewidth=1.2,
                                    edgecolor=color, facecolor=relleno))
        ax.text(x + w / 2, y + h - 2.2, titulo, ha="center", va="top", fontsize=8, color=TINTA, weight="bold")
        if detalle:
            ax.text(x + w / 2, y + h - 5.6, detalle, ha="center", va="top", fontsize=7, color=TINTA_2,
                    linespacing=1.35)

    def flecha(x0, y0, x1, y1):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color=TINTA_2, linewidth=1))

    caja(1, 40, 17, 17, "Fuentes", "GEIH 2024 (12 meses)\nSisbén IV nacional\nSisbén Bogotá (SDP)\nIPM 2024")
    caja(23, 40, 17, 17, "Ingesta", "crudos → Parquet\nAzure Blob Storage\ncatálogo versionado\ningesta/, 1_, 2_")
    caja(45, 40, 19, 17, "Armonización", "esquema canónico\npor hogar\ncontrato de datos\narmonizacion/", AZUL)
    caja(69, 40, 30, 17, "Enlace y resultados", "Hot-Deck por celda (993 celdas)\npobreza monetaria e IPM-GEIH\nemparejamiento/, indicadores/\nvalidacion/")
    for x0, x1 in [(18.8, 22.2), (40.8, 44.2), (64.8, 68.2)]:
        flecha(x0, 48.5, x1, 48.5)
    caja(1, 5, 30, 25, "1. Diagnóstico con datos reales",
         "DAG y d-separación\nDML y Causal Forest (placebo)\ncotas de Fréchet-Manski\nerrores de focalización por celda\nselección y recomendación\nde variables\ndiagnostico/, 4_, 5_", AZUL, "#f2f7fd")
    caja(35, 5, 30, 25, "2. Simulación semisintética",
         "efecto conocido sobre\nhogares reales\noráculo, vínculo parcial, Hot-Deck\nmodo simulado y\nmodo de datos propios\nsimulacion/", NARANJA, "#fdf3ee")
    caja(69, 5, 30, 25, "3. Reglas de focalización",
         "proxy de medios, CATE,\nvigente y aleatoria\nmismo número de hogares\ny mismo dinero\nfocalizacion/", AGUA, "#eefaf5")
    for x in (16, 50, 84):  # del enlace a los tres componentes
        flecha(84, 39.2, x, 31.2)
    flecha(65.6, 17, 68.4, 17)  # la simulación alimenta las reglas
    ax.text(50, 0.5, "Pruebas automáticas y prueba de mutación sobre todo el flujo (tests/); "
            "salidas en docs/reports/, lectura en docs/resultados/", ha="center", fontsize=7, color=TINTA_2)
    return _guardar(fig, "fig_arquitectura.png")


def estabilidad_hotdeck() -> Path:
    """Estable por celda, inestable por hogar (100 sorteos del Hot-Deck)."""
    c = pd.read_csv(R / "variabilidad_hotdeck_celdas.csv")
    texto = (R / "variabilidad_hotdeck.txt").read_text(encoding="utf-8")
    conc = float(texto.split("concordancia_ab:")[1].split()[0])
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw=dict(width_ratios=[1, 1.15]))
    grande = c["hogares"] >= 30
    a.errorbar(c.loc[grande, "pi_ab_donantes"] * 100, c.loc[grande, "prop_ab_media"] * 100,
               yerr=2 * c.loc[grande, "prop_ab_sd"] * 100, fmt="o", color=AZUL, ecolor=REJILLA, markersize=2.5,
               elinewidth=0.8, label="Celda (media ± 2 d.e. de los sorteos)")
    a.plot([0, 100], [0, 100], color=TENUE, linewidth=1, linestyle="--", label="Igual a los donantes")
    a.set_xlim(0, 100)
    a.set_ylim(0, 100)
    a.set_xlabel("A/B entre los donantes del Sisbén en la celda (%)")
    a.set_ylabel("A/B imputado a los hogares GEIH de la celda (%)")
    a.set_title("Por celda: la proporción se reproduce")
    a.legend(loc="upper left", fontsize=8)
    a.text(98, 3, f"{int(grande.sum())} celdas con 30 hogares o más", ha="right", fontsize=7.5, color=TINTA_2)
    # Un hogar de una celda con proporción p coincide en A/B entre dos sorteos con probabilidad p² + (1 − p)².
    p = c["pi_ab_donantes"]
    b.hist((p**2 + (1 - p) ** 2) * 100, bins=np.linspace(50, 100, 26), weights=c["peso"] / c["peso"].sum() * 100,
           color=NARANJA, rwidth=0.92)
    b.axvline(conc * 100, color=TINTA, linewidth=1, linestyle="--")
    b.text(conc * 100 + 1, b.get_ylim()[1] * 0.92, f"Promedio: {conc * 100:.1f} %".replace(".", ","), fontsize=8,
           color=TINTA)
    b.set_xlim(50, 100)
    b.set_xlabel("Probabilidad de que dos sorteos den el mismo A/B (%)")
    b.set_ylabel("Hogares GEIH (% ponderado)")
    b.set_title("Por hogar: dos sorteos coinciden poco")
    b.text(51, -b.get_ylim()[1] * 0.25, "50 %: igual que lanzar una moneda; 100 %: el sorteo no cambia el grupo.",
           fontsize=7.5, color=TINTA_2)
    fig.tight_layout()
    return _guardar(fig, "fig_estabilidad_hotdeck.png")


ETIQUETAS_OE1 = {"geo_depto": "Departamento", "viv_pisos": "Material de pisos", "hog_num_personas": "Personas del hogar",
                 "viv_alcantarillado": "Alcantarillado", "viv_paredes": "Material de paredes", "jefe_sexo": "Sexo del jefe",
                 "viv_cuartos": "Cuartos", "viv_acueducto": "Acueducto", "geo_zona": "Zona (urbano/rural)",
                 "jefe_edad": "Edad del jefe"}


def importancia_oe1() -> Path:
    """Importancia normalizada de cada variable al predecir el grupo del Sisbén."""
    d = pd.read_csv(R / "seleccion_variables_lasso_ridge_shap.csv").sort_values("promedio")
    fig, ax = plt.subplots(figsize=(7, 4.6))
    y = np.arange(len(d))
    alto = 0.26
    for k, (col, nom, color) in enumerate([("lasso_norm", "LASSO", AZUL), ("ridge_norm", "Ridge", NARANJA),
                                           ("shap_norm", "SHAP (bosque aleatorio)", AGUA)]):
        ax.barh(y + (k - 1) * alto, d[col], height=alto - 0.04, color=color, label=nom)
    ax.set_yticks(y, [ETIQUETAS_OE1.get(v, v) + (" (control)" if g else "") for v, g in
                      zip(d["variable"], d["es_control_geografico"])])
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Importancia normalizada (1 = la mayor de cada método)")
    _coma(ax, "x", 1)
    ax.grid(axis="y", visible=False)
    ax.set_title("Qué variables explican el grupo del Sisbén (OE1)")
    ax.legend(loc="lower right", fontsize=8)
    return _guardar(fig, "fig_importancia_variables_oe1.png")


def main(con_datos: bool = True) -> None:
    _estilo()
    rutas = [cotas_por_celda(), errores_por_departamento(), atenuacion(), arquitectura(), estabilidad_hotdeck(),
             importancia_oe1()]
    if con_datos:
        rutas.append(propension_celda())
    print("\n".join(f"Guardado: {r}" for r in rutas))


if __name__ == "__main__":
    main(con_datos="sin_datos" not in sys.argv[1:])
