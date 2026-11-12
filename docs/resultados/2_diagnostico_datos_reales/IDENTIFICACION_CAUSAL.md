# Identificación causal: los DAG del proyecto

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
| ¿El grupo del Hot-Deck es independiente de Y? | X | **No** |
| | X y la elegibilidad | Sí |

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
| ¿El grupo del Hot-Deck es independiente de Y? | X (celda) | **Sí** |
| | Nada | No |
| ¿Se identifica el efecto de la elegibilidad del propio hogar? | X y Z | No |

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
| ¿T es independiente del registro, dado X y Z? | El registro depende de U | **No** |
| | El registro no depende de U | Sí |

Las cotas del efecto (`RESULTADOS_FRECHET_MANSKI.md`) y los errores de
focalización (`RESULTADOS_ERRORES_FOCALIZACION_FRECHET.md`) toman la
proporción de A/B de los registrados como la de toda la celda. El grafo
dice cuándo vale: solo si lo que lleva a un hogar a registrarse no está
relacionado con su elegibilidad más allá de X y Z. La cobertura del
registro varía 5,6 veces entre los departamentos del archivo nacional
(`RESULTADOS_REPRESENTATIVIDAD_SISBEN.md`), así que es un supuesto que se
declara, no que se verifica.

## 4. Generador de la simulación semisintética

Hogares reales de la GEIH (X, Z, U e Y0 reales) y una asignación
simulada: score = logit P_Sisbén(T | celda) + Z·b + gamma·U, por sorteo o
por corte del puntaje; Y = Y0 + tau(Z)·T (`src/simulacion/`).

| Pregunta | Escenario | Respuesta |
|---|---|---|
| ¿Ajustar por X y Z identifica el efecto de T? | gamma = 0 (confusión observada) | **Sí** |
| | gamma > 0 (confusión no observada) | **No** |
| ¿El T del Hot-Deck es independiente de Y, dado X? | Cualquiera | Sí |

Es la estructura que la simulación pone a prueba
(`SIMULACION_SEMISINTETICA.md`): con confusión observada, regresión, DML
y Causal Forest recuperan el efecto; con confusión no observada, ninguno;
con el T del Hot-Deck, todos dan ≈0\*, como dice la última fila.

\* Resultado simulado.

## 5. Diseño de una sola tabla (Sisbén III a IV)

| Pregunta | Respuesta |
|---|---|
| ¿La regla nueva es independiente de las condiciones del hogar? | Sí |

Si la regla del Sisbén IV es nacional (no se decide hogar por hogar), el
cambio de clasificación que produce aísla una variación limpia. Requiere
los dos cortes del Sisbén para los mismos hogares; con los datos del
proyecto (solo el Sisbén IV) no se ejecuta. El resultado no puede ser una
privación calculada por el propio Sisbén (`I1`-`I15`, `H_5`).
