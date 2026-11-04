# Variabilidad de la imputación del Hot-Deck

Generado 2026-11-04 por `src/validacion/variabilidad_hotdeck.py`
(prioridad 1 de `docs/seguimiento/SEGUIMIENTO_TESIS_2026-11-04.md`,
pregunta del tutor del 2026-11-03). Salidas en `docs/reports/`:
`variabilidad_hotdeck.txt` (consola), `_celdas.csv` (por celda),
`_agregados.csv` (nacional y por departamento) y `_estimacion.csv`
(contraste placebo con reglas de Rubin).

**Pregunta.** El Hot-Deck sortea, para cada hogar de la GEIH, un donante
del Sisbén de su misma celda. ¿Cuánto cambia el resultado si el sorteo se
repite con otra semilla?

**Cómo.** La misma función `hotdeck()` del pipeline, sobre los mismos
290.968 hogares GEIH y 3.106.489 donantes, con **100 semillas**. La
semilla 42 es la del pipeline y reproduce el grupo guardado en el 100 %
de los hogares. Son datos reales: la variabilidad medida es la de la
imputación que usa el proyecto, no una simulación.

## 1. Por hogar: el grupo imputado no es estable

| Medida (ponderada por `fex`) | Resultado | Teórico de la celda |
|---|---|---|
| Probabilidad de que dos sorteos den el mismo grupo | **34,4 %** | 34,4 % |
| Probabilidad de que dos sorteos coincidan en A/B | **62,7 %** | 62,7 % |
| Hogares con el mismo grupo en los 100 sorteos | 0,008 % | |
| Hogares con el mismo estado A/B en los 100 sorteos | 0,04 % | |
| Hogares con P(A/B) ≤ 0,1 o ≥ 0,9 (casi seguro) | 7,8 % | |
| Hogares con P(A/B) entre 0,3 y 0,7 (incierto) | 39,1 % | |

La concordancia teórica de un hogar es Σ_g π_g², con π_g la proporción de
donantes de su celda en el grupo g: la probabilidad de que dos donantes
sorteados al azar compartan grupo. La empírica (estimador insesgado con
los 100 sorteos) la reproduce en el agregado y hogar por hogar
(correlación 0,90). **El grupo de cada hogar es un sorteo**: lo que el
Hot-Deck fija es la probabilidad, no el grupo.

## 2. Por celda: proporciones estables, salvo en celdas pequeñas

Proporción de hogares GEIH en A/B dentro de cada celda (985 celdas con
receptores), en cada sorteo, frente a la proporción A/B de los donantes
de la celda:

| Medida | Mediana entre celdas | Ponderada por población | Percentil 90 |
|---|---|---|---|
| Coeficiente de variación (sd / media entre sorteos) | 0,091 | 0,049 | 0,336 |
| Error relativo medio, \|p_sorteo − π\| / π | 0,072 | 0,039 | |

| Hogares GEIH en la celda | Celdas | CV mediano | Error relativo mediano |
|---|---|---|---|
| Hasta 30 | 425 | 0,171 | 0,130 |
| 31-99 | 202 | 0,086 | 0,070 |
| 100-299 | 183 | 0,066 | 0,054 |
| 300-999 | 107 | 0,049 | 0,039 |
| 1.000 o más | 68 | 0,033 | 0,027 |

- La variación cae con el tamaño de la celda, como en un muestreo
  binomial (CV ≈ √((1 − π) / (n π))).
- 458 celdas tienen CV > 0,1, pero suman el **6,7 %** de la población;
  las 204 con CV > 0,2, el 0,8 %. Casi la mitad de las celdas tiene
  hasta 30 hogares GEIH: ahí cualquier proporción por celda es ruidosa.
- Ponderado por población, el error relativo frente a los donantes es
  de 3,9 %: en las celdas grandes, el Hot-Deck reproduce bien la
  distribución de los donantes.

## 3. Agregados: las cifras publicadas apenas se mueven

| Grupo (nacional, % ponderado) | Media | Desviación | CV | Mínimo-máximo | Semilla 42 (publicada) |
|---|---|---|---|---|---|
| A | 14,20 | 0,10 | 0,007 | 13,96-14,43 | 14,19 |
| B | 29,37 | 0,14 | 0,005 | 29,03-29,70 | 29,44 |
| C | 34,31 | 0,14 | 0,004 | 33,92-34,56 | 34,36 |
| D | 22,13 | 0,15 | 0,007 | 21,82-22,53 | 22,01 |

Por departamento, la proporción A/B tiene CV de 0,006 (Magdalena) a 0,052
(San Andrés). Los rangos más amplios entre sorteos están en los
departamentos con menos hogares en la GEIH: Amazonas 6,9 puntos (1.579
hogares), Vaupés 6,5, Arauca 6,3, Guainía 6,3. En los grandes es de 2
puntos o menos (Bogotá 1,8).

## 4. Consecuencia para la estimación: el único resultado "significativo" es suerte del sorteo

Contraste placebo (regresión de la pobreza sobre A/B con efectos fijos de
celda) en cada sorteo, combinado con las reglas de Rubin (1987) para
imputación múltiple: varianza total = varianza dentro + (1 + 1/m) ×
varianza entre sorteos.

| Outcome | Semilla 42 [error] | Media de 100 sorteos | IC 95 % con Rubin | Varianza de la imputación / total | Sorteos con IC sin el 0 |
|---|---|---|---|---|---|
| `POBRE_MONETARIO` | −0,0004 [0,0018] | −0,0003 | [−0,0051; +0,0046] | 49 % | 4 % |
| `POBRE_GEIH` | **−0,0030 [0,0013]** | −0,00003 | [−0,0036; +0,0036] | 49 % | 3 % |
| log-ingreso per cápita | +0,0004 [0,0069] | +0,0012 | [−0,0186; +0,0210] | 55 % | 8 % |

- Con la semilla 42, `POBRE_GEIH` da −0,0030 con un IC que excluye el
  cero: es el mismo resultado que el DML con la celda exacta (−0,0026,
  `RESULTADOS_DML_ATE_ATT_ATU.md`), el único de los ocho que lo excluía.
  **En los 100 sorteos, la media es −0,00003 y solo el 3 % excluye el
  cero**, lo que el azar produce por sí solo con un 5 % de error. Ese
  resultado era suerte del sorteo, no señal.
- **Cerca de la mitad de la varianza total viene de la imputación** (49-55
  %). Los intervalos que se calculan con un solo sorteo, como los del DML
  de `5_estimacion.py`, no la incluyen: en `POBRE_GEIH` el error que
  corresponde es 0,0018 y el de un solo sorteo 0,0013 (un 28 % más
  angosto; el correcto es un 40 % mayor).

## Respuesta a la pregunta del tutor

- **A nivel de hogar, la imputación es inestable por diseño:** dos
  sorteos coinciden en el grupo de un hogar solo el 34 % de las veces, y
  en A/B el 63 %. Esa es exactamente la probabilidad que implica la
  composición de los donantes de cada celda; no es un error del código.
- **A nivel de celda grande, departamento y país, es estable:** CV del
  0,5 % al 0,7 % en la distribución nacional, error relativo del 3,9 %
  por celda (ponderado). El Hot-Deck reproduce distribuciones, no
  hogares.
- **Para cualquier estimación con el grupo imputado** hay que repetir el
  sorteo y combinar con Rubin: con un solo sorteo, los intervalos son
  demasiado angostos y aparecen "efectos" que dependen de la semilla.

## Limitaciones

- La variabilidad medida es solo la del sorteo dentro de la celda; no
  incluye la incertidumbre de la elección de la celda ni el error de
  muestreo de la GEIH.
- El contraste placebo usa una regresión con efectos fijos, no el DML
  completo (más costoso de repetir 100 veces); con la semilla 42 dan lo
  mismo (−0,0030 frente a −0,0026).
- El 0,02 % de los hogares que cae a una celda de respaldo se cuenta en
  su celda exacta, que no tiene donantes (sin concordancia teórica).

## Para reproducir

```bash
PYTHONIOENCODING=utf-8 ./.venv/Scripts/python.exe -m src.validacion.variabilidad_hotdeck 2 > docs/reports/variabilidad_hotdeck.txt 2>&1
poetry run pytest tests/test_variabilidad_hotdeck.py
```

El argumento es el número de procesos (cada uno carga los 3,1 millones
de donantes: con 2 caben en ~5 GB de RAM libre). Tarda ≈23 minutos
(≈20 s por sorteo).
