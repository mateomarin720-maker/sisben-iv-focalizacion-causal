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
vinculados se parecen a los demás dentro de su celda. Falta comprobarlo
con LinearDML y Causal Forest en el módulo de simulación; la tabla viene de un
script provisional y se reemplaza por la corrida de la fase 2.

## 6. Plan e implementación

| Fase | Qué | Estado |
|---|---|---|
| 0 | Reglas, validación del enlace y comparación con el Hot-Deck (`reglas.py`, `validacion.py`, `__main__.py`) | Hecho el 2026-11-18 |
| 1 | Enlace fraccional por hogar guardado y publicado en Azure (`enlace.py` → `geih_sisben_fhdi_2024.parquet`) | Hecho el 2026-11-18 |
| 2 | Régimen FHDI en la simulación junto al Hot-Deck (`vinculo.py`, `evaluacion.py`, sensibilidad del vínculo parcial); «no identificable» cuando no hay variación; recta de atenuación con las dos curvas | Pendiente |
| 3 | Reglas de focalización con el enlace fraccional (regla vigente con probabilidad; CATE con FHDI no identificable) | Pendiente |
| 4 | Estimación con datos reales en modo FHDI (`5_estimacion.py`): contraste 0 exacto y DML marcado como no identificable | Pendiente |
| 5 | Texto de la tesis: Proposición 2 acotada al sorteo, figura de la recta con las dos curvas, párrafo de la FHDI como alternativa evaluada | Después de 2-4 |

## 7. Qué decir en la tesis (borrador de ideas, no texto final)

- La FHDI no hace exacto el enlace: dice exactamente cuánto se sabe de
  cada hogar. El límite es la información común entre las fuentes, no el
  método (techo de 78-80 % en A/B).
- Los resultados descriptivos del Hot-Deck no cambian; la FHDI los da sin
  el ruido del sorteo.
- La Proposición 2 (recta L·τ) es de la imputación por un solo sorteo;
  con imputación fraccional el vínculo parcial reduce la precisión pero no
  sesga (si la fase 2 lo confirma con los estimadores del proyecto).

## Referencias

- Kim, J. K. y Fuller, W. (2004). Fractional hot deck imputation.
  *Biometrika*, 91(3), 559-578.
- Im, J., Cho, I. H. y Kim, J. K. (2018). FHDI: An R package for fractional
  hot deck imputation. *The R Journal*, 10(1), 140-154.

(Verificar los datos bibliográficos antes de citarlos.)
