# Metodología: imputación fraccional (FHDI) sobre la celda del Hot-Deck

Documento de referencia para llevar la FHDI a la tesis: reglas,
fórmulas, decisiones tomadas y su porqué, resultados hasta la fecha y
qué falta. Código en `src/emparejamiento/fhdi/` (reglas resumidas en su
`README.md`); resultados en
[`RESULTADOS_FHDI.md`](../resultados/1_datos_y_enlace/RESULTADOS_FHDI.md).
Iniciado el 2026-11-18.

## 1. Motivación

El Hot-Deck le asigna a cada hogar de la GEIH el grupo del Sisbén de **un**
donante sorteado en su celda. Eso tiene dos costos ya medidos en el
proyecto:

- **Ruido de la imputación.** Entre el 47 % y el 53 % de la varianza de un
  contraste viene del sorteo; hay que repetirlo 100 veces y combinar con
  las reglas de Rubin (`RESULTADOS_VARIABILIDAD_HOTDECK.md`).
- **Atenuación con vínculo parcial.** El sorteo mete en el tratamiento una
  variación que no tiene relación con el resultado, y el estimador cae a
  L·τ (Proposición 2).

La imputación fraccional (*fractional hot-deck imputation*, Kim y Fuller,
2004) reemplaza el donante único por varios donantes con peso fraccional.
La pregunta de este módulo es qué cambia con eso **sin cambiar la celda**.

## 2. Notación

- i: hogar de la GEIH (receptor); j: hogar del Sisbén (donante).
- C_i: celda del hogar i (departamento, ciclo de vida del jefe, tramo de
  cuartos, nivel de pisos, personas 1-2 / 3+, menores 0 / 1 / 2+), en el
  primer nivel de la cadena de respaldos con donantes.
- G_j ∈ {A, B, C, D}: grupo del Sisbén del donante; T = 1[G ∈ {A, B}].
- π_g(c) = proporción de donantes de la celda c en el grupo g.
- M = 10: donantes por hogar.

## 3. Reglas

**R1. Celda y cadena de respaldos: las del Hot-Deck, sin cambios.** Se
importan de `emparejamiento_hotdeck_geih_sisben.claves_por_nivel`: celda
exacta → sin menores → sin personas → sin pisos → departamento y edad →
departamento → todo el registro. 99,92 % de los hogares en la celda
exacta.

**R2. Donantes: M = 10, sin reemplazo y estratificados por grupo.** En la
celda de cada hogar se sortea al menos un donante de cada grupo presente y
el resto según la proporción del grupo, por mayores restos:

    cupo_g = 1[π_g > 0] + reparto de (M − nº de grupos presentes) según π_g

sin pasar de los donantes que tiene el grupo en la celda (si tiene menos,
entran todos).

**R3. Pesos calibrados a la celda.** Para el donante j del hogar i, con
n_g(i) donantes del grupo g entre los sorteados:

    w_ij = π_{G_j}(C_i) / n_{G_j}(i),   Σ_j w_ij = 1

Así la distribución por grupo ponderada de los donantes de cada hogar es
exactamente la de su celda: Σ_j w_ij · 1[G_j = g] = π_g(C_i).

**R4. FEFI** (*fully efficient fractional imputation*): todos los
donantes de la celda, que equivale a asignarle a cada hogar π(C_i). Por
R3, toda cantidad que dependa del grupo da lo mismo con FHDI (M = 10) que
con FEFI.

**R5. Lo que se guarda.** Por hogar, la probabilidad de cada grupo y de
A/B (`data/2_models/geih_sisben_fhdi_2024.parquet`, también en Azure). La
base expandida de 10 donantes por hogar no se guarda: por R4 no agrega
información, y se reconstruye con la semilla 42.

**R6. Varianza.** Jackknife de grupos eliminados sobre los hogares de la
GEIH (100 grupos al azar). Para una razón R = Σ w·a / Σ w·b:

    v(R) = (G − 1)/G · Σ_g (R_(g) − R̄)²

Mide la variación muestral de la GEIH. No incluye la del lado de los
donantes (el Sisbén es un registro de 3,1 millones de hogares) ni ruido
de imputación, que R3 elimina.

## 4. Decisiones y su porqué

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Misma celda del Hot-Deck | Celda nueva o colapso de celdas del paquete FHDI | La celda está validada (homologación, placebo, catálogo de variables); cambiarla obligaría a regenerar toda la secuencia y la comparación con el Hot-Deck dejaría de ser limpia |
| Sorteo estratificado por grupo | Sorteo simple de 10 donantes | Con el sorteo simple, en el 37 % de los hogares (datos de prueba) algún grupo poco frecuente no salía y la calibración no era exacta |
| M = 10 | M mayor | Con la calibración, M no cambia ninguna cantidad que dependa del grupo; 10 deja la base expandida en 2,9 millones de filas |
| Guardar la probabilidad, no la base expandida | Guardar los 2,9 millones de filas | Por R4 dan lo mismo; la probabilidad es lo que leen los módulos |
| Sin variante de vecinos dentro de la celda (ordenar donantes por zona, paredes, sexo) | Usarla como método | Esas variables suben el techo del enlace entre 0,1 y 0,3 pp y ya están descartadas con placebo |
| Jackknife sobre la GEIH | Bootstrap de donantes | El Sisbén es casi un censo de la población registrada; la varianza está en la muestra de la GEIH |
| El Hot-Deck sigue siendo el enlace principal | Reemplazarlo por la FHDI | Los resultados descriptivos coinciden; la FHDI entra como módulo adicional y comprobación de robustez |

## 5. Propiedades

**P1. No hace más exacto el enlace hogar por hogar.** Sin llave común, la
única información sobre el grupo de un hogar de la GEIH es su celda. El
techo de acierto de cualquier método que la use es la moda de la celda:
80,5 % en A/B y 55,2 % en el grupo (validación dentro del Sisbén; 78,4 %
ponderado por la GEIH), frente a 73,0 % y 44,0 % del sorteo. La moda
distorsiona las incidencias (13,5 pp por departamento); la FHDI no acierta
más por hogar pero está calibrada.

**P2. Quita el ruido de la imputación.** Las cantidades que dependen del
grupo (incidencias, errores de exclusión e inclusión) son las de la media
de infinitos sorteos, en una corrida.

**P3. Contraste con efectos fijos de celda = 0 exacto** con el grupo
imputado (la Proposición 1 sin ruido): todos los hogares de una celda
tienen la misma probabilidad de A/B.

**P4. Los errores de focalización de FEFI son el punto con independencia
dentro de la celda** de las cotas de Fréchet
(`errores_focalizacion_frechet.py`): no estrecha las cotas.

**P5. Con vínculo parcial no atenúa el efecto** (resultado preliminar*,
pendiente de la fase 2). Si una fracción L de hogares tiene vínculo exacto
y al resto se le imputa π(C_i), los imputados no varían dentro de la
celda y no diluyen el contraste: la regresión con efectos fijos de celda
recupera τ con la información de los vinculados, con la varianza de una
muestra de tamaño L·n. Con el sorteo, el estimador cae a L·τ. Es la
diferencia entre un error de medición clásico (atenúa) y uno de Berkson
(no atenúa). Monte Carlo rápido* (regresión con efectos fijos, τ = 0,095,
30.000 hogares, 60 repeticiones):

| L | Sorteo | L·τ | FHDI |
|---|---|---|---|
| 0 | +0,001* | 0 | no identificable |
| 0,25 | +0,024* | +0,024 | +0,096* (sd 0,012) |
| 0,50 | +0,048* | +0,048 | +0,096* (sd 0,009) |
| 0,75 | +0,071* | +0,071 | +0,095* (sd 0,007) |
| 1 | +0,095* | +0,095 | +0,095* |

Límites: con L = 0 (el caso de la tesis) no se identifica; la FHDI no
agrega información frente a usar solo los vinculados; supone que los
vinculados se parecen a los demás dentro de su celda. La tabla anterior
viene de un script provisional; la comprobación con los hogares reales del
módulo de simulación es la de abajo.

**Comprobación con el módulo de simulación (fase 2a, 2026-11-18).**
`sensibilidad_semisintetica.py vinculo`: hogares reales de la GEIH,
encuestas de 30.000 hogares (≈8 por celda), 288 repeticiones, MCSE del
sesgo ≤ 0,003. Confusión observada, τ = 0,095*:

| L | Regresión, Hot-Deck | Regresión, FHDI | L·τ | LinearDML, Hot-Deck | LinearDML, FHDI |
|---|---|---|---|---|---|
| 0 | +0,000* | no identificable | 0 | −0,036* | no identificable |
| 0,25 | +0,023* | **+0,092*** | +0,024 | −0,012* | −0,071* |
| 0,50 | +0,046* | **+0,093*** | +0,047 | +0,014* | +0,005* |
| 0,75 | +0,069* | **+0,093*** | +0,071 | +0,036* | +0,034* |
| 1 | +0,092* | +0,092* | +0,095 | +0,061* | +0,061* |

Con efecto nulo, la regresión con FHDI da entre −0,003* y −0,005*
(cobertura 0,96-0,97) y LinearDML con FHDI −0,161*, −0,089* y −0,062* en
L = 0,25; 0,5; 0,75 (con Hot-Deck, −0,036* en todos los L). Cobertura de la
regresión con FHDI: 0,95-0,98; su desviación entre repeticiones es mayor
cuanto menor es L (0,046* con L = 0,25 frente a 0,023* con Hot-Deck),
porque solo informan los vinculados.

**P5 se confirma para la regresión con efectos fijos:** con FHDI recupera τ
(97-98 %) en todo L > 0; con Hot-Deck, L·τ.

**P6. LinearDML con FHDI empeora** (resultado no esperado). Con L = 0,25
el sesgo con efecto nulo es −0,161*, cuatro veces el de Hot-Deck. Hipótesis
(pendiente de comprobar): la parte imputada solo varía entre celdas, y la
regularización de los modelos auxiliares de LinearDML (Ridge alpha = 1
sobre ≈8 hogares por celda) no quita del todo los efectos de celda; todo
lo que queda de la diferencia entre celdas pasa al efecto. Con Hot-Deck la
parte imputada varía dentro de la celda (ruido) y diluye el sesgo en vez
de concentrarlo. Es el mismo mecanismo del sesgo de LinearDML con celdas
pequeñas (CLAUDE.md), amplificado.

**Diagnóstico de P6 (pregunta 6 de `sensibilidad_semisintetica.py`,
2026-11-18, 96 repeticiones, MCSE ≤ 0,006).** Sesgo con efecto nulo y
L = 0,25:

| Hogares por celda | LinearDML, FHDI | LinearDML sin regularizar, FHDI | LinearDML, Hot-Deck | Regresión, FHDI |
|---|---|---|---|---|
| ≈8 (30.000 hogares) | −0,161* | −0,105* | −0,038* | +0,004* |
| ≈16 (60.000) | −0,091* | −0,052* | −0,017* | +0,001* |
| ≈32 (120.000) | −0,047* | −0,025* | −0,011* | +0,002* |

- **Es sobre todo el tamaño de las celdas:** el sesgo de LinearDML con
  FHDI se reduce a la mitad cada vez que se duplican los hogares por celda,
  con y sin regularizar.
- **La regularización suma alrededor de un tercio:** sin regularizar el
  sesgo baja de −0,161* a −0,105*, pero no desaparece. El ajuste cruzado
  estima los efectos de celda en otras particiones, con pocos hogares, y
  lo que queda sin quitar pasa al efecto.
- **Crece como 1/L:** con 30.000 hogares el sesgo por L es casi constante
  (−0,161 × 0,25 = −0,040; −0,089 × 0,5 = −0,044; −0,062 × 0,75 = −0,047).
  La fuga de efectos de celda viene de la parte imputada y se divide por
  la variación de T dentro de la celda, que solo aportan los vinculados
  (proporcional a L). Con Hot-Deck no depende de L.
- **La regresión con efectos fijos exactos no se sesga** con ninguna
  imputación ni tamaño: quita la celda completa, sin estimarla.
- **Con los datos reales** (78 hogares por celda en promedio, unas 10 veces
  las encuestas de 30.000) el sesgo extrapolado de LinearDML con FHDI y
  L = 0,25 sería del orden de −0,016 (−0,010 sin regularizar).

Consecuencia para la fase 2b: con FHDI, LinearDML necesita quitar la celda
exactamente (no estimarla en el ajuste cruzado) o celdas grandes. Opción a
evaluar: transformación dentro de la celda (restar la media de la celda a
Y y a T) antes de LinearDML, que hace con el DML lo que la regresión con
efectos fijos hace con MCO.

**P7. LinearDML dentro de la celda quita el sesgo** (pregunta 7 de
`sensibilidad_semisintetica.py`, `linear_dml_intra_celda`, 2026-11-19).

Regla: antes de LinearDML se resta la media de la celda a Y, a T y a los
controles de `diseno_x`; la celda ya no entra a los modelos auxiliares
(está quitada); T transformado es continuo (Ridge para Y y para T, con la
regularización vigente); los modificadores del efecto X no se
transforman; el IC se multiplica por √(n / (n − celdas)), la corrección
de grados de libertad de la regresión con efectos fijos. Es el estimador
de Robinson con efectos fijos de celda: la celda se quita sin estimarla,
y el DML queda para la parte de X.

Encuestas de 30.000 hogares (≈8 por celda), 264 repeticiones, MCSE del
sesgo ≤ 0,003. Confusión observada, τ = 0,095*:

| L | Imputación | Regresión con efectos fijos | LinearDML vigente | LinearDML dentro de la celda | L·τ |
|---|---|---|---|---|---|
| 0 | Hot-Deck | +0,001* | −0,034* | +0,001* | 0 |
| 0,25 | Hot-Deck | +0,024* | −0,011* | +0,024* | +0,024 |
| 0,50 | Hot-Deck | +0,046* | +0,013* | +0,047* | +0,047 |
| 0,75 | Hot-Deck | +0,069* | +0,037* | +0,070* | +0,071 |
| 0,25 | FHDI | +0,093* | −0,067* | **+0,094*** | |
| 0,50 | FHDI | +0,093* | +0,007* | **+0,094*** | |
| 0,75 | FHDI | +0,091* | +0,034* | **+0,092*** | |
| 1 | (vínculo exacto) | +0,092* | +0,060* | **+0,094*** | +0,095 |

Con efecto nulo, LinearDML dentro de la celda da entre −0,003* y +0,001*
en todos los L y las dos imputaciones (la regresión, lo mismo); el
vigente, −0,035* a −0,037* con Hot-Deck y −0,160*, −0,088*, −0,063* con
FHDI y L = 0,25; 0,5; 0,75. Cobertura del IC 95 %: 0,93-0,96 dentro de la
celda (como la regresión) frente a 0,06-0,67 del vigente. Con Hot-Deck y
L < 1 la cobertura de τ es baja en los tres estimadores porque estiman
L·τ, no τ (la Proposición 2).

Lectura:

- **El sesgo de LinearDML era de estimar la celda, no del DML:** quitada
  exactamente, LinearDML coincide con la regresión con efectos fijos
  (diferencias ≤ 0,0015) con las dos imputaciones y en todo L.
- **Con FHDI recupera τ en todo L > 0** (P5 se cumple también para el
  DML); con Hot-Deck da L·τ (la Proposición 2 no cambia).
- **También corrige el sesgo vigente sin imputación:** con el vínculo
  exacto (L = 1) el LinearDML vigente da +0,060* (−0,035* con efecto
  nulo), el sesgo por celdas pequeñas de CLAUDE.md; dentro de la celda,
  +0,094* (−0,002*). Por eso adoptarlo **movería las filas de LinearDML
  de la Tabla 6** (simulación principal), no solo las de la FHDI. No se
  ha cambiado: `linear_dml`, `estimadores.dml` y la simulación principal
  siguen como estaban; la decisión es de la fase 2b.
- **Límites:** no cubre el Causal Forest (su sesgo con celdas pequeñas
  queda por medir con la misma transformación); con datos reales (78
  hogares por celda) la diferencia esperada es pequeña (≈0,016 según P6).

## 6. Plan e implementación

| Fase | Qué | Estado |
|---|---|---|
| 0 | Reglas, validación del enlace y comparación con el Hot-Deck (`reglas.py`, `validacion.py`, `__main__.py`) | Hecho el 2026-11-18 |
| 1 | Enlace fraccional por hogar guardado y publicado en Azure (`enlace.py` → `geih_sisben_fhdi_2024.parquet`) | Hecho el 2026-11-18 |
| 2a | Sensibilidad del vínculo parcial con las dos imputaciones (pregunta 5 de `sensibilidad_semisintetica.py`): L = 0; 0,25; 0,5; 0,75; 1, Hot-Deck frente a FHDI, regresión con efectos fijos y LinearDML, efecto nulo y confusión observada | Hecho el 2026-11-18 (288 repeticiones; resultados en §5, P5 y P6) |
| 2a′ | Diagnóstico del sesgo de LinearDML con FHDI (pregunta 6): tamaño de celda, regularización | Hecho el 2026-11-18 (P6) |
| 2a″ | LinearDML dentro de la celda (pregunta 7): la celda se quita exactamente antes del DML | Hecho el 2026-11-19 (P7); no cambia la simulación principal |
| 2b | Régimen FHDI en la simulación principal (`evaluacion.py`, las 8 filas de la Tabla 6, incluido el Causal Forest y la pobreza monetaria), para ver si quitar el ruido del sorteo mueve los modelos causales | **Pendiente obligatoria**: se hace aunque no sea en la misma corrida que la 2a |
| 3 | Reglas de focalización con el enlace fraccional (regla vigente con probabilidad; CATE con FHDI no identificable) | Pendiente |
| 4 | Estimación con datos reales en modo FHDI (`5_estimacion.py`): contraste 0 exacto y DML marcado como no identificable | Pendiente |
| 5 | Texto de la tesis: Proposición 2 acotada al sorteo, figura de la recta con las dos curvas, párrafo de la FHDI como alternativa evaluada | Después de 2-4 |

## 6.1 Implementación de la fase 2

- **Imputación en la simulación** (`src/simulacion/vinculo.py`):
  `probabilidad_celda` da a cada hogar de la encuesta la proporción de
  T = 1 entre los donantes del registro de su celda, con la misma cadena
  de respaldos que `sortear_donante`. Es FEFI, que por R4 equivale a la
  FHDI con pesos calibrados.
- **T observado** (`sensibilidad_semisintetica.t_observado`): el T
  verdadero en una fracción L de hogares (vinculados) y, en el resto, el
  del donante sorteado (Hot-Deck) o la probabilidad de la celda (FHDI).
  Los mismos hogares vinculados en las dos imputaciones, para que la
  comparación sea pareada.
- **No identificable** (`estimadores.identificable`): si T no varía
  dentro de las celdas (FHDI con L = 0), no se estima y se reporta vacío
  con `identificable = False`, no 0. Un 0 se leería como «efecto nulo
  estimado», y no lo es.
- **LinearDML con tratamiento continuo.** Con la FHDI, T en los no
  vinculados es una probabilidad. Se ajusta LinearDML con tratamiento
  continuo y, para T, el mismo modelo de regresión que para Y (en vez de
  la logística). Decisión frente a la alternativa de expandir a 10
  donantes con pesos: por R4 dan lo mismo, y la base expandida obligaría
  a que los donantes de un mismo hogar no queden en particiones distintas
  del ajuste cruzado.
- **Datos.** La simulación lee `muestra_estimacion_monetaria_2024` y
  `sisben_estandarizado_2024_con_bogota` de `data/2_models/`; antes de la
  corrida del 2026-11-18 se verificó que son idénticos (MD5) a los del
  banco de Azure.
- **Pruebas:** `tests/test_vinculo_fhdi.py` (probabilidad de la celda con
  respaldos, no identificable con L = 0, T observado, la recta con sorteo
  frente a la imputación fraccional en datos sintéticos, y la repetición
  completa sobre una base sintética).
- **LinearDML dentro de la celda** (`sensibilidad_semisintetica.linear_dml_intra_celda`,
  pregunta 7): función nueva al lado de `linear_dml`, que no cambia.
  Pruebas: con celdas de 8 hogares, efecto nulo y FHDI con L = 0,25 el
  vigente se sesga (+0,13 en la base de prueba) y el nuevo no; con celdas
  grandes coincide con la regresión (FHDI τ, Hot-Deck L·τ). Mutación: el
  estimador sin quitar la media de la celda.

## 7. Qué decir en la tesis (borrador de ideas, no texto final)

- La FHDI no hace exacto el enlace: dice exactamente cuánto se sabe de
  cada hogar. El límite es la información común entre las fuentes, no el
  método (techo de 78-80 % en A/B).
- Los resultados descriptivos del Hot-Deck no cambian; la FHDI los da sin
  el ruido del sorteo.
- La Proposición 2 (recta L·τ) es de la imputación por un solo sorteo;
  con imputación fraccional el vínculo parcial reduce la precisión pero no
  sesga (si la fase 2 lo confirma con los estimadores del proyecto).
- Con un enlace por celdas, el estimador debe quitar la celda
  exactamente: el DML que la estima en el ajuste cruzado se sesga con
  celdas pequeñas, y más con imputación fraccional (P6, P7).

## Referencias

- Kim, J. K. y Fuller, W. (2004). Fractional hot deck imputation.
  *Biometrika*, 91(3), 559-578.
- Im, J., Cho, I. H. y Kim, J. K. (2018). FHDI: An R package for fractional
  hot deck imputation. *The R Journal*, 10(1), 140-154.

(Verificar los datos bibliográficos antes de citarlos.)
