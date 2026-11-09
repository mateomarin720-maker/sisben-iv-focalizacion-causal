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

5. **En cantidades:** con el mismo presupuesto, la composición del hogar identifica
   261.400 hogares pobres más (796.700 personas), y la cuenta de ahorros 41.500
   (111.600 personas). Ver [Población involucrada](#población-involucrada).
6. **Las ayudas declaradas llegan a 2,8 millones de hogares (9,4 millones de personas);**
   el 78,5 % del dinero va a los dos quintiles más pobres, y 3,4 millones de hogares pobres
   no declaran ninguna. Ver [A quién llegan las ayudas](#a-quién-llegan-las-ayudas-declaradas).

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

## Población involucrada

Las cantidades son de un **mes promedio de 2024**: el factor de expansión de cada mes
reproduce la población, así que se divide por 12. El universo es de 17,9 millones de
hogares y 51,6 millones de personas; son pobres por ingreso 4,84 millones de hogares,
donde viven 17,1 millones de personas. "Personas" cuenta a todos los miembros del hogar.

Estas cifras dicen a cuánta gente corresponde cada condición. No dicen que la variable
le cause algo a esa población.

### Cuántos hogares cambian de situación con cada modelo

Con el mismo presupuesto (43,6 % de los hogares), cada modelo saca a unos hogares pobres
de la selección y mete a otros. "Neto" son los pobres adicionales identificados. El IC
95 % es el del neto en hogares.

| Información agregada | Hogares pobres que entran | Hogares pobres que salen | **Neto hogares** [IC 95 %] | Neto personas |
|---|---|---|---|---|
| Composición del hogar (sobre la ficha) | 443.400 | 181.900 | **261.400** [245.300; 281.200] | 796.700 |
| Todos los candidatos | 162.900 | 94.900 | **67.900** [55.300; 77.900] | 194.000 |
| Inclusión financiera + estrato | 155.900 | 96.000 | **59.800** [47.600; 71.200] | 170.800 |
| Inclusión financiera | 132.200 | 84.100 | **48.100** [35.800; 57.100] | 133.000 |
| Solo cuenta de ahorros | 124.000 | 82.500 | **41.500** [29.300; 50.500] | 111.600 |
| Estrato | 91.000 | 65.700 | **25.400** [15.800; 32.700] | 74.900 |
| Campesino | 19.300 | 13.900 | 5.500 [800; 9.300] | 12.700 |
| Discapacidad | 29.800 | 25.100 | 4.700 [−1.300; 9.900] | 14.500 |
| Autoconsumo | 14.800 | 11.400 | 3.400 [−300; 6.400] | 6.200 |
| Víctimas | 21.300 | 18.100 | 3.200 [−1.700; 7.200] | 7.400 |
| Etnia | 3.700 | 4.600 | −900 [−3.700; 1.300] | −4.000 |
| Migración | 12.800 | 14.800 | −1.900 [−5.800; 2.200] | −8.300 |

El neto esconde que hay ganadores y perdedores: al agregar la cuenta de ahorros, entran
124.000 hogares pobres, pero salen 82.500. Son comparaciones entre modelos, no una
proyección de lo que lograría el Sisbén.

### A cuánta gente corresponde cada condición

En miles. La tasa es el porcentaje de hogares con la condición que son pobres.

| Condición | Hogares | Personas | Hogares pobres | Personas en hogares pobres | Tasa de pobreza |
|---|---|---|---|---|---|
| Con cuenta de ahorros | 11.316 | 32.670 | 1.800 | 6.748 | 15,9 % |
| Sin cuenta de ahorros | 6.588 | 18.881 | 3.039 | 10.359 | 46,1 % |
| Con tarjeta de crédito | 1.949 | 5.342 | 83 | 283 | 4,3 % |
| Estrato 1 | 5.915 | 18.475 | 2.471 | 9.090 | 41,8 % |
| Conexión pirata (estrato 0) | 357 | 1.168 | 195 | 741 | 54,8 % |
| Estratos 4 a 6 | 1.770 | 4.284 | 74 | 181 | 4,2 % |
| Hogar monoparental | 3.015 | 10.374 | 1.422 | 5.215 | 47,2 % |
| Algún miembro con discapacidad | 2.136 | 6.871 | 791 | 2.834 | 37,0 % |
| Alguna víctima | 3.584 | 11.823 | 1.447 | 5.524 | 40,4 % |
| Algún desplazado | 3.244 | 10.828 | 1.362 | 5.234 | 42,0 % |
| Jefe campesino | 8.153 | 23.920 | 2.707 | 9.459 | 33,2 % |
| Jefe indígena | 736 | 2.430 | 370 | 1.399 | 50,3 % |
| Jefe afrodescendiente | 1.374 | 4.130 | 511 | 1.882 | 37,2 % |
| Algún nacido en el exterior | 1.034 | 3.650 | 399 | 1.728 | 38,6 % |
| Huerta para consumo propio | 948 | 2.968 | 392 | 1.435 | 41,3 % |
| Cría de animales para consumo | 1.337 | 4.444 | 585 | 2.208 | 43,7 % |

**Por qué estas cantidades importan para decidir:**
- **La cuenta de ahorros no separa limpiamente.** 1,8 millones de hogares pobres, con 6,7
  millones de personas, sí tienen cuenta. Una regla que la penalice con fuerza los
  desfavorecería. Su aporte es como una variable más dentro de un modelo, no como filtro.
- **Discapacidad, víctimas, desplazamiento y etnia no agregan identificación, pero
  involucran a millones.** 5,2 millones de personas viven en hogares pobres con algún
  desplazado, y 2,8 millones en hogares pobres con alguna persona con discapacidad.
  Justificar criterios propios para ellas es una discusión normativa que la capacidad
  predictiva no resuelve.

## A quién llegan las ayudas declaradas

Primera medición del proyecto con participación observada, sin Hot-Deck ni simulación.
La GEIH pregunta por ayudas en dinero del gobierno (`P750S2`) y por programa (`P1661S1`-`S3`).
**Es descriptiva: no estima un efecto.** La participación tampoco permite una
discontinuidad: en Colombia Mayor sube gradualmente con la edad, sin salto (de 3,6 % a
los 65 años a 24,8 % a los 72, en hombres).

"Pobre" se mide aquí con el ingreso **sin** la ayuda declarada. En un mes promedio:

| | Alguna ayuda del gobierno | Familias en Acción | Colombia Mayor | Jóvenes en Acción |
|---|---|---|---|---|
| Personas que declaran recibirla | 3.177.400 | 883.300 | 1.415.000 | 123.700 |
| Hogares receptores | 2.763.900 | 860.900 | 1.215.100 | 117.300 |
| Personas en esos hogares | 9.372.300 | 3.633.600 | 3.372.300 | 444.700 |
| Hogares pobres receptores | 1.571.800 | 575.100 | 650.100 | 51.400 |
| Personas en hogares pobres receptores | 5.707.200 | 2.523.800 | 1.883.400 | 213.000 |
| Hogares pobres **sin** el programa | 3.430.300 | 4.427.000 | 4.352.000 | 4.950.700 |
| Personas en hogares pobres **sin** el programa | 11.860.800 | 15.044.200 | 15.684.500 | 17.355.000 |
| Hogares no pobres receptores | 1.192.200 | 285.800 | 565.000 | 65.900 |
| Personas en hogares no pobres receptores | 3.665.100 | 1.109.800 | 1.488.900 | 231.700 |
| % de receptores que son pobres | 56,9 % | 66,8 % | 53,5 % | 43,8 % |
| % de hogares pobres cubiertos | 31,4 % | 11,5 % | 13,0 % | 1,0 % |
| % de hogares no pobres cubiertos | 9,2 % | 2,2 % | 4,4 % | 0,5 % |

Una **persona** puede recibir más de un programa, y un hogar puede tener varios receptores:
por eso las filas no se suman entre columnas.

**Por quintil de ingreso sin la ayuda.** Se declaran 3,74 billones de pesos al año.

| Quintil | Hogares | Personas | Hogares con ayuda | Personas en esos hogares | % de hogares con ayuda | Miles de millones al año | % del dinero |
|---|---|---|---|---|---|---|---|
| 1 (más pobre) | 3.581.000 | 12.496.200 | 1.309.900 | 4.732.100 | 36,6 % | 1.908,6 | 51,0 % |
| 2 | 3.581.000 | 11.920.100 | 819.100 | 2.773.000 | 22,9 % | 1.028,8 | 27,5 % |
| 3 | 3.580.900 | 10.551.400 | 432.700 | 1.320.600 | 12,1 % | 506,7 | 13,5 % |
| 4 | 3.580.900 | 8.996.400 | 162.500 | 442.200 | 4,5 % | 199,4 | 5,3 % |
| 5 | 3.580.900 | 7.586.800 | 39.800 | 104.500 | 1,1 % | 99,7 | 2,7 % |

**Pobreza con y sin el dinero declarado (contabilidad).**

| | Hogares con la ayuda | Hogares sin la ayuda | Personas con la ayuda | Personas sin la ayuda | Hogares sobre la línea solo por la ayuda | Personas |
|---|---|---|---|---|---|---|
| Pobreza | 4.839.500 (27,03 %) | 5.002.100 (27,94 %) | 17.107.300 | 17.568.000 | 162.600 | 460.700 |
| Pobreza extrema | 1.855.900 (10,37 %) | 2.036.600 (11,37 %) | 6.450.000 | 7.007.500 | 180.700 | 557.500 |

La brecha de pobreza (FGT1) pasa de 12,03 % sin la ayuda a 11,19 % con ella.

**Cómo leerlo:**
- Las ayudas están bien dirigidas en promedio: el 78,5 % del dinero va a los dos quintiles
  más pobres. Aun así, 3,4 millones de hogares pobres (11,9 millones de personas) no
  declaran ninguna, y 1,2 millones de hogares no pobres sí.
- **"Pobres sin programa" no equivale a error de exclusión.** Cada programa tiene
  requisitos propios (menores en el hogar, edad), y no todo hogar pobre es elegible.
- La contabilidad supone que el hogar no cambiaría su conducta sin la ayuda. Tampoco se
  puede atribuir lo observado al Sisbén, que no se observa en la GEIH.

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
- **Ayudas declaradas:** hay subdeclaración, por eso el DANE cruza registros
  administrativos, y la cobertura real debe ser mayor. En 2024 [Familias en Acción y
  Jóvenes en Acción se transformaron](https://www.eltiempo.com/economia/finanzas-personales/renta-ciudadana-estos-son-los-cambios-en-familias-y-jovenes-en-accion-825955)
  en Renta Ciudadana y Renta Joven, así que parte de los beneficiarios pudo declararse
  en otra categoría: los totales por programa son aproximados y la columna "Alguna ayuda"
  es la más firme. No se encontró un total oficial consolidado de 2024 para contrastar.
  Una referencia parcial: [más de 122.000 jóvenes](https://www.larepublica.co/economia/prosperidad-social-comienza-el-primer-ciclo-de-pagos-para-mas-de-122-000-jovenes-3847777)
  en el primer ciclo de Renta Joven, frente a 123.700 declarados. La [Contraloría cuestionó
  en 2024](https://ambitojuridico.com/sites/default/files/2024-08/COMUNICADO-ContraloriaGeneralencontro-2024.pdf)
  la exactitud de los datos de estos programas.
- **Verificabilidad y costo:** no se evaluaron con datos. Si cada variable se puede
  comprobar en registros administrativos queda por confirmar.

## Cómo reproducirlo

```bash
poetry run python -m src.estimacion.variables_candidatas_pobreza 6             # ≈50 min, todo
poetry run python -m src.estimacion.variables_candidatas_pobreza 6 posterior   # ≈5 min, solo las revisiones
poetry run python -m src.estimacion.variables_candidatas_pobreza 6 poblacion   # ≈10 min, cantidades por variable y modelo
poetry run python -m src.estimacion.incidencia_transferencias                   # ≈1 min, ayudas declaradas
```

El argumento es el número de procesos en paralelo. La tabla de trabajo queda en
`data/2_models/variables_candidatas_hogar_2024.parquet`.
