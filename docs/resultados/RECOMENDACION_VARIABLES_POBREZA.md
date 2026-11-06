# Recomendación de variables para ampliar la medición de pobreza

Generado 2026-11-06 por `src/estimacion/variables_candidatas_pobreza.py`.
Salidas en `docs/reports/variables_candidatas*`.

## Qué pregunta responde

¿Qué variables del hogar, que hoy no aparecen en el diccionario del Sisbén IV,
se asocian con la pobreza más allá de lo que el Sisbén ya recoge, y ayudan a
identificar mejor a los hogares pobres?

Es una **pregunta abierta con una recomendación, no una conclusión causal**. Una
variable que predice pobreza no la causa, y aquí no se evalúa qué pasaría al
incorporarla a la política. Los resultados son con datos reales de la GEIH 2024:
no usan el Hot-Deck ni la simulación.

## Resultado en breve

1. **Lo que más mejora la identificación no es una variable nueva.** Calcular
   la composición del hogar con lo que el Sisbén ya recoge (dependencia,
   monoparentalidad, ocupados, educación superior de los adultos) reduce el error
   de exclusión en 5,40 puntos. Todas las variables nuevas juntas lo reducen en
   1,40. No sabemos si la fórmula del DNP ya los usa.
2. **Tener cuenta de ahorros es la única variable nueva con un aporte claro:**
   −0,86 puntos por sí sola. Cumple el criterio dentro del grupo de inclusión
   financiera (−0,99), estable en todas las pruebas. Los productos de crédito
   aportan poco (−0,16).
3. **El estrato cumple el criterio por poco** (−0,52 frente al mínimo de −0,50) y
   baja en varias pruebas de robustez. Es una recomendación débil.
4. **Discapacidad, desplazamiento, migración, etnia y condición campesina casi no
   mejoran la identificación.** Eso no significa que esos hogares no sean más
   pobres: en bruto lo son, pero lo que el Sisbén ya recoge captura la diferencia.

## Cómo se evaluó

**Datos.** 290.968 hogares de la GEIH 2024, ponderados con `fex` (≈17,9 millones
de hogares, ≈4,84 millones pobres por ingreso). El resultado principal es
`POBRE_MONETARIO`. Se contrastó con la pobreza extrema, con la clasificación
oficial del DANE (24 departamentos) y con el IPM-GEIH.

**Modelos anidados.** Cada uno agrega información al anterior:

| Modelo | Contenido |
|---|---|
| `canonico` | Las 10 variables del esquema canónico del Hot-Deck |
| `ficha` | Todo lo que recogen en común la GEIH y la ficha del Sisbén IV: vivienda, servicios, sanitario, agua, cocina, combustible, tenencia, y educación, ocupación y estado civil del jefe |
| `ficha_derivadas` | **La referencia:** lo anterior más variables calculables con los datos que el Sisbén ya tiene |
| `+grupo` | La referencia más un grupo de variables que no están en el diccionario del Sisbén |

**Candidatas (8 grupos).** Inclusión financiera (`P5222`), estrato (`P4030S1A1`),
discapacidad (`P1906`), autorreconocimiento étnico (`P6080`) y campesino (`P2057`,
`P2061`), migración (`P3373`, `P3374`, `P3382`, `P3384`), víctimas y desplazamiento
(base `Victimas_MPMD` del DANE) y autoconsumo (`P3092`, `P3094`, `P3095`).

**Fuera por diseño.** Las variables en dinero (arriendo, valor de la vivienda,
cuota, ingresos, subsidios), que entran en el ingreso o lo miden, e `I1`-`I15` y
`H_5` del Sisbén (circularidad). Para predecir el IPM-GEIH se quitan de la
referencia sus componentes; si no, el modelo reconstruiría la fórmula.

**Medidas.** Las predicciones son siempre fuera de muestra (5 pliegues por vivienda):
- **Error de exclusión:** pobres que quedan fuera al elegir el 43,6 % de hogares
  con mayor predicción. Ese presupuesto es el peso de los grupos A y B, igual para
  todos los modelos.
- **Área bajo la curva (AUC):** capacidad de ordenar pobres por encima de no pobres.
- **Significancia:** logit con errores agrupados por departamento y corrección de
  Holm, porque con 290.000 hogares casi todo resulta significativo.

### Criterio de decisión, fijado antes de ver los resultados

| Decisión | Condición |
|---|---|
| **Recomendar** | Wald conjunta significativa con Holm; reduce la exclusión al menos 0,5 puntos con IC que excluye el cero, y sigue reduciéndola con meses y departamentos no vistos, en zona urbana y rural, y con los demás grupos presentes |
| **Considerar** | Significativa y con IC sin el cero en exclusión o AUC, pero pequeña o inestable |
| **No recomendar** | El resto |

## Resultados

### Lo que ya se recoge pesa más que lo nuevo

| Modelo | Exclusión (logística) | AUC (logística) | Exclusión (boosting) | AUC (boosting) |
|---|---|---|---|---|
| `canonico` | 26,39 % | 0,775 | 24,10 % | 0,794 |
| `ficha` | 18,09 % | 0,847 | 14,53 % | 0,873 |
| `ficha_derivadas` | 12,69 % | 0,891 | 10,42 % | 0,907 |
| Referencia + todos los candidatos | 11,29 % | 0,900 | 9,32 % | 0,914 |

Las derivadas mejoran 5,40 puntos [5,07; 5,81] sobre la ficha; todos los candidatos
juntos, 1,40 [1,14; 1,61] sobre la referencia.

Esta comparación favorece en parte a la composición del hogar: la pobreza se mide
con ingreso **per cápita**, así que el número de menores entra de forma casi
mecánica, y la tasa de ocupados está cerca del ingreso. Aun así, son datos ya
recogidos, sin costo de encuesta.

### Decisión por grupo

Diferencias en puntos porcentuales de error de exclusión frente a la referencia
(negativo es mejor), con IC 95 %. Regresión logística, `POBRE_MONETARIO`.

| Grupo | Exclusión [IC 95 %] | Meses no vistos | Deptos. no vistos | Urbano / rural | Con los demás | Holm (Wald) | Decisión |
|---|---|---|---|---|---|---|---|
| Inclusión financiera | **−0,99** [−1,18; −0,74] | −0,91 | −1,18 | −1,07 / −0,80 | −0,85 | <0,001 | **Recomendar** |
| Estrato | **−0,52** [−0,68; −0,33] | −0,26 | −0,66 | −0,52 / −0,55 | −0,28 | <0,001 | **Recomendar** (débil) |
| Discapacidad | −0,10 [−0,20; +0,03] | −0,10 | −0,01 | −0,05 / −0,22 | −0,09 | <0,001 | Considerar |
| Autoconsumo | −0,07 [−0,13; +0,01] | −0,04 | −0,03 | −0,05 / −0,13 | −0,08 | 0,003 | Considerar |
| Víctimas | −0,07 [−0,15; +0,04] | −0,03 | −0,10 | −0,14 / +0,12 | −0,05 | 0,005 | Considerar |
| Campesino | −0,11 [−0,19; −0,02] | −0,16 | −0,05 | −0,13 / −0,06 | −0,03 | 1,00 | No recomendar |
| Migración | +0,04 [−0,05; +0,12] | −0,08 | +0,04 | 0,00 / +0,14 | −0,02 | <0,001 | No recomendar |
| Etnia | +0,02 [−0,03; +0,08] | +0,01 | 0,00 | 0,00 / +0,07 | 0,00 | 1,00 | No recomendar |

Con el presupuesto fijo, −0,99 puntos equivalen a unos 48.000 hogares pobres más
identificados, de 4,84 millones. Es una comparación entre modelos, no una
proyección de lo que lograría el Sisbén.

**El estrato es la decisión más frágil.** Pasa el umbral por dos centésimas, su IC
incluye valores por debajo de 0,5, y baja a −0,39 con boosting, −0,26 con meses no
vistos y −0,28 con los demás grupos presentes. Cumple el criterio y por eso queda
recomendado, pero con menos respaldo que la cuenta.

### Por otros resultados

Exclusión frente a la referencia, en puntos.

| Grupo | Monetaria | Boosting | Oficial DANE | Extrema | IPM-GEIH |
|---|---|---|---|---|---|
| Inclusión financiera | −0,99 | −0,97 | −1,02 | −0,35 | −0,80 |
| Estrato | −0,52 | −0,39 | −0,56 | −0,14 (el IC incluye el cero) | −0,61 |
| Migración | +0,04 | −0,08 | +0,04 | 0,00 | **−0,31** [−0,45; −0,16] |
| Campesino | −0,11 | −0,14 | +0,02 | 0,00 | **−0,23** [−0,36; −0,10] |
| Discapacidad | −0,10 | −0,13 | −0,07 | −0,13 | −0,06 |
| Víctimas | −0,07 | −0,18 | −0,02 | −0,02 | −0,07 |

Inclusión financiera es consistente en todos. Migración y condición campesina solo
aportan en el IPM-GEIH, donde se quitaron de la referencia componentes como el
aseguramiento en salud y la cotización a pensión. Una explicación posible, no
comprobada, es que estén actuando como sustitutos de esos componentes.

### Por variable

Cambio medio en la probabilidad de ser pobre con todo lo demás en el modelo, frente
a las tasas en bruto. Pobreza monetaria.

| Variable | % de hogares | Tasa de pobreza con / sin | Cambio ajustado (puntos) | p (Holm) |
|---|---|---|---|---|
| Cuenta de ahorros | 63,2 | 15,9 / 46,1 | −9,1 | <0,001 |
| Tarjeta de crédito | 10,9 | 4,3 / 29,8 | −5,2 | <0,001 |
| Cuenta corriente o CDT | 1,8 | 6,5 / 27,4 | −6,2 | 0,03 |
| Estrato 1 (frente a 2) | 33,0 | 41,8 / 19,8 | +4,2 | <0,001 |
| Estrato 3 (frente a 2) | 19,5 | 12,2 / 30,6 | −4,9 | <0,001 |
| Estrato 4 (frente a 2) | 6,3 | 4,6 / 28,5 | −9,6 | <0,001 |
| Algún miembro con discapacidad | 11,9 | 37,0 / 25,7 | +3,4 | <0,001 |
| Huerta para consumo propio | 5,3 | 41,3 / 26,2 | +2,9 | 0,02 |
| Algún desplazado | 18,1 | 42,0 / 23,7 | +2,1 | 0,06 |
| Algún nacido en el exterior | 5,8 | 38,6 / 26,3 | +1,9 | 0,001 |
| Jefe indígena | 4,1 | 50,3 / 26,0 | −0,1 | 1,00 |
| Jefe afrodescendiente | 7,7 | 37,2 / 26,2 | −0,6 | 1,00 |
| Jefe campesino | 45,5 | 33,2 / 21,9 | −0,2 | 1,00 |

Las brechas en bruto de jefes indígenas, afrodescendientes y campesinos desaparecen
al considerar lo que el Sisbén ya recoge. Eso dice que no agregan capacidad de
ordenar hogares, **no** que la brecha no exista.

Discapacidad muestra la diferencia entre significancia y utilidad: la asociación es
clara en los cuatro resultados (Holm <0,04), pero casi no cambia a quién se identifica.

### LASSO, Ridge y SHAP

Coinciden con la decisión. En SHAP, `fin_ahorros` es la tercera variable de 63 y el
estrato la sexta; la primera candidata de otro grupo es
`hog_desplazado`, en el puesto 23.

Con el C elegido por validación (0,1, el borde superior de la rejilla) el LASSO casi
no elimina nada, así que no discrimina. Con penalización más fuerte sí:

| C | Candidatas que se conservan en las 30 mitades de la muestra |
|---|---|
| 0,001 | `fin_ahorros` y `estrato` (de 18 variables seleccionadas en todas) |
| 0,0001 | Solo `fin_ahorros` (de 7) |

## Revisiones hechas después de ver los resultados

Estas tres revisiones no formaban parte del criterio y no cambian la decisión.

**1. ¿De dónde viene el aporte financiero?** De tener o no la cuenta.

| Modelo | Exclusión [IC 95 %] | Meses no vistos | Urbano / rural |
|---|---|---|---|
| Referencia + cuenta de ahorros o ninguno | −0,86 [−1,04; −0,61] | −0,85 | −0,89 / −0,79 |
| Referencia + productos de crédito y CDT | −0,16 [−0,28; −0,03] | −0,19 | −0,25 / +0,07 |
| Referencia + crédito + estrato | −0,63 [−0,83; −0,44] | −0,43 | −0,72 / −0,39 |
| Referencia + inclusión financiera + estrato | −1,24 [−1,47; −0,98] | −1,03 | −1,36 / −0,92 |

**2. ¿La cuenta es consecuencia de las transferencias?** Era la objeción más seria:
si los subsidios se pagan por cuenta, tenerla marcaría a los ya focalizados. Los datos
declarados no la respaldan: quienes reciben ayudas tienen *menos* cuenta.

| Población | Hogares con ayuda del gobierno | Con cuenta, con ayuda | Con cuenta, sin ayuda |
|---|---|---|---|
| Todos | 15,4 % | 34,7 % | 68,4 % |
| Pobres | 29,1 % | 26,7 % | 41,5 % |
| No pobres | 10,4 % | 43,0 % | 76,3 % |

Ajustado por la referencia, recibir ayuda se asocia con 6,5 puntos menos de cuenta.
Esto no cierra el tema: es un corte transversal, la ayuda es declarada, y no se sabe si
los encuestados cuentan las billeteras digitales como cuenta de ahorros.

**3. LASSO con penalización fuerte,** en la tabla anterior.

## Recomendación

Se presenta como pregunta abierta para quien diseñe el instrumento. Los datos
sustentan la asociación y la capacidad de identificar; no sustentan efectos de la
política.

| Prioridad | Propuesta | Respaldo con datos | Qué falta resolver |
|---|---|---|---|
| 1 | Revisar si la fórmula aprovecha la composición del hogar: dependencia, monoparentalidad, tasa de ocupados, educación superior de algún adulto | Fuerte (−5,40), con la salvedad del ingreso per cápita | Confirmar con el DNP si ya las usa. No requiere recoger nada nuevo |
| 2 | Evaluar la tenencia de cuenta de ahorros | Clara y estable (−0,86) | Se puede ocultar si reduce la probabilidad de recibir ayudas, y penalizarla puede ir contra la inclusión financiera. Conviene una fuente verificable, no solo declarada |
| 3 | Considerar el estrato | Débil (−0,52, inestable) | Se asigna a la vivienda, no al hogar, y falta en quienes tienen conexión pirata o no lo saben |
| — | No incorporar por focalización: etnia, condición campesina, migración | Sin aporte a la identificación | Pueden importar por otras razones |
| — | Discapacidad, desplazamiento y autoconsumo: asociación clara, aporte mínimo | Identifican poco | Pueden justificar criterios propios en un programa: por ejemplo, la pobreza monetaria no mide los gastos adicionales por discapacidad. Eso es una decisión normativa, no un resultado de este análisis |

## Limitaciones

- **La referencia no es la fórmula del Sisbén,** que no está disponible. Es un modelo
  con las mismas preguntas.
- **La GEIH no trae nevera, lavadora, internet ni varias preguntas de salud** que el
  Sisbén sí recoge. La referencia queda por debajo de la ficha real, y el aporte de la
  cuenta y del estrato **puede estar sobreestimado**, porque en parte podrían reflejar
  esos bienes. Con las fuentes disponibles no se puede medir; es la limitación más
  importante.
- **Predice, no explica.** Ninguna cifra indica qué pasaría con la pobreza de un hogar
  al cambiar la variable, ni cómo responderían los hogares si la variable se usara
  para asignar ayudas.
- **El resultado tiene error de medición:** la pobreza monetaria es una reconstrucción
  con ingreso declarado (1,4 puntos sobre la oficial), aunque la clasificación oficial
  da lo mismo.
- **Población:** son los hogares de la GEIH, no los registrados en el Sisbén.
- **Incertidumbre subestimada.** Los IC remuestrean viviendas en la evaluación; no
  incluyen el ajuste del modelo ni el diseño muestral (los microdatos no traen la unidad
  primaria de muestreo). La agrupación por departamento en las pruebas Wald es una
  aproximación, con 33 grupos.
- **Umbral de 0,5 puntos:** es una elección nuestra, no un estándar.
- **Víctimas:** la marca viene del DANE (base `Victimas_MPMD`, catálogo 874 de microdatos, el mismo de la pobreza monetaria;
  ver `data/catalogo.yaml`). No es el Registro Único de Víctimas. Solo trae a las personas marcadas, así que
  quien no aparece se toma como no víctima.
- **Verificabilidad y costo:** no se evaluaron con datos. Si cada variable se puede
  comprobar en registros administrativos queda por confirmar.

## Cómo reproducirlo

```bash
poetry run python -m src.estimacion.variables_candidatas_pobreza 6             # ≈50 min, todo
poetry run python -m src.estimacion.variables_candidatas_pobreza 6 posterior   # ≈5 min, solo las revisiones
```

El argumento es el número de procesos en paralelo. La tabla de trabajo queda en
`data/2_models/variables_candidatas_hogar_2024.parquet`.
