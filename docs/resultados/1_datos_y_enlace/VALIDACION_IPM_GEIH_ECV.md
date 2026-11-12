# Validación del IPM-GEIH contra la ECV y el IPM oficial

Generado por `src/validacion/validar_ipm_geih_ecv.py` (salida:
`docs/reports/validacion_ipm_geih_ecv*.{txt,csv}`). Responde a la
anotación del director: «proxy propio sin validar; o se valida contra la
ECV o se retira».

## Corrección del 2026-11-11: vivienda con la definición oficial por zona

Esta validación encontró que el proxy usaba la regla urbana de vivienda en
todo el país. Se corrigió (`src/indicadores/ipm_proxy.py`): en lo rural, la
excreta se mide por el tipo de sanitario, el agua por la fuente y el
hacinamiento con > 3. El 2026-11-12 se regeneró la muestra de estimación
y se volvieron a correr los modelos; las secciones A y B ya son del proxy
corregido. Antes y después, contra el IPM oficial 2024:

| | Proxy anterior (K = 3) | Proxy corregido (K = 3) | IPM oficial 2024 |
|---|---|---|---|
| Nacional | 18,7 % | **13,8 %** | 9,2 % |
| Cabeceras | 6,5 % | 7,5 % | 5,9 % |
| Rural | 63,7 % | **37,0 %** | 21,5 % |
| Concordancia con el oficial | 85,6 % | **90,0 %** | — |
| Kappa | 0,41 | **0,51** | — |
| Correlación de rangos con el IPM | 0,72 | **0,76** | — |
| `POBRE_GEIH` en la GEIH 2024 (ponderado) | 20,4 % | **14,5 %** | — |

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

- **A. Hogar por hogar, contra el IPM oficial 2024.** La base del IPM 2024
  (Azure, `0_raw/ipm/2024/`) sale de la misma ECV 2024: coinciden el 100 %
  de sus `DIRECTORIO` y de sus factores de expansión. Trae, para cada
  hogar, las respuestas crudas y la clasificación oficial (15
  privaciones, corte del 33 %). Se calcula el proxy en esos mismos
  hogares y se compara con `POBRE` oficial; la zona sale del módulo de
  vivienda de la ECV.
- **B. Mismo año, ECV 2024 frente a GEIH 2024.** El proxy en los módulos
  crudos de la ECV 2024 frente al de la GEIH 2024.

Todo se lee directo de Azure, sin copiarlo a `data/`. La base del IPM que
estaba en `data/0_raw/ipm/nacional/` es la de 2025 (`PERIODO` = 20250731;
sus factores no coinciden con la ECV 2024) y no trae la zona del hogar;
no se usa en la validación.

## A. El proxy frente a la clasificación oficial 2024, hogar por hogar

77.568 hogares. La tasa oficial de hogares pobres es 9,2 %.

| Corte K | Tasa del proxy | Concordancia | Sensibilidad | Especificidad | Kappa |
|---|---|---|---|---|---|
| 2 | 39,5 % | 68,3 % | 92,1 % | 65,9 % | 0,24 |
| **3 (adoptado)** | **13,8 %** | **90,0 %** | **70,5 %** | **92,0 %** | **0,51** |
| 4 | 4,4 % | 93,0 % | 36,0 % | 98,8 % | 0,46 |
| 5 | 1,2 % | 91,9 % | 12,9 % | 100,0 % | 0,21 |

Sensibilidad: de los hogares pobres según el IPM oficial, cuántos marca
el proxy. Especificidad: de los no pobres, cuántos deja fuera. La
correlación de rangos entre el puntaje del proxy (0 a 8) y el IPM oficial
es **0,76**.

### Por zona (K = 3)

| Zona | Proxy | Oficial | Concordancia | Sensibilidad | Kappa |
|---|---|---|---|---|---|
| Cabeceras | 7,5 % | 5,9 % | 93,4 % | 57,1 % | 0,47 |
| Centros poblados y rural disperso | 37,0 % | 21,5 % | 77,7 % | 84,0 % | 0,48 |

**Lectura.**
- El proxy ordena a los hogares como el IPM oficial (correlación 0,76;
  kappa 0,51, moderado) y **se acerca a su nivel sin reproducirlo**: con
  K = 3 marca como pobres al 13,8 % de los hogares, frente al 9,2 %
  oficial.
- **La diferencia que queda es rural** (37,0 % frente a 21,5 %; en las
  cabeceras, 7,5 % frente a 5,9 %). Ya no viene de vivienda, que coincide
  exactamente con la oficial, sino de las privaciones que el proxy mide
  solo sobre el jefe: la falta de cotización a pensión, casi universal en
  el campo, y el bajo logro educativo.
- **K = 3 es el mejor corte**: el mayor kappa (0,51). K = 4 da una tasa
  más baja (4,4 %) pero deja fuera a dos tercios de los pobres oficiales
  (sensibilidad 36 %).

### Cada privación frente a la oficial (base 2024)

| Privación del proxy | Oficial | Prevalencia proxy | Prevalencia oficial | Kappa |
|---|---|---|---|---|
| Analfabetismo (jefe) | Analfabetismo | 4,2 % | 7,1 % | 0,73 |
| Bajo logro educativo (jefe) | Bajo logro educativo | 31,4 % | 39,3 % | 0,70 |
| Inasistencia escolar (6-16 años) | Inasistencia escolar | 1,8 % | 1,8 % | 0,99 |
| Sin aseguramiento en salud (jefe) | Sin aseguramiento | 3,1 % | 6,0 % | 0,66 |
| Sin cotización a pensión (jefe) | Trabajo informal | 72,1 % | 70,7 % | 0,64 |
| Hacinamiento | Hacinamiento crítico | 6,1 % | 6,1 % | 1,00 |
| Sin alcantarillado | Sin alcantarillado | 9,1 % | 9,1 % | 1,00 |
| Sin acueducto | Sin acueducto | 8,6 % | 8,6 % | 1,00 |

Las tres privaciones de vivienda coinciden hogar por hogar con las
oficiales. Las otras cinco difieren por la definición, no por los datos
(son los mismos hogares y las mismas respuestas): varias privaciones
oficiales miran a todos los miembros del hogar y el proxy solo al jefe,
por lo que el proxy marca menos analfabetismo, bajo logro y falta de
aseguramiento. Las definiciones oficiales están en la metodología del IPM
(Azure, `0_raw/ipm/2024/docs_ipm/Metodologia_IPM.pdf`).

## B. ECV 2024 frente a GEIH 2024, el mismo proxy

| | ECV 2024 | GEIH 2024 |
|---|---|---|
| Hogares | 85.387 | 290.968 |
| `POBRE_GEIH` nacional | 14,2 % | 14,5 % |
| Cabeceras | 7,5 % | 8,1 % |
| Centros poblados y rural disperso | 37,5 % | 37,5 % |
| Puntaje medio (0 a 8) | 1,37 | 1,37 |

Por departamento, sobre el mismo marco:

| | Departamentos | Correlación | Diferencia media GEIH − ECV | Diferencia absoluta mediana |
|---|---|---|---|---|
| Departamento completo | 24 | 0,987 | +0,8 puntos | 1,5 puntos |
| Cabecera de la capital | 9 | 0,961 | −3,6 puntos | 4,8 puntos |

En los 9 departamentos de la Orinoquía, la Amazonía y San Andrés la GEIH
solo encuesta la cabecera de la capital; ahí la ECV se restringe a la
misma cabecera (municipio 001, `CLASE` 1). Las prevalencias de cada
privación coinciden entre las dos encuestas dentro de 1,5 puntos
(`validacion_ipm_geih_ecv_privaciones.csv`).

**Lectura.** Con las mismas reglas, la GEIH 2024 y la ECV 2024 dan el
mismo indicador: 0,3 puntos de diferencia nacional y correlación de 0,99
entre departamentos. El proxy no es un artefacto de la GEIH.

## Conclusión para el documento

1. **El proxy está validado como medida de privación** (mide lo mismo en
   la GEIH que en la ECV, la encuesta del IPM oficial) y **como
   ordenamiento** (correlación 0,76 con el IPM oficial 2024, hogar por
   hogar).
2. **No es el IPM oficial ni reproduce su tasa.** Con K = 3 marca
   13,8 % de hogares frente al 9,2 % oficial; la diferencia es rural (37,0 %
   frente a 21,5 %) y en las cabeceras queda cerca (7,5 % frente a 5,9 %).
   Debe presentarse como «índice de privaciones con 8 de los 15
   indicadores, validado contra la ECV», no como IPM.
3. Para los resultados causales esto pesa poco: con el grupo imputado el
   DML es un placebo (Proposición 1) y da cero con cualquier medida de
   resultado; las cotas de Fréchet-Manski usan solo la proporción de
   pobres por celda. Con el proxy corregido se repitieron todos los
   modelos y las conclusiones no cambian
   (`docs/seguimiento/CHANGELOG_PENDIENTES.md`, entrada 43).

## Reproducir

```bash
poetry run python -m src.validacion.validar_ipm_geih_ecv
```

Lee de Azure, en memoria: `0_raw/ipm/2024/BasesDatos-IMP-2024.zip` (IPM
2024) y seis módulos de la ECV 2024
bajo `ecv/` (`Caracteristicas_composicion_hogar`, `Educacion`,
`Salud2024`, `Fuerza_trabajo`, `Servicios_hogar`, `Datos_vivienda`). Pide
las credenciales de Azure del `.env`.
