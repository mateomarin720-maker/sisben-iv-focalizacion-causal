"""Especificación del DAG causal y análisis de identificabilidad (OE3).

Implementa los dos diseños del documento de pipeline (Roncancio y Fonseca,
2026, "Pipeline de datos y modelos para estimar el efecto causal del Sisbén
IV...", Figuras 2 y 3):

  1. Diseño principal (GEIH + Sisbén + IPM): tratamiento = elegibilidad A/B
     real (no observada; lo que se observa es el grupo asignado por
     Hot-Deck), resultado = IPM/bienestar del hogar, covariables X = depto +
     ciclo de vida del jefe + vivienda.
  2. Diseño de una sola tabla (transición Sisbén III -> IV): evita cruzar
     bases; aísla el cambio de regla de un cambio en las condiciones del
     hogar. Requiere los dos cortes del Sisbén (III no se tiene todavía).

En vez de inventar aristas, se codifican EXACTAMENTE las que describe el
documento (ver docstrings de cada función `grafo_*`), y se usa
`networkx` para una pregunta concreta: dado el DAG, ¿el grupo asignado por
Hot-Deck queda d-separado del resultado condicionando en X? Esa es la
afirmación central del documento ("dado X, el grupo del Hot-Deck no
depende de Y") y se puede verificar formalmente, no solo narrarla.

⚠️ Esto NO reemplaza la implementación de 5_estimacion.py (DML/Causal
Forest siguen pendientes) — es el paso previo de identificación que ese
script necesita para saber qué conjunto de covariables usar como ajuste.

Uso:
    poetry run python src/4_dag_identificacion.py
Salida:
    docs/resultados/dag_diseno_principal.png
    docs/resultados/dag_una_tabla.png
    docs/resultados/IDENTIFICACION_CAUSAL.md
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

OUT_DIR = Path("docs/resultados")

# Estilo de los nodos: observado en los datos que ya tenemos (gris), no
# observado o pendiente (blanco con borde punteado), lo que efectivamente
# usa el Hot-Deck hoy (azul).
COLOR_OBSERVADO = "#D9DDD3"
COLOR_NO_OBSERVADO = "#FFFFFF"
COLOR_CLAVE = "#2C6E63"


def grafo_diseno_principal() -> nx.DiGraph:
    """Figura 2 del documento: GEIH + Sisbén + IPM.

    Nodos:
      U                  no observado — capacidad de generar ingresos.
      X                  covariables comunes: geo_depto, jefe_edad (ciclo
                         de vida), vivienda (paredes/pisos/cuartos).
      elegibilidad_real  elegibilidad A/B real del hogar — NO observada en
                         GEIH, solo en el Sisbén de hogares registrados.
      grupo_hotdeck      lo que sí se observa en GEIH tras el Hot-Deck —
                         se sortea dentro de la celda de X (geo_depto +
                         ciclo de vida), ver
                         src/emparejamiento/emparejamiento_hotdeck_geih_sisben.py.
      participacion_dps  recibe o no subsidios DPS — fuente todavía
                         pendiente (catalogo.yaml: dps, estado=pendiente).
      resultado_y        IPM / bienestar del hogar, construido sobre GEIH.

    Aristas (tal como las describe el documento):
      U -> elegibilidad_real, U -> resultado_y        (confusor no observado)
      X -> elegibilidad_real, X -> grupo_hotdeck, X -> resultado_y
      elegibilidad_real -> grupo_hotdeck               (relación con error de medición)
      elegibilidad_real -> participacion_dps -> resultado_y
    """
    g = nx.DiGraph()
    g.add_nodes_from([
        ("U", {"obs": False, "label": "No observado U\n(capacidad de generar ingresos)"}),
        ("X", {"obs": True, "label": "Covariables X\n(depto, edad, vivienda)"}),
        ("elegibilidad_real", {"obs": False, "label": "Elegibilidad real A/B\n(no observada en GEIH)"}),
        ("grupo_hotdeck", {"obs": True, "clave": True, "label": "Grupo Hot-Deck\n(lo que se observa en GEIH)"}),
        ("participacion_dps", {"obs": False, "label": "Participación (DPS)\n(fuente pendiente)"}),
        ("resultado_y", {"obs": True, "label": "Resultado Y: IPM\n(bienestar del hogar, GEIH)"}),
    ])
    g.add_edges_from([
        ("U", "elegibilidad_real"), ("U", "resultado_y"),
        ("X", "elegibilidad_real"), ("X", "grupo_hotdeck"), ("X", "resultado_y"),
        ("elegibilidad_real", "grupo_hotdeck"),
        ("elegibilidad_real", "participacion_dps"),
        ("participacion_dps", "resultado_y"),
    ])
    return g


def grafo_diseno_principal_refinado() -> nx.DiGraph:
    """Misma Figura 2, pero separando dos variables que el diagrama original
    colapsa en un solo nodo "elegibilidad_real" — y que el chequeo de
    d-separación (ver `main()`) muestra que SÍ hay que separar para que la
    afirmación del documento ("dado X, el grupo no depende de Y") sea
    formalmente cierta, no solo narrada.

    El Hot-Deck no copia la elegibilidad real DEL HOGAR RECEPTOR (no la
    conoce) — copia la de un hogar DONANTE sorteado al azar dentro de la
    misma celda de X (ver `emparejamiento_hotdeck_geih_sisben.hotdeck`).
    Son dos variables distintas:
      elegibilidad_receptor  afecta a participacion_dps y resultado_y DEL
                              MISMO hogar — nunca a grupo_hotdeck.
      elegibilidad_donante   la elegibilidad de OTRO hogar en la misma
                              celda de X — determina grupo_hotdeck, no tiene
                              ninguna arista hacia participacion_dps ni
                              resultado_y del receptor.
    Con esta separación, el único camino de grupo_hotdeck a resultado_y
    vuelve a pasar por X.
    """
    g = nx.DiGraph()
    g.add_nodes_from([
        ("U", {"obs": False, "label": "No observado U\n(capacidad de generar ingresos)"}),
        ("X", {"obs": True, "label": "Covariables X\n(depto, edad, vivienda)"}),
        ("elegibilidad_receptor", {"obs": False, "label": "Elegibilidad real\n(hogar RECEPTOR)"}),
        ("elegibilidad_donante", {"obs": False, "label": "Elegibilidad real\n(hogar DONANTE, misma celda X)"}),
        ("grupo_hotdeck", {"obs": True, "clave": True, "label": "Grupo Hot-Deck\n(lo que se observa en GEIH)"}),
        ("participacion_dps", {"obs": False, "label": "Participación (DPS)\n(fuente pendiente)"}),
        ("resultado_y", {"obs": True, "label": "Resultado Y: IPM\n(bienestar del hogar, GEIH)"}),
    ])
    g.add_edges_from([
        ("U", "elegibilidad_receptor"), ("U", "resultado_y"),
        ("X", "elegibilidad_receptor"), ("X", "elegibilidad_donante"),
        ("X", "grupo_hotdeck"), ("X", "resultado_y"),
        ("elegibilidad_donante", "grupo_hotdeck"),
        ("elegibilidad_receptor", "participacion_dps"),
        ("participacion_dps", "resultado_y"),
    ])
    return g


def grafo_una_tabla() -> nx.DiGraph:
    """Figura 3 del documento: transición Sisbén III -> Sisbén IV.

    Nodos:
      X               condiciones del hogar — no cambian entre cortes.
      regla_nueva     la regla del Sisbén IV — cambia el modelo, no el hogar.
      clasif_siii     clasificación bajo Sisbén III (antes de la transición).
      clasif_siv      clasificación bajo Sisbén IV (después de la transición).
      resultado_y     por definir — depende de qué traigan ambos cortes;
                      NO puede ser I1-I15 ni H_5 (circularidad, ver
                      docs/insumos/DICCIONARIO_HOTDECK.md §7).

    Aristas:
      X -> clasif_siii, X -> clasif_siv, X -> resultado_y
      regla_nueva -> clasif_siv
      clasif_siii -> resultado_y, clasif_siv -> resultado_y   (punteadas: Y por definir)
    """
    g = nx.DiGraph()
    g.add_nodes_from([
        ("X", {"obs": True, "label": "Condiciones del hogar X\n(no cambian entre cortes)"}),
        ("regla_nueva", {"obs": True, "clave": True, "label": "Regla nueva (Sisbén IV)\n(cambia el modelo, no el hogar)"}),
        ("clasif_siii", {"obs": False, "label": "Clasificación Sisbén III\n(antes de la transición)"}),
        ("clasif_siv", {"obs": True, "label": "Clasificación Sisbén IV\n(después de la transición)"}),
        ("resultado_y", {"obs": False, "label": "Resultado Y: por definir\n(no calculado por el Sisbén)"}),
    ])
    g.add_edges_from([
        ("X", "clasif_siii"), ("X", "clasif_siv"), ("X", "resultado_y"),
        ("regla_nueva", "clasif_siv"),
        ("clasif_siii", "resultado_y"), ("clasif_siv", "resultado_y"),
    ])
    return g


def analizar_dseparacion(g: nx.DiGraph, extra_condicionantes: tuple[str, ...] = ()) -> dict:
    """Verifica, con el DAG dado, si grupo_hotdeck queda d-separado de
    resultado_y condicionando en X (y opcionalmente en nodos adicionales)."""
    base = {"X"}
    dsep_X = nx.is_d_separator(g, {"grupo_hotdeck"}, {"resultado_y"}, base)
    resultado = {"d_separado_dado_X": dsep_X}
    if extra_condicionantes:
        cond = base | set(extra_condicionantes)
        resultado[f"d_separado_dado_X_mas_{'_'.join(extra_condicionantes)}"] = nx.is_d_separator(
            g, {"grupo_hotdeck"}, {"resultado_y"}, cond
        )
    return resultado


def _dibujar(g: nx.DiGraph, pos: dict, titulo: str, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    colores = []
    for n in g.nodes:
        if g.nodes[n].get("clave"):
            colores.append(COLOR_CLAVE)
        elif g.nodes[n].get("obs"):
            colores.append(COLOR_OBSERVADO)
        else:
            colores.append(COLOR_NO_OBSERVADO)

    nx.draw_networkx_nodes(g, pos, ax=ax, node_color=colores, node_size=5200,
                            edgecolors="#4B564E", linewidths=1.2)
    nx.draw_networkx_edges(g, pos, ax=ax, arrows=True, arrowsize=18,
                            connectionstyle="arc3,rad=0.05", node_size=5200)
    labels = {n: g.nodes[n]["label"] for n in g.nodes}
    nx.draw_networkx_labels(g, pos, labels=labels, ax=ax, font_size=8)

    ax.set_title(titulo, fontsize=11)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    g1 = grafo_diseno_principal()
    pos1 = {
        "U": (0.5, 1.0), "X": (0.0, 0.55), "elegibilidad_real": (0.5, 0.55),
        "participacion_dps": (1.0, 0.55), "grupo_hotdeck": (0.5, 0.0),
        "resultado_y": (1.0, 0.0),
    }
    _dibujar(g1, pos1, "Diseño principal (Figura 2 literal)", OUT_DIR / "dag_diseno_principal.png")

    g1r = grafo_diseno_principal_refinado()
    pos1r = {
        "U": (0.5, 1.0), "X": (0.0, 0.55),
        "elegibilidad_receptor": (0.35, 0.55), "elegibilidad_donante": (0.75, 0.75),
        "participacion_dps": (1.0, 0.55), "grupo_hotdeck": (0.5, 0.0),
        "resultado_y": (1.0, 0.0),
    }
    _dibujar(g1r, pos1r, "Diseño principal (refinado: donante ≠ receptor)",
             OUT_DIR / "dag_diseno_principal_refinado.png")

    g2 = grafo_una_tabla()
    pos2 = {
        "X": (0.0, 1.0), "regla_nueva": (1.0, 1.0),
        "clasif_siii": (0.0, 0.5), "clasif_siv": (1.0, 0.5),
        "resultado_y": (0.5, 0.0),
    }
    _dibujar(g2, pos2, "Diseño de una sola tabla: Sisbén III -> IV", OUT_DIR / "dag_una_tabla.png")

    r_literal = analizar_dseparacion(g1, extra_condicionantes=("elegibilidad_real",))
    r_refinado = analizar_dseparacion(g1r, extra_condicionantes=("elegibilidad_receptor", "elegibilidad_donante"))

    print("=== Diseño principal LITERAL (un solo nodo elegibilidad_real) ===")
    for k, v in r_literal.items():
        print(f"  {k}: {v}")
    print("=== Diseño principal REFINADO (elegibilidad donante != receptor) ===")
    for k, v in r_refinado.items():
        print(f"  {k}: {v}")

    reporte = f"""# Identificación causal — diseño principal y diseño de una sola tabla

Generado por `src/4_dag_identificacion.py` a partir de las Figuras 2 y 3 de
Roncancio y Fonseca (2026), *Pipeline de datos y modelos para estimar el
efecto causal del Sisbén IV...*. Diagramas: `dag_diseno_principal.png`
(literal), `dag_diseno_principal_refinado.png`, `dag_una_tabla.png` (esta
misma carpeta).

## 1. Diseño principal (GEIH + Sisbén + IPM)

Tratamiento: elegibilidad A/B del Sisbén (lo que se observa en GEIH es
`grupo_hotdeck`, asignado por `src/emparejamiento/`). Resultado: IPM /
bienestar del hogar. Covariables X: `geo_depto`, `jefe_edad` (ciclo de
vida), vivienda.

**Chequeo formal de d-separación** (`networkx.is_d_separator`) — se probó el
grafo de la Figura 2 tal como la describe el documento (un solo nodo
`elegibilidad_real`) y una versión refinada (ver más abajo):

| Grafo | Condicionando en | ¿`grupo_hotdeck` ⊥ `resultado_y`? |
|---|---|---|
| Literal (Fig. 2) | Solo X | **{r_literal['d_separado_dado_X']}** |
| Literal (Fig. 2) | X + elegibilidad_real | {r_literal['d_separado_dado_X_mas_elegibilidad_real']} |
| Refinado | Solo X | **{r_refinado['d_separado_dado_X']}** |
| Refinado | X + ambas elegibilidades | {r_refinado['d_separado_dado_X_mas_elegibilidad_receptor_elegibilidad_donante']} |

### El grafo literal de la Figura 2 NO sostiene formalmente su propia afirmación

El documento dice "dado X, el grupo del Hot-Deck no depende de Y". Puesto el
grafo exactamente como lo describe la Figura 2 (`elegibilidad_real` como un
solo nodo con aristas hacia `grupo_hotdeck` *y* hacia `participacion_dps`),
`networkx.is_d_separator` dice que **NO** quedan d-separados condicionando
solo en X. La razón es un camino que el texto no menciona:
`grupo_hotdeck <- elegibilidad_real -> participacion_dps -> resultado_y`.
`elegibilidad_real` es una bifurcación (fork) en ese camino — conectar X a
`elegibilidad_real` no cierra la bifurcación; hay que condicionar en
`elegibilidad_real` misma (imposible: no se observa) o en algo que bloquee
ese camino específico.

### Por qué el diseño sí funciona en la práctica: hay que separar receptor de donante

El Hot-Deck real no copia la elegibilidad del hogar receptor (no la
conoce) — copia la de un **hogar donante** sorteado al azar dentro de la
misma celda de X. Son dos variables distintas que la Figura 2 colapsa en un
solo nodo. Separándolas (`dag_diseno_principal_refinado.png`):
`elegibilidad_donante` determina `grupo_hotdeck` pero no tiene ninguna
arista hacia `participacion_dps` ni `resultado_y` del receptor;
`elegibilidad_receptor` sí las tiene, pero no determina `grupo_hotdeck`. Con
esa separación, **condicionar solo en X sí basta** (ver tabla: Refinado /
Solo X = {r_refinado['d_separado_dado_X']}) — el camino problemático desaparece porque ya
no comparten el nodo intermedio. `U` (capacidad de generar ingresos) afecta
a `elegibilidad_receptor` y a `resultado_y`, pero no tiene arista hacia
`grupo_hotdeck`, así que tampoco abre un camino adicional.

**Conclusión práctica:** la afirmación del documento es correcta, pero su
justificación formal depende de distinguir "elegibilidad del hogar" de
"elegibilidad del donante que le tocó en el sorteo" — un matiz que vale la
pena dejar explícito en el marco teórico-metodológico (ítem pendiente de la
sección "Próximos pasos" del documento), porque el diagrama tal como está
dibujado hoy no cierra solo.

### Por qué la prueba empírica (2026-10-21, `src/estimacion/prueba_ate_att_cate.py`) no colapsó del todo para el ingreso

La Figura 2 define X como **depto + edad + vivienda**. El Hot-Deck
implementado (`emparejamiento_hotdeck_geih_sisben.py`) arma la celda con
**solo depto + ciclo de vida del jefe** — vivienda NO está en la celda
todavía (es justamente el primer punto de "Próximos pasos" del documento:
"sumar variables de vivienda a la celda"). La prueba exploratoria de ATE/CATE
controló por depto+edad (el X *implementado*), no por el X *completo* que
pide la Figura 2. El residuo de -2,3 % en log(ingreso) y la importancia alta
de `viv_cuartos`/`viv_paredes` en el Causal Forest son exactamente lo
esperable si falta esa parte de X — no una contradicción del diseño, sino la
confirmación empírica de por qué ese paso está en la lista de pendientes.

### Limitación que el grafo no resuelve

`U` (capacidad de generar ingresos) es un confusor de `elegibilidad_receptor`
y `resultado_y`, y no es observado. Esto **no** bloquea la identificación de
`grupo_hotdeck -> resultado_y` (ver arriba — `U` no tiene arista hacia
`grupo_hotdeck`), pero sí bloquea la identificación del efecto de la
**elegibilidad real del propio hogar** si en algún momento se quisiera
estimar esa versión del tratamiento directamente (en vez del grupo asignado
por Hot-Deck) — el backdoor por X no es suficiente ahí porque existe el
camino `elegibilidad_receptor <- U -> resultado_y` sin forma de cerrarlo
con variables observadas.

## 2. Diseño de una sola tabla (transición Sisbén III -> IV)

Evita cruzar GEIH con Sisbén. La identificación depende de que `regla_nueva`
sea exógena a las condiciones del hogar (`X -> regla_nueva` NO existe en el
grafo: el cambio de regla es nacional, no decidido por hogar) — si eso se
sostiene, el cambio de clasificación atribuible solo a `regla_nueva` (no a
`X`) aísla una fuente de variación limpia. **Bloqueador actual: no tenemos
el corte Sisbén III** — este diseño queda sin poder correrse hasta
conseguirlo. `resultado_y` sigue sin definir (no puede ser `I1`-`I15` ni
`H_5`, ver `docs/insumos/DICCIONARIO_HOTDECK.md` §7, por circularidad).

## 3. Qué sigue (según la Tabla 1 del documento)

Identificado el diseño, lo que falta para llegar a estimación:
- LASSO/Ridge/SHAP sobre el Sisbén solo (determinantes de clasificación, P1/OE1) — planeado, no implementado.
- DML y Causal Forest sobre `grupo_hotdeck -> resultado_y` con X completo (P2/OE2) — planeado; requiere primero construir `resultado_y` (IPM desde GEIH) y sumar vivienda a la celda del Hot-Deck.
- RD en frontera B/C — en duda (no hay puntaje continuo en la microdata).
- Estudio de eventos Sisbén III/IV — bloqueado por falta del corte III.
- Cotas de Fréchet-Manski — por explorar.
- Vecino más cercano (Gower) — pendiente, prueba de robustez del Hot-Deck.
"""
    (OUT_DIR / "IDENTIFICACION_CAUSAL.md").write_text(reporte, encoding="utf-8")
    print(f"\nGuardado: {OUT_DIR / 'IDENTIFICACION_CAUSAL.md'}")
    print(f"Guardado: {OUT_DIR / 'dag_diseno_principal.png'}")
    print(f"Guardado: {OUT_DIR / 'dag_diseno_principal_refinado.png'}")
    print(f"Guardado: {OUT_DIR / 'dag_una_tabla.png'}")


if __name__ == "__main__":
    main()
