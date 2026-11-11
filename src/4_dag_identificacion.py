"""DAG del proyecto y chequeos formales de identificación.

Cada diagrama se codifica como un grafo de `networkx` y cada afirmación de
identificación que hace el proyecto se comprueba con d-separación
(`networkx.is_d_separator`), no solo se narra:

  1. Diseño principal, tal como lo dibuja el documento de pipeline
     (Roncancio y Fonseca, 2026, Figura 2): un solo nodo de elegibilidad.
  2. Diseño principal refinado: separa la elegibilidad del hogar receptor
     de la del donante del Hot-Deck, y la celda del emparejamiento de las
     modificadoras del efecto. Es el que usa la estimación.
  3. Fusión de fuentes: qué se observa en cada base, y el registro en el
     Sisbén. Sustenta las cotas de Fréchet y los errores de focalización.
  4. Generador de la simulación semisintética: qué confunde la asignación
     en cada escenario y por qué el Hot-Deck da un placebo.
  5. Diseño de una sola tabla (transición Sisbén III -> IV): no se ejecuta
     con los datos del proyecto (no hay corte del Sisbén III); se deja como
     referencia del documento.

Uso:
    PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe src/4_dag_identificacion.py
Salida:
    docs/resultados/2_diagnostico_datos_reales/dag_*.png (uno por diagrama)
    docs/resultados/2_diagnostico_datos_reales/IDENTIFICACION_CAUSAL.md
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

OUT_DIR = Path("docs/resultados/2_diagnostico_datos_reales")

# Tipo de nodo -> (relleno, borde, texto, estilo del borde, leyenda)
ESTILOS = {
    "geih": ("#DCE9F5", "#2F5D8A", "#10263D", "solid", "Observado en la GEIH"),
    "sisben": ("#F6E3CF", "#9A5B1E", "#3D2208", "solid", "Observado en el Sisbén"),
    "ambas": ("#E2EEDF", "#3F6B3A", "#132611", "solid", "Observado en las dos fuentes"),
    "hotdeck": ("#2C6E63", "#1B4740", "#FFFFFF", "solid", "Grupo imputado por el Hot-Deck"),
    "no_observado": ("#FFFFFF", "#6B6B6B", "#333333", "dashed", "No observado"),
    "simulado": ("#EDE4F5", "#5E3C85", "#24123A", "solid", "Fijado por la simulación"),
}


def _nodo(g: nx.DiGraph, nombre: str, etiqueta: str, tipo: str, pos: tuple[float, float]) -> None:
    g.add_node(nombre, label=etiqueta, tipo=tipo, pos=pos)


# --------------------------------------------------------------------------
# 1-2. Diseño principal (GEIH + Sisbén por Hot-Deck)
# --------------------------------------------------------------------------

def grafo_diseno_principal() -> nx.DiGraph:
    """Figura 2 del documento, tal cual: un solo nodo `elegibilidad_real`
    con aristas hacia el grupo del Hot-Deck y hacia la participación."""
    g = nx.DiGraph(titulo="Diseño principal, como en la Figura 2 del documento")
    _nodo(g, "U", "U: capacidad de\ngenerar ingresos", "no_observado", (0.50, 1.00))
    _nodo(g, "X", "X: depto, edad\ndel jefe, vivienda", "ambas", (0.00, 0.55))
    _nodo(g, "elegibilidad_real", "Elegibilidad A/B\ndel hogar", "no_observado", (0.50, 0.55))
    _nodo(g, "participacion_dps", "Participación en\nprogramas", "no_observado", (1.00, 0.55))
    _nodo(g, "grupo_hotdeck", "Grupo del\nHot-Deck", "hotdeck", (0.25, 0.05))
    _nodo(g, "resultado_y", "Y: pobreza\ny bienestar", "geih", (1.00, 0.05))
    g.add_edges_from([
        ("U", "elegibilidad_real"), ("U", "resultado_y"),
        ("X", "elegibilidad_real"), ("X", "grupo_hotdeck"), ("X", "resultado_y"),
        ("elegibilidad_real", "grupo_hotdeck"),
        ("elegibilidad_real", "participacion_dps"), ("participacion_dps", "resultado_y"),
    ])
    for arista in [("elegibilidad_real", "grupo_hotdeck"), ("elegibilidad_real", "participacion_dps"),
                   ("participacion_dps", "resultado_y")]:
        g.edges[arista]["abierto"] = True
    return g


def grafo_diseno_principal_refinado() -> nx.DiGraph:
    """El diseño que usa la estimación. Dos separaciones respecto de la
    Figura 2:
      - el Hot-Deck no copia la elegibilidad del hogar receptor (no la
        conoce), sino la de un donante sorteado en su misma celda;
      - X es la celda del emparejamiento (departamento, ciclo de vida del
        jefe, cuartos, nivel de pisos) y Z son las modificadoras del efecto
        que no están en la celda (zona, sexo del jefe, paredes): las X del
        Causal Forest.
    Z afecta la elegibilidad y el resultado del receptor, pero no el
    sorteo, así que el conjunto de ajuste es solo la celda."""
    g = nx.DiGraph(titulo="Diseño principal refinado: receptor y donante separados")
    _nodo(g, "U", "U: capacidad de\ngenerar ingresos", "no_observado", (0.50, 1.00))
    _nodo(g, "X", "X: celda del Hot-Deck\n(depto, ciclo de vida,\ncuartos, pisos)", "ambas", (0.00, 0.55))
    _nodo(g, "Z", "Z: zona, sexo del\njefe, paredes", "ambas", (0.50, 0.10))
    _nodo(g, "elegibilidad_receptor", "Elegibilidad A/B\ndel hogar (receptor)", "no_observado", (0.50, 0.55))
    _nodo(g, "elegibilidad_donante", "Elegibilidad A/B\ndel donante\n(misma celda)", "sisben", (0.00, 0.10))
    _nodo(g, "participacion_dps", "Participación en\nprogramas", "no_observado", (1.00, 0.55))
    _nodo(g, "grupo_hotdeck", "Grupo del\nHot-Deck", "hotdeck", (0.00, -0.32))
    _nodo(g, "resultado_y", "Y: pobreza monetaria,\nIPM, ingreso", "geih", (1.00, 0.10))
    g.add_edges_from([
        ("U", "elegibilidad_receptor"), ("U", "resultado_y"),
        ("X", "elegibilidad_receptor"), ("X", "elegibilidad_donante"), ("X", "resultado_y"),
        ("Z", "elegibilidad_receptor"), ("Z", "resultado_y"),
        ("elegibilidad_donante", "grupo_hotdeck"),
        ("elegibilidad_receptor", "participacion_dps"), ("participacion_dps", "resultado_y"),
    ])
    return g


def analizar_dseparacion(g: nx.DiGraph, extra_condicionantes: tuple[str, ...] = ()) -> dict:
    """¿`grupo_hotdeck` queda d-separado de `resultado_y` condicionando en
    X (y opcionalmente en nodos adicionales)?"""
    resultado = {"d_separado_dado_X": nx.is_d_separator(g, {"grupo_hotdeck"}, {"resultado_y"}, {"X"})}
    if extra_condicionantes:
        resultado[f"d_separado_dado_X_mas_{'_'.join(extra_condicionantes)}"] = nx.is_d_separator(
            g, {"grupo_hotdeck"}, {"resultado_y"}, {"X", *extra_condicionantes})
    return resultado


# --------------------------------------------------------------------------
# 3. Fusión de fuentes y registro en el Sisbén
# --------------------------------------------------------------------------

def grafo_fusion_fuentes(registro_depende_de_u: bool = True) -> nx.DiGraph:
    """Qué se observa en cada fuente. La GEIH trae X, Z y el resultado; el
    Sisbén trae X, Z y el grupo, pero solo de los hogares registrados (S).
    Ningún hogar tiene a la vez grupo y resultado: la conjunta (T, Y) no
    se observa, y por eso solo se acota (Fréchet).

    Las cotas usan P(T | celda) del registro como la de toda la celda. Eso
    exige T ⊥ S | X, Z: falla si lo que lleva a registrarse (U) también
    mueve la elegibilidad. `registro_depende_de_u=False` es el mundo en que
    el supuesto vale."""
    g = nx.DiGraph(titulo="Fusión de fuentes: ninguna base observa grupo y resultado juntos")
    _nodo(g, "U", "U: capacidad de\ngenerar ingresos", "no_observado", (0.66, 1.00))
    _nodo(g, "X", "X: celda del\nHot-Deck", "ambas", (0.00, 0.60))
    _nodo(g, "Z", "Z: zona, sexo\ndel jefe, paredes", "ambas", (0.00, 0.10))
    _nodo(g, "S", "S: hogar registrado\nen el Sisbén", "sisben", (0.66, -0.32))
    _nodo(g, "T", "T: grupo A/B\n(solo si S = 1)", "sisben", (1.00, 0.60))
    _nodo(g, "Y", "Y: pobreza\n(muestra GEIH)", "geih", (1.00, 0.10))
    g.add_edges_from([("U", "T"), ("U", "Y"), ("X", "T"), ("X", "Y"), ("Z", "T"), ("Z", "Y"),
                      ("X", "S"), ("Z", "S"), ("T", "Y")])
    if registro_depende_de_u:
        g.add_edge("U", "S", condicional=True)
    return g


# --------------------------------------------------------------------------
# 4. Generador de la simulación semisintética
# --------------------------------------------------------------------------

def grafo_simulacion(gamma: bool = True) -> nx.DiGraph:
    """El mundo de `src/simulacion/`: hogares reales de la GEIH (X, Z, U y
    Y0 reales) y una asignación simulada,
        score = logit P_Sisbén(T | celda) + Z·b + gamma·U,
    con T por sorteo o por corte del puntaje. Y = Y0 + tau(Z)·T. El
    Hot-Deck le da a cada hogar el T de un donante de su celda.
    `gamma=False` es el escenario sin confusión no observada."""
    g = nx.DiGraph(titulo="Generador de la simulación semisintética" + ("" if gamma else " (gamma = 0)"))
    _nodo(g, "X", "X: celda del\nHot-Deck", "geih", (0.00, 0.95))
    _nodo(g, "Z", "Z: zona, sexo\ndel jefe, paredes", "geih", (0.45, 0.95))
    _nodo(g, "U", "U: residuo del\ningreso real", "no_observado", (0.85, 0.95))
    _nodo(g, "T", "T verdadero\n(sorteo o corte)", "simulado", (0.30, 0.45))
    _nodo(g, "T_donante", "T del donante\n(misma celda)", "simulado", (0.00, 0.45))
    _nodo(g, "T_hotdeck", "T del\nHot-Deck", "hotdeck", (0.00, -0.05))
    _nodo(g, "Y0", "Y0: ingreso real\nsin programa", "geih", (0.85, 0.45))
    _nodo(g, "Y", "Y = Y0 + tau(Z)·T", "simulado", (0.60, -0.05))
    g.add_edges_from([("X", "T"), ("Z", "T"), ("X", "T_donante"), ("T_donante", "T_hotdeck"),
                      ("X", "Y0"), ("Z", "Y0"), ("U", "Y0"), ("Y0", "Y"), ("T", "Y"), ("Z", "Y")])
    if gamma:
        g.add_edge("U", "T", condicional=True)
    return g


def ajuste_valido(g: nx.DiGraph, tratamiento: str, resultado: str, ajuste: set[str]) -> bool:
    """Criterio de la puerta trasera: ningún nodo de ajuste desciende del
    tratamiento, y el ajuste bloquea todo camino que entra al tratamiento."""
    if ajuste & nx.descendants(g, tratamiento):
        return False
    sin_salida = g.copy()
    sin_salida.remove_edges_from(list(g.out_edges(tratamiento)))
    return nx.is_d_separator(sin_salida, {tratamiento}, {resultado}, ajuste)


# --------------------------------------------------------------------------
# 5. Diseño de una sola tabla (Sisbén III -> IV)
# --------------------------------------------------------------------------

def grafo_una_tabla() -> nx.DiGraph:
    """Figura 3 del documento: la regla nueva cambia la clasificación sin
    cambiar el hogar. El resultado no puede ser una privación calculada por
    el propio Sisbén (`I1`-`I15`, `H_5`)."""
    g = nx.DiGraph(titulo="Diseño de una sola tabla: transición Sisbén III a IV")
    _nodo(g, "X", "X: condiciones del hogar\n(no cambian entre cortes)", "sisben", (0.00, 1.00))
    _nodo(g, "regla_nueva", "Regla del Sisbén IV\n(cambia el modelo,\nno el hogar)", "sisben", (1.00, 1.00))
    _nodo(g, "clasif_siii", "Clasificación\nSisbén III", "no_observado", (0.00, 0.45))
    _nodo(g, "clasif_siv", "Clasificación\nSisbén IV", "sisben", (1.00, 0.45))
    _nodo(g, "resultado_y", "Y: por definir\n(no calculado por el Sisbén)", "no_observado", (0.50, -0.05))
    g.add_edges_from([("X", "clasif_siii"), ("X", "clasif_siv"), ("X", "resultado_y"),
                      ("regla_nueva", "clasif_siv"), ("clasif_siii", "resultado_y"), ("clasif_siv", "resultado_y")])
    return g


# --------------------------------------------------------------------------
# Dibujo
# --------------------------------------------------------------------------

def dibujar(g: nx.DiGraph, out_path: Path, curvas: dict[tuple[str, str], float] | None = None,
            nota: str = "") -> None:
    """Cajas ajustadas al texto, flechas que terminan en el borde de cada
    caja, borde punteado para lo no observado y leyenda de los tipos."""
    curvas = curvas or {}
    xs = [p[0] for _, p in g.nodes(data="pos")]
    ys = [p[1] for _, p in g.nodes(data="pos")]
    fig, ax = plt.subplots(figsize=(10, 6.6))
    ax.set_xlim(min(xs) - 0.22, max(xs) + 0.22)
    ax.set_ylim(min(ys) - 0.32, max(ys) + 0.18)
    ax.axis("off")
    cajas = {}
    for n, d in g.nodes(data=True):
        relleno, borde, texto, estilo, _ = ESTILOS[d["tipo"]]
        t = ax.text(*d["pos"], d["label"], ha="center", va="center", fontsize=9.5, color=texto, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.55", facecolor=relleno, edgecolor=borde,
                              linewidth=1.6, linestyle=estilo))
        cajas[n] = t
    fig.canvas.draw()  # las cajas existen recién después de dibujar el texto
    for u, v, d in g.edges(data=True):
        color = "#B23A3A" if d.get("abierto") else "#3A3A3A"
        ax.annotate("", xy=g.nodes[v]["pos"], xytext=g.nodes[u]["pos"], zorder=2,
                    arrowprops=dict(arrowstyle="-|>", mutation_scale=16, color=color,
                                    linewidth=2.2 if d.get("abierto") else 1.3,
                                    linestyle="--" if d.get("condicional") else "-",
                                    shrinkA=3, shrinkB=3, patchA=cajas[u].get_bbox_patch(),
                                    patchB=cajas[v].get_bbox_patch(),
                                    connectionstyle=f"arc3,rad={curvas.get((u, v), 0.0)}"))
    tipos = list(dict.fromkeys(d["tipo"] for _, d in g.nodes(data=True)))
    manejadores = [Patch(facecolor=ESTILOS[t][0], edgecolor=ESTILOS[t][1], linestyle=ESTILOS[t][3],
                         linewidth=1.4, label=ESTILOS[t][4]) for t in tipos]
    manejadores.append(Line2D([], [], color="#3A3A3A", marker=">", markersize=6, label="Efecto directo"))
    if any(d.get("condicional") for *_, d in g.edges(data=True)):
        manejadores.append(Line2D([], [], color="#3A3A3A", linestyle="--", label="Solo en algunos escenarios"))
    if any(d.get("abierto") for *_, d in g.edges(data=True)):
        manejadores.append(Line2D([], [], color="#B23A3A", linewidth=2.2, label="Camino que X no bloquea"))
    ax.legend(handles=manejadores, loc="lower center", bbox_to_anchor=(0.5, -0.02), ncol=min(len(manejadores), 4),
              frameon=False, fontsize=8.5)
    ax.set_title(g.graph["titulo"], fontsize=12, pad=12)
    if nota:
        fig.text(0.5, 0.005, nota, ha="center", va="bottom", fontsize=8.5, color="#444444", style="italic")
    fig.tight_layout(rect=(0, 0.03 if nota else 0, 1, 1))
    fig.savefig(out_path, dpi=160, facecolor="white")
    plt.close(fig)


# --------------------------------------------------------------------------
# Chequeos y reporte
# --------------------------------------------------------------------------

def chequeos() -> dict[str, bool]:
    """Cada afirmación de identificación del proyecto, comprobada en su DAG."""
    lit, ref = grafo_diseno_principal(), grafo_diseno_principal_refinado()
    fus, fus_sin_u = grafo_fusion_fuentes(), grafo_fusion_fuentes(registro_depende_de_u=False)
    sim, sim_sin_u = grafo_simulacion(), grafo_simulacion(gamma=False)
    return {
        "literal_grupo_indep_y_dado_X": nx.is_d_separator(lit, {"grupo_hotdeck"}, {"resultado_y"}, {"X"}),
        "literal_grupo_indep_y_dado_X_y_elegibilidad": nx.is_d_separator(
            lit, {"grupo_hotdeck"}, {"resultado_y"}, {"X", "elegibilidad_real"}),
        "refinado_grupo_indep_y_dado_X": nx.is_d_separator(ref, {"grupo_hotdeck"}, {"resultado_y"}, {"X"}),
        "refinado_grupo_indep_y_sin_ajuste": nx.is_d_separator(ref, {"grupo_hotdeck"}, {"resultado_y"}, set()),
        "refinado_elegibilidad_identificada_dado_X_Z": ajuste_valido(ref, "elegibilidad_receptor", "resultado_y",
                                                                     {"X", "Z"}),
        "fusion_registro_ignorable_con_U": nx.is_d_separator(fus, {"T"}, {"S"}, {"X", "Z"}),
        "fusion_registro_ignorable_sin_U": nx.is_d_separator(fus_sin_u, {"T"}, {"S"}, {"X", "Z"}),
        "simulacion_ajuste_X_Z_con_gamma": ajuste_valido(sim, "T", "Y", {"X", "Z"}),
        "simulacion_ajuste_X_Z_sin_gamma": ajuste_valido(sim_sin_u, "T", "Y", {"X", "Z"}),
        "simulacion_hotdeck_indep_y_dado_X": nx.is_d_separator(sim, {"T_hotdeck"}, {"Y"}, {"X"}),
        "una_tabla_regla_exogena": nx.is_d_separator(grafo_una_tabla(), {"regla_nueva"}, {"X"}, set()),
    }


def _si(v: bool) -> str:
    return "Sí" if v else "No"


def reporte(c: dict[str, bool]) -> str:
    return f"""# Identificación causal: los DAG del proyecto

Generado por `src/4_dag_identificacion.py`. Cada afirmación de
identificación se comprueba con d-separación en su grafo
(`networkx.is_d_separator`); las pruebas están en
`tests/test_ingesta_y_validacion.py`. Colores: azul, observado en la GEIH;
naranja, en el Sisbén; verde, en las dos fuentes; verde oscuro, el grupo
imputado por el Hot-Deck; morado, fijado por la simulación; borde
punteado, no observado.

| Diagrama | Archivo | Para qué sirve |
|---|---|---|
| Diseño principal (Figura 2 del documento) | `dag_diseno_principal.png` | Muestra por qué el diagrama original no sostiene su propia afirmación |
| Diseño principal refinado | `dag_diseno_principal_refinado.png` | El que usa la estimación: conjunto de ajuste y placebo del Hot-Deck |
| Fusión de fuentes | `dag_fusion_fuentes.png` | Qué observa cada base; supuesto de las cotas de Fréchet y de los errores de focalización |
| Generador de la simulación | `dag_simulacion.png` | Qué confunde la asignación en cada escenario |
| Una sola tabla (Sisbén III a IV) | `dag_una_tabla.png` | Diseño alternativo del documento; no se ejecuta con los datos del proyecto |

## 1. Diseño principal, como en la Figura 2

| Pregunta | Condicionando en | Respuesta |
|---|---|---|
| ¿El grupo del Hot-Deck es independiente de Y? | X | **{_si(c['literal_grupo_indep_y_dado_X'])}** |
| | X y la elegibilidad | {_si(c['literal_grupo_indep_y_dado_X_y_elegibilidad'])} |

El documento afirma que, dado X, el grupo del Hot-Deck no depende de Y.
Con un solo nodo de elegibilidad, el grafo no lo sostiene: queda abierto
el camino grupo ← elegibilidad → participación → Y, y la elegibilidad no
se observa en la GEIH.

## 2. Diseño principal refinado (el que usa la estimación)

El Hot-Deck no copia la elegibilidad del hogar receptor, que no conoce,
sino la de un donante sorteado en su misma celda. Además, la celda X
(departamento, ciclo de vida del jefe, cuartos, nivel de pisos) se separa
de Z (zona, sexo del jefe, paredes), que modifican el efecto pero no
entran al sorteo.

| Pregunta | Condicionando en | Respuesta |
|---|---|---|
| ¿El grupo del Hot-Deck es independiente de Y? | X (celda) | **{_si(c['refinado_grupo_indep_y_dado_X'])}** |
| | Nada | {_si(c['refinado_grupo_indep_y_sin_ajuste'])} |
| ¿Se identifica el efecto de la elegibilidad del propio hogar? | X y Z | {_si(c['refinado_elegibilidad_identificada_dado_X_Z'])} |

Lectura:
- **El conjunto de ajuste es la celda, y basta.** Por eso el DML usa la
  celda exacta como indicadoras (`W_CELDA` en `5_estimacion.py`), y Z va
  en las X del Causal Forest solo para la heterogeneidad.
- **Dado X, el grupo imputado es independiente de Y: el DML sobre ese
  grupo es un placebo del emparejamiento**, no el efecto del Sisbén. El
  ≈0 que da (`RESULTADOS_DML_ATE_ATT_ATU.md`) es lo que predice el grafo.
- **El efecto de la elegibilidad real no se identifica** con variables
  observadas: el camino elegibilidad ← U → Y no se cierra. Por eso, con
  datos reales, solo se acota (`RESULTADOS_FRECHET_MANSKI.md`).

## 3. Fusión de fuentes

La GEIH trae X, Z e Y; el Sisbén trae X, Z y el grupo T, solo de los
hogares registrados (S). Ningún hogar tiene T e Y a la vez, así que su
conjunta solo se acota celda por celda (cotas de Fréchet).

| Pregunta | Mundo | Respuesta |
|---|---|---|
| ¿T es independiente del registro, dado X y Z? | El registro depende de U | **{_si(c['fusion_registro_ignorable_con_U'])}** |
| | El registro no depende de U | {_si(c['fusion_registro_ignorable_sin_U'])} |

Las cotas del efecto (`RESULTADOS_FRECHET_MANSKI.md`) y los errores de
focalización (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`) toman la
proporción de A/B de los registrados como la de toda la celda. El grafo
dice cuándo vale: solo si lo que lleva a un hogar a registrarse no está
relacionado con su elegibilidad más allá de X y Z. La cobertura del
registro varía 32 veces entre departamentos
(`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`), así que es un supuesto que se
declara, no que se verifica.

## 4. Generador de la simulación semisintética

Hogares reales de la GEIH (X, Z, U e Y0 reales) y una asignación
simulada: score = logit P_Sisbén(T | celda) + Z·b + gamma·U, por sorteo o
por corte del puntaje; Y = Y0 + tau(Z)·T (`src/simulacion/`).

| Pregunta | Escenario | Respuesta |
|---|---|---|
| ¿Ajustar por X y Z identifica el efecto de T? | gamma = 0 (confusión observada) | **{_si(c['simulacion_ajuste_X_Z_sin_gamma'])}** |
| | gamma > 0 (confusión no observada) | **{_si(c['simulacion_ajuste_X_Z_con_gamma'])}** |
| ¿El T del Hot-Deck es independiente de Y, dado X? | Cualquiera | {_si(c['simulacion_hotdeck_indep_y_dado_X'])} |

Es la estructura que la simulación pone a prueba
(`SIMULACION_SEMISINTETICA.md`): con confusión observada, regresión, DML
y Causal Forest recuperan el efecto; con confusión no observada, ninguno;
con el T del Hot-Deck, todos dan ≈0\\*, como dice la última fila.

\\* Resultado simulado.

## 5. Diseño de una sola tabla (Sisbén III a IV)

| Pregunta | Respuesta |
|---|---|
| ¿La regla nueva es independiente de las condiciones del hogar? | {_si(c['una_tabla_regla_exogena'])} |

Si la regla del Sisbén IV es nacional (no se decide hogar por hogar), el
cambio de clasificación que produce aísla una variación limpia. Requiere
los dos cortes del Sisbén para los mismos hogares; con los datos del
proyecto (solo el Sisbén IV) no se ejecuta. El resultado no puede ser una
privación calculada por el propio Sisbén (`I1`-`I15`, `H_5`).
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dibujar(grafo_diseno_principal(), OUT_DIR / "dag_diseno_principal.png",
            curvas={("X", "resultado_y"): -0.12},
            nota="Con un solo nodo de elegibilidad, el camino grupo ← elegibilidad → participación → Y queda abierto.")
    dibujar(grafo_diseno_principal_refinado(), OUT_DIR / "dag_diseno_principal_refinado.png",
            curvas={},
            nota="Ajuste: solo la celda X. Dado X, el grupo imputado es independiente de Y (placebo del emparejamiento).")
    dibujar(grafo_fusion_fuentes(), OUT_DIR / "dag_fusion_fuentes.png",
            curvas={("U", "Y"): -0.1, ("U", "T"): 0.1},
            nota="T e Y nunca se observan juntos. Usar P(T | celda) del registro exige que S no dependa de U.")
    dibujar(grafo_simulacion(), OUT_DIR / "dag_simulacion.png",
            curvas={},
            nota="La arista U → T existe solo en los escenarios con confusión no observada (gamma > 0).")
    dibujar(grafo_una_tabla(), OUT_DIR / "dag_una_tabla.png",
            nota="Requiere los dos cortes del Sisbén para los mismos hogares; no se ejecuta con los datos del proyecto.")
    c = chequeos()
    for k, v in c.items():
        print(f"  {k}: {v}")
    (OUT_DIR / "IDENTIFICACION_CAUSAL.md").write_text(reporte(c), encoding="utf-8")
    print(f"\nGuardado: {OUT_DIR / 'IDENTIFICACION_CAUSAL.md'} y {len(list(OUT_DIR.glob('dag_*.png')))} diagramas")


if __name__ == "__main__":
    main()
