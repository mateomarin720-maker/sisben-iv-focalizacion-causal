# Identificación causal — diseño principal y diseño de una sola tabla

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
| Literal (Fig. 2) | Solo X | **False** |
| Literal (Fig. 2) | X + elegibilidad_real | True |
| Refinado | Solo X | **True** |
| Refinado | X + ambas elegibilidades | True |

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
Solo X = True) — el camino problemático desaparece porque ya
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
