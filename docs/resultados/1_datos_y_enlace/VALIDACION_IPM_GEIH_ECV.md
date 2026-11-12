# Validación del IPM-GEIH contra la ECV y el IPM oficial

Generado por `src/validacion/validar_ipm_geih_ecv.py` (salida:
`docs/reports/validacion_ipm_geih_ecv*.{txt,csv}`). Responde a la
anotación del director: «proxy propio sin validar; o se valida contra la
ECV o se retira».

## Por qué se puede validar

El IPM oficial del DANE se calcula con la Encuesta Nacional de Calidad de
Vida (ECV), y la ECV usa los mismos códigos de pregunta que la GEIH para
las 8 privaciones del proxy (`P6160`, `P6090`, `P6920`, `P5010`,
acueducto y alcantarillado; el nivel educativo es `P8587` en la ECV y
`P3042` en la GEIH, con las mismas categorías; la asistencia escolar,
`P8586` frente a `P6170`). Las reglas del proxy están en un solo lugar
(`src/indicadores/ipm_proxy.py`) y las usan tanto la GEIH como la
validación: el proxy validado es exactamente el que se estima.

Dos comparaciones, con hogares ponderados por el factor de expansión:

- **A. Hogar por hogar.** La base del IPM del DANE trae, para cada hogar,
  las respuestas crudas de la ECV y la clasificación oficial (15
  privaciones, corte del 33 %). Se calcula el proxy en esos mismos
  hogares y se compara con `POBRE` oficial.
- **B. Mismo año.** Se calcula el proxy en los módulos crudos de la ECV
  2024 y se compara con el de la GEIH 2024.

**Año de la base del IPM.** La base que tiene el banco de datos (catálogo
903) es la del **IPM 2025**; la de 2024 es el catálogo 860, que no está
en el banco. A compara el proxy con la clasificación oficial de 2025; B
usa la ECV 2024, el mismo año de la GEIH. El módulo de vivienda de la ECV
no cruza con la base del IPM (el `DIRECTORIO` está anonimizado distinto),
así que A no se abre por zona ni departamento.

## A. El proxy frente a la clasificación oficial, hogar por hogar

79.125 hogares de la base del IPM 2025. La tasa oficial de hogares pobres
es 8,1 % (9,9 % de las personas).

| Corte K | Tasa del proxy | Concordancia | Sensibilidad | Especificidad | Kappa |
|---|---|---|---|---|---|
| 2 | 40,7 % | 66,3 % | 93,3 % | 63,9 % | 0,20 |
| **3 (adoptado)** | **18,3 %** | **86,0 %** | **76,8 %** | **86,9 %** | **0,41** |
| 4 | 7,3 % | 92,6 % | 49,0 % | 96,4 % | 0,48 |
| 5 | 1,9 % | 93,5 % | 22,1 % | 99,8 % | 0,34 |

Sensibilidad: de los hogares pobres según el IPM oficial, cuántos marca
el proxy. Especificidad: de los no pobres, cuántos deja fuera. La
correlación de rangos entre el puntaje del proxy (0 a 8) y el IPM oficial
es **0,72**.

**Lectura.**
- El proxy ordena a los hogares como el IPM oficial (correlación 0,72;
  kappa moderado, 0,41 con K = 3 y 0,48 con K = 4), pero **no reproduce
  su nivel**: con K = 3 marca como pobres al 18,3 % de los hogares, más
  del doble del 8,1 % oficial. Con K = 3 encuentra 3 de cada 4 pobres
  oficiales, a costa de que solo un tercio de los que marca lo sean
  (precisión 34 %).
- **El corte que reproduce la tasa oficial es K = 4** (7,3 % frente a
  8,1 %), con la mayor concordancia y el mayor kappa. K = 3 se había
  elegido por cercanía a un 13 % que era la tasa sin ponderar de esta
  base, no la oficial (`docs/insumos/METODOLOGIA_INDICADOR_IPM_GEIH.md`).
  Cambiarlo mueve todos los resultados con `POBRE_GEIH`; queda como
  decisión del equipo.

### Cada privación frente a la oficial

| Privación del proxy | Oficial | Prevalencia proxy | Prevalencia oficial | Kappa |
|---|---|---|---|---|
| Analfabetismo (jefe) | Analfabetismo | 3,8 % | 6,4 % | 0,73 |
| Bajo logro educativo (jefe) | Bajo logro educativo | 30,5 % | 37,7 % | 0,72 |
| Inasistencia escolar (6-16 años) | Inasistencia escolar | 1,7 % | 1,8 % | 0,99 |
| Sin aseguramiento en salud (jefe) | Sin aseguramiento | 2,3 % | 4,7 % | 0,64 |
| Sin cotización a pensión (jefe) | Trabajo informal | 71,8 % | 70,0 % | 0,65 |
| Hacinamiento | Hacinamiento crítico | 2,5 % | 5,4 % | 0,63 |
| Sin alcantarillado | Sin alcantarillado | 23,0 % | 9,2 % | 0,51 |
| Sin acueducto | Sin acueducto | 9,6 % | 8,3 % | 0,85 |

Las diferencias vienen de la definición, no de los datos (son los mismos
hogares y las mismas respuestas): varias privaciones oficiales miran a
todos los miembros del hogar y el proxy solo al jefe, por lo que el proxy
marca menos analfabetismo, bajo logro y falta de aseguramiento; el
hacinamiento oficial usa otro umbral en la zona urbana. La de mayor
diferencia es alcantarillado (23,0 % frente a 9,2 %): la definición
oficial no toma la falta de alcantarillado como privación en la zona
rural de la misma forma, y el proxy sí. Las definiciones oficiales están
en la metodología del IPM del DANE; conviene citarlas al discutir esta
tabla.

## B. ECV 2024 frente a GEIH 2024, el mismo proxy

| | ECV 2024 | GEIH 2024 |
|---|---|---|
| Hogares | 85.387 | 290.968 |
| `POBRE_GEIH` nacional | 19,6 % | 20,4 % |
| Cabeceras | 6,5 % | 7,1 % |
| Centros poblados y rural disperso | 64,9 % | 68,6 % |
| Puntaje medio (0 a 8) | 1,49 | 1,51 |

Por departamento, sobre el mismo marco:

| | Departamentos | Correlación | Diferencia media GEIH − ECV | Diferencia absoluta mediana |
|---|---|---|---|---|
| Departamento completo | 24 | 0,988 | +2,1 puntos | 2,2 puntos |
| Cabecera de la capital | 9 | 0,968 | −3,4 puntos | 4,6 puntos |

En los 9 departamentos de la Orinoquía, la Amazonía y San Andrés la GEIH
solo encuesta la cabecera de la capital; ahí la ECV se restringe a la
misma cabecera (municipio 001, `CLASE` 1). Las prevalencias de cada
privación coinciden entre las dos encuestas dentro de 1,5 puntos
(`validacion_ipm_geih_ecv_privaciones.csv`).

**Lectura.** Con las mismas reglas, la GEIH 2024 y la ECV 2024 dan el
mismo indicador: 0,8 puntos de diferencia nacional y correlación de 0,99
entre departamentos. El proxy no es un artefacto de la GEIH.

## Conclusión para el documento

1. **El proxy está validado como medida de privación** (mide lo mismo en
   la GEIH que en la ECV, la encuesta del IPM oficial) y **como
   ordenamiento** (correlación 0,72 con el IPM oficial, hogar por hogar).
2. **No es el IPM oficial ni reproduce su tasa.** Con K = 3 duplica la
   incidencia oficial; con K = 4 la reproduce. Debe presentarse como
   «índice de privaciones con 8 de los 15 indicadores, validado contra la
   ECV», no como IPM.
3. Para los resultados causales esto pesa poco: con el grupo imputado el
   DML es un placebo (Proposición 1) y da cero con cualquier medida de
   resultado; las cotas de Fréchet-Manski usan solo la proporción de
   pobres por celda.

## Reproducir

La ECV 2024 está en Azure bajo `ecv/` (no en `0_raw/`, así que
`restaurar_banco_datos_azure.py` no la baja): los seis módulos que usa la
validación (`Caracteristicas_composicion_hogar`, `Educacion`, `Salud2024`,
`Fuerza_trabajo`, `Servicios_hogar`, `Datos_vivienda`) se copian a
`data/0_raw/ecv/` sin descomprimir. Diccionario y ficha:
`ecv/docs_ecv/`.

```bash
poetry run python -m src.validacion.validar_ipm_geih_ecv
```
