"""Tablas y figura de la evaluación semisintética.

Pendiente (paso 5 del diseño): asterisco (*) en cada cifra simulada y
columna `simulado` en los CSV.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.simulacion.escenarios import ESCENARIOS, OUTCOMES, VINCULOS

FIGURA = Path("docs/resultados/simulacion_semisintetica_convergencia.png")
OUT_TABLAS = Path("docs/reports/simulacion_semisintetica_tablas.md")
PANELES = [  # (escenario, outcome, estimador)
    ("confusion_observada", "log_ingreso", "linear_dml"),
    ("confusion_observada", "pobre_monetario", "linear_dml"),
    ("confusion_no_observada", "log_ingreso", "linear_dml"),
    ("regla_corte", "log_ingreso", "discontinuidad_rd"),
]
COLORES = {"oraculo": "#2a78d6", "vinculo_parcial_50": "#eb6834", "hotdeck": "#1baf7a"}  # paleta de referencia, 3 primeros
ETIQUETAS = {"oraculo": "Oráculo", "vinculo_parcial_50": "Vínculo 50 %", "hotdeck": "Hot-Deck"}
TITULOS = {"confusion_observada": "Confusión observada", "confusion_no_observada": "Confusión no observada fuerte",
           "regla_corte": "Regla de corte", "linear_dml": "LinearDML", "discontinuidad_rd": "RD en el corte",
           "log_ingreso": "log-ingreso", "pobre_monetario": "pobreza monetaria"}
ORDEN_EST = ["diferencia_medias", "regresion_efectos_fijos", "linear_dml", "causal_forest", "discontinuidad_rd"]
NOMBRES_EST = {"diferencia_medias": "Dif. de medias", "regresion_efectos_fijos": "Regresión EF celda",
               "linear_dml": "LinearDML", "causal_forest": "Causal Forest", "discontinuidad_rd": "RD en el corte"}


def graficar_convergencia(traza: pd.DataFrame, ruta: Path = FIGURA) -> None:
    """Estimación media ± 1,96·MCSE según se acumulan repeticiones, por
    integración, en cuatro celdas clave. La línea punteada es el efecto
    verdadero."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    texto, texto2, superficie, rejilla = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
    fig, ejes = plt.subplots(2, 2, figsize=(11, 7.5), facecolor=superficie)
    for ax, (esc, out, est) in zip(ejes.ravel(), PANELES):
        ax.set_facecolor(superficie)
        g = traza[(traza["escenario"] == esc) & (traza["outcome"] == out) & (traza["estimador"] == est)]
        verdad = g["efecto_verdadero"].mean()
        ax.axhline(verdad, color=texto2, lw=1, ls=(0, (4, 3)), zorder=1)
        ax.annotate("efecto verdadero", (0.4, verdad), xycoords=("axes fraction", "data"), xytext=(0, 4),
                    textcoords="offset points", color=texto2, fontsize=8)
        for v, color in COLORES.items():
            s = g[g["vinculo"] == v].sort_values("reps_total")
            if s.empty:
                continue
            x, m, e = s["reps_total"], s["estimacion"], 1.96 * s["mcse_sesgo"]
            ax.fill_between(x, m - e, m + e, color=color, alpha=0.18, lw=0, zorder=2)
            ax.plot(x, m, color=color, lw=2, zorder=3, label=ETIQUETAS[v])
            ax.annotate(ETIQUETAS[v], (x.iloc[-1], m.iloc[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=8, color=texto)
        ax.set_title(f"{TITULOS[esc]} · {TITULOS[out]} · {TITULOS[est]}", fontsize=9.5, color=texto, loc="left")
        ax.grid(axis="y", color=rejilla, lw=0.8)
        ax.tick_params(colors=texto2, labelsize=8)
        for lado in ("top", "right"):
            ax.spines[lado].set_visible(False)
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(rejilla)
        ax.set_xlabel("repeticiones acumuladas", fontsize=8, color=texto2)
        ax.set_ylabel("estimación media", fontsize=8, color=texto2)
        ax.margins(x=0.12)
    manijas, nombres = ejes.ravel()[0].get_legend_handles_labels()
    fig.suptitle("Convergencia de la simulación semisintética (banda: ± 1,96 · MCSE)", y=0.985, fontsize=11,
                 color=texto)
    fig.legend(manijas, nombres, loc="upper center", bbox_to_anchor=(0.5, 0.955), ncol=3, frameon=False,
               fontsize=9, labelcolor=texto)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150, facecolor=superficie)
    plt.close(fig)


def tablas_markdown(res: pd.DataFrame, ruta: Path = OUT_TABLAS) -> str:
    """Tablas del documento de resultados, generadas del resumen: media de
    la estimación (cobertura del IC 95 % entre paréntesis) por escenario,
    integración y estimador, una tabla por outcome."""
    num = lambda v, fmt: format(v, fmt).replace(".", ",")  # noqa: E731
    partes = []
    for out in OUTCOMES:
        x = res[res["outcome"] == out]
        ests = [e for e in ORDEN_EST if e in set(x["estimador"])]
        partes.append(f"### {TITULOS.get(out, out)}\n")
        partes.append("| Escenario | Efecto verdadero | Integración | " + " | ".join(NOMBRES_EST[e] for e in ests) + " |")
        partes.append("|" + "---|" * (len(ests) + 3))
        for esc in ESCENARIOS:
            for v in VINCULOS:
                g = x[(x["escenario"] == esc) & (x["vinculo"] == v)].set_index("estimador")
                if g.empty:
                    continue
                verdad = g.loc[[e for e in g.index if e != "discontinuidad_rd"], "efecto_verdadero"].mean()
                celdas = []
                for e in ests:
                    if e in g.index:
                        c = g.loc[e]
                        celdas.append(f"{num(c['estimacion'], '+.3f')} ({num(c['cobertura'], '.2f')})")
                    else:
                        celdas.append("—")
                cab = esc.replace("_", " ") if v == "oraculo" else ""
                partes.append(f"| {cab} | {num(verdad, '+.3f')} | {ETIQUETAS[v]} | " + " | ".join(celdas) + " |")
        partes.append("")
    rd = res[res["estimador"] == "discontinuidad_rd"]
    if not rd.empty:
        partes.append("Efecto verdadero en el corte (objetivo de la RD): " + ", ".join(
            f"{TITULOS.get(o, o)} {num(g['efecto_verdadero'].mean(), '+.3f')}" for o, g in rd.groupby("outcome", sort=False)))
    texto = "\n".join(partes) + "\n"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
    return texto
