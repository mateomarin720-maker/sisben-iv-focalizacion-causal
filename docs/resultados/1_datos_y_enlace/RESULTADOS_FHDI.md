# Imputación fraccional (FHDI) frente al Hot-Deck

Generado el 2026-11-18 y actualizado el 2026-11-21 (donantes ponderados por el `fex` del Sisbén) por `src/emparejamiento/fhdi/` (reglas en su
`README.md`), con los datos del banco de Azure leídos en memoria. Salidas
en `docs/reports/`: `fhdi.txt` (consola), `fhdi_validacion.csv`,
`fhdi_comparacion.csv` y `fhdi_placebo.csv`. Son datos reales, no
simulados.

**Pregunta.** El Hot-Deck le da a cada hogar de la GEIH el grupo de un
donante sorteado en su celda. ¿Se puede hacer el enlace más exacto, o al
menos quitarle el ruido del sorteo, sin cambiar la celda?

**Cómo.** La misma celda y la misma cadena de respaldos del Hot-Deck; en
vez de un donante, 10 donantes por hogar, estratificados por grupo, con
pesos calibrados a la proporción de cada grupo en la celda (Kim y
Fuller, 2004), y FEFI (todos los donantes de la celda). 290.968 hogares
de la GEIH y 3.093.411 donantes del Sisbén con clasificación; 99,92 % en
celda exacta y 100 % de los hogares calibrados exactamente.

## 1. Cuánto puede acertar el enlace por celda

Validación dentro del Sisbén: se esconde el grupo del 20 % de los hogares
(618.907), se imputa con el resto como donantes y se compara con el grupo
verdadero.

| Método | Acierta A/B | Acierta el grupo A-D | Error cuadrático A/B (Brier) | Descalibración | Error en A/B por departamento (pp) |
|---|---|---|---|---|---|
| Sin celda (todo el registro) | 51,9 % | 27,0 % | 0,240 | 0,006 | 14,8 |
| Sorteo (Hot-Deck) | 70,9 % | 43,1 % | 0,291 | 0,291 | 1,27 |
| **Moda de la celda** | **78,2 %** | **53,6 %** | 0,218 | 0,218 | **11,2** |
| **FHDI (M = 10)** | 70,9 % (esperado) | 43,1 % (esperado) | **0,148** | **0,012** | **0,93** |
| FEFI | 70,9 % (esperado) | 43,1 % (esperado) | 0,148 | 0,012 | 0,93 |

Las medidas se ponderan por el `fex` de los hogares de prueba. El `fex`
del Sisbén nacional tiene cola larga (mediana 1,7, máximo 922): los
3,09 millones de donantes equivalen a unos 151.000 efectivos (Kish), y
la proporción de A/B ponderada difiere 0,6 pp entre la muestra de prueba
y la de entrenamiento por puro muestreo. Por eso la descalibración de la
FHDI sube de 0,002 (sin ponderar) a 0,012; sigue siendo la menor de los
métodos con celda.

Lectura:

- **El techo del enlace por celda es la moda: 78,2 % en A/B y 53,6 % en
  el grupo.** Ningún método que use solo la celda acierta más hogar por
  hogar. Ponderado por los hogares de la GEIH el techo es 79,0 % y el
  sorteo 71,2 % (la cifra de «dos sorteos coinciden en A/B» de
  `RESULTADOS_VARIABILIDAD_HOTDECK.md`). Agregar zona, paredes o sexo del
  jefe subía el techo entre 0,1 y 0,3 pp (medido antes de ponderar por `fex`): lo que limita el enlace es la
  información común entre las fuentes, no el método.
- **La moda acierta más por hogar pero distorsiona la distribución:**
  le da a todos los hogares de una celda su grupo más frecuente, y la
  proporción de A/B por departamento se aleja 11,2 pp de la verdadera.
  Para la tesis, que estima incidencias y errores de focalización, es el
  peor de los métodos con celda.
- **La FHDI no acierta más que el sorteo, pero dice exactamente cuánto se
  sabe:** su probabilidad está calibrada (cuando dice 60 % de A/B, el 60 %
  lo es; descalibración 0,012), tiene el menor error cuadrático (0,148,
  la mitad del sorteo) y el menor error por departamento (0,93 pp).
- **FHDI y FEFI coinciden** en todas las medidas: con la calibración, 10
  donantes bastan.

## 2. Cantidades sobre la GEIH

| Cantidad | Hot-Deck (semilla 42) | Hot-Deck (media de 100 sorteos) | FHDI = FEFI | Error jackknife | Desviación entre sorteos |
|---|---|---|---|---|---|
| Grupo A | 13,62 % | 13,64 % | 13,64 % | 0,06 | 0,07 |
| Grupo B | 28,63 % | 28,77 % | 28,76 % | 0,05 | 0,14 |
| Grupo C | 36,35 % | 36,06 % | 36,08 % | 0,05 | 0,16 |
| Grupo D | 21,40 % | 21,53 % | 21,53 % | 0,07 | 0,11 |
| A/B | 42,25 % | | 42,39 % | 0,10 | |
| Exclusión (pobreza monetaria) | 36,38 % | | **36,06 %** | 0,17 | |
| Inclusión (pobreza monetaria) | 59,30 % | | **59,23 %** | 0,17 | |
| Exclusión (IPM-GEIH) | 31,17 % | | 30,80 % | 0,22 | |
| Inclusión (IPM-GEIH) | 76,40 % | | 76,36 % | 0,16 | |
| Pobreza monetaria en A/B | 40,70 % | | 40,77 % | 0,17 | |
| Pobreza monetaria en C/D | 17,03 % | | 16,92 % | 0,13 | |

Lectura:

- **La FHDI reproduce la media de los 100 sorteos** (diferencias de 0,02
  pp o menos) en una sola corrida, y su error estándar ya no tiene la
  parte del sorteo: la desviación entre sorteos (0,07 a 0,16 pp en los
  grupos) era mayor que el error muestral de la GEIH (0,05 a 0,07 pp).
- **Por departamento**, el sorteo guardado se aleja hasta 2,1 pp de FEFI
  en la proporción de A/B, y la desviación entre sorteos llega a 1,5 pp;
  la FHDI coincide con FEFI (diferencia máxima 0,00 pp).
- **Los errores de exclusión e inclusión de FEFI son exactamente el valor
  «con independencia» de `errores_focalizacion_frechet.py`** (36,06 % y
  59,23 % en pobreza monetaria), calculado por otro camino: es el punto
  que corresponde a suponer que, dentro de la celda, pobreza y grupo no
  se relacionan. Sigue dentro de las cotas de Fréchet, que no cambian
  (exclusión [4,4 %; 59,5 %], inclusión [39,0 %; 74,2 %]). La FHDI da un
  punto con su error, no estrecha la cota.

## 3. Contraste placebo: cero exacto

| Outcome | FHDI | Hot-Deck: 100 sorteos con Rubin | IC 95 % | Varianza por imputación |
|---|---|---|---|---|
| Pobreza monetaria | 0 | +0,0002 | [−0,0051; +0,0055] | 48 % |
| Pobreza IPM-GEIH | 0 | +0,0002 | [−0,0037; +0,0041] | 51 % |
| Log del ingreso per cápita | 0 | +0,0001 | [−0,0193; +0,0195] | 47 % |

Con los pesos calibrados, todos los hogares de una celda tienen la misma
proporción ponderada de A/B, así que el grupo imputado no varía entre
hogares dentro de la celda y la regresión con efectos fijos da 0 exacto.
Es la Proposición 1 sin ruido: el Hot-Deck llega a lo mismo en promedio
(los IC de Rubin contienen el 0), pero cada sorteo da un número distinto
y la mitad de su varianza es del sorteo.

## 4. Vínculo parcial en la simulación*: la recta de atenuación con las dos imputaciones

`src/simulacion/sensibilidad_semisintetica.py vinculo` (pregunta 5; salidas
`docs/reports/sensibilidad_vinculo_fhdi*.csv` y `.txt`). Hogares reales de
la GEIH con tratamiento y efecto simulados*, encuestas de 30.000 hogares,
288 repeticiones. A una fracción L de los hogares se le da su T verdadero;
al resto, el T de un donante sorteado (Hot-Deck) o la proporción de T = 1
de su celda (FHDI). Confusión observada, τ = 0,095*:

| L | Regresión, Hot-Deck | Regresión, FHDI | L·τ | LinearDML, Hot-Deck | LinearDML, FHDI |
|---|---|---|---|---|---|
| 0 | +0,000* | no identificable | 0 | −0,036* | no identificable |
| 0,25 | +0,023* | **+0,092*** | +0,024 | −0,012* | −0,071* |
| 0,50 | +0,046* | **+0,093*** | +0,047 | +0,014* | +0,005* |
| 0,75 | +0,069* | **+0,093*** | +0,071 | +0,036* | +0,034* |
| 1 | +0,092* | +0,092* | +0,095 | +0,061* | +0,061* |

- **Regresión con efectos fijos:** con Hot-Deck cae a L·τ (la recta de la
  Proposición 2); con FHDI recupera τ en todo L > 0, con cobertura de
  0,95-0,98 y más varianza cuanto menor es L. Con L = 0 no se identifica.
- **LinearDML con FHDI se sesga más que con Hot-Deck** (con efecto nulo,
  −0,161* con L = 0,25 frente a −0,036*). Hipótesis en
  `METODOLOGIA_FHDI.md` (P6): la parte imputada solo varía entre celdas y
  la regularización de LinearDML no quita del todo los efectos de celda
  con ≈8 hogares por celda.
- **Diagnóstico** (`vinculo_diagnostico`, 96 repeticiones). Sesgo con
  efecto nulo y L = 0,25:

| Hogares por celda | LinearDML, FHDI | LinearDML sin regularizar, FHDI | LinearDML, Hot-Deck | Regresión, FHDI |
|---|---|---|---|---|
| ≈8 (30.000 hogares) | −0,161* | −0,105* | −0,038* | +0,004* |
| ≈16 (60.000) | −0,091* | −0,052* | −0,017* | +0,001* |
| ≈32 (120.000) | −0,047* | −0,025* | −0,011* | +0,002* |

  El sesgo se reduce a la mitad cada vez que se duplican los hogares por
  celda; sin regularizar baja un tercio pero no desaparece, y crece como
  1/L. Es la parte de los efectos de celda que el ajuste cruzado no quita,
  concentrada en la poca variación de T que aportan los vinculados. La
  regresión con efectos fijos exactos no se sesga. Con los datos reales
  (78 hogares por celda) sería del orden de −0,016.

### LinearDML dentro de la celda (pregunta 7)

`sensibilidad_semisintetica.py intra_celda` (salidas
`docs/reports/sensibilidad_intra_celda*`): antes de LinearDML se resta la
media de la celda a Y, a T y a los controles, como en la regresión con
efectos fijos. 264 repeticiones, 30.000 hogares por encuesta. Confusión
observada, τ = 0,095*:

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

- Quitada la celda exactamente, LinearDML coincide con la regresión con
  efectos fijos: con FHDI recupera τ; con Hot-Deck, L·τ.
- Corrige también el sesgo del LinearDML vigente con vínculo exacto
  (+0,060* frente a τ = 0,095*). Adoptarlo movería las filas de LinearDML
  de la Tabla 6; por ahora no se cambió nada de lo vigente (decisión de la
  fase 2b, `METODOLOGIA_FHDI.md` P7).

### Causal Forest dentro de la celda (pregunta 8)

`sensibilidad_semisintetica.py bosque_intra_celda` (salidas
`docs/reports/sensibilidad_bosque_intra_celda*`): la misma
transformación antes del Causal Forest, con sus hiperparámetros vigentes.
96 repeticiones, 30.000 hogares por encuesta; PEHE es el error en el
efecto por hogar:

| Escenario | Vínculo | Regresión con efectos fijos | Causal Forest vigente | Causal Forest dentro de la celda | PEHE vigente | PEHE dentro de la celda |
|---|---|---|---|---|---|---|
| Confusión observada (τ = 0,095*) | Hot-Deck, L = 1 (vínculo exacto) | +0,090* | +0,058* | **+0,092*** | 0,085* | **0,067*** |
| | Hot-Deck, L = 0 | −0,001* | −0,036* | −0,002* | 0,159* | 0,119* |
| | FHDI, L = 0,25 | +0,089* | −0,073* | **+0,091*** | 0,257* | **0,129*** |
| | FHDI, L = 0,5 | +0,086* | −0,002* | **+0,089*** | 0,160* | **0,094*** |
| Efecto nulo | Hot-Deck, L = 1 | −0,002* | −0,037* | −0,001* | 0,087* | 0,064* |
| | Hot-Deck, L = 0 | +0,001* | −0,037* | +0,000* | 0,088* | 0,063* |
| | FHDI, L = 0,25 | −0,002* | −0,167* | −0,002* | 0,261* | 0,132* |
| | FHDI, L = 0,5 | −0,004* | −0,094* | −0,004* | 0,159* | 0,091* |

- **El Causal Forest se corrige igual que LinearDML:** dentro de la celda
  su efecto promedio coincide con la regresión con efectos fijos y con
  LinearDML dentro de la celda (diferencias ≤ 0,003) en los ocho casos;
  el vigente se sesga −0,035* con vínculo exacto y hasta −0,167* con FHDI.
- **Mejora también el efecto por hogar (PEHE),** que es para lo que se usa
  el Causal Forest (heterogeneidad): baja entre 21 % y 50 %, más con FHDI
  (0,257* → 0,129* con L = 0,25). La celda mal quitada contaminaba el
  efecto de cada hogar, no solo el promedio.
- **Sus IC son demasiado anchos en las dos versiones:** cobertura de 1,00
  en casi todos los casos (el vigente también; en la simulación principal
  su IC es unas tres veces más ancho que el de LinearDML). Con Hot-Deck y
  L = 0 el corregido «cubre» τ el 84 % de las veces aunque estima ≈0. El
  IC del Causal Forest no sirve para decidir si hay efecto; para eso
  están la regresión y LinearDML.
- **Costo:** el mismo tiempo de ajuste que el vigente (≈17 s con 30.000
  hogares).

## 5. Simulación principal ampliada*: los 8 escenarios con estimadores dentro de la celda y FHDI

`python -m src.simulacion ampliada` (`src/simulacion/ampliada.py`;
salidas `docs/reports/simulacion_ampliada*`, tabla completa en
`simulacion_ampliada_tablas.md`). Mismas encuestas, donantes y hogares con
donante que la corrida de la Tabla 6, que no cambia: la regresión con
efectos fijos la reproduce repetición por repetición (diferencia máxima
8,9e-16). 600 repeticiones (el máximo; Causal Forest en 216), 30.000
hogares por encuesta. Extracto de log-ingreso (τ = 0,095*; efecto
promedio y, entre paréntesis, cobertura del IC del 95 %):

| Escenario | Integración | Regresión EF celda | LinearDML vigente | LinearDML dentro de la celda | Causal Forest vigente | Causal Forest dentro de la celda |
|---|---|---|---|---|---|---|
| Aleatoria | Oráculo | +0,094\* (0,97\*) | +0,094\* (0,93\*) | +0,095\* (0,97\*) | +0,093\* (1,00\*) | +0,093\* (1,00\*) |
| Confusión observada | Oráculo | +0,090\* (0,94\*) | +0,059\* (0,64\*) | **+0,092\* (0,95\*)** | +0,061\* (1,00\*) | **+0,092\* (1,00\*)** |
| | Hot-Deck | +0,001\* (0,03\*) | −0,034\* (0,00\*) | +0,000\* (0,03\*) | −0,034\* (0,50\*) | −0,000\* (0,86\*) |
| | FHDI, vínculo 50 % | +0,091\* (0,94\*) | +0,004\* (0,24\*) | **+0,093\* (0,94\*)** | — | **+0,094\* (1,00\*)** |
| Efecto nulo (τ = 0) | Oráculo | −0,001\* (0,97\*) | −0,035\* (0,65\*) | −0,001\* (0,96\*) | −0,038\* (1,00\*) | −0,004\* (1,00\*) |
| | FHDI, vínculo 50 % | −0,001\* (0,95\*) | −0,092\* (0,24\*) | −0,001\* (0,95\*) | — | −0,003\* (1,00\*) |
| Solapamiento débil | Oráculo | +0,085\* (0,97\*) | −0,016\* (0,24\*) | **+0,082\* (0,96\*)** | −0,015\* (0,99\*) | **+0,085\* (1,00\*)** |
| | FHDI, vínculo 50 % | +0,087\* (0,97\*) | −0,164\* (0,00\*) | **+0,085\* (0,96\*)** | — | **+0,086\* (1,00\*)** |
| Confusión no observada media | Oráculo | −0,604\* (0,00\*) | −0,603\* (0,00\*) | −0,594\* (0,00\*) | −0,605\* (0,00\*) | −0,597\* (0,00\*) |

FHDI sin vínculo: no identificable en todos los escenarios y estimadores
(T = p_celda es función de la celda).

- **Dentro de la celda, LinearDML y Causal Forest dan lo mismo que la
  regresión con efectos fijos en los 8 escenarios** (diferencias ≤ 0,01
  salvo en la regla de corte, donde las tres se sesgan en torno a −2), con
  cualquier integración y en los dos outcomes.
- **Las filas vigentes de LinearDML y Causal Forest de la Tabla 6 llevan
  el sesgo de estimar la celda.** Se ve donde la regresión acierta: con
  efecto nulo el LinearDML vigente da −0,035* en log-ingreso y +0,015* en
  pobreza en todas las integraciones; con confusión observada da +0,059*
  frente a +0,092*; con solapamiento débil, −0,016* frente a +0,082*. La
  versión dentro de la celda quita esas diferencias y recupera la
  cobertura nominal (0,95-0,97 en el oráculo).
- **Con Hot-Deck los estimadores dentro de la celda dan ≈0, como la
  regresión** (la atenuación completa del placebo). Los −0,03* del
  LinearDML y el Causal Forest vigentes con Hot-Deck no son información
  del enlace sino el mismo sesgo.
- **La FHDI con vínculo del 50 % recupera τ con la regresión y con los
  estimadores dentro de la celda** (cobertura 0,94-0,97), en todos los
  escenarios en que el oráculo lo recupera. Con el LinearDML vigente falla
  (+0,004*, −0,092* con efecto nulo, −0,164* con solapamiento débil): es la
  combinación en la que más pesa el sesgo.
- **No corrige la falta de identificación:** con confusión no observada o
  regla de corte todos los estimadores se sesgan casi igual, con o sin la
  corrección. La corrección quita un sesgo del estimador, no del diseño.
- **Pobreza monetaria** (τ = −0,033*) repite el patrón: el LinearDML
  vigente se aleja de la regresión en +0,013* a +0,015* con Hot-Deck y
  efecto nulo, y la versión dentro de la celda coincide con ella.
- **Convergencia:** 9 de las 168 combinaciones identificables quedaron sobre el umbral del
  MCSE al llegar al máximo de repeticiones (600, o 200 del Causal Forest).
  Ocho tienen sesgos de −0,7 a −2,1 (confusión no observada y regla de
  corte, MCSE del sesgo 0,0033-0,0063 frente a un umbral de 0,003) y una es
  la cobertura del Causal Forest con Hot-Deck en el escenario aleatorio
  (0,56, MCSE 0,034). Ninguna cambia una lectura.
- **Costo:** 4 h 7 min con 4 procesos (lotes de 24 repeticiones: 11-13 min
  con Causal Forest, 4-17 min sin él).

## Conclusión

La FHDI es una alternativa al Hot-Deck que **no cambia ninguna conclusión
de la tesis** y quita el ruido de la imputación: reproduce en una
corrida la media de los 100 sorteos, con un error estándar que solo mide
la muestra de la GEIH, y da el contraste placebo como 0 exacto. **No hace
más exacto el enlace hogar por hogar:** el techo con la celda actual es la
moda (78,2 % en A/B dentro del Sisbén; 79,0 % ponderado por la GEIH), y
asignarla distorsiona las incidencias. Subir ese techo exige más
información común entre las fuentes o una llave, no otro método de
imputación.

Supuesto que se mantiene: el mismo del Hot-Deck, que dentro de la celda
el grupo del Sisbén no depende de la pobreza medida en la GEIH. La
validación interna mide lo bien que la celda predice el grupo en el
Sisbén; no mide si la GEIH y el Sisbén registran igual las variables de
la celda (eso lo cubre la homologación, `RESULTADOS_HOTDECK.md`).
