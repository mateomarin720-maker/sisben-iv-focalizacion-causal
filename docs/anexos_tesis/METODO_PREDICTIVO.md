# Modelo base y validación de los ejercicios predictivos

Respuesta a la observación del tutor sobre la Tabla 5 (guía de correcciones,
pp. 14-16): cuál es el modelo base, cómo se separan los datos de
entrenamiento y de evaluación, y cómo se usan los factores de expansión. La
tesis tiene dos ejercicios predictivos distintos; los dos se evalúan fuera
de la muestra en la que se entrenan.

## 1. Recomendación de variables (datos reales)

`src/diagnostico/variables_candidatas_pobreza.py`. Resultado:
`docs/resultados/2_diagnostico_datos_reales/RECOMENDACION_VARIABLES_POBREZA.md`.

| Elemento | Qué se hizo |
|---|---|
| Resultado | Pobreza monetaria del hogar (GEIH 2024, 12 meses), independiente del Sisbén |
| Modelo base | `ficha_derivadas`: las variables que la GEIH y la ficha del Sisbén IV recogen en común, más las del hogar calculables con ellas (dependencia, monoparentalidad, etc.). Un candidato solo cuenta si mejora sobre este modelo |
| Modelos anidados | `canonico` (las variables del Hot-Deck) < `ficha` < `ficha_derivadas` < `+grupo` (base más un grupo nuevo) < `todo` |
| Estimador | Regresión logística (C = 1); como segundo modelo, gradient boosting |
| Partición | Validación cruzada de 5 pliegues **por vivienda** (`DIRECTORIO`): todos los hogares de una vivienda quedan en el mismo pliegue. Las métricas se calculan solo con predicciones fuera de muestra |
| Factores de expansión | Pesos del ajuste y de las métricas (`fex`) |
| Métrica principal | Error de exclusión con el mismo presupuesto que los A/B vigentes (hogares pobres no seleccionados / hogares pobres); también AUC, error de inclusión y Brier |
| Incertidumbre | IC 95 % por bootstrap bayesiano de viviendas (200 réplicas), con los mismos pesos para todos los modelos (comparación pareada) |
| Robustez | Entrenar con enero-junio y evaluar con julio-diciembre; pliegues por departamento (departamentos no vistos) |
| Criterio de decisión | Se recomienda un grupo si su prueba de Wald (errores agrupados por departamento, corrección de Holm) es significativa al 5 %, baja el error de exclusión al menos 0,5 puntos con IC sin el cero, y la mejora se mantiene en urbano, rural, meses y departamentos no vistos y en presencia de los demás grupos. Significativo pero sin mejora clara o estable: «considerar» |

Esto no es circular: el modelo se entrena con unos hogares y se evalúa con
otros, y el resultado (pobreza monetaria) no se construye con las
variables candidatas. Sí es predictivo: que una variable mejore la
predicción no dice que incorporarla al Sisbén mejore la política.

## 2. Reglas de focalización (simulación semisintética\*)

`src/focalizacion/reglas_focalizacion.py`. Resultado:
`docs/resultados/4_focalizacion/RESULTADOS_REGLAS_FOCALIZACION.md`.

| Elemento | Qué se hizo |
|---|---|
| Proxy de medios | Ridge (alpha = 1) del log-ingreso per cápita sobre variables observables del hogar, nunca el ingreso: celda del Hot-Deck, paredes, acueducto, alcantarillado, sexo del jefe, zona, personas, cuartos, analfabetismo, bajo logro educativo del jefe, inasistencia escolar, sin aseguramiento en salud, jefe sin cotización a pensión y hacinamiento |
| Partición | En cada una de las 300 repeticiones, una partición aleatoria nueva: 30.000 hogares para entrenar el proxy y el Causal Forest y otros 30.000, distintos, donde se aplican y se evalúan las reglas. El resto hace de registro para el Hot-Deck simulado |
| Referencias | Regla aleatoria (cota inferior), clasificación vigente imputada por Hot-Deck y regla ideal con el ingreso y el efecto verdaderos (cota superior, no factible) |
| Presupuesto | El mismo para todas: el número de hogares A/B vigentes en la muestra de evaluación (46,7 %), o el mismo dinero con transferencia de monto fijo |
| Factores de expansión | Métricas sobre personas: `fex` × personas de la unidad de gasto |
| Incertidumbre | Error estándar Monte Carlo de cada métrica bajo un umbral fijo (repeticiones hasta la convergencia) |

El proxy predice el ingreso y se califica con la pobreza, que se define con
ese mismo ingreso. No es circular en el sentido de evaluar con los datos
de entrenamiento: se evalúa en hogares que el modelo no vio. Pero sí mide
solo cuánto se parece la regla a ordenar por ingreso; por eso la regla
ideal y la reducción de la brecha (FGT1) se reportan juntas, y el
resultado no dice nada de la regla real del Sisbén, que usa datos que la
GEIH no tiene. La regla "vigente" es la clasificación imputada por celda,
no la del Sisbén: su error mezcla el error del Sisbén con el ruido del
Hot-Deck.

\* Resultado simulado.
